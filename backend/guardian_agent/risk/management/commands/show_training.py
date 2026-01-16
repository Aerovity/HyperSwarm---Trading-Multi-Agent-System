"""
Django management command to view and visualize training runs.

Usage:
    uv run python manage.py show_training --list
    uv run python manage.py show_training --run run_20250116_123456
    uv run python manage.py show_training --run run_20250116_123456 --plot
    uv run python manage.py show_training --run run_20250116_123456 --report
"""

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "View and visualize training runs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--list",
            action="store_true",
            help="List all training runs",
        )
        parser.add_argument(
            "--run",
            type=str,
            default=None,
            help="Show specific run by ID",
        )
        parser.add_argument(
            "--plot",
            action="store_true",
            help="Generate plots for the run",
        )
        parser.add_argument(
            "--report",
            action="store_true",
            help="Generate markdown report",
        )
        parser.add_argument(
            "--compare",
            nargs="+",
            default=None,
            help="Compare multiple runs",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete the specified run",
        )

    def handle(self, *args, **options):
        from risk.utils.rl.training_history import TrainingHistoryManager
        from risk.utils.rl.visualizer import TrainingVisualizer

        history = TrainingHistoryManager()
        visualizer = TrainingVisualizer()

        if options["list"]:
            self._list_runs(history)

        elif options["compare"]:
            self._compare_runs(history, visualizer, options["compare"])

        elif options["run"]:
            run_id = options["run"]

            if options["delete"]:
                self._delete_run(history, run_id)
            else:
                self._show_run(history, visualizer, run_id, options)

        else:
            self.stdout.write("Use --list to see all runs or --run <id> to see a specific run")

    def _list_runs(self, history):
        """List all training runs."""
        runs = history.list_runs()

        if not runs:
            self.stdout.write(self.style.WARNING("No training runs found."))
            self.stdout.write("Start training with: uv run python manage.py train_policy")
            return

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Training Runs ==="))
        self.stdout.write("")

        for run in runs:
            status_color = {
                "completed": self.style.SUCCESS,
                "in_progress": self.style.WARNING,
                "failed": self.style.ERROR,
            }.get(run["status"], lambda x: x)

            last_reward = f"{run['last_reward']:.2f}" if run['last_reward'] is not None else "N/A"

            self.stdout.write(
                f"  {run['run_id']}  |  "
                f"Episodes: {run['num_episodes']:>5}  |  "
                f"Last Reward: {last_reward:>8}  |  "
                f"Status: {status_color(run['status'])}"
            )

        self.stdout.write("")
        self.stdout.write(f"Total: {len(runs)} runs")

    def _show_run(self, history, visualizer, run_id: str, options: dict):
        """Show details for a specific run."""
        try:
            config = history.get_run_config(run_id)
            metrics = history.get_run_metrics(run_id)
        except FileNotFoundError:
            raise CommandError(f"Run not found: {run_id}")

        # Generate plots if requested
        if options["plot"]:
            self.stdout.write("Generating plots...")
            path = visualizer.plot_training_curve(run_id, metrics)
            if path:
                self.stdout.write(self.style.SUCCESS(f"Training curve saved: {path}"))

            path = visualizer.plot_evaluation_curve(run_id, metrics)
            if path:
                self.stdout.write(self.style.SUCCESS(f"Evaluation curve saved: {path}"))

        # Generate report if requested
        if options["report"]:
            self.stdout.write("Generating report...")
            # Also generate plots for the report
            visualizer.plot_training_curve(run_id, metrics)
            visualizer.plot_evaluation_curve(run_id, metrics)

            path = visualizer.generate_report(run_id, metrics, config)
            self.stdout.write(self.style.SUCCESS(f"Report saved: {path}"))

        # Always print summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"=== Run: {run_id} ==="))
        self.stdout.write("")

        # Config
        self.stdout.write("Configuration:")
        self.stdout.write(f"  Algorithm: {config.get('algorithm', 'PPO')}")
        self.stdout.write(f"  Total Timesteps: {config.get('total_timesteps', 'N/A')}")
        self.stdout.write(f"  Learning Rate: {config.get('learning_rate', 'N/A')}")
        self.stdout.write(f"  Batch Size: {config.get('batch_size', 'N/A')}")
        self.stdout.write(f"  Created: {config.get('created_at', 'N/A')}")
        self.stdout.write(f"  Status: {config.get('status', 'unknown')}")

        # Metrics
        episodes = metrics.get("episodes", [])
        if episodes:
            rewards = [e["reward"] for e in episodes]

            self.stdout.write("")
            self.stdout.write("Results:")
            self.stdout.write(f"  Total Episodes: {len(episodes)}")
            self.stdout.write(f"  Mean Reward: {sum(rewards) / len(rewards):.4f}")
            self.stdout.write(f"  Max Reward: {max(rewards):.4f}")
            self.stdout.write(f"  Min Reward: {min(rewards):.4f}")

            if len(rewards) >= 100:
                first_100 = sum(rewards[:100]) / 100
                last_100 = sum(rewards[-100:]) / 100
                improvement = ((last_100 - first_100) / abs(first_100)) * 100 if first_100 != 0 else 0

                self.stdout.write(f"  First 100 avg: {first_100:.4f}")
                self.stdout.write(f"  Last 100 avg: {last_100:.4f}")
                self.stdout.write(f"  Improvement: {improvement:+.1f}%")
        else:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("No episode data available."))

        # Checkpoints
        checkpoints = metrics.get("checkpoints", [])
        if checkpoints:
            self.stdout.write("")
            self.stdout.write(f"Checkpoints: {len(checkpoints)}")
            latest = checkpoints[-1]
            self.stdout.write(f"  Latest: step {latest['step']} ({latest['path']})")

        # TensorBoard hint
        self.stdout.write("")
        self.stdout.write("TensorBoard:")
        tb_dir = history.get_tensorboard_dir(run_id)
        self.stdout.write(f"  uv run tensorboard --logdir {tb_dir}")

    def _compare_runs(self, history, visualizer, run_ids: list):
        """Compare multiple training runs."""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Comparing Runs ==="))
        self.stdout.write("")

        metrics_list = []
        for run_id in run_ids:
            try:
                metrics = history.get_run_metrics(run_id)
                metrics_list.append(metrics)

                episodes = metrics.get("episodes", [])
                if episodes:
                    rewards = [e["reward"] for e in episodes]
                    last_100 = sum(rewards[-100:]) / min(100, len(rewards))
                    self.stdout.write(
                        f"  {run_id}: {len(episodes)} episodes, final_100_mean={last_100:.4f}"
                    )
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f"  {run_id}: NOT FOUND"))
                metrics_list.append({"episodes": []})

        # Generate comparison plot
        if len(metrics_list) >= 2:
            self.stdout.write("")
            self.stdout.write("Generating comparison plot...")
            path = visualizer.compare_runs(run_ids, metrics_list)
            if path:
                self.stdout.write(self.style.SUCCESS(f"Comparison saved: {path}"))

    def _delete_run(self, history, run_id: str):
        """Delete a training run."""
        try:
            history.get_run_config(run_id)  # Check exists
        except FileNotFoundError:
            raise CommandError(f"Run not found: {run_id}")

        confirm = input(f"Are you sure you want to delete {run_id}? [y/N]: ")
        if confirm.lower() == 'y':
            history.delete_run(run_id, confirm=True)
            self.stdout.write(self.style.SUCCESS(f"Deleted: {run_id}"))
        else:
            self.stdout.write("Cancelled.")
