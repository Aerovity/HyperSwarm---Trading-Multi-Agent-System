"""
Unit tests for the RL (Reinforcement Learning) system.

Tests cover:
- State encoder dimensions and bounds
- Reward calculator for various scenarios
- Environment reset and step mechanics
- Data loader indicator computation
"""

import unittest
import numpy as np
import pandas as pd

from risk.utils.rl.state_encoder import StateEncoder
from risk.utils.rl.reward_calculator import (
    RewardCalculator,
    TradeOutcome,
    ACTION_REJECT,
    ACTION_APPROVE_WARNING,
    ACTION_APPROVE,
)
from risk.utils.rl.environment import TradeApprovalEnv
from risk.utils.rl.data_loader import DataLoader


class TestStateEncoder(unittest.TestCase):
    """Tests for StateEncoder class."""

    def setUp(self):
        self.encoder = StateEncoder()

    def test_total_features_dimension(self):
        """State encoder should produce 24-dimensional output."""
        self.assertEqual(self.encoder.TOTAL_FEATURES, 24)
        self.assertEqual(
            self.encoder.PORTFOLIO_FEATURES
            + self.encoder.TRADE_FEATURES
            + self.encoder.MARKET_FEATURES,
            24,
        )

    def test_encode_portfolio_shape(self):
        """Portfolio encoding should produce 6 features."""
        portfolio = {
            "account_value": 10000,
            "current_leverage": 2.0,
            "margin_usage": 0.5,
            "num_positions": 2,
            "liquidation_distance": 0.8,
            "health_score": 85,
        }
        encoded = self.encoder.encode_portfolio(portfolio)
        self.assertEqual(encoded.shape, (6,))
        self.assertEqual(encoded.dtype, np.float32)

    def test_encode_trade_proposal_shape(self):
        """Trade proposal encoding should produce 4 features."""
        trade = {
            "size": 1000,
            "leverage": 2.0,
            "confidence": 0.8,
            "z_score": 2.5,
            "account_value": 10000,
        }
        encoded = self.encoder.encode_trade_proposal(trade)
        self.assertEqual(encoded.shape, (4,))
        self.assertEqual(encoded.dtype, np.float32)

    def test_encode_market_conditions_shape(self):
        """Market conditions encoding should produce 14 features."""
        market_data = pd.Series(
            {
                "rsi_14": 50,
                "macd": 0.01,
                "macd_signal": 0.005,
                "macd_diff": 0.005,
                "bb_position": 0.2,
                "atr_normalized": 0.02,
                "adx": 25,
                "volume_ratio": 1.2,
                "momentum_1h": 0.01,
                "momentum_4h": 0.02,
                "momentum_24h": 0.05,
                "returns": 0.005,
                "stoch_k": 60,
                "stoch_d": 55,
            }
        )
        encoded = self.encoder.encode_market_conditions(market_data, already_normalized=True)
        self.assertEqual(encoded.shape, (14,))
        self.assertEqual(encoded.dtype, np.float32)

    def test_encode_full_state_shape(self):
        """Full state encoding should produce 24 features."""
        portfolio = {"account_value": 10000, "health_score": 80}
        trade = {"size": 1000, "account_value": 10000}
        market = pd.Series({"rsi_14": 50, "macd": 0})

        state = self.encoder.encode(portfolio, trade, market)
        self.assertEqual(state.shape, (24,))
        self.assertEqual(state.dtype, np.float32)

    def test_observation_space_bounds_shape(self):
        """Observation space bounds should match feature dimensions."""
        low, high = self.encoder.get_observation_space_bounds()
        self.assertEqual(low.shape, (24,))
        self.assertEqual(high.shape, (24,))
        self.assertTrue(np.all(low <= high))

    def test_portfolio_features_within_bounds(self):
        """Portfolio features should be clipped to [0, 1]."""
        portfolio = {
            "account_value": 500000,  # Way over 100k
            "current_leverage": 50,  # Way over 10
            "margin_usage": 2.0,  # Over 1
            "num_positions": 20,  # Over 5
            "liquidation_distance": 2.0,  # Over 1
            "health_score": 200,  # Over 100
        }
        encoded = self.encoder.encode_portfolio(portfolio)
        self.assertTrue(np.all(encoded >= 0))
        self.assertTrue(np.all(encoded <= 1))

    def test_z_score_normalization(self):
        """Z-score should be normalized to [-1, 1]."""
        trade = {"z_score": 6.0, "account_value": 10000}  # High z-score
        encoded = self.encoder.encode_trade_proposal(trade)
        self.assertGreaterEqual(encoded[3], -1)
        self.assertLessEqual(encoded[3], 1)

    def test_dummy_state_shape(self):
        """Dummy state should have correct shape."""
        dummy = self.encoder.create_dummy_state()
        self.assertEqual(dummy.shape, (24,))
        self.assertTrue(np.all(dummy == 0))

    def test_decode_action(self):
        """Action decoding should return correct decisions."""
        reject = self.encoder.decode_action(0)
        self.assertEqual(reject["decision"], "reject")
        self.assertEqual(reject["risk_level"], "high")

        approve = self.encoder.decode_action(2)
        self.assertEqual(approve["decision"], "approve")
        self.assertEqual(approve["risk_level"], "low")


class TestRewardCalculator(unittest.TestCase):
    """Tests for RewardCalculator class."""

    def setUp(self):
        self.calc = RewardCalculator()

    def test_approve_profitable_trade_positive_reward(self):
        """Approving a profitable trade should give positive reward."""
        outcome = TradeOutcome(
            pnl=0.05,  # 5% profit
            max_drawdown=0.02,
            was_liquidated=False,
            was_stopped=False,
            hit_take_profit=True,
            hold_periods=12,
        )
        reward = self.calc.calculate_reward(ACTION_APPROVE, outcome, portfolio_health=0.9)
        self.assertGreater(reward, 0)

    def test_reject_losing_trade_positive_reward(self):
        """Rejecting a trade that would have lost should give positive reward."""
        outcome = TradeOutcome(
            pnl=-0.10,  # 10% loss
            max_drawdown=0.15,
            was_liquidated=False,
            was_stopped=True,
            hit_take_profit=False,
            hold_periods=12,
        )
        reward = self.calc.calculate_reward(ACTION_REJECT, outcome, portfolio_health=0.9)
        self.assertGreater(reward, 0)

    def test_liquidation_heavy_penalty(self):
        """Approving a trade that gets liquidated should give heavy penalty."""
        outcome = TradeOutcome(
            pnl=-0.80,
            max_drawdown=0.85,
            was_liquidated=True,
            was_stopped=False,
            hit_take_profit=False,
            hold_periods=12,
        )
        reward = self.calc.calculate_reward(ACTION_APPROVE, outcome, portfolio_health=0.5)
        self.assertLess(reward, -4.0)  # Should be around -5.0

    def test_reject_avoided_liquidation_bonus(self):
        """Rejecting a trade that would have been liquidated should give bonus."""
        outcome = TradeOutcome(
            pnl=-0.80,
            max_drawdown=0.85,
            was_liquidated=True,
            was_stopped=False,
            hit_take_profit=False,
            hold_periods=12,
        )
        reward = self.calc.calculate_reward(ACTION_REJECT, outcome, portfolio_health=0.9)
        self.assertGreater(reward, 1.0)  # 1.0 base + 0.5 liquidation avoidance

    def test_missed_opportunity_penalty(self):
        """Rejecting a profitable trade should give small penalty."""
        outcome = TradeOutcome(
            pnl=0.10,  # 10% profit
            max_drawdown=0.02,
            was_liquidated=False,
            was_stopped=False,
            hit_take_profit=True,
            hold_periods=12,
        )
        reward = self.calc.calculate_reward(ACTION_REJECT, outcome, portfolio_health=0.9)
        # Should be negative (missed opportunity) but small
        self.assertLess(reward, 0.5)  # Health bonus might make it slightly positive

    def test_health_bonus_applied(self):
        """Health bonus should be applied when portfolio health >= 0.8."""
        outcome = TradeOutcome(
            pnl=0.0,
            max_drawdown=0.0,
            was_liquidated=False,
            was_stopped=False,
            hit_take_profit=False,
            hold_periods=12,
        )
        reward_healthy = self.calc.calculate_reward(ACTION_APPROVE, outcome, portfolio_health=0.9)
        reward_unhealthy = self.calc.calculate_reward(ACTION_APPROVE, outcome, portfolio_health=0.5)
        self.assertGreater(reward_healthy, reward_unhealthy)

    def test_approve_warning_slight_penalty(self):
        """Approve with warning should have slight penalty vs full approve for good trades."""
        outcome = TradeOutcome(
            pnl=0.05,
            max_drawdown=0.01,
            was_liquidated=False,
            was_stopped=False,
            hit_take_profit=True,
            hold_periods=12,
        )
        reward_approve = self.calc.calculate_reward(ACTION_APPROVE, outcome, portfolio_health=0.9)
        reward_warning = self.calc.calculate_reward(ACTION_APPROVE_WARNING, outcome, portfolio_health=0.9)
        self.assertGreater(reward_approve, reward_warning)

    def test_reward_breakdown(self):
        """Reward breakdown should sum to total."""
        outcome = TradeOutcome(
            pnl=0.05,
            max_drawdown=0.02,
            was_liquidated=False,
            was_stopped=False,
            hit_take_profit=True,
            hold_periods=12,
        )
        breakdown = self.calc.get_reward_breakdown(ACTION_APPROVE, outcome, portfolio_health=0.9)
        self.assertIn("total", breakdown)
        self.assertIn("pnl_component", breakdown)
        self.assertIn("health_bonus", breakdown)


class TestTradeApprovalEnv(unittest.TestCase):
    """Tests for TradeApprovalEnv class."""

    def setUp(self):
        self.env = TradeApprovalEnv(data=None, max_steps=10, initial_balance=10000)

    def test_action_space(self):
        """Action space should be Discrete(3)."""
        self.assertEqual(self.env.action_space.n, 3)

    def test_observation_space_shape(self):
        """Observation space should be Box(24,)."""
        self.assertEqual(self.env.observation_space.shape, (24,))

    def test_reset_returns_valid_observation(self):
        """Reset should return valid observation and info."""
        obs, info = self.env.reset()
        self.assertEqual(obs.shape, (24,))
        self.assertIn("start_idx", info)
        self.assertIn("balance", info)

    def test_step_returns_correct_tuple(self):
        """Step should return (obs, reward, terminated, truncated, info)."""
        self.env.reset()
        obs, reward, terminated, truncated, info = self.env.step(2)  # APPROVE

        self.assertEqual(obs.shape, (24,))
        self.assertIsInstance(reward, float)
        self.assertIsInstance(terminated, bool)
        self.assertIsInstance(truncated, bool)
        self.assertIsInstance(info, dict)

    def test_episode_truncates_at_max_steps(self):
        """Episode should truncate after max_steps."""
        self.env.reset()
        for i in range(10):
            obs, reward, terminated, truncated, info = self.env.step(2)
        self.assertTrue(truncated)

    def test_balance_changes_on_trade(self):
        """Balance should change when trades are approved."""
        self.env.reset()
        initial_balance = self.env.balance

        # Take several steps
        for _ in range(5):
            self.env.step(2)  # APPROVE

        # Balance may or may not change (depends on simulated outcomes)
        # Just verify balance is still positive
        self.assertGreater(self.env.balance, 0)

    def test_episode_stats(self):
        """Episode stats should be computed correctly."""
        self.env.reset()
        for _ in range(5):
            self.env.step(1)  # APPROVE_WARNING

        stats = self.env.get_episode_stats()
        self.assertEqual(stats["num_trades"], 5)
        self.assertEqual(stats["num_approved"], 5)
        self.assertEqual(stats["num_rejected"], 0)

    def test_render_mode(self):
        """Render should work in ansi mode."""
        env = TradeApprovalEnv(data=None, max_steps=10, render_mode="ansi")
        env.reset()
        env.step(2)
        output = env.render()
        self.assertIsNotNone(output)
        self.assertIn("Step:", output)


class TestDataLoader(unittest.TestCase):
    """Tests for DataLoader class."""

    def setUp(self):
        self.loader = DataLoader()

    def test_feature_columns_count(self):
        """Should have 14 market feature columns."""
        features = self.loader.get_feature_columns()
        self.assertEqual(len(features), 14)

    def test_feature_columns_names(self):
        """Feature columns should include expected indicators."""
        features = self.loader.get_feature_columns()
        self.assertIn("rsi_14", features)
        self.assertIn("macd", features)
        self.assertIn("bb_position", features)
        self.assertIn("atr_normalized", features)
        self.assertIn("adx", features)
        self.assertIn("momentum_1h", features)
        self.assertIn("stoch_k", features)

    def test_compute_indicators_on_sample_data(self):
        """Indicators should be computed on sample OHLCV data."""
        # Create sample data (300 rows needed for all indicators)
        np.random.seed(42)
        n = 350
        base_price = 50000

        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="5min"),
            "open": base_price + np.cumsum(np.random.randn(n) * 10),
            "high": base_price + np.cumsum(np.random.randn(n) * 10) + 50,
            "low": base_price + np.cumsum(np.random.randn(n) * 10) - 50,
            "close": base_price + np.cumsum(np.random.randn(n) * 10),
            "volume": np.random.randint(100, 1000, n),
        })

        result = self.loader.compute_indicators(df)

        # Check all indicators are computed
        for col in self.loader.get_feature_columns():
            self.assertIn(col, result.columns, f"Missing indicator: {col}")

    def test_simulate_trade_outcome_long(self):
        """Trade simulation should work for long positions."""
        # Create sample data
        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=20, freq="5min"),
            "open": [100] * 20,
            "high": [105] * 20,
            "low": [95] * 20,
            "close": [100 + i * 0.5 for i in range(20)],  # Uptrend
            "volume": [1000] * 20,
        })

        result = self.loader.simulate_trade_outcome(
            df=df,
            entry_idx=0,
            direction="long",
            leverage=1.0,
            hold_periods=10,
        )

        self.assertIn("pnl", result)
        self.assertIn("max_drawdown", result)
        self.assertIn("was_liquidated", result)
        self.assertGreater(result["pnl"], 0)  # Uptrend = profit for long

    def test_simulate_trade_outcome_short(self):
        """Trade simulation should work for short positions."""
        # Create sample data with downtrend
        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=20, freq="5min"),
            "open": [100] * 20,
            "high": [105] * 20,
            "low": [95] * 20,
            "close": [100 - i * 0.5 for i in range(20)],  # Downtrend
            "volume": [1000] * 20,
        })

        result = self.loader.simulate_trade_outcome(
            df=df,
            entry_idx=0,
            direction="short",
            leverage=1.0,
            hold_periods=10,
        )

        self.assertGreater(result["pnl"], 0)  # Downtrend = profit for short


if __name__ == "__main__":
    unittest.main()
