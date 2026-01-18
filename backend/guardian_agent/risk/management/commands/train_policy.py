"""
Django management command to train PPO policy for trade approval.

Usage:
    uv run python manage.py train_policy --timesteps 500000 --eval-freq 10000
    uv run python manage.py train_policy --resume run_20250116_123456 --timesteps 100000
"""

import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Train PPO policy for trade approval decisions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timesteps",
            type=int,
            default=500000,
            help="Total training timesteps (default: 500000)",
        )
        parser.add_argument(
            "--eval-freq",
            type=int,
            default=10000,
            help="Evaluation frequency in steps (default: 10000)",
        )
        parser.add_argument(
            "--eval-episodes",
            type=int,
            default=5,
            help="Episodes per evaluation (default: 5)",
        )
        parser.add_argument(
            "--checkpoint-freq",
            type=int,
            default=50000,
            help="Checkpoint frequency in steps (default: 50000)",
        )
        parser.add_argument(
            "--resume",
            type=str,
            default=None,
            help="Resume from run ID",
        )
        parser.add_argument(
            "--data-file",
            type=str,
            default="btcusd_5m.parquet",
            help="Historical data file (default: btcusd_5m.parquet)",
        )
        parser.add_argument(
            "--learning-rate",
            type=float,
            default=3e-4,
            help="Learning rate (default: 3e-4)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=64,
            help="Batch size (default: 64)",
        )
        parser.add_argument(
            "--max-steps",
            type=int,
            default=100,
            help="Max steps per episode (default: 100)",
        )

    def handle(self, *args, **options):
        # Import here to avoid Django startup issues
        from risk.utils.rl.data_loader import DataLoader
        from risk.utils.rl.environment import TradeApprovalEnv
        from risk.utils.rl.training_history import TrainingHistoryManager
        from risk.utils.rl.policy import PolicyWrapper, create_policy

        timesteps = options["timesteps"]
        eval_freq = options["eval_freq"]
        eval_episodes = options["eval_episodes"]
        checkpoint_freq = options["checkpoint_freq"]
        resume_id = options["resume"]
        data_file = options["data_file"]
        learning_rate = options["learning_rate"]
        batch_size = options["batch_size"]
        max_steps = options["max_steps"]

        # Initialize history manager
        history = TrainingHistoryManager()

        self.stdout.write("Loading historical data...")
        try:
            data_loader = DataLoader()
            train_df, test_df = data_loader.prepare_training_data(data_file)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Loaded {len(train_df)} training and {len(test_df)} test samples"
                )
            )
        except FileNotFoundError as e:
            raise CommandError(
                f"Data file not found: {e}. "
                "Run 'python manage.py fetch_historical_data' first."
            )

        # Create environments
        self.stdout.write("Creating training environment...")
        train_env = TradeApprovalEnv(data=train_df, max_steps=max_steps)
        eval_env = TradeApprovalEnv(data=test_df, max_steps=max_steps)

        # Create or resume training run
        if resume_id:
            self.stdout.write(f"Resuming from run: {resume_id}")
            run_id = resume_id
            try:
                config = history.get_run_config(run_id)
                checkpoint_path = history.load_checkpoint(run_id)
                self.stdout.write(f"Loading checkpoint: {checkpoint_path}")

                policy = PolicyWrapper.load(checkpoint_path, env=train_env)
            except FileNotFoundError as e:
                raise CommandError(f"Could not resume: {e}")
        else:
            # New training run
            config = {
                "algorithm": "PPO",
                "total_timesteps": timesteps,
                "learning_rate": learning_rate,
                "batch_size": batch_size,
                "eval_freq": eval_freq,
                "max_steps": max_steps,
                "data_file": data_file,
            }
            run_id = history.create_run(config)
            self.stdout.write(f"Created new run: {run_id}")

            # Get tensorboard directory
            tb_log = history.get_tensorboard_dir(run_id)

            # Create policy
            policy = create_policy(
                env=train_env,
                config={
                    "learning_rate": learning_rate,
                    "batch_size": batch_size,
                },
                tensorboard_log=tb_log,
            )

        # Train
        self.stdout.write(
            self.style.SUCCESS(f"\nStarting training for {timesteps} timesteps...")
        )
        self.stdout.write(f"TensorBoard: uv run tensorboard --logdir {history.get_tensorboard_dir(run_id)}")
        self.stdout.write("")

        try:
            results = policy.train(
                total_timesteps=timesteps,
                eval_env=eval_env,
                eval_freq=eval_freq,
                n_eval_episodes=eval_episodes,
                history_manager=history,
                run_id=run_id,
                checkpoint_freq=checkpoint_freq,
            )

            # Save final model
            final_path = f"./data/models/guardian_ppo_{run_id}"
            policy.save(final_path)
            history.save_checkpoint(run_id, policy.model, timesteps)

            # Mark completed
            metrics = history.get_run_metrics(run_id)
            episodes = metrics.get("episodes", [])
            final_metrics = {}
            if episodes:
                rewards = [e["reward"] for e in episodes]
                final_metrics = {
                    "mean_reward": sum(rewards) / len(rewards),
                    "final_100_mean": sum(rewards[-100:]) / min(100, len(rewards)),
                    "total_episodes": len(episodes),
                }
            history.mark_completed(run_id, final_metrics)

            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("Training completed!"))
            self.stdout.write(f"Run ID: {run_id}")
            self.stdout.write(f"Model saved: {final_path}")
            self.stdout.write(f"\nTo view results:")
            self.stdout.write(f"  uv run python manage.py show_training --run {run_id}")
            self.stdout.write(f"  uv run python manage.py show_training --run {run_id} --plot")

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nTraining interrupted by user"))
            self.stdout.write(f"Run can be resumed with: --resume {run_id}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nTraining failed: {e}"))
            raise CommandError(str(e))
