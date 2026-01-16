"""
Pure Python risk calculation functions for portfolio analysis.
All functions are deterministic mathematical operations (NO LLM).
Uses NumPy for performance where needed.
"""

import numpy as np
from typing import List, Dict, Tuple


def calculate_portfolio_value(positions: List[Dict]) -> float:
    """
    Calculate total portfolio notional value from open positions.

    Args:
        positions: List of position dicts with 'size', 'current_price' keys
                   'size' should be absolute value (positive)

    Returns:
        Total portfolio notional value in USD

    Example:
        positions = [
            {'size': 1.0, 'current_price': 50000},  # 1 BTC at $50k
            {'size': 10.0, 'current_price': 3000},   # 10 ETH at $3k
        ]
        value = calculate_portfolio_value(positions)  # Returns 80000.0
    """
    if not positions:
        return 0.0

    total = 0.0
    for pos in positions:
        size = abs(float(pos.get('size', 0)))
        price = float(pos.get('current_price', 0))
        total += size * price

    return total


def calculate_margin_usage(used_margin: float, total_margin: float) -> float:
    """
    Calculate margin utilization percentage.

    Args:
        used_margin: Currently used margin in USD
        total_margin: Total available margin in USD

    Returns:
        Margin usage as percentage (0.0 to 1.0)

    Raises:
        ValueError: If total_margin is zero or negative
    """
    if total_margin <= 0:
        raise ValueError("Total margin must be positive")

    return used_margin / total_margin


def calculate_liquidation_distance(
    current_value: float,
    liquidation_value: float
) -> float:
    """
    Calculate distance to liquidation as percentage.

    Args:
        current_value: Current account/position value
        liquidation_value: Value at which liquidation occurs

    Returns:
        Distance to liquidation as percentage (0.0 to 1.0+)
        Example: 0.25 means 25% buffer before liquidation

    Raises:
        ValueError: If current_value is zero or negative
    """
    if current_value <= 0:
        raise ValueError("Current value must be positive")

    if liquidation_value <= 0:
        return 1.0  # No liquidation risk

    return (current_value - liquidation_value) / current_value


def calculate_position_pnl(
    entry_price: float,
    current_price: float,
    size: float,
    is_long: bool
) -> Tuple[float, float]:
    """
    Calculate unrealized PnL for a position.

    Args:
        entry_price: Entry price of the position
        current_price: Current market price
        size: Position size in base asset (always positive)
        is_long: True for long position, False for short

    Returns:
        Tuple of (pnl_usd, pnl_percent)
        - pnl_usd: Unrealized PnL in USD
        - pnl_percent: PnL as percentage of entry value

    Raises:
        ValueError: If entry_price is zero or negative
    """
    if entry_price <= 0:
        raise ValueError("Entry price must be positive")

    size = abs(size)

    if is_long:
        pnl_usd = (current_price - entry_price) * size
    else:
        pnl_usd = (entry_price - current_price) * size

    entry_value = entry_price * size
    pnl_percent = (pnl_usd / entry_value) * 100 if entry_value > 0 else 0.0

    return pnl_usd, pnl_percent


def calculate_portfolio_leverage(
    total_position_value: float,
    account_value: float
) -> float:
    """
    Calculate effective portfolio leverage.

    Args:
        total_position_value: Sum of all position notional values
        account_value: Total account equity

    Returns:
        Leverage multiplier (e.g., 2.5 means 2.5x leverage)

    Raises:
        ValueError: If account_value is zero or negative
    """
    if account_value <= 0:
        raise ValueError("Account value must be positive")

    return total_position_value / account_value


def calculate_health_score(
    liquidation_distance: float,
    leverage: float,
    num_positions: int,
    margin_usage: float = 0.0
) -> int:
    """
    Calculate overall portfolio health score (0-100).

    Scoring factors:
    - Liquidation distance: 40% weight (>50% = max points)
    - Leverage: 30% weight (<2x = max, >5x = 0)
    - Position count: 15% weight (1-3 = max, >5 = 0)
    - Margin usage: 15% weight (<50% = max, >80% = 0)

    Args:
        liquidation_distance: Distance to liquidation (0.0 to 1.0+)
        leverage: Current portfolio leverage
        num_positions: Number of open positions
        margin_usage: Margin utilization percentage (0.0 to 1.0)

    Returns:
        Health score from 0 (critical) to 100 (excellent)
    """
    score = 0.0

    # Liquidation distance component (40% weight, max 40 points)
    # >50% distance = 40 points, 0% = 0 points
    liq_score = min(liquidation_distance / 0.5, 1.0) * 40
    score += liq_score

    # Leverage component (30% weight, max 30 points)
    # <2x = 30 points, 2-5x = scaled, >5x = 0 points
    if leverage <= 2.0:
        lev_score = 30
    elif leverage >= 5.0:
        lev_score = 0
    else:
        lev_score = 30 * (1 - (leverage - 2.0) / 3.0)
    score += lev_score

    # Position count component (15% weight, max 15 points)
    # 0-3 positions = 15 points, 4-5 = scaled, >5 = 0 points
    if num_positions <= 3:
        pos_score = 15
    elif num_positions >= 6:
        pos_score = 0
    else:
        pos_score = 15 * (1 - (num_positions - 3) / 3.0)
    score += pos_score

    # Margin usage component (15% weight, max 15 points)
    # <50% usage = 15 points, 50-80% = scaled, >80% = 0 points
    if margin_usage <= 0.5:
        margin_score = 15
    elif margin_usage >= 0.8:
        margin_score = 0
    else:
        margin_score = 15 * (1 - (margin_usage - 0.5) / 0.3)
    score += margin_score

    return int(round(max(0, min(100, score))))


def check_risk_limits(
    proposed_trade: Dict,
    portfolio_state: Dict,
    risk_limits: Dict
) -> Tuple[bool, List[str]]:
    """
    Check if a proposed trade violates any risk limits.

    Args:
        proposed_trade: Dict with 'size', 'leverage', 'confidence' keys
        portfolio_state: Dict with 'account_value', 'num_positions',
                        'current_leverage', 'liquidation_distance' keys
        risk_limits: Dict of risk limit thresholds

    Returns:
        Tuple of (passes_all_checks: bool, violations: List[str])

    Default risk limits:
    - max_positions: 3
    - max_leverage: 3.0
    - max_position_pct: 0.30 (30% of portfolio)
    - min_liquidation_distance: 0.20 (20%)
    - min_signal_confidence: 0.7
    """
    violations = []

    # Extract values with defaults
    max_positions = risk_limits.get('MAX_POSITIONS', 3)
    max_leverage = risk_limits.get('MAX_LEVERAGE', 3.0)
    max_position_pct = risk_limits.get('MAX_POSITION_PCT', 0.30)
    min_liq_distance = risk_limits.get('MIN_LIQUIDATION_DISTANCE', 0.20)
    min_confidence = risk_limits.get('MIN_SIGNAL_CONFIDENCE', 0.7)

    # Check position count
    num_positions = portfolio_state.get('num_positions', 0)
    if num_positions >= max_positions:
        violations.append(
            f"max_positions_exceeded: {num_positions}/{max_positions} positions"
        )

    # Check leverage
    current_leverage = portfolio_state.get('current_leverage', 0)
    trade_leverage = proposed_trade.get('leverage', 1.0)
    # Estimate new leverage after trade
    account_value = portfolio_state.get('account_value', 0)
    trade_size = proposed_trade.get('size', 0)

    if account_value > 0:
        current_position_value = current_leverage * account_value
        new_position_value = current_position_value + trade_size
        new_leverage = new_position_value / account_value

        if new_leverage > max_leverage:
            violations.append(
                f"leverage_limit_exceeded: {new_leverage:.2f}x > {max_leverage}x max"
            )

    # Check position size percentage
    if account_value > 0:
        position_pct = trade_size / account_value
        if position_pct > max_position_pct:
            violations.append(
                f"position_size_exceeded: {position_pct*100:.1f}% > {max_position_pct*100:.0f}% max"
            )

    # Check liquidation distance
    liq_distance = portfolio_state.get('liquidation_distance', 1.0)
    if liq_distance < min_liq_distance:
        violations.append(
            f"liquidation_risk_high: {liq_distance*100:.1f}% < {min_liq_distance*100:.0f}% min"
        )

    # Check signal confidence
    confidence = proposed_trade.get('confidence', 0)
    if confidence < min_confidence:
        violations.append(
            f"low_signal_confidence: {confidence:.2f} < {min_confidence} min"
        )

    return (len(violations) == 0, violations)


def calculate_position_risk_level(
    leverage: float,
    liquidation_distance: float,
    pnl_percent: float
) -> str:
    """
    Calculate risk level for a single position.

    Args:
        leverage: Position leverage
        liquidation_distance: Distance to liquidation (0.0 to 1.0)
        pnl_percent: Current PnL percentage

    Returns:
        Risk level: "low", "medium", "high", or "critical"
    """
    # Critical: High leverage + close to liquidation + large loss
    if liquidation_distance < 0.10 or (leverage > 4 and pnl_percent < -10):
        return "critical"

    # High: Elevated risk on multiple factors
    if liquidation_distance < 0.20 or leverage > 3 or pnl_percent < -15:
        return "high"

    # Medium: Some risk factors present
    if liquidation_distance < 0.35 or leverage > 2 or pnl_percent < -5:
        return "medium"

    return "low"


def calculate_concentration_risk(positions: List[Dict]) -> Dict[str, float]:
    """
    Calculate position concentration by asset.

    Args:
        positions: List of position dicts with 'symbol', 'size', 'current_price'

    Returns:
        Dict mapping symbol to concentration percentage (0.0 to 1.0)
    """
    if not positions:
        return {}

    total_value = calculate_portfolio_value(positions)
    if total_value <= 0:
        return {}

    concentration = {}
    for pos in positions:
        symbol = pos.get('symbol', 'UNKNOWN')
        size = abs(float(pos.get('size', 0)))
        price = float(pos.get('current_price', 0))
        value = size * price

        if symbol in concentration:
            concentration[symbol] += value / total_value
        else:
            concentration[symbol] = value / total_value

    return concentration
