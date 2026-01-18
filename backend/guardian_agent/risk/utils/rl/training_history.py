"""
Training History Manager

Manages training runs, checkpoints, and metrics for later viewing and resuming.

## Data Schema Documentation

This module saves RL training data in the following structure:

```
data/training_runs/
└── run_YYYYMMDD_HHMMSS/
    ├── config.json              # Training configuration & hyperparameters
    ├── metrics.json             # Episode metrics, evaluations, checkpoints
    ├── detailed_episodes.jsonl  # Detailed per-episode data (JSONL format)
    ├── checkpoints/             # Model checkpoint files (.zip)
    └── tensorboard/             # TensorBoard event logs
```

### config.json Schema
{
    "run_id": str,               # Unique identifier (e.g., "run_20250116_143022")
    "created_at": str,           # ISO timestamp of run start
    "completed_at": str | null,  # ISO timestamp of run completion
    "status": str,               # "in_progress" | "completed" | "failed"
    "algorithm": str,            # "PPO"
    "total_timesteps": int,      # Target training timesteps
    "learning_rate": float,      # Learning rate (e.g., 0.0003)
    "batch_size": int,           # Minibatch size (e.g., 64)
    "n_steps": int,              # Steps per update (e.g., 2048)
    "gamma": float,              # Discount factor (e.g., 0.99)
    "eval_freq": int,            # Evaluation frequency in steps
    "max_steps": int,            # Max steps per episode
    "data_file": str,            # Training data filename
    "final_metrics": {           # Added on completion
        "mean_reward": float,
        "final_100_mean": float,
        "total_episodes": int
    }
}

### metrics.json Schema
{
    "episodes": [                # Per-episode summary (lightweight)
        {
            "episode": int,      # Episode number (1-indexed)
            "reward": float,     # Total episode reward
            "length": int,       # Episode length in steps
            "timestep": int,     # Global timestep at episode end
            "timestamp": str     # ISO timestamp
        }
    ],
    "evaluations": [             # Periodic evaluation results
        {
            "step": int,         # Global training step
            "mean_reward": float,
            "std_reward": float,
            "min_reward": float,
            "max_reward": float,
            "num_episodes": int,
            "timestamp": str
        }
    ],
    "checkpoints": [             # Saved model checkpoints
        {
            "step": int,
            "path": str,
            "timestamp": str
        }
    ]
}

### detailed_episodes.jsonl Schema (one JSON object per line)
{
    "episode": int,              # Episode number
    "reward": float,             # Total episode reward
    "length": int,               # Episode length
    "timestep": int,             # Global timestep
    "timestamp": str,            # ISO timestamp

    # Action distribution
    "action_counts": {
        "reject": int,           # Action 0 count
        "approve_warning": int,  # Action 1 count
        "approve": int           # Action 2 count
    },
    "action_percentages": {
        "reject": float,         # Percentage (0-100)
        "approve_warning": float,
        "approve": float
    },

    # Trade outcomes
    "trade_outcomes": {
        "total_trades": int,           # Total trade decisions
        "approved_trades": int,        # Trades approved (action 1 or 2)
        "rejected_trades": int,        # Trades rejected (action 0)
        "profitable_approved": int,    # Approved trades with positive PnL
        "losing_approved": int,        # Approved trades with negative PnL
        "liquidations": int,           # Trades that got liquidated
        "good_rejections": int,        # Rejected trades that would have lost
        "missed_opportunities": int    # Rejected trades that would have profited
    },

    # Portfolio performance
    "portfolio": {
        "starting_balance": float,
        "ending_balance": float,
        "return_pct": float,           # Percentage return
        "max_drawdown": float,         # Maximum drawdown during episode
        "min_health_score": float,     # Lowest health score reached
        "final_health_score": float
    },

    # Reward breakdown
    "reward_breakdown": {
        "pnl_rewards": float,          # Sum of PnL-based rewards
        "rejection_rewards": float,    # Sum of rejection rewards
        "health_bonuses": float,       # Sum of health bonuses
        "liquidation_penalties": float # Sum of liquidation penalties
    }
}

### Extracting Data

```python
import json
import pandas as pd

# Load config
with open("data/training_runs/run_xxx/config.json") as f:
    config = json.load(f)

# Load metrics summary
with open("data/training_runs/run_xxx/metrics.json") as f:
    metrics = json.load(f)
episodes_df = pd.DataFrame(metrics["episodes"])

# Load detailed episodes (JSONL)
detailed = []
with open("data/training_runs/run_xxx/detailed_episodes.jsonl") as f:
    for line in f:
        detailed.append(json.loads(line))
detailed_df = pd.json_normalize(detailed)

# Access nested data
action_counts = detailed_df["action_counts.reject"]
portfolio_returns = detailed_df["portfolio.return_pct"]
```
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class TrainingHistoryManager:
    """
    Manages training runs, checkpoints, and metrics for later viewing.

    Directory structure:
        data/training_runs/
        └── run_<timestamp>/
            ├── config.json         # Hyperparameters and config
            ├── metrics.json        # Episode rewards, losses
            ├── checkpoints/        # Model checkpoints
            └── tensorboard/        # TensorBoard logs
    """

    def __init__(self, base_dir: str = "./data/training_runs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_run(self, config: Dict[str, Any]) -> str:
        """
        Start a new training run.

        Args:
            config: Training configuration (hyperparameters, etc.)

        Returns:
            run_id: Unique identifier for this run
        """
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "checkpoints").mkdir(exist_ok=True)
        (run_dir / "tensorboard").mkdir(exist_ok=True)

        # Save config
        full_config = {
            "run_id": run_id,
            "created_at": datetime.now().isoformat(),
            "status": "in_progress",
            **config,
        }
        with open(run_dir / "config.json", "w") as f:
            json.dump(full_config, f, indent=2)

        # Initialize metrics file
        with open(run_dir / "metrics.json", "w") as f:
            json.dump({"episodes": [], "evaluations": [], "checkpoints": []}, f)

        return run_id

    def log_episode(
        self,
        run_id: str,
        episode: int,
        reward: float,
        length: int,
        info: Optional[Dict[str, Any]] = None,
    ):
        """
        Log episode metrics.

        Args:
            run_id: Training run ID
            episode: Episode number
            reward: Total episode reward
            length: Episode length (steps)
            info: Additional info dict
        """
        metrics_path = self.base_dir / run_id / "metrics.json"
        with open(metrics_path, "r") as f:
            metrics = json.load(f)

        metrics["episodes"].append(
            {
                "episode": episode,
                "reward": float(reward),
                "length": int(length),
                "timestamp": datetime.now().isoformat(),
                **(info or {}),
            }
        )

        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

    def log_detailed_episode(
        self,
        run_id: str,
        episode: int,
        reward: float,
        length: int,
        timestep: int,
        action_counts: Dict[str, int],
        trade_outcomes: Dict[str, int],
        portfolio: Dict[str, float],
        reward_breakdown: Dict[str, float],
    ):
        """
        Log detailed episode data to JSONL file.

        This provides rich data for analysis including action distributions,
        trade outcomes, and reward breakdowns.

        Args:
            run_id: Training run ID
            episode: Episode number
            reward: Total episode reward
            length: Episode length (steps)
            timestep: Global timestep at episode end
            action_counts: Dict with keys 'reject', 'approve_warning', 'approve'
            trade_outcomes: Dict with trade outcome statistics
            portfolio: Dict with portfolio performance metrics
            reward_breakdown: Dict with reward component sums
        """
        detailed_path = self.base_dir / run_id / "detailed_episodes.jsonl"

        total_actions = sum(action_counts.values()) or 1
        action_percentages = {
            k: (v / total_actions) * 100 for k, v in action_counts.items()
        }

        entry = {
            "episode": episode,
            "reward": float(reward),
            "length": int(length),
            "timestep": int(timestep),
            "timestamp": datetime.now().isoformat(),
            "action_counts": action_counts,
            "action_percentages": action_percentages,
            "trade_outcomes": trade_outcomes,
            "portfolio": portfolio,
            "reward_breakdown": reward_breakdown,
        }

        with open(detailed_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_evaluation(
        self,
        run_id: str,
        step: int,
        mean_reward: float,
        std_reward: float,
        num_episodes: int,
        info: Optional[Dict[str, Any]] = None,
    ):
        """
        Log evaluation metrics.

        Args:
            run_id: Training run ID
            step: Training step
            mean_reward: Mean evaluation reward
            std_reward: Std of evaluation reward
            num_episodes: Number of evaluation episodes
            info: Additional info
        """
        metrics_path = self.base_dir / run_id / "metrics.json"
        with open(metrics_path, "r") as f:
            metrics = json.load(f)

        metrics["evaluations"].append(
            {
                "step": step,
                "mean_reward": float(mean_reward),
                "std_reward": float(std_reward),
                "num_episodes": num_episodes,
                "timestamp": datetime.now().isoformat(),
                **(info or {}),
            }
        )

        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

    def save_checkpoint(self, run_id: str, model: Any, step: int) -> str:
        """
        Save model checkpoint.

        Args:
            run_id: Training run ID
            model: Model to save (must have .save() method)
            step: Training step

        Returns:
            Path to saved checkpoint
        """
        checkpoint_dir = self.base_dir / run_id / "checkpoints"
        checkpoint_path = checkpoint_dir / f"model_step_{step}"
        model.save(str(checkpoint_path))

        # Log checkpoint in metrics
        metrics_path = self.base_dir / run_id / "metrics.json"
        with open(metrics_path, "r") as f:
            metrics = json.load(f)

        metrics["checkpoints"].append(
            {
                "step": step,
                "path": str(checkpoint_path),
                "timestamp": datetime.now().isoformat(),
            }
        )

        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        return str(checkpoint_path)

    def load_checkpoint(self, run_id: str, step: Optional[int] = None) -> str:
        """
        Get path to checkpoint for loading.

        Args:
            run_id: Training run ID
            step: Specific step (None for latest)

        Returns:
            Path to checkpoint file
        """
        checkpoint_dir = self.base_dir / run_id / "checkpoints"

        if step is not None:
            checkpoint_path = checkpoint_dir / f"model_step_{step}.zip"
            if not checkpoint_path.exists():
                raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
            return str(checkpoint_path)

        # Get latest checkpoint
        checkpoints = sorted(checkpoint_dir.glob("model_step_*.zip"))
        if not checkpoints:
            raise FileNotFoundError(f"No checkpoints found in {run_id}")
        return str(checkpoints[-1])

    def mark_completed(self, run_id: str, final_metrics: Optional[Dict[str, Any]] = None):
        """
        Mark a training run as completed.

        Args:
            run_id: Training run ID
            final_metrics: Optional final metrics to save
        """
        config_path = self.base_dir / run_id / "config.json"
        with open(config_path, "r") as f:
            config = json.load(f)

        config["status"] = "completed"
        config["completed_at"] = datetime.now().isoformat()
        if final_metrics:
            config["final_metrics"] = final_metrics

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def list_runs(self) -> List[Dict[str, Any]]:
        """
        List all training runs with metadata.

        Returns:
            List of run info dicts
        """
        runs = []
        for run_dir in sorted(self.base_dir.iterdir()):
            if run_dir.is_dir() and (run_dir / "config.json").exists():
                try:
                    with open(run_dir / "config.json") as f:
                        config = json.load(f)
                    with open(run_dir / "metrics.json") as f:
                        metrics = json.load(f)

                    episodes = metrics.get("episodes", [])
                    runs.append(
                        {
                            "run_id": run_dir.name,
                            "config": config,
                            "num_episodes": len(episodes),
                            "last_reward": episodes[-1]["reward"] if episodes else None,
                            "status": config.get("status", "unknown"),
                            "created_at": config.get("created_at", ""),
                        }
                    )
                except Exception as e:
                    print(f"Error loading run {run_dir.name}: {e}")

        return runs

    def get_run_config(self, run_id: str) -> Dict[str, Any]:
        """Get configuration for a run."""
        config_path = self.base_dir / run_id / "config.json"
        with open(config_path, "r") as f:
            return json.load(f)

    def get_run_metrics(self, run_id: str) -> Dict[str, Any]:
        """Get full metrics for a run."""
        metrics_path = self.base_dir / run_id / "metrics.json"
        with open(metrics_path, "r") as f:
            return json.load(f)

    def get_tensorboard_dir(self, run_id: str) -> str:
        """Get TensorBoard log directory for a run."""
        return str(self.base_dir / run_id / "tensorboard")

    def delete_run(self, run_id: str, confirm: bool = False):
        """
        Delete a training run.

        Args:
            run_id: Run to delete
            confirm: Must be True to actually delete
        """
        if not confirm:
            raise ValueError("Must set confirm=True to delete a run")

        run_dir = self.base_dir / run_id
        if run_dir.exists():
            import shutil

            shutil.rmtree(run_dir)

    def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """Get summary statistics for a run."""
        config = self.get_run_config(run_id)
        metrics = self.get_run_metrics(run_id)

        episodes = metrics.get("episodes", [])
        if not episodes:
            return {"run_id": run_id, "status": config.get("status"), "no_data": True}

        rewards = [e["reward"] for e in episodes]
        lengths = [e["length"] for e in episodes]

        return {
            "run_id": run_id,
            "status": config.get("status"),
            "algorithm": config.get("algorithm", "PPO"),
            "total_episodes": len(episodes),
            "total_timesteps": config.get("total_timesteps", sum(lengths)),
            "mean_reward": sum(rewards) / len(rewards),
            "max_reward": max(rewards),
            "min_reward": min(rewards),
            "std_reward": (sum((r - sum(rewards) / len(rewards)) ** 2 for r in rewards) / len(rewards)) ** 0.5,
            "final_100_mean": sum(rewards[-100:]) / min(100, len(rewards)),
            "created_at": config.get("created_at"),
            "completed_at": config.get("completed_at"),
        }
