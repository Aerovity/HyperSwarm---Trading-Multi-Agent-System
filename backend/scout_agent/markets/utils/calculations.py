"""
Pure Python mathematical calculation functions for statistical analysis.
All functions use NumPy for performance and are deterministic (no LLM).
"""

import numpy as np
from typing import List, Tuple


def calculate_zscore(prices: List[float], window: int = 20) -> float:
    """
    Calculate z-score for price spread.

    Z-score = (current_value - mean) / std_dev

    Args:
        prices: List of price values
        window: Rolling window size (default: 20)

    Returns:
        Z-score value (positive or negative)

    Raises:
        ValueError: If insufficient data or std_dev is zero
    """
    if len(prices) < window:
        raise ValueError(f"Need at least {window} prices, got {len(prices)}")

    recent = np.array(prices[-window:], dtype=float)
    mean = np.mean(recent)
    std = np.std(recent)

    if std == 0:
        raise ValueError("Standard deviation is zero - no variation in prices")

    return (prices[-1] - mean) / std


def calculate_correlation(series1: List[float], series2: List[float],
                         window: int = 50) -> float:
    """
    Calculate Pearson correlation between two price series.

    Args:
        series1: First price series
        series2: Second price series
        window: Rolling window size (default: 50)

    Returns:
        Correlation coefficient (-1 to 1)
    """
    if len(series1) != len(series2):
        raise ValueError("Series must have equal length")

    if len(series1) < window:
        raise ValueError(f"Need at least {window} data points")

    s1 = np.array(series1[-window:], dtype=float)
    s2 = np.array(series2[-window:], dtype=float)

    return np.corrcoef(s1, s2)[0, 1]


def calculate_spread(price1: float, price2: float,
                     normalize: bool = True) -> float:
    """
    Calculate price spread between two assets.

    Args:
        price1: First asset price
        price2: Second asset price
        normalize: If True, return spread / avg_price

    Returns:
        Spread value (normalized or absolute)
    """
    spread = price1 - price2

    if normalize:
        avg_price = (price1 + price2) / 2
        if avg_price == 0:
            raise ValueError("Cannot normalize with zero average price")
        return spread / avg_price

    return spread


def identify_mean_reversion(zscore: float, threshold: float = 2.0) -> Tuple[bool, str]:
    """
    Determine if z-score indicates mean reversion opportunity.

    Args:
        zscore: Calculated z-score value
        threshold: Absolute value threshold (default: 2.0)

    Returns:
        Tuple of (is_signal, signal_type)
        signal_type: "long_spread", "short_spread", or "none"
    """
    if zscore > threshold:
        return (True, "short_spread")  # Spread too high, expect reversion down
    elif zscore < -threshold:
        return (True, "long_spread")   # Spread too low, expect reversion up
    else:
        return (False, "none")


def calculate_confidence(zscore: float, correlation: float) -> Tuple[float, str]:
    """
    Calculate confidence score for signal based on zscore and correlation.

    Args:
        zscore: Absolute z-score value
        correlation: Pearson correlation coefficient

    Returns:
        Tuple of (confidence_score, confidence_label)
        confidence_score: 0.0 to 1.0
        confidence_label: "low", "medium", "high"
    """
    # Higher zscore = stronger signal (up to a point)
    zscore_component = min(abs(zscore) / 4.0, 1.0)  # Cap at 4.0 std devs

    # Higher correlation = more reliable
    correlation_component = abs(correlation)

    # Weighted average (60% correlation, 40% zscore)
    confidence = (0.6 * correlation_component) + (0.4 * zscore_component)

    if confidence >= 0.7:
        label = "high"
    elif confidence >= 0.5:
        label = "medium"
    else:
        label = "low"

    return (confidence, label)
