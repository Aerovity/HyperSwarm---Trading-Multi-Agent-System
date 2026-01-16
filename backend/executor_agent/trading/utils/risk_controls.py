"""
Risk control validation functions.
NO LLM - only boolean checks.
"""
from typing import Tuple

def validate_max_positions(current_positions: int, max_positions: int = 3) -> bool:
    """Ensure maximum concurrent positions limit."""
    return current_positions < max_positions

def validate_position_size(
    position_size: float,
    portfolio_value: float,
    max_allocation: float = 0.30
) -> bool:
    """Ensure position size doesn't exceed allocation limit."""
    if portfolio_value <= 0:
        return False
    max_size = portfolio_value * max_allocation
    return position_size <= max_size

def validate_leverage(leverage: float, max_leverage: float = 3.0) -> bool:
    """Ensure leverage doesn't exceed maximum."""
    return leverage <= max_leverage

def validate_portfolio_value(portfolio_value: float, min_value: float = 100.0) -> bool:
    """Ensure portfolio has minimum value to trade."""
    return portfolio_value >= min_value

def validate_all_risk_controls(
    position_size: float,
    portfolio_value: float,
    leverage: float,
    current_positions: int,
    max_positions: int = 3,
    max_allocation: float = 0.30,
    max_leverage: float = 3.0,
    min_portfolio: float = 100.0
) -> Tuple[bool, str]:
    """Validate all risk controls at once."""
    if not validate_portfolio_value(portfolio_value, min_portfolio):
        return False, f"Portfolio value ${portfolio_value:.2f} below minimum ${min_portfolio:.2f}"
    if not validate_max_positions(current_positions, max_positions):
        return False, f"Maximum {max_positions} concurrent positions already open"
    if not validate_position_size(position_size, portfolio_value, max_allocation):
        return False, f"Position size ${position_size:.2f} exceeds {max_allocation*100}% allocation limit"
    if not validate_leverage(leverage, max_leverage):
        return False, f"Leverage {leverage:.2f}x exceeds maximum {max_leverage}x"
    return True, "All risk controls passed"
