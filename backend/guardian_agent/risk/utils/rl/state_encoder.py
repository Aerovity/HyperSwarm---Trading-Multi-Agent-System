"""
State Encoder for RL Training

Encodes portfolio state, trade proposals, and market conditions into a feature vector.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd


class StateEncoder:
    """
    Encodes the environment state into a normalized feature vector for the RL agent.

    State components:
    1. Portfolio state (from existing risk_calculator)
    2. Trade proposal features
    3. Market conditions (from historical data / technical indicators)
    """

    # Feature dimensions
    PORTFOLIO_FEATURES = 6
    TRADE_FEATURES = 4
    MARKET_FEATURES = 14
    TOTAL_FEATURES = PORTFOLIO_FEATURES + TRADE_FEATURES + MARKET_FEATURES  # 24

    def __init__(self):
        self.feature_names = self._get_feature_names()

    def _get_feature_names(self) -> list:
        """Get ordered list of feature names."""
        return [
            # Portfolio state (6)
            "account_value_norm",
            "current_leverage",
            "margin_usage",
            "num_positions",
            "liquidation_distance",
            "health_score_norm",
            # Trade proposal (4)
            "proposed_size_norm",
            "proposed_leverage",
            "signal_confidence",
            "z_score",
            # Market conditions (14)
            "rsi_14",
            "macd",
            "macd_signal",
            "macd_diff",
            "bb_position",
            "atr_normalized",
            "adx",
            "volume_ratio",
            "momentum_1h",
            "momentum_4h",
            "momentum_24h",
            "returns",
            "stoch_k",
            "stoch_d",
        ]

    def encode_portfolio(self, portfolio_state: Dict[str, Any]) -> np.ndarray:
        """
        Encode portfolio state into normalized features.

        Args:
            portfolio_state: Dict with keys:
                - account_value: float (USD)
                - current_leverage: float (0-10+)
                - margin_usage: float (0-1)
                - num_positions: int (0-10+)
                - liquidation_distance: float (0-1)
                - health_score: float (0-100)

        Returns:
            np.ndarray of shape (6,)
        """
        return np.array(
            [
                np.clip(portfolio_state.get("account_value", 10000) / 100000, 0, 1),
                np.clip(portfolio_state.get("current_leverage", 1.0) / 10, 0, 1),
                np.clip(portfolio_state.get("margin_usage", 0.0), 0, 1),
                np.clip(portfolio_state.get("num_positions", 0) / 5, 0, 1),
                np.clip(portfolio_state.get("liquidation_distance", 1.0), 0, 1),
                np.clip(portfolio_state.get("health_score", 100) / 100, 0, 1),
            ],
            dtype=np.float32,
        )

    def encode_trade_proposal(self, trade_proposal: Dict[str, Any]) -> np.ndarray:
        """
        Encode trade proposal into normalized features.

        Args:
            trade_proposal: Dict with keys:
                - size: float (position size in USD)
                - leverage: float (1-10+)
                - confidence: float (0-1)
                - z_score: float (-3 to 3 typically)
                - account_value: float (for normalization)

        Returns:
            np.ndarray of shape (4,)
        """
        account_value = trade_proposal.get("account_value", 10000)
        size = trade_proposal.get("size", 0)

        return np.array(
            [
                np.clip(size / account_value, 0, 1),  # Size as fraction of account
                np.clip(trade_proposal.get("leverage", 1.0) / 10, 0, 1),
                np.clip(trade_proposal.get("confidence", 0.5), 0, 1),
                np.clip(trade_proposal.get("z_score", 0) / 3, -1, 1),  # Normalize to -1,1
            ],
            dtype=np.float32,
        )

    def encode_market_conditions(
        self, market_data: pd.Series, already_normalized: bool = True
    ) -> np.ndarray:
        """
        Encode market conditions from a row of processed data.

        Args:
            market_data: pd.Series with technical indicator columns
            already_normalized: Whether features are already z-scored

        Returns:
            np.ndarray of shape (14,)
        """
        feature_cols = [
            "rsi_14",
            "macd",
            "macd_signal",
            "macd_diff",
            "bb_position",
            "atr_normalized",
            "adx",
            "volume_ratio",
            "momentum_1h",
            "momentum_4h",
            "momentum_24h",
            "returns",
            "stoch_k",
            "stoch_d",
        ]

        features = []
        for col in feature_cols:
            val = market_data.get(col, 0.0)
            if not already_normalized:
                # Apply rough normalization if not pre-normalized
                if col == "rsi_14":
                    val = (val - 50) / 50  # Center around 0
                elif col in ["stoch_k", "stoch_d"]:
                    val = (val - 50) / 50
                elif col == "adx":
                    val = val / 50 - 1  # ADX 0-100, center around 0
                elif col == "bb_position":
                    val = np.clip(val, -2, 2) / 2
                elif col == "volume_ratio":
                    val = np.clip(val - 1, -2, 2) / 2
                else:
                    val = np.clip(val, -3, 3) / 3
            features.append(val)

        return np.array(features, dtype=np.float32)

    def encode(
        self,
        portfolio_state: Dict[str, Any],
        trade_proposal: Dict[str, Any],
        market_data: pd.Series,
        already_normalized: bool = True,
    ) -> np.ndarray:
        """
        Encode full state for the RL agent.

        Args:
            portfolio_state: Portfolio metrics dict
            trade_proposal: Trade proposal dict
            market_data: Row from processed data with indicators

        Returns:
            np.ndarray of shape (24,) - full state vector
        """
        portfolio_features = self.encode_portfolio(portfolio_state)
        trade_features = self.encode_trade_proposal(trade_proposal)
        market_features = self.encode_market_conditions(market_data, already_normalized)

        state = np.concatenate([portfolio_features, trade_features, market_features])
        return state.astype(np.float32)

    def get_observation_space_bounds(self) -> tuple:
        """
        Get bounds for Gymnasium observation space.

        Returns:
            (low, high) bounds arrays
        """
        low = np.array(
            [0, 0, 0, 0, 0, 0]  # Portfolio (all 0-1)
            + [0, 0, 0, -1]  # Trade proposal (size, leverage, confidence: 0-1; z_score: -1 to 1)
            + [-3] * 14,  # Market features (normalized)
            dtype=np.float32,
        )
        high = np.array(
            [1, 1, 1, 1, 1, 1]  # Portfolio
            + [1, 1, 1, 1]  # Trade proposal
            + [3] * 14,  # Market features
            dtype=np.float32,
        )
        return low, high

    def decode_action(self, action: int) -> Dict[str, Any]:
        """
        Decode agent action into human-readable decision.

        Args:
            action: Integer action (0=REJECT, 1=APPROVE_WARNING, 2=APPROVE)

        Returns:
            Dict with decision details
        """
        action_map = {
            0: {
                "decision": "reject",
                "risk_level": "high",
                "description": "Trade rejected due to high risk assessment",
            },
            1: {
                "decision": "approve_with_warning",
                "risk_level": "medium",
                "description": "Trade approved with risk warnings",
            },
            2: {
                "decision": "approve",
                "risk_level": "low",
                "description": "Trade approved - low risk assessment",
            },
        }
        return action_map.get(action, action_map[0])

    def create_dummy_state(self) -> np.ndarray:
        """Create a dummy state for testing."""
        return np.zeros(self.TOTAL_FEATURES, dtype=np.float32)
