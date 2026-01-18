"""
Reward Calculator for RL Training

Defines the reward function balancing returns vs risk management.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class TradeOutcome:
    """Represents the outcome of a trade."""

    pnl: float  # Profit/loss as percentage
    max_drawdown: float  # Maximum drawdown during trade
    was_liquidated: bool  # Whether position was liquidated
    was_stopped: bool  # Whether stop loss was hit
    hit_take_profit: bool  # Whether take profit was hit
    hold_periods: int  # How long position was held


# Action constants
ACTION_REJECT = 0
ACTION_APPROVE_WARNING = 1
ACTION_APPROVE = 2


class RewardCalculator:
    """
    Calculates rewards for trade approval decisions.

    Reward design principles:
    1. Heavily penalize liquidations (-5.0)
    2. Reward good rejections (avoided losses)
    3. Small penalty for missed opportunities
    4. Risk-adjusted returns (Sharpe-like)
    5. Bonus for maintaining healthy portfolio
    """

    def __init__(
        self,
        liquidation_penalty: float = -5.0,
        good_rejection_reward: float = 1.0,
        missed_opportunity_factor: float = 0.3,
        drawdown_penalty_factor: float = 0.5,
        health_bonus: float = 0.1,
        health_threshold: float = 0.8,
    ):
        """
        Initialize reward calculator with configurable weights.

        Args:
            liquidation_penalty: Penalty for approving trades that get liquidated
            good_rejection_reward: Reward for rejecting trades that would have lost
            missed_opportunity_factor: Penalty factor for rejecting profitable trades
            drawdown_penalty_factor: Factor for penalizing drawdown in approved trades
            health_bonus: Bonus for maintaining healthy portfolio
            health_threshold: Health score threshold for bonus (normalized 0-1)
        """
        self.liquidation_penalty = liquidation_penalty
        self.good_rejection_reward = good_rejection_reward
        self.missed_opportunity_factor = missed_opportunity_factor
        self.drawdown_penalty_factor = drawdown_penalty_factor
        self.health_bonus = health_bonus
        self.health_threshold = health_threshold

    def calculate_reward(
        self,
        action: int,
        trade_outcome: TradeOutcome,
        portfolio_health: float = 0.8,
    ) -> float:
        """
        Calculate reward for a trade approval decision.

        Args:
            action: The action taken (0=REJECT, 1=APPROVE_WARNING, 2=APPROVE)
            trade_outcome: Outcome of the trade (simulated or actual)
            portfolio_health: Current portfolio health score (0-1)

        Returns:
            Reward value (float)
        """
        reward = 0.0

        if action == ACTION_REJECT:
            # Rejected the trade
            if trade_outcome.was_liquidated or trade_outcome.pnl < 0:
                # Good rejection - avoided a loss
                reward = self.good_rejection_reward
                if trade_outcome.was_liquidated:
                    # Extra reward for avoiding liquidation
                    reward += 0.5
            else:
                # Missed opportunity - trade would have been profitable
                reward = -self.missed_opportunity_factor * min(
                    trade_outcome.pnl, 0.5
                )  # Cap the penalty

        elif action in [ACTION_APPROVE_WARNING, ACTION_APPROVE]:
            # Approved the trade
            if trade_outcome.was_liquidated:
                # Very bad - liquidation
                reward = self.liquidation_penalty
            else:
                # Risk-adjusted reward: PnL minus drawdown penalty
                pnl_reward = trade_outcome.pnl * 10  # Scale PnL
                drawdown_penalty = (
                    trade_outcome.max_drawdown * self.drawdown_penalty_factor * 10
                )
                reward = pnl_reward - drawdown_penalty

                # Extra penalty for being stopped out at a loss
                if trade_outcome.was_stopped and trade_outcome.pnl < 0:
                    reward -= 0.3

                # Bonus for hitting take profit
                if trade_outcome.hit_take_profit:
                    reward += 0.2

            # Slight penalty for approve_warning vs full approve if outcome is good
            if action == ACTION_APPROVE_WARNING and trade_outcome.pnl > 0:
                reward -= 0.05  # Small penalty for being too cautious

        # Health bonus for maintaining healthy portfolio
        if portfolio_health >= self.health_threshold:
            reward += self.health_bonus

        return reward

    def calculate_reward_from_dict(
        self, action: int, outcome_dict: Dict[str, Any], portfolio_health: float = 0.8
    ) -> float:
        """
        Calculate reward from a dictionary outcome (convenience method).

        Args:
            action: Action taken
            outcome_dict: Dict with pnl, max_drawdown, was_liquidated, etc.
            portfolio_health: Portfolio health score (0-1)

        Returns:
            Reward value
        """
        outcome = TradeOutcome(
            pnl=outcome_dict.get("pnl", 0.0),
            max_drawdown=outcome_dict.get("max_drawdown", 0.0),
            was_liquidated=outcome_dict.get("was_liquidated", False),
            was_stopped=outcome_dict.get("was_stopped", False),
            hit_take_profit=outcome_dict.get("hit_take_profit", False),
            hold_periods=outcome_dict.get("hold_periods", 0),
        )
        return self.calculate_reward(action, outcome, portfolio_health)

    def get_reward_breakdown(
        self,
        action: int,
        trade_outcome: TradeOutcome,
        portfolio_health: float = 0.8,
    ) -> Dict[str, float]:
        """
        Get detailed breakdown of reward components.

        Returns:
            Dict with individual reward components
        """
        components = {
            "base_reward": 0.0,
            "pnl_component": 0.0,
            "drawdown_penalty": 0.0,
            "liquidation_penalty": 0.0,
            "missed_opportunity": 0.0,
            "good_rejection_bonus": 0.0,
            "health_bonus": 0.0,
            "total": 0.0,
        }

        if action == ACTION_REJECT:
            if trade_outcome.was_liquidated or trade_outcome.pnl < 0:
                components["good_rejection_bonus"] = self.good_rejection_reward
                if trade_outcome.was_liquidated:
                    components["good_rejection_bonus"] += 0.5
            else:
                components["missed_opportunity"] = (
                    -self.missed_opportunity_factor
                    * min(trade_outcome.pnl, 0.5)
                )

        elif action in [ACTION_APPROVE_WARNING, ACTION_APPROVE]:
            if trade_outcome.was_liquidated:
                components["liquidation_penalty"] = self.liquidation_penalty
            else:
                components["pnl_component"] = trade_outcome.pnl * 10
                components["drawdown_penalty"] = (
                    -trade_outcome.max_drawdown * self.drawdown_penalty_factor * 10
                )

        if portfolio_health >= self.health_threshold:
            components["health_bonus"] = self.health_bonus

        components["total"] = sum(
            v for k, v in components.items() if k != "total"
        )
        return components

    @staticmethod
    def get_default_config() -> Dict[str, float]:
        """Get default reward configuration."""
        return {
            "liquidation_penalty": -5.0,
            "good_rejection_reward": 1.0,
            "missed_opportunity_factor": 0.3,
            "drawdown_penalty_factor": 0.5,
            "health_bonus": 0.1,
            "health_threshold": 0.8,
        }
