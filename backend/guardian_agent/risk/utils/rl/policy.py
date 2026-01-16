"""
Policy Wrapper for PPO

Wraps Stable-Baselines3 PPO for the trade approval task.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import (
        BaseCallback,
        EvalCallback,
        CheckpointCallback,
    )
    from stable_baselines3.common.vec_env import DummyVecEnv

    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    PPO = None


class TrainingCallback(BaseCallback):
    """
    Custom callback for logging training metrics to TrainingHistoryManager.

    Logs both lightweight episode summaries (metrics.json) and detailed
    episode data (detailed_episodes.jsonl) including action distributions,
    trade outcomes, and reward breakdowns.
    """

    def __init__(self, history_manager, run_id: str, verbose: int = 0):
        super().__init__(verbose)
        self.history_manager = history_manager
        self.run_id = run_id
        self.episode_rewards = []
        self.episode_lengths = []
        self.episode_count = 0

    def _on_step(self) -> bool:
        # Check for episode completion
        if "episode" in self.locals.get("infos", [{}])[0]:
            info = self.locals["infos"][0]
            ep_reward = info.get("episode", {}).get("r", 0)
            ep_length = info.get("episode", {}).get("l", 0)

            self.episode_count += 1
            self.episode_rewards.append(ep_reward)
            self.episode_lengths.append(ep_length)

            # Log lightweight episode summary
            self.history_manager.log_episode(
                run_id=self.run_id,
                episode=self.episode_count,
                reward=float(ep_reward),
                length=int(ep_length),
                info={"timestep": self.num_timesteps},
            )

            # Log detailed episode data if environment supports it
            try:
                env = self.training_env.envs[0]
                if hasattr(env, "get_detailed_episode_stats"):
                    detailed_stats = env.get_detailed_episode_stats()
                    if detailed_stats:
                        self.history_manager.log_detailed_episode(
                            run_id=self.run_id,
                            episode=self.episode_count,
                            reward=float(ep_reward),
                            length=int(ep_length),
                            timestep=self.num_timesteps,
                            action_counts=detailed_stats["action_counts"],
                            trade_outcomes=detailed_stats["trade_outcomes"],
                            portfolio=detailed_stats["portfolio"],
                            reward_breakdown=detailed_stats["reward_breakdown"],
                        )
            except (AttributeError, IndexError, KeyError):
                # Environment doesn't support detailed stats or not available
                pass

        return True


class PolicyWrapper:
    """
    Wrapper for PPO policy with training and inference methods.
    """

    def __init__(
        self,
        env,
        learning_rate: float = 3e-4,
        n_steps: int = 2048,
        batch_size: int = 64,
        n_epochs: int = 10,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_range: float = 0.2,
        ent_coef: float = 0.01,
        tensorboard_log: Optional[str] = None,
        verbose: int = 1,
        device: str = "auto",
    ):
        """
        Initialize PPO policy.

        Args:
            env: Gymnasium environment
            learning_rate: Learning rate
            n_steps: Steps per update
            batch_size: Minibatch size
            n_epochs: Epochs per update
            gamma: Discount factor
            gae_lambda: GAE lambda
            clip_range: PPO clip range
            ent_coef: Entropy coefficient
            tensorboard_log: TensorBoard log directory
            verbose: Verbosity level
            device: Device to use ("auto", "cpu", "cuda")
        """
        if not SB3_AVAILABLE:
            raise ImportError(
                "stable-baselines3 is not installed. "
                "Run: uv add stable-baselines3"
            )

        self.env = env
        self.config = {
            "learning_rate": learning_rate,
            "n_steps": n_steps,
            "batch_size": batch_size,
            "n_epochs": n_epochs,
            "gamma": gamma,
            "gae_lambda": gae_lambda,
            "clip_range": clip_range,
            "ent_coef": ent_coef,
        }

        # Wrap environment in VecEnv if needed
        if not hasattr(env, "num_envs"):
            env = DummyVecEnv([lambda e=env: e])

        self.model = PPO(
            "MlpPolicy",
            env,
            learning_rate=learning_rate,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            gamma=gamma,
            gae_lambda=gae_lambda,
            clip_range=clip_range,
            ent_coef=ent_coef,
            verbose=verbose,
            tensorboard_log=tensorboard_log,
            device=device,
        )

    def train(
        self,
        total_timesteps: int = 500000,
        eval_env=None,
        eval_freq: int = 10000,
        n_eval_episodes: int = 5,
        history_manager=None,
        run_id: Optional[str] = None,
        checkpoint_freq: int = 50000,
        log_dir: str = "./data/models",
    ) -> Dict[str, Any]:
        """
        Train the policy.

        Args:
            total_timesteps: Total training timesteps
            eval_env: Evaluation environment
            eval_freq: Evaluation frequency (steps)
            n_eval_episodes: Episodes per evaluation
            history_manager: TrainingHistoryManager for logging
            run_id: Training run ID
            checkpoint_freq: Checkpoint frequency (steps)
            log_dir: Directory for saving checkpoints

        Returns:
            Training results dict
        """
        callbacks = []

        # Training callback for logging
        if history_manager and run_id:
            callbacks.append(TrainingCallback(history_manager, run_id))

        # Evaluation callback
        if eval_env is not None:
            if not hasattr(eval_env, "num_envs"):
                eval_env = DummyVecEnv([lambda e=eval_env: e])

            eval_callback = EvalCallback(
                eval_env,
                best_model_save_path=f"{log_dir}/best_model",
                log_path=f"{log_dir}/eval_logs",
                eval_freq=eval_freq,
                n_eval_episodes=n_eval_episodes,
                deterministic=True,
            )
            callbacks.append(eval_callback)

        # Checkpoint callback
        checkpoint_callback = CheckpointCallback(
            save_freq=checkpoint_freq,
            save_path=f"{log_dir}/checkpoints",
            name_prefix="ppo_guardian",
        )
        callbacks.append(checkpoint_callback)

        # Train
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks if callbacks else None,
            progress_bar=True,
        )

        return {
            "total_timesteps": total_timesteps,
            "final_model": self.model,
        }

    def predict(
        self, observation: np.ndarray, deterministic: bool = True
    ) -> Tuple[int, float]:
        """
        Get action for observation.

        Args:
            observation: State observation
            deterministic: Whether to use deterministic policy

        Returns:
            Tuple of (action, value estimate)
        """
        action, _states = self.model.predict(observation, deterministic=deterministic)
        return int(action), 0.0  # Value not directly available in simple predict

    def predict_with_probs(
        self, observation: np.ndarray
    ) -> Tuple[int, np.ndarray, float]:
        """
        Get action with action probabilities.

        Args:
            observation: State observation

        Returns:
            Tuple of (action, action_probs, value)
        """
        obs_tensor = self.model.policy.obs_to_tensor(observation)[0]
        with self.model.policy.no_grad():
            distribution = self.model.policy.get_distribution(obs_tensor)
            value = self.model.policy.predict_values(obs_tensor)

        probs = distribution.distribution.probs.cpu().numpy()[0]
        action = int(np.argmax(probs))

        return action, probs, float(value.cpu().numpy()[0])

    def save(self, path: str):
        """Save the model."""
        self.model.save(path)

    @classmethod
    def load(cls, path: str, env=None) -> "PolicyWrapper":
        """
        Load a saved model.

        Args:
            path: Path to saved model
            env: Environment (optional)

        Returns:
            PolicyWrapper instance
        """
        if not SB3_AVAILABLE:
            raise ImportError("stable-baselines3 is not installed")

        instance = object.__new__(cls)
        instance.model = PPO.load(path, env=env)
        instance.env = env
        instance.config = {}
        return instance

    def evaluate(
        self,
        env,
        n_episodes: int = 10,
        deterministic: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluate the policy.

        Args:
            env: Environment to evaluate on
            n_episodes: Number of episodes
            deterministic: Whether to use deterministic policy

        Returns:
            Evaluation results
        """
        episode_rewards = []
        episode_lengths = []
        action_counts = {0: 0, 1: 0, 2: 0}

        for _ in range(n_episodes):
            obs, _ = env.reset()
            done = False
            episode_reward = 0
            episode_length = 0

            while not done:
                action, _ = self.model.predict(obs, deterministic=deterministic)
                action = int(action)
                action_counts[action] = action_counts.get(action, 0) + 1

                obs, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                episode_reward += reward
                episode_length += 1

            episode_rewards.append(episode_reward)
            episode_lengths.append(episode_length)

        return {
            "n_episodes": n_episodes,
            "mean_reward": float(np.mean(episode_rewards)),
            "std_reward": float(np.std(episode_rewards)),
            "min_reward": float(np.min(episode_rewards)),
            "max_reward": float(np.max(episode_rewards)),
            "mean_length": float(np.mean(episode_lengths)),
            "action_counts": action_counts,
            "action_percentages": {
                k: v / sum(action_counts.values()) * 100
                for k, v in action_counts.items()
            },
        }

    def get_config(self) -> Dict[str, Any]:
        """Get training configuration."""
        return self.config.copy()


def create_policy(
    env,
    config: Optional[Dict[str, Any]] = None,
    tensorboard_log: Optional[str] = None,
) -> PolicyWrapper:
    """
    Factory function to create a policy.

    Args:
        env: Gymnasium environment
        config: Optional config dict
        tensorboard_log: TensorBoard log directory

    Returns:
        PolicyWrapper instance
    """
    default_config = {
        "learning_rate": 3e-4,
        "n_steps": 2048,
        "batch_size": 64,
        "n_epochs": 10,
        "gamma": 0.99,
        "gae_lambda": 0.95,
        "clip_range": 0.2,
        "ent_coef": 0.01,
    }

    if config:
        default_config.update(config)

    return PolicyWrapper(
        env=env,
        tensorboard_log=tensorboard_log,
        **default_config,
    )
