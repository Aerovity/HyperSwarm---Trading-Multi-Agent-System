"""
Hyperliquid balance checker for user wallet verification.
Uses hyperliquid-python-sdk to check user state and funds.
"""

import requests
import logging
from typing import Dict, Tuple, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class HyperliquidClient:
    """Client for checking Hyperliquid balances"""

    def __init__(self):
        self.api_url = settings.HYPERLIQUID['API_URL']

    def get_user_balance(self, address: str) -> Optional[Dict]:
        """
        Get user balance and account state from Hyperliquid.

        Args:
            address: User's wallet address (0x...)

        Returns:
            Dict with balance info or None on error
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

            # Extract key balance fields
            return {
                'address': address,
                'withdrawable': float(data.get('withdrawable', 0)),
                'account_value': float(data.get('marginSummary', {}).get('accountValue', 0)),
                'total_margin_used': float(data.get('marginSummary', {}).get('totalMarginUsed', 0)),
                'total_raw_usd': float(data.get('crossMarginSummary', {}).get('totalRawUsd', 0)),
            }

        except requests.exceptions.Timeout:
            logger.error("Hyperliquid API timeout")
            return None
        except Exception as e:
            logger.error(f"Failed to get Hyperliquid balance: {e}")
            return None

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
            balance = self.get_user_balance(address)

            if balance is None:
                logger.warning(f"Could not check funds for {address}")
                return False, 0.0

            # Use withdrawable amount as available funds
            available = balance['withdrawable']
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


# Create singleton instance
hyperliquid_client = HyperliquidClient()
