"""
Gymnasium Environment for Trade Approval

Custom environment for training RL agents on trade approval decisions.
"""

from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces

from .data_loader import DataLoader
from .state_encoder import StateEncoder
from .reward_calculator import RewardCalculator, TradeOutcome


class TradeApprovalEnv(gym.Env):
    """
    RL environment for trade approval decisions.

    The agent receives trade proposals and must decide whether to approve/reject
    based on portfolio state and market conditions.

    Action Space:
        Discrete(3):
        - 0: REJECT (high risk)
        - 1: APPROVE_WITH_WARNING (medium risk)
        - 2: APPROVE (low risk)

    Observation Space:
        Box(24,): Continuous features representing:
        - Portfolio state (6 features)
        - Trade proposal (4 features)
        - Market conditions (14 features)

    Episode:
        - Starts at a random point in training data
        - Each step presents a new trade proposal
        - Episode ends after max_steps or end of data window
    """

    metadata = {"render_modes": ["human", "ansi"]}

    def __init__(
        self,
        data: Optional[pd.DataFrame] = None,
        max_steps: int = 100,
        hold_periods: int = 12,  # 1 hour for 5min data
        initial_balance: float = 10000.0,
        max_leverage: float = 3.0,
        render_mode: Optional[str] = None,
    ):
        """
        Initialize the trade approval environment.

        Args:
            data: Preprocessed DataFrame with OHLCV and indicators
            max_steps: Maximum steps per episode
            hold_periods: Number of periods to hold trades for outcome simulation
            initial_balance: Starting account balance
            max_leverage: Maximum leverage allowed
            render_mode: Rendering mode ("human" or "ansi")
        """
        super().__init__()

        self.data = data
        self.max_steps = max_steps
        self.hold_periods = hold_periods
        self.initial_balance = initial_balance
        self.max_leverage = max_leverage
        self.render_mode = render_mode

        # Initialize components
        self.state_encoder = StateEncoder()
        self.reward_calculator = RewardCalculator()
        self.data_loader = DataLoader()

        # Action and observation spaces
        self.action_space = spaces.Discrete(3)

        low, high = self.state_encoder.get_observation_space_bounds()
        self.observation_space = spaces.Box(
            low=low, high=high, dtype=np.float32
        )

        # Episode state
        self.current_step = 0
        self.current_idx = 0
        self.balance = initial_balance
        self.num_positions = 0
        self.episode_rewards = []
        self.episode_trades = []

        # Portfolio state tracking
        self.portfolio_state = self._get_initial_portfolio_state()

        # Detailed tracking for logging
        self._reset_detailed_tracking()

    def _reset_detailed_tracking(self):
        """Reset detailed tracking for a new episode."""
        self._action_counts = {"reject": 0, "approve_warning": 0, "approve": 0}
        self._trade_outcomes = {
            "total_trades": 0,
            "approved_trades": 0,
            "rejected_trades": 0,
            "profitable_approved": 0,
            "losing_approved": 0,
            "liquidations": 0,
            "good_rejections": 0,
            "missed_opportunities": 0,
        }
        self._portfolio_tracking = {
            "starting_balance": self.initial_balance,
            "min_balance": self.initial_balance,
            "max_balance": self.initial_balance,
            "min_health_score": 100.0,
        }
        self._reward_breakdown = {
            "pnl_rewards": 0.0,
            "rejection_rewards": 0.0,
            "health_bonuses": 0.0,
            "liquidation_penalties": 0.0,
        }

    def _get_initial_portfolio_state(self) -> Dict[str, Any]:
        """Get initial portfolio state."""
        return {
            "account_value": self.initial_balance,
            "current_leverage": 0.0,
            "margin_usage": 0.0,
            "num_positions": 0,
            "liquidation_distance": 1.0,
            "health_score": 100.0,
        }

    def _generate_trade_proposal(self) -> Dict[str, Any]:
        """Generate a trade proposal based on current market conditions."""
        if self.data is None or self.current_idx >= len(self.data):
            return self._get_dummy_proposal()

        row = self.data.iloc[self.current_idx]

        # Generate proposal based on market signals
        rsi = row.get("rsi_14", 50)
        macd_diff = row.get("macd_diff", 0)
        momentum = row.get("momentum_1h", 0)

        # Simple signal: combine indicators
        signal_strength = abs(macd_diff) * 10 + abs(momentum) * 5
        confidence = min(0.9, 0.3 + signal_strength * 0.1)

        # Z-score from BB position
        z_score = row.get("bb_position", 0)

        # Size based on confidence
        base_size = self.balance * 0.1
        size = base_size * (0.5 + confidence)

        # Leverage based on volatility (lower vol = higher leverage ok)
        atr = row.get("atr_normalized", 0.02)
        leverage = min(self.max_leverage, max(1.0, 2.0 - atr * 50))

        # Direction based on signals
        direction = "long" if macd_diff > 0 and momentum > 0 else "short"

        return {
            "size": size,
            "leverage": leverage,
            "confidence": confidence,
            "z_score": z_score,
            "direction": direction,
            "account_value": self.balance,
            "symbol": "BTC/USD",
        }

    def _get_dummy_proposal(self) -> Dict[str, Any]:
        """Get a dummy proposal when no data is available."""
        return {
            "size": self.balance * 0.1,
            "leverage": 1.0,
            "confidence": 0.5,
            "z_score": 0.0,
            "direction": "long",
            "account_value": self.balance,
            "symbol": "BTC/USD",
        }

    def _get_observation(self) -> np.ndarray:
        """Get current observation (state)."""
        if self.data is None or self.current_idx >= len(self.data):
            return self.state_encoder.create_dummy_state()

        market_data = self.data.iloc[self.current_idx]
        trade_proposal = self._generate_trade_proposal()

        return self.state_encoder.encode(
            self.portfolio_state, trade_proposal, market_data, already_normalized=True
        )

    def _simulate_outcome(self, action: int) -> TradeOutcome:
        """Simulate trade outcome based on action and future price data."""
        if self.data is None:
            # Return neutral outcome
            return TradeOutcome(
                pnl=0.0,
                max_drawdown=0.0,
                was_liquidated=False,
                was_stopped=False,
                hit_take_profit=False,
                hold_periods=0,
            )

        proposal = self._generate_trade_proposal()

        # If rejected, simulate what would have happened
        outcome_dict = self.data_loader.simulate_trade_outcome(
            df=self.data,
            entry_idx=self.current_idx,
            direction=proposal["direction"],
            leverage=proposal["leverage"],
            hold_periods=self.hold_periods,
        )

        return TradeOutcome(
            pnl=outcome_dict["pnl"],
            max_drawdown=outcome_dict["max_drawdown"],
            was_liquidated=outcome_dict["was_liquidated"],
            was_stopped=outcome_dict["was_stopped"],
            hit_take_profit=outcome_dict["hit_take_profit"],
            hold_periods=outcome_dict["hold_periods"],
        )

    def _update_portfolio(self, action: int, outcome: TradeOutcome):
        """Update portfolio state based on action and outcome."""
        if action in [1, 2]:  # Approved
            # Update balance based on outcome (if approved)
            if not outcome.was_liquidated:
                pnl_amount = self.balance * outcome.pnl * 0.1  # Position was 10%
                self.balance += pnl_amount
            else:
                # Lost the position value
                self.balance *= 0.9  # Lose 10%

        # Update portfolio state
        self.portfolio_state = {
            "account_value": self.balance,
            "current_leverage": 0.0,  # Simplified: no open positions tracking
            "margin_usage": 0.0,
            "num_positions": 0,
            "liquidation_distance": 1.0,
            "health_score": min(100, max(0, self.balance / self.initial_balance * 100)),
        }

    def _update_detailed_tracking(self, action: int, outcome, reward_breakdown: Dict[str, float]):
        """Update detailed tracking after each step."""
        # Track action counts
        action_names = {0: "reject", 1: "approve_warning", 2: "approve"}
        self._action_counts[action_names[action]] += 1

        # Track trade outcomes
        self._trade_outcomes["total_trades"] += 1

        if action == 0:  # Reject
            self._trade_outcomes["rejected_trades"] += 1
            if outcome.pnl < 0 or outcome.was_liquidated:
                self._trade_outcomes["good_rejections"] += 1
            elif outcome.pnl > 0:
                self._trade_outcomes["missed_opportunities"] += 1
        else:  # Approved (action 1 or 2)
            self._trade_outcomes["approved_trades"] += 1
            if outcome.was_liquidated:
                self._trade_outcomes["liquidations"] += 1
            elif outcome.pnl > 0:
                self._trade_outcomes["profitable_approved"] += 1
            else:
                self._trade_outcomes["losing_approved"] += 1

        # Track portfolio performance
        self._portfolio_tracking["min_balance"] = min(
            self._portfolio_tracking["min_balance"], self.balance
        )
        self._portfolio_tracking["max_balance"] = max(
            self._portfolio_tracking["max_balance"], self.balance
        )
        self._portfolio_tracking["min_health_score"] = min(
            self._portfolio_tracking["min_health_score"],
            self.portfolio_state["health_score"]
        )

        # Track reward breakdown
        if reward_breakdown.get("pnl_component", 0) != 0:
            self._reward_breakdown["pnl_rewards"] += reward_breakdown.get("pnl_component", 0)
        if reward_breakdown.get("good_rejection_bonus", 0) != 0:
            self._reward_breakdown["rejection_rewards"] += reward_breakdown.get("good_rejection_bonus", 0)
        if reward_breakdown.get("health_bonus", 0) != 0:
            self._reward_breakdown["health_bonuses"] += reward_breakdown.get("health_bonus", 0)
        if reward_breakdown.get("liquidation_penalty", 0) != 0:
            self._reward_breakdown["liquidation_penalties"] += reward_breakdown.get("liquidation_penalty", 0)

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset the environment to start a new episode.

        Args:
            seed: Random seed
            options: Additional options (can include "start_idx")

        Returns:
            Tuple of (observation, info)
        """
        super().reset(seed=seed)

        # Reset state
        self.current_step = 0
        self.balance = self.initial_balance
        self.num_positions = 0
        self.episode_rewards = []
        self.episode_trades = []
        self.portfolio_state = self._get_initial_portfolio_state()
        self._reset_detailed_tracking()

        # Set starting index
        if options and "start_idx" in options:
            self.current_idx = options["start_idx"]
        elif self.data is not None:
            # Random start, leaving room for episode and hold period
            max_start = len(self.data) - self.max_steps - self.hold_periods - 1
            self.current_idx = self.np_random.integers(0, max(1, max_start))
        else:
            self.current_idx = 0

        observation = self._get_observation()
        info = {
            "start_idx": self.current_idx,
            "balance": self.balance,
        }

        return observation, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Take a step in the environment.

        Args:
            action: The action to take (0=REJECT, 1=APPROVE_WARNING, 2=APPROVE)

        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        # Simulate outcome
        outcome = self._simulate_outcome(action)

        # Calculate reward
        portfolio_health = self.portfolio_state["health_score"] / 100.0
        reward = self.reward_calculator.calculate_reward(action, outcome, portfolio_health)

        # Get reward breakdown for detailed tracking
        reward_breakdown = self.reward_calculator.get_reward_breakdown(action, outcome, portfolio_health)

        # Update portfolio
        self._update_portfolio(action, outcome)

        # Track episode data
        self.episode_rewards.append(reward)
        self.episode_trades.append({
            "step": self.current_step,
            "action": action,
            "outcome_pnl": outcome.pnl,
            "reward": reward,
        })

        # Update detailed tracking
        self._update_detailed_tracking(action, outcome, reward_breakdown)

        # Move to next step
        self.current_step += 1
        self.current_idx += 1

        # Check termination
        terminated = False
        truncated = False

        if self.balance <= self.initial_balance * 0.1:
            # Account blown - terminate
            terminated = True
        elif self.data is not None and self.current_idx >= len(self.data) - self.hold_periods:
            # End of data
            truncated = True
        elif self.current_step >= self.max_steps:
            # Max steps reached
            truncated = True

        observation = self._get_observation()

        info = {
            "step": self.current_step,
            "balance": self.balance,
            "action": action,
            "outcome": {
                "pnl": outcome.pnl,
                "max_drawdown": outcome.max_drawdown,
                "was_liquidated": outcome.was_liquidated,
            },
            "reward": reward,
            "episode_return": sum(self.episode_rewards),
        }

        return observation, reward, terminated, truncated, info

    def render(self) -> Optional[str]:
        """Render the environment."""
        if self.render_mode == "human" or self.render_mode == "ansi":
            output = (
                f"Step: {self.current_step}/{self.max_steps} | "
                f"Balance: ${self.balance:.2f} | "
                f"Health: {self.portfolio_state['health_score']:.1f}% | "
                f"Episode Return: {sum(self.episode_rewards):.3f}"
            )
            if self.render_mode == "human":
                print(output)
            return output
        return None

    def close(self):
        """Clean up resources."""
        pass

    def set_data(self, data: pd.DataFrame):
        """Set the data for the environment."""
        self.data = data

    def get_episode_stats(self) -> Dict[str, Any]:
        """Get statistics for the current episode."""
        if not self.episode_trades:
            return {}

        actions = [t["action"] for t in self.episode_trades]
        rewards = [t["reward"] for t in self.episode_trades]
        pnls = [t["outcome_pnl"] for t in self.episode_trades]

        return {
            "num_trades": len(self.episode_trades),
            "num_approved": sum(1 for a in actions if a > 0),
            "num_rejected": sum(1 for a in actions if a == 0),
            "total_reward": sum(rewards),
            "mean_reward": np.mean(rewards),
            "mean_pnl": np.mean(pnls),
            "final_balance": self.balance,
            "return_pct": (self.balance - self.initial_balance) / self.initial_balance * 100,
        }

    def get_detailed_episode_stats(self) -> Dict[str, Any]:
        """
        Get detailed statistics for the current episode.

        Returns complete data for logging including action distributions,
        trade outcomes, portfolio performance, and reward breakdowns.
        """
        if not self.episode_trades:
            return {}

        # Calculate max drawdown
        max_balance = self._portfolio_tracking["max_balance"]
        min_balance = self._portfolio_tracking["min_balance"]
        max_drawdown = (max_balance - min_balance) / max_balance if max_balance > 0 else 0

        return {
            "action_counts": self._action_counts.copy(),
            "trade_outcomes": self._trade_outcomes.copy(),
            "portfolio": {
                "starting_balance": float(self._portfolio_tracking["starting_balance"]),
                "ending_balance": float(self.balance),
                "return_pct": float((self.balance - self.initial_balance) / self.initial_balance * 100),
                "max_drawdown": float(max_drawdown),
                "min_health_score": float(self._portfolio_tracking["min_health_score"]),
                "final_health_score": float(self.portfolio_state["health_score"]),
            },
            "reward_breakdown": {
                "pnl_rewards": float(self._reward_breakdown["pnl_rewards"]),
                "rejection_rewards": float(self._reward_breakdown["rejection_rewards"]),
                "health_bonuses": float(self._reward_breakdown["health_bonuses"]),
                "liquidation_penalties": float(self._reward_breakdown["liquidation_penalties"]),
            },
        }
