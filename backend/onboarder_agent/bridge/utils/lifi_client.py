"""
LI.FI API client for cross-chain bridge quotes and status checking.
Pure API wrapper - NO LLM, only HTTP requests.
"""

import requests
import logging
import time
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from django.conf import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, calls: int, period: int):
        """
        Args:
            calls: Number of calls allowed
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.timestamps = []

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()

        # Remove timestamps older than period
        self.timestamps = [ts for ts in self.timestamps if now - ts < self.period]

        if len(self.timestamps) >= self.calls:
            sleep_time = self.period - (now - self.timestamps[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self.timestamps.append(time.time())


class LiFiClient:
    """LI.FI API client for bridge operations"""

    def __init__(self):
        self.api_url = settings.LIFI['API_URL']
        self.api_key = settings.LIFI['API_KEY']
        self.integrator = settings.LIFI['INTEGRATOR']
        self.rate_limiter = RateLimiter(
            settings.RATE_LIMIT_CALLS,
            settings.RATE_LIMIT_PERIOD
        )
        self.session = requests.Session()

        # Set headers
        self.session.headers.update({
            'Content-Type': 'application/json',
        })

        if self.api_key:
            self.session.headers.update({
                'x-lifi-api-key': self.api_key
            })

    def get_quote(
        self,
        from_chain_id: str,
        to_chain_id: str,
        from_token: str,
        to_token: str,
        from_amount: str,
        from_address: str,
        slippage: float = 0.03
    ) -> Optional[Dict]:
        """
        Get bridge quote from LI.FI.

        Args:
            from_chain_id: Source chain ID (e.g., "137" for Polygon)
            to_chain_id: Destination chain ID (e.g., "998" for Hyperliquid)
            from_token: Source token address or symbol
            to_token: Destination token address or symbol
            from_amount: Amount in smallest unit (e.g., "1000000" for 1 USDC)
            from_address: User's wallet address
            slippage: Slippage tolerance (default 0.03 = 3%)

        Returns:
            Quote data dict or None on error
        """
        try:
            self.rate_limiter.wait_if_needed()

            params = {
                'fromChain': from_chain_id,
                'toChain': to_chain_id,
                'fromToken': from_token,
                'toToken': to_token,
                'fromAmount': from_amount,
                'fromAddress': from_address,
                'slippage': slippage,
                'integrator': self.integrator,
            }

            url = f"{self.api_url}/quote"
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"LI.FI quote error {response.status_code}: {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.error("LI.FI API timeout")
            return None
        except Exception as e:
            logger.error(f"Failed to get LI.FI quote: {e}")
            return None

    def get_status(
        self,
        tx_hash: str,
        from_chain_id: Optional[str] = None,
        to_chain_id: Optional[str] = None,
        bridge: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Check bridge transaction status.

        Args:
            tx_hash: Transaction hash
            from_chain_id: Source chain ID (speeds up request)
            to_chain_id: Destination chain ID (optional)
            bridge: Bridge tool name (optional)

        Returns:
            Status data dict or None on error
        """
        try:
            self.rate_limiter.wait_if_needed()

            params = {'txHash': tx_hash}

            if from_chain_id:
                params['fromChain'] = from_chain_id
            if to_chain_id:
                params['toChain'] = to_chain_id
            if bridge:
                params['bridge'] = bridge

            url = f"{self.api_url}/status"
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"LI.FI status error {response.status_code}: {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.error("LI.FI API timeout")
            return None
        except Exception as e:
            logger.error(f"Failed to get LI.FI status: {e}")
            return None

    def get_chains(self) -> List[Dict]:
        """
        Get list of supported chains.

        Returns:
            List of chain info dicts
        """
        try:
            self.rate_limiter.wait_if_needed()

            url = f"{self.api_url}/chains"
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                return response.json()['chains']
            else:
                logger.error(f"LI.FI chains error {response.status_code}: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Failed to get LI.FI chains: {e}")
            return []

    def get_tokens(self, chain_id: Optional[str] = None) -> List[Dict]:
        """
        Get list of supported tokens.

        Args:
            chain_id: Filter by chain ID (optional)

        Returns:
            List of token info dicts
        """
        try:
            self.rate_limiter.wait_if_needed()

            url = f"{self.api_url}/tokens"
            params = {}

            if chain_id:
                params['chains'] = chain_id

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()['tokens']
            else:
                logger.error(f"LI.FI tokens error {response.status_code}: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Failed to get LI.FI tokens: {e}")
            return []


# Create singleton instance
lifi_client = LiFiClient()
