"""
Training Visualizer

Generate plots and reports from training history.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import pandas as pd
import numpy as np


class TrainingVisualizer:
    """Generate visualizations from training history."""

    def __init__(self, output_dir: str = "./data/visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_training_curve(
        self,
        run_id: str,
        metrics: Dict[str, Any],
        save: bool = True,
        show: bool = False,
    ) -> Optional[str]:
        """
        Plot training curves (reward, length, cumulative, distribution).

        Args:
            run_id: Training run ID
            metrics: Metrics dict from TrainingHistoryManager
            save: Whether to save the plot
            show: Whether to display the plot

        Returns:
            Path to saved plot (if save=True)
        """
        episodes = metrics.get("episodes", [])
        if not episodes:
            print(f"No episodes to plot for {run_id}")
            return None

        df = pd.DataFrame(episodes)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f"Training Run: {run_id}", fontsize=14, fontweight="bold")

        # 1. Episode Reward
        ax1 = axes[0, 0]
        ax1.plot(df["episode"], df["reward"], alpha=0.3, color="blue", label="Raw")
        if len(df) >= 100:
            ax1.plot(
                df["episode"],
                df["reward"].rolling(100).mean(),
                label="MA-100",
                linewidth=2,
                color="red",
            )
        ax1.set_xlabel("Episode")
        ax1.set_ylabel("Reward")
        ax1.set_title("Episode Reward")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Episode Length
        ax2 = axes[0, 1]
        ax2.plot(df["episode"], df["length"], alpha=0.5, color="green")
        ax2.set_xlabel("Episode")
        ax2.set_ylabel("Steps")
        ax2.set_title("Episode Length")
        ax2.grid(True, alpha=0.3)

        # 3. Cumulative Reward
        ax3 = axes[1, 0]
        cumsum = df["reward"].cumsum()
        ax3.plot(df["episode"], cumsum, color="purple")
        ax3.fill_between(df["episode"], 0, cumsum, alpha=0.3, color="purple")
        ax3.set_xlabel("Episode")
        ax3.set_ylabel("Cumulative Reward")
        ax3.set_title("Cumulative Reward")
        ax3.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
        ax3.grid(True, alpha=0.3)

        # 4. Reward Distribution
        ax4 = axes[1, 1]
        ax4.hist(df["reward"], bins=50, edgecolor="black", alpha=0.7, color="orange")
        mean_reward = df["reward"].mean()
        ax4.axvline(
            mean_reward,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {mean_reward:.2f}",
        )
        ax4.axvline(0, color="gray", linestyle=":", alpha=0.5)
        ax4.set_xlabel("Reward")
        ax4.set_ylabel("Frequency")
        ax4.set_title("Reward Distribution")
        ax4.legend()

        plt.tight_layout()

        if save:
            path = self.output_dir / f"{run_id}_training_curve.png"
            plt.savefig(path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            return str(path)

        if show:
            plt.show()

        plt.close(fig)
        return None

    def plot_evaluation_curve(
        self,
        run_id: str,
        metrics: Dict[str, Any],
        save: bool = True,
    ) -> Optional[str]:
        """Plot evaluation metrics over training."""
        evaluations = metrics.get("evaluations", [])
        if not evaluations:
            return None

        df = pd.DataFrame(evaluations)

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(df["step"], df["mean_reward"], marker="o", label="Mean Reward")
        ax.fill_between(
            df["step"],
            df["mean_reward"] - df["std_reward"],
            df["mean_reward"] + df["std_reward"],
            alpha=0.3,
        )

        ax.set_xlabel("Training Step")
        ax.set_ylabel("Evaluation Reward")
        ax.set_title(f"Evaluation Performance: {run_id}")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            path = self.output_dir / f"{run_id}_evaluation_curve.png"
            plt.savefig(path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            return str(path)

        plt.close(fig)
        return None

    def compare_runs(
        self,
        run_ids: List[str],
        metrics_list: List[Dict[str, Any]],
        save: bool = True,
    ) -> Optional[str]:
        """
        Compare multiple training runs.

        Args:
            run_ids: List of run IDs
            metrics_list: List of metrics dicts (same order as run_ids)
            save: Whether to save the plot

        Returns:
            Path to saved plot
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        colors = plt.cm.tab10(np.linspace(0, 1, len(run_ids)))

        # 1. Learning curves comparison
        ax1 = axes[0]
        for i, (run_id, metrics) in enumerate(zip(run_ids, metrics_list)):
            episodes = metrics.get("episodes", [])
            if episodes:
                df = pd.DataFrame(episodes)
                if len(df) >= 100:
                    smoothed = df["reward"].rolling(100).mean()
                    ax1.plot(df["episode"], smoothed, label=run_id, color=colors[i])

        ax1.set_xlabel("Episode")
        ax1.set_ylabel("Reward (MA-100)")
        ax1.set_title("Learning Curves Comparison")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Final performance comparison
        ax2 = axes[1]
        final_rewards = []
        for metrics in metrics_list:
            episodes = metrics.get("episodes", [])
            if episodes:
                rewards = [e["reward"] for e in episodes[-100:]]
                final_rewards.append(sum(rewards) / len(rewards))
            else:
                final_rewards.append(0)

        bars = ax2.bar(run_ids, final_rewards, color=colors)
        ax2.set_xlabel("Run ID")
        ax2.set_ylabel("Final 100-Episode Mean Reward")
        ax2.set_title("Final Performance Comparison")
        ax2.tick_params(axis="x", rotation=45)

        for bar, val in zip(bars, final_rewards):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:.2f}",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()

        if save:
            path = self.output_dir / "runs_comparison.png"
            plt.savefig(path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            return str(path)

        plt.close(fig)
        return None

    def generate_report(
        self,
        run_id: str,
        metrics: Dict[str, Any],
        config: Dict[str, Any],
    ) -> str:
        """
        Generate markdown report for a training run.

        Args:
            run_id: Training run ID
            metrics: Metrics dict
            config: Configuration dict

        Returns:
            Path to saved report
        """
        episodes = metrics.get("episodes", [])
        if not episodes:
            report = f"# Training Report: {run_id}\n\nNo episode data available.\n"
        else:
            df = pd.DataFrame(episodes)

            # Calculate stats
            mean_reward = df["reward"].mean()
            max_reward = df["reward"].max()
            min_reward = df["reward"].min()
            std_reward = df["reward"].std()
            first_100_mean = df["reward"].head(100).mean() if len(df) >= 100 else df["reward"].mean()
            last_100_mean = df["reward"].tail(100).mean()

            improvement = 0
            if abs(first_100_mean) > 0.0001:
                improvement = ((last_100_mean - first_100_mean) / abs(first_100_mean)) * 100

            report = f"""# Training Report: {run_id}

## Configuration
- **Algorithm**: {config.get('algorithm', 'PPO')}
- **Total Timesteps**: {config.get('total_timesteps', 'N/A')}
- **Learning Rate**: {config.get('learning_rate', 'N/A')}
- **Batch Size**: {config.get('batch_size', 'N/A')}
- **Created**: {config.get('created_at', 'N/A')}
- **Status**: {config.get('status', 'unknown')}

## Results Summary

| Metric | Value |
|--------|-------|
| Total Episodes | {len(episodes)} |
| Mean Reward | {mean_reward:.4f} |
| Max Reward | {max_reward:.4f} |
| Min Reward | {min_reward:.4f} |
| Std Reward | {std_reward:.4f} |
| Final 100-ep Mean | {last_100_mean:.4f} |

## Training Progress

- **First 100 episodes avg**: {first_100_mean:.4f}
- **Last 100 episodes avg**: {last_100_mean:.4f}
- **Improvement**: {improvement:+.1f}%

## Visualizations

![Training Curve](./{run_id}_training_curve.png)
"""

            # Add evaluation section if available
            evaluations = metrics.get("evaluations", [])
            if evaluations:
                eval_df = pd.DataFrame(evaluations)
                report += f"""
## Evaluation Results

| Step | Mean Reward | Std Reward |
|------|-------------|------------|
"""
                for _, row in eval_df.iterrows():
                    report += f"| {row['step']} | {row['mean_reward']:.4f} | {row['std_reward']:.4f} |\n"

                report += f"\n![Evaluation Curve](./{run_id}_evaluation_curve.png)\n"

        # Save report
        report_path = self.output_dir / f"{run_id}_report.md"
        with open(report_path, "w") as f:
            f.write(report)

        return str(report_path)

    def plot_action_distribution(
        self,
        run_id: str,
        action_counts: Dict[int, int],
        save: bool = True,
    ) -> Optional[str]:
        """Plot distribution of actions taken."""
        fig, ax = plt.subplots(figsize=(8, 6))

        actions = ["REJECT", "APPROVE_WARNING", "APPROVE"]
        counts = [action_counts.get(i, 0) for i in range(3)]

        colors = ["red", "orange", "green"]
        bars = ax.bar(actions, counts, color=colors, edgecolor="black")

        ax.set_xlabel("Action")
        ax.set_ylabel("Count")
        ax.set_title(f"Action Distribution: {run_id}")

        total = sum(counts)
        for bar, count in zip(bars, counts):
            pct = count / total * 100 if total > 0 else 0
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{count}\n({pct:.1f}%)",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()

        if save:
            path = self.output_dir / f"{run_id}_action_distribution.png"
            plt.savefig(path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            return str(path)

        plt.close(fig)
        return None
