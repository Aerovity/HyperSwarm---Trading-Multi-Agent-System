"""
Pure mathematical functions for trade calculations.
NO LLM - only deterministic math.
"""
from typing import List, Tuple

def calculate_position_size(
    portfolio_value: float,
    max_allocation: float = 0.30
) -> float:
    """
    Calculate maximum position size based on portfolio allocation.

    Args:
        portfolio_value: Total portfolio value in USD
        max_allocation: Maximum allocation (default 30%)

    Returns:
        Maximum position size in USD
    """
    if portfolio_value <= 0:
        raise ValueError("Portfolio value must be positive")
    if not 0 < max_allocation <= 1:
        raise ValueError("Max allocation must be between 0 and 1")

    return portfolio_value * max_allocation

def calculate_leverage(
    position_size: float,
    available_margin: float
) -> float:
    """
    Calculate leverage for position.

    Args:
        position_size: Desired position size in USD
        available_margin: Available margin in USD

    Returns:
        Required leverage multiplier
    """
    if available_margin <= 0:
        raise ValueError("Available margin must be positive")

    return position_size / available_margin

def split_twap_order(
    total_size: float,
    num_chunks: int = 5
) -> List[float]:
    """
    Split order into TWAP chunks.

    Args:
        total_size: Total order size
        num_chunks: Number of chunks to split into

    Returns:
        List of chunk sizes
    """
    if total_size <= 0:
        raise ValueError("Total size must be positive")
    if num_chunks <= 0:
        raise ValueError("Number of chunks must be positive")

    chunk_size = total_size / num_chunks
    return [chunk_size] * num_chunks

def calculate_take_profit_spread(
    entry_spread: float,
    target_sigma: float = 0.5
) -> float:
    """
    Calculate take-profit spread level (convergence target).

    Args:
        entry_spread: Entry spread value
        target_sigma: Target sigma for take profit (default 0.5)

    Returns:
        Take profit spread threshold
    """
    # For mean reversion: profit when spread converges back toward mean
    # Entry at 2.5σ -> TP at 0.5σ
    return abs(entry_spread) * (target_sigma / abs(entry_spread)) if entry_spread != 0 else target_sigma

def calculate_stop_loss_spread(
    entry_spread: float,
    max_sigma: float = 3.0
) -> float:
    """
    Calculate stop-loss spread level (divergence limit).

    Args:
        entry_spread: Entry spread value
        max_sigma: Maximum sigma before stop loss (default 3.0)

    Returns:
        Stop loss spread threshold
    """
    # For mean reversion: stop loss when spread diverges further
    # Entry at 2.5σ -> SL at 3σ
    return abs(entry_spread) * (max_sigma / abs(entry_spread)) if entry_spread != 0 else max_sigma

def calculate_spread(price_a: float, price_b: float, normalize: bool = True) -> float:
    """
    Calculate spread between two assets.

    Args:
        price_a: Price of asset A
        price_b: Price of asset B
        normalize: Whether to normalize spread

    Returns:
        Spread value
    """
    if price_b == 0:
        raise ValueError("Price B cannot be zero")

    if normalize:
        return (price_a / price_b) - 1.0  # Percentage spread
    else:
        return price_a - price_b  # Absolute spread

def calculate_position_pnl(
    entry_spread: float,
    current_spread: float,
    long_size: float,
    short_size: float,
    long_entry_price: float,
    short_entry_price: float,
    long_current_price: float,
    short_current_price: float
) -> float:
    """
    Calculate current PnL for a pair trade position.

    Args:
        entry_spread: Spread at entry
        current_spread: Current spread
        long_size: Size of long position
        short_size: Size of short position
        long_entry_price: Entry price for long
        short_entry_price: Entry price for short
        long_current_price: Current price for long
        short_current_price: Current price for short

    Returns:
        Total PnL in USD
    """
    # PnL from long leg
    long_pnl = long_size * (long_current_price - long_entry_price)

    # PnL from short leg (inverse)
    short_pnl = short_size * (short_entry_price - short_current_price)

    # Total PnL
    return long_pnl + short_pnl
