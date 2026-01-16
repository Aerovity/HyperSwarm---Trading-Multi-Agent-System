"""
Hyperliquid client for Guardian Agent.
Fetches positions, account state, and margin information from testnet.
Extended from Onboarder's client to include position tracking.
"""

import requests
import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)


class HyperliquidClient:
    """Client for Hyperliquid position and account data"""

    def __init__(self):
        self.api_url = settings.HYPERLIQUID['API_URL']

    def get_user_state(self, address: str) -> Optional[Dict]:
        """
        Get complete user state from Hyperliquid.

        Args:
            address: User's wallet address (0x...)

        Returns:
            Dict with keys:
                - account_value: float
                - withdrawable: float
                - total_margin_used: float
                - available_margin: float
                - positions: List[Dict]
                - leverage: float (effective portfolio leverage)
        """
        try:
            response = requests.post(
                f"{self.api_url}/info",
                json={
                    "type": "clearinghouseState",
                    "user": address,
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"Hyperliquid API error {response.status_code}: {response.text}")
                return None

            data = response.json()

            # Extract margin summary
            margin_summary = data.get('marginSummary', {})
            account_value = float(margin_summary.get('accountValue', 0))
            total_margin_used = float(margin_summary.get('totalMarginUsed', 0))
            withdrawable = float(data.get('withdrawable', 0))

            # Calculate available margin
            available_margin = account_value - total_margin_used

            # Extract positions
            positions = self._parse_positions(data.get('assetPositions', []))

            # Calculate total position value and leverage
            total_position_value = sum(
                abs(float(p.get('size', 0))) * float(p.get('mark_price', 0))
                for p in positions
            )
            leverage = total_position_value / account_value if account_value > 0 else 0

            return {
                'address': address,
                'account_value': account_value,
                'withdrawable': withdrawable,
                'total_margin_used': total_margin_used,
                'available_margin': available_margin,
                'positions': positions,
                'leverage': leverage,
                'num_positions': len(positions),
            }

        except requests.exceptions.Timeout:
            logger.error("Hyperliquid API timeout")
            return None
        except Exception as e:
            logger.error(f"Failed to get Hyperliquid user state: {e}")
            return None

    def get_positions(self, address: str) -> List[Dict]:
        """
        Get all open positions for a user.

        Args:
            address: User's wallet address

        Returns:
            List of position dicts with keys:
                - symbol: str (e.g., "BTC")
                - size: float (signed, negative for short)
                - entry_price: float
                - mark_price: float
                - unrealized_pnl: float
                - leverage: float
                - liquidation_price: float
                - margin_used: float
                - is_long: bool
        """
        try:
            response = requests.post(
                f"{self.api_url}/info",
                json={
                    "type": "clearinghouseState",
                    "user": address,
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"Hyperliquid API error {response.status_code}")
                return []

            data = response.json()
            return self._parse_positions(data.get('assetPositions', []))

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    def _parse_positions(self, asset_positions: List) -> List[Dict]:
        """
        Parse raw asset positions into structured format.

        Args:
            asset_positions: Raw positions from Hyperliquid API

        Returns:
            List of structured position dicts
        """
        positions = []

        for asset_pos in asset_positions:
            position = asset_pos.get('position', {})

            # Skip if no position
            szi = float(position.get('szi', 0))
            if szi == 0:
                continue

            entry_px = float(position.get('entryPx', 0))
            mark_px = float(position.get('markPx', entry_px))
            liquidation_px = float(position.get('liquidationPx', 0))
            margin_used = float(position.get('marginUsed', 0))
            unrealized_pnl = float(position.get('unrealizedPnl', 0))

            # Determine if long or short
            is_long = szi > 0
            size = abs(szi)

            # Calculate leverage
            position_value = size * entry_px
            leverage = position_value / margin_used if margin_used > 0 else 1.0

            positions.append({
                'symbol': position.get('coin', 'UNKNOWN'),
                'size': szi,  # Keep signed for direction
                'entry_price': entry_px,
                'mark_price': mark_px,
                'current_price': mark_px,  # Alias
                'unrealized_pnl': unrealized_pnl,
                'leverage': leverage,
                'liquidation_price': liquidation_px,
                'margin_used': margin_used,
                'is_long': is_long,
            })

        return positions

    def get_account_summary(self, address: str) -> Optional[Dict]:
        """
        Get account summary with margin info.

        Args:
            address: User's wallet address

        Returns:
            Dict with keys:
                - account_value: float
                - total_margin_used: float
                - total_position_value: float
                - withdrawable: float
                - maintenance_margin: float
        """
        state = self.get_user_state(address)
        if not state:
            return None

        # Calculate total position value
        total_position_value = sum(
            abs(float(p.get('size', 0))) * float(p.get('mark_price', 0))
            for p in state.get('positions', [])
        )

        return {
            'address': address,
            'account_value': state['account_value'],
            'total_margin_used': state['total_margin_used'],
            'total_position_value': total_position_value,
            'withdrawable': state['withdrawable'],
            'available_margin': state['available_margin'],
        }

    def check_sufficient_funds(
        self,
        address: str,
        required_amount: float
    ) -> Tuple[bool, float]:
        """
        Check if user has sufficient funds for a trade.

        Args:
            address: User's wallet address
            required_amount: Required amount in USD

        Returns:
            Tuple of (has_sufficient_funds: bool, available_amount: float)
        """
        try:
            state = self.get_user_state(address)

            if state is None:
                logger.warning(f"Could not check funds for {address}")
                return False, 0.0

            available = state['available_margin']
            has_sufficient = available >= required_amount

            if not has_sufficient:
                logger.info(
                    f"Insufficient funds for {address}: "
                    f"required ${required_amount:.2f}, "
                    f"available ${available:.2f}"
                )

            return has_sufficient, available

        except Exception as e:
            logger.error(f"Failed to check sufficient funds: {e}")
            return False, 0.0

    def get_asset_info(self, symbol: str) -> Optional[Dict]:
        """
        Get asset/market information.

        Args:
            symbol: Asset symbol (e.g., "BTC")

        Returns:
            Dict with max_leverage, tick_size, lot_size, etc.
        """
        try:
            response = requests.post(
                f"{self.api_url}/info",
                json={"type": "meta"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code != 200:
                return None

            data = response.json()
            universe = data.get('universe', [])

            for asset in universe:
                if asset.get('name', '').upper() == symbol.upper():
                    return {
                        'symbol': asset.get('name'),
                        'max_leverage': asset.get('maxLeverage', 50),
                        'sz_decimals': asset.get('szDecimals', 3),
                    }

            return None

        except Exception as e:
            logger.error(f"Failed to get asset info: {e}")
            return None


# Singleton instance
hyperliquid_client = HyperliquidClient()


def get_demo_user_state(address: str) -> Dict:
    """
    Generate demo user state for testing.

    Args:
        address: User's wallet address

    Returns:
        Mock user state dict
    """
    return {
        'address': address,
        'account_value': 10000.0,
        'withdrawable': 5000.0,
        'total_margin_used': 2500.0,
        'available_margin': 7500.0,
        'leverage': 2.0,
        'num_positions': 2,
        'positions': [
            {
                'symbol': 'BTC',
                'size': 0.1,
                'entry_price': 50000.0,
                'mark_price': 51000.0,
                'current_price': 51000.0,
                'unrealized_pnl': 100.0,
                'leverage': 2.0,
                'liquidation_price': 40000.0,
                'margin_used': 2500.0,
                'is_long': True,
            },
            {
                'symbol': 'ETH',
                'size': 2.0,
                'entry_price': 2500.0,
                'mark_price': 2550.0,
                'current_price': 2550.0,
                'unrealized_pnl': 100.0,
                'leverage': 2.5,
                'liquidation_price': 2000.0,
                'margin_used': 2000.0,
                'is_long': True,
            },
        ],
    }


def get_demo_positions(address: str) -> List[Dict]:
    """
    Generate demo positions for testing.

    Args:
        address: User's wallet address

    Returns:
        Mock positions list
    """
    state = get_demo_user_state(address)
    return state['positions']
