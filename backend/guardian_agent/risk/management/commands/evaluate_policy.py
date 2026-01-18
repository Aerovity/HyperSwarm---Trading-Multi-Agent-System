"""
Django management command to evaluate a trained PPO policy.

Usage:
    uv run python manage.py evaluate_policy --model ./data/models/guardian_ppo_v1
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Evaluate a trained PPO policy on test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            required=True,
            help="Path to trained model",
        )
        parser.add_argument(
            "--data-file",
            type=str,
            default="btcusd_5m.parquet",
            help="Historical data file (default: btcusd_5m.parquet)",
        )
        parser.add_argument(
            "--episodes",
            type=int,
            default=100,
            help="Number of evaluation episodes (default: 100)",
        )
        parser.add_argument(
            "--max-steps",
            type=int,
            default=100,
            help="Max steps per episode (default: 100)",
        )
        parser.add_argument(
            "--compare-baseline",
            action="store_true",
            help="Compare against baseline strategies",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Output JSON file for results",
        )

    def handle(self, *args, **options):
        from risk.utils.rl.data_loader import DataLoader
        from risk.utils.rl.environment import TradeApprovalEnv
        from risk.utils.rl.policy import PolicyWrapper

        model_path = options["model"]
        data_file = options["data_file"]
        n_episodes = options["episodes"]
        max_steps = options["max_steps"]
        compare_baseline = options["compare_baseline"]
        output_path = options["output"]

        # Check model exists
        if not Path(model_path).exists() and not Path(f"{model_path}.zip").exists():
            raise CommandError(f"Model not found: {model_path}")

        # Load data
        self.stdout.write("Loading test data...")
        try:
            data_loader = DataLoader()
            _, test_df = data_loader.prepare_training_data(data_file)
            self.stdout.write(f"Loaded {len(test_df)} test samples")
        except FileNotFoundError as e:
            raise CommandError(f"Data file not found: {e}")

        # Create environment
        env = TradeApprovalEnv(data=test_df, max_steps=max_steps)

        # Load policy
        self.stdout.write(f"Loading model: {model_path}")
        try:
            policy = PolicyWrapper.load(model_path, env=env)
        except Exception as e:
            raise CommandError(f"Failed to load model: {e}")

        # Evaluate
        self.stdout.write(f"\nEvaluating over {n_episodes} episodes...")
        results = policy.evaluate(env, n_episodes=n_episodes, deterministic=True)

        # Print results
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Evaluation Results ==="))
        self.stdout.write(f"Episodes: {results['n_episodes']}")
        self.stdout.write(f"Mean Reward: {results['mean_reward']:.4f} (+/- {results['std_reward']:.4f})")
        self.stdout.write(f"Min Reward: {results['min_reward']:.4f}")
        self.stdout.write(f"Max Reward: {results['max_reward']:.4f}")
        self.stdout.write(f"Mean Episode Length: {results['mean_length']:.1f}")
        self.stdout.write("")
        self.stdout.write("Action Distribution:")
        for action, count in results['action_counts'].items():
            pct = results['action_percentages'][action]
            action_names = {0: "REJECT", 1: "APPROVE_WARNING", 2: "APPROVE"}
            self.stdout.write(f"  {action_names[action]}: {count} ({pct:.1f}%)")

        # Compare with baselines
        if compare_baseline:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("=== Baseline Comparisons ==="))

            # Random baseline
            random_results = self._evaluate_random(env, n_episodes, max_steps)
            self.stdout.write(f"\nRandom Policy:")
            self.stdout.write(f"  Mean Reward: {random_results['mean_reward']:.4f}")

            # Always approve baseline
            approve_results = self._evaluate_always_approve(env, n_episodes, max_steps)
            self.stdout.write(f"\nAlways Approve:")
            self.stdout.write(f"  Mean Reward: {approve_results['mean_reward']:.4f}")

            # Always reject baseline
            reject_results = self._evaluate_always_reject(env, n_episodes, max_steps)
            self.stdout.write(f"\nAlways Reject:")
            self.stdout.write(f"  Mean Reward: {reject_results['mean_reward']:.4f}")

            # Summary
            self.stdout.write("")
            improvement_random = (
                (results['mean_reward'] - random_results['mean_reward'])
                / abs(random_results['mean_reward']) * 100
                if random_results['mean_reward'] != 0 else 0
            )
            self.stdout.write(
                f"Improvement over random: {improvement_random:+.1f}%"
            )

            results['baselines'] = {
                'random': random_results,
                'always_approve': approve_results,
                'always_reject': reject_results,
            }

        # Save results
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            self.stdout.write(f"\nResults saved to: {output_path}")

    def _evaluate_random(self, env, n_episodes: int, max_steps: int) -> dict:
        """Evaluate random policy."""
        import numpy as np

        rewards = []
        for _ in range(n_episodes):
            obs, _ = env.reset()
            done = False
            episode_reward = 0
            steps = 0

            while not done and steps < max_steps:
                action = np.random.randint(0, 3)
                obs, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                episode_reward += reward
                steps += 1

            rewards.append(episode_reward)

        return {
            'mean_reward': float(np.mean(rewards)),
            'std_reward': float(np.std(rewards)),
        }

    def _evaluate_always_approve(self, env, n_episodes: int, max_steps: int) -> dict:
        """Evaluate always-approve policy."""
        import numpy as np

        rewards = []
        for _ in range(n_episodes):
            obs, _ = env.reset()
            done = False
            episode_reward = 0
            steps = 0

            while not done and steps < max_steps:
                action = 2  # APPROVE
                obs, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                episode_reward += reward
                steps += 1

            rewards.append(episode_reward)

        return {
            'mean_reward': float(np.mean(rewards)),
            'std_reward': float(np.std(rewards)),
        }

    def _evaluate_always_reject(self, env, n_episodes: int, max_steps: int) -> dict:
        """Evaluate always-reject policy."""
        import numpy as np

        rewards = []
        for _ in range(n_episodes):
            obs, _ = env.reset()
            done = False
            episode_reward = 0
            steps = 0

            while not done and steps < max_steps:
                action = 0  # REJECT
                obs, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                episode_reward += reward
                steps += 1

            rewards.append(episode_reward)

        return {
            'mean_reward': float(np.mean(rewards)),
            'std_reward': float(np.std(rewards)),
        }
