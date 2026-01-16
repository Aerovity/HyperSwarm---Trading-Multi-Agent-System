"""
Unit tests for pure risk calculation functions.
All functions should be deterministic (no LLM).
"""

from django.test import TestCase
from risk.utils.risk_calculator import (
    calculate_portfolio_value,
    calculate_margin_usage,
    calculate_liquidation_distance,
    calculate_position_pnl,
    calculate_portfolio_leverage,
    calculate_health_score,
    check_risk_limits,
    calculate_position_risk_level,
    calculate_concentration_risk,
)


class PortfolioValueTests(TestCase):
    """Test calculate_portfolio_value function"""

    def test_single_position(self):
        """Test with single position"""
        positions = [
            {'size': 1.0, 'current_price': 50000}
        ]
        value = calculate_portfolio_value(positions)
        self.assertEqual(value, 50000.0)

    def test_multiple_positions(self):
        """Test with multiple positions"""
        positions = [
            {'size': 1.0, 'current_price': 50000},  # $50k
            {'size': 10.0, 'current_price': 3000},   # $30k
        ]
        value = calculate_portfolio_value(positions)
        self.assertEqual(value, 80000.0)

    def test_empty_positions(self):
        """Test with no positions"""
        value = calculate_portfolio_value([])
        self.assertEqual(value, 0.0)

    def test_negative_size_uses_absolute(self):
        """Test that negative sizes are handled (short positions)"""
        positions = [
            {'size': -1.0, 'current_price': 50000}
        ]
        value = calculate_portfolio_value(positions)
        self.assertEqual(value, 50000.0)


class MarginUsageTests(TestCase):
    """Test calculate_margin_usage function"""

    def test_basic_calculation(self):
        """Test basic margin usage"""
        usage = calculate_margin_usage(2500, 10000)
        self.assertEqual(usage, 0.25)

    def test_full_margin(self):
        """Test 100% margin usage"""
        usage = calculate_margin_usage(10000, 10000)
        self.assertEqual(usage, 1.0)

    def test_zero_total_raises_error(self):
        """Test that zero total margin raises error"""
        with self.assertRaises(ValueError):
            calculate_margin_usage(100, 0)

    def test_negative_total_raises_error(self):
        """Test that negative total margin raises error"""
        with self.assertRaises(ValueError):
            calculate_margin_usage(100, -1000)


class LiquidationDistanceTests(TestCase):
    """Test calculate_liquidation_distance function"""

    def test_safe_distance(self):
        """Test safe liquidation distance"""
        distance = calculate_liquidation_distance(10000, 8000)
        self.assertEqual(distance, 0.20)

    def test_close_to_liquidation(self):
        """Test close to liquidation"""
        distance = calculate_liquidation_distance(10000, 9500)
        self.assertEqual(distance, 0.05)

    def test_no_liquidation_risk(self):
        """Test no liquidation price (0)"""
        distance = calculate_liquidation_distance(10000, 0)
        self.assertEqual(distance, 1.0)

    def test_zero_current_raises_error(self):
        """Test that zero current value raises error"""
        with self.assertRaises(ValueError):
            calculate_liquidation_distance(0, 8000)


class PositionPnLTests(TestCase):
    """Test calculate_position_pnl function"""

    def test_long_profit(self):
        """Test profitable long position"""
        pnl_usd, pnl_pct = calculate_position_pnl(
            entry_price=50000, current_price=51000, size=1.0, is_long=True
        )
        self.assertEqual(pnl_usd, 1000.0)
        self.assertEqual(pnl_pct, 2.0)

    def test_long_loss(self):
        """Test losing long position"""
        pnl_usd, pnl_pct = calculate_position_pnl(
            entry_price=50000, current_price=49000, size=1.0, is_long=True
        )
        self.assertEqual(pnl_usd, -1000.0)
        self.assertEqual(pnl_pct, -2.0)

    def test_short_profit(self):
        """Test profitable short position"""
        pnl_usd, pnl_pct = calculate_position_pnl(
            entry_price=50000, current_price=49000, size=1.0, is_long=False
        )
        self.assertEqual(pnl_usd, 1000.0)
        self.assertEqual(pnl_pct, 2.0)

    def test_short_loss(self):
        """Test losing short position"""
        pnl_usd, pnl_pct = calculate_position_pnl(
            entry_price=50000, current_price=51000, size=1.0, is_long=False
        )
        self.assertEqual(pnl_usd, -1000.0)
        self.assertEqual(pnl_pct, -2.0)

    def test_zero_entry_raises_error(self):
        """Test that zero entry price raises error"""
        with self.assertRaises(ValueError):
            calculate_position_pnl(0, 51000, 1.0, True)


class PortfolioLeverageTests(TestCase):
    """Test calculate_portfolio_leverage function"""

    def test_basic_leverage(self):
        """Test basic leverage calculation"""
        leverage = calculate_portfolio_leverage(25000, 10000)
        self.assertEqual(leverage, 2.5)

    def test_no_leverage(self):
        """Test 1x leverage"""
        leverage = calculate_portfolio_leverage(10000, 10000)
        self.assertEqual(leverage, 1.0)

    def test_zero_account_raises_error(self):
        """Test that zero account value raises error"""
        with self.assertRaises(ValueError):
            calculate_portfolio_leverage(25000, 0)


class HealthScoreTests(TestCase):
    """Test calculate_health_score function"""

    def test_excellent_health(self):
        """Test excellent portfolio health"""
        score = calculate_health_score(
            liquidation_distance=0.60,
            leverage=1.5,
            num_positions=1,
            margin_usage=0.20
        )
        self.assertGreater(score, 80)

    def test_good_health(self):
        """Test good portfolio health"""
        score = calculate_health_score(
            liquidation_distance=0.35,
            leverage=2.5,
            num_positions=3,
            margin_usage=0.50
        )
        self.assertGreater(score, 50)
        self.assertLess(score, 85)

    def test_critical_health(self):
        """Test critical portfolio health"""
        score = calculate_health_score(
            liquidation_distance=0.05,
            leverage=5.0,
            num_positions=6,
            margin_usage=0.90
        )
        self.assertLess(score, 20)

    def test_score_bounded_0_to_100(self):
        """Test score is always between 0 and 100"""
        # Best case
        score_best = calculate_health_score(0.8, 0.5, 0, 0.0)
        self.assertLessEqual(score_best, 100)
        self.assertGreaterEqual(score_best, 0)

        # Worst case
        score_worst = calculate_health_score(0.0, 10.0, 10, 1.0)
        self.assertLessEqual(score_worst, 100)
        self.assertGreaterEqual(score_worst, 0)


class RiskLimitsTests(TestCase):
    """Test check_risk_limits function"""

    def setUp(self):
        self.risk_limits = {
            'MAX_POSITIONS': 3,
            'MAX_LEVERAGE': 3.0,
            'MAX_POSITION_PCT': 0.30,
            'MIN_LIQUIDATION_DISTANCE': 0.20,
            'MIN_SIGNAL_CONFIDENCE': 0.7,
        }

    def test_all_rules_pass(self):
        """Test when all rules pass"""
        trade = {'size': 2500, 'leverage': 2.0, 'confidence': 0.85}
        portfolio = {
            'account_value': 10000,
            'num_positions': 1,
            'current_leverage': 1.0,
            'liquidation_distance': 0.40
        }

        passes, violations = check_risk_limits(trade, portfolio, self.risk_limits)

        self.assertTrue(passes)
        self.assertEqual(len(violations), 0)

    def test_max_positions_exceeded(self):
        """Test max positions violation"""
        trade = {'size': 2500, 'leverage': 2.0, 'confidence': 0.85}
        portfolio = {
            'account_value': 10000,
            'num_positions': 3,  # Already at max
            'current_leverage': 1.0,
            'liquidation_distance': 0.40
        }

        passes, violations = check_risk_limits(trade, portfolio, self.risk_limits)

        self.assertFalse(passes)
        self.assertTrue(any('max_positions' in v for v in violations))

    def test_leverage_exceeded(self):
        """Test leverage limit violation"""
        trade = {'size': 10000, 'leverage': 2.0, 'confidence': 0.85}
        portfolio = {
            'account_value': 10000,
            'num_positions': 1,
            'current_leverage': 2.5,  # Already high, adding 10k makes it 3.5x
            'liquidation_distance': 0.40
        }

        passes, violations = check_risk_limits(trade, portfolio, self.risk_limits)

        self.assertFalse(passes)
        self.assertTrue(any('leverage' in v for v in violations))

    def test_low_confidence(self):
        """Test low signal confidence violation"""
        trade = {'size': 2500, 'leverage': 2.0, 'confidence': 0.5}  # Below 0.7
        portfolio = {
            'account_value': 10000,
            'num_positions': 1,
            'current_leverage': 1.0,
            'liquidation_distance': 0.40
        }

        passes, violations = check_risk_limits(trade, portfolio, self.risk_limits)

        self.assertFalse(passes)
        self.assertTrue(any('confidence' in v for v in violations))


class PositionRiskLevelTests(TestCase):
    """Test calculate_position_risk_level function"""

    def test_low_risk(self):
        """Test low risk position"""
        level = calculate_position_risk_level(
            leverage=1.5, liquidation_distance=0.50, pnl_percent=5.0
        )
        self.assertEqual(level, "low")

    def test_medium_risk(self):
        """Test medium risk position"""
        level = calculate_position_risk_level(
            leverage=2.5, liquidation_distance=0.30, pnl_percent=0.0
        )
        self.assertEqual(level, "medium")

    def test_high_risk(self):
        """Test high risk position"""
        level = calculate_position_risk_level(
            leverage=3.5, liquidation_distance=0.15, pnl_percent=-10.0
        )
        self.assertEqual(level, "high")

    def test_critical_risk(self):
        """Test critical risk position"""
        level = calculate_position_risk_level(
            leverage=5.0, liquidation_distance=0.05, pnl_percent=-20.0
        )
        self.assertEqual(level, "critical")


class ConcentrationRiskTests(TestCase):
    """Test calculate_concentration_risk function"""

    def test_single_position(self):
        """Test concentration with single position"""
        positions = [
            {'symbol': 'BTC', 'size': 1.0, 'current_price': 50000}
        ]
        concentration = calculate_concentration_risk(positions)

        self.assertEqual(concentration['BTC'], 1.0)

    def test_balanced_positions(self):
        """Test balanced concentration"""
        positions = [
            {'symbol': 'BTC', 'size': 1.0, 'current_price': 50000},  # $50k
            {'symbol': 'ETH', 'size': 16.67, 'current_price': 3000},  # ~$50k
        ]
        concentration = calculate_concentration_risk(positions)

        # Should be roughly 50/50
        self.assertAlmostEqual(concentration['BTC'], 0.5, places=1)
        self.assertAlmostEqual(concentration['ETH'], 0.5, places=1)

    def test_empty_positions(self):
        """Test with no positions"""
        concentration = calculate_concentration_risk([])
        self.assertEqual(concentration, {})
