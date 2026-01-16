"""
Unit tests for mathematical calculation functions.
Uses Django TestCase framework for comprehensive testing.
"""

from django.test import TestCase
from markets.utils.calculations import (
    calculate_zscore,
    calculate_correlation,
    calculate_spread,
    identify_mean_reversion,
    calculate_confidence
)


class CalculationTests(TestCase):
    """Test pure mathematical calculation functions"""

    def test_zscore_calculation(self):
        """Test z-score with known values"""
        prices = [100, 102, 98, 105, 95, 100, 103, 97, 101, 99,
                  100, 102, 98, 105, 95, 100, 103, 97, 101, 110]

        zscore = calculate_zscore(prices, window=20)

        # 110 is 2+ std devs above mean of ~100
        self.assertGreater(zscore, 2.0)

    def test_zscore_insufficient_data(self):
        """Test z-score raises error with insufficient data"""
        prices = [100, 102, 98]

        with self.assertRaises(ValueError):
            calculate_zscore(prices, window=20)

    def test_zscore_zero_std_dev(self):
        """Test z-score raises error when standard deviation is zero"""
        prices = [100] * 20  # All same values

        with self.assertRaises(ValueError):
            calculate_zscore(prices, window=20)

    def test_correlation_perfect(self):
        """Test correlation with perfectly correlated series"""
        series1 = [1, 2, 3, 4, 5] * 10
        series2 = [2, 4, 6, 8, 10] * 10

        corr = calculate_correlation(series1, series2)

        self.assertAlmostEqual(corr, 1.0, places=3)

    def test_correlation_anticorrelated(self):
        """Test correlation with anti-correlated series"""
        series1 = [1, 2, 3, 4, 5] * 10
        series2 = [5, 4, 3, 2, 1] * 10

        corr = calculate_correlation(series1, series2)

        self.assertAlmostEqual(corr, -1.0, places=3)

    def test_correlation_insufficient_data(self):
        """Test correlation raises error with insufficient data"""
        series1 = [1, 2, 3]
        series2 = [2, 4, 6]

        with self.assertRaises(ValueError):
            calculate_correlation(series1, series2, window=50)

    def test_correlation_unequal_length(self):
        """Test correlation raises error with unequal length series"""
        series1 = [1, 2, 3, 4, 5]
        series2 = [2, 4, 6]

        with self.assertRaises(ValueError):
            calculate_correlation(series1, series2)

    def test_spread_calculation_normalized(self):
        """Test spread calculation with normalization"""
        spread = calculate_spread(50000, 3000, normalize=True)

        expected = (50000 - 3000) / ((50000 + 3000) / 2)
        self.assertAlmostEqual(spread, expected, places=3)

    def test_spread_calculation_absolute(self):
        """Test spread calculation without normalization"""
        spread = calculate_spread(50000, 3000, normalize=False)

        expected = 50000 - 3000
        self.assertEqual(spread, expected)

    def test_spread_zero_average(self):
        """Test spread raises error when average is zero"""
        with self.assertRaises(ValueError):
            calculate_spread(0, 0, normalize=True)

    def test_mean_reversion_signal_short(self):
        """Test mean reversion signal detection for short spread"""
        is_signal, signal_type = identify_mean_reversion(2.5)

        self.assertTrue(is_signal)
        self.assertEqual(signal_type, "short_spread")

    def test_mean_reversion_signal_long(self):
        """Test mean reversion signal detection for long spread"""
        is_signal, signal_type = identify_mean_reversion(-2.5)

        self.assertTrue(is_signal)
        self.assertEqual(signal_type, "long_spread")

    def test_mean_reversion_no_signal(self):
        """Test no signal when threshold not met"""
        is_signal, signal_type = identify_mean_reversion(1.5)

        self.assertFalse(is_signal)
        self.assertEqual(signal_type, "none")

    def test_confidence_high(self):
        """Test high confidence calculation"""
        confidence, label = calculate_confidence(3.0, 0.9)

        self.assertGreater(confidence, 0.7)
        self.assertEqual(label, "high")

    def test_confidence_medium(self):
        """Test medium confidence calculation"""
        confidence, label = calculate_confidence(2.0, 0.6)

        self.assertGreaterEqual(confidence, 0.5)
        self.assertLess(confidence, 0.7)
        self.assertEqual(label, "medium")

    def test_confidence_low(self):
        """Test low confidence calculation"""
        confidence, label = calculate_confidence(1.0, 0.3)

        self.assertLess(confidence, 0.5)
        self.assertEqual(label, "low")

    def test_confidence_negative_correlation(self):
        """Test confidence with negative correlation (should still work)"""
        confidence, label = calculate_confidence(3.0, -0.9)

        # Should use absolute value of correlation
        self.assertGreater(confidence, 0.5)
