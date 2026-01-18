"""
Unit tests for risk_controls.py
"""
from django.test import TestCase
from trading.utils.risk_controls import (
    validate_max_positions,
    validate_position_size,
    validate_leverage,
    validate_portfolio_value,
    validate_all_risk_controls,
)

class RiskControlsTests(TestCase):
    """Test risk control functions"""

    def test_validate_max_positions(self):
        """Test max positions validation"""
        self.assertTrue(validate_max_positions(2, 3))
        self.assertFalse(validate_max_positions(3, 3))

    def test_validate_position_size(self):
        """Test position size validation"""
        self.assertTrue(validate_position_size(3000, 10000, 0.30))
        self.assertFalse(validate_position_size(4000, 10000, 0.30))
        self.assertFalse(validate_position_size(1000, -100, 0.30))

    def test_validate_leverage(self):
        """Test leverage validation"""
        self.assertTrue(validate_leverage(2.5, 3.0))
        self.assertFalse(validate_leverage(3.5, 3.0))

    def test_validate_portfolio_value(self):
        """Test portfolio value validation"""
        self.assertTrue(validate_portfolio_value(1000, 100))
        self.assertFalse(validate_portfolio_value(50, 100))

    def test_validate_all_risk_controls(self):
        """Test all risk controls together"""
        passed, msg = validate_all_risk_controls(
            position_size=3000,
            portfolio_value=10000,
            leverage=2.5,
            current_positions=2
        )
        self.assertTrue(passed)
        self.assertEqual(msg, "All risk controls passed")

        passed, msg = validate_all_risk_controls(
            position_size=4000,
            portfolio_value=10000,
            leverage=2.5,
            current_positions=2
        )
        self.assertFalse(passed)
        self.assertIn("allocation limit", msg)
