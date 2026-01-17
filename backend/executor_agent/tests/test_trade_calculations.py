"""
Unit tests for trade_calculator.py
"""
from django.test import TestCase
from trading.utils.trade_calculator import (
    calculate_position_size,
    calculate_leverage,
    split_twap_order,
    calculate_take_profit_spread,
    calculate_stop_loss_spread,
    calculate_spread,
    calculate_position_pnl,
)

class TradeCalculatorTests(TestCase):
    """Test trade calculator functions"""

    def test_calculate_position_size(self):
        """Test position size calculation"""
        self.assertEqual(calculate_position_size(10000, 0.30), 3000)
        self.assertEqual(calculate_position_size(5000, 0.20), 1000)

        with self.assertRaises(ValueError):
            calculate_position_size(-100, 0.30)

    def test_calculate_leverage(self):
        """Test leverage calculation"""
        self.assertEqual(calculate_leverage(3000, 1000), 3.0)
        self.assertEqual(calculate_leverage(2000, 1000), 2.0)

        with self.assertRaises(ValueError):
            calculate_leverage(1000, -100)

    def test_split_twap_order(self):
        """Test TWAP order splitting"""
        chunks = split_twap_order(1.0, 5)
        self.assertEqual(len(chunks), 5)
        self.assertEqual(sum(chunks), 1.0)
        self.assertTrue(all(c == 0.2 for c in chunks))

        with self.assertRaises(ValueError):
            split_twap_order(-1, 5)

    def test_calculate_spread(self):
        """Test spread calculation"""
        self.assertAlmostEqual(calculate_spread(110, 100, True), 0.1)
        self.assertEqual(calculate_spread(110, 100, False), 10)

        with self.assertRaises(ValueError):
            calculate_spread(100, 0)

    def test_calculate_position_pnl(self):
        """Test PnL calculation"""
        pnl = calculate_position_pnl(
            entry_spread=2.0,
            current_spread=1.0,
            long_size=0.1,
            short_size=1.0,
            long_entry_price=50000,
            short_entry_price=3000,
            long_current_price=51000,
            short_current_price=2900
        )
        # Long: 0.1 * (51000 - 50000) = 100
        # Short: 1.0 * (3000 - 2900) = 100
        # Total = 200
        self.assertEqual(pnl, 200)

    def test_calculate_take_profit_spread(self):
        """Test take-profit spread calculation"""
        tp = calculate_take_profit_spread(0.02, 0.5)
        self.assertGreater(tp, 0)
        # For entry spread of 0.02 (2%) with target sigma 0.5
        self.assertAlmostEqual(tp, 0.5)

    def test_calculate_stop_loss_spread(self):
        """Test stop-loss spread calculation"""
        sl = calculate_stop_loss_spread(0.02, 3.0)
        self.assertGreater(sl, 0)
        # For entry spread of 0.02 (2%) with max sigma 3.0
        self.assertAlmostEqual(sl, 3.0)
