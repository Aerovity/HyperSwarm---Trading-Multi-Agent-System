"""
Hyperliquid WebSocket client for real-time market data.
Runs in background thread with auto-reconnect.
"""

import time
import threading
import logging
from datetime import datetime
from hyperliquid.info import Info
from hyperliquid.utils import constants

from django.conf import settings
from .utils.redis_cache import RedisCache
from .utils.logger import log_agent_activity

logger = logging.getLogger(__name__)


class HyperliquidWebSocketClient:
    """
    Manages persistent WebSocket connection to Hyperliquid testnet.
    Runs in background thread, auto-reconnects on disconnect.
    """

    def __init__(self):
        """Initialize WebSocket client"""
        self.info = None
        self.cache = RedisCache()
        # Hyperliquid uses simple symbol names like "BTC", "ETH", "SOL"
        self.subscriptions = ["BTC", "ETH", "SOL", "AVAX", "MATIC"]
        self.running = False
        self.thread = None
        self.reconnect_delay = settings.HYPERLIQUID['RECONNECT_DELAY']

    def start(self):
        """Start WebSocket client in background thread"""
        if self.running:
            logger.warning("WebSocket client already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("WebSocket client started in background thread")

    def _run(self):
        """Main WebSocket loop (runs in background thread)"""
        while self.running:
            try:
                self._connect_and_monitor()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                log_agent_activity("scout", "error",
                    f"WebSocket connection error: {str(e)}")

                if self.running:
                    logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)

    def _connect_and_monitor(self):
        """Connect to Hyperliquid and monitor markets"""
        try:
            # Connect to testnet
            self.info = Info(constants.TESTNET_API_URL, skip_ws=False)

            log_agent_activity("scout", "success",
                f"Connected to Hyperliquid testnet")

            # Monitor markets (poll every 5 seconds to avoid rate limits)
            while self.running:
                self._fetch_and_store_prices()
                time.sleep(5)  # Increased from 1 to 5 seconds to avoid 429 errors

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    def _fetch_and_store_prices(self):
        """Fetch current prices and store to Redis"""
        try:
            # Get all mid prices (faster than fetching meta + trades)
            all_mids = self.info.all_mids()

            if all_mids:
                # Log available symbols for debugging (only first time)
                available_symbols = list(all_mids.keys())
                if not hasattr(self, '_logged_symbols'):
                    logger.info(f"Available symbols from Hyperliquid: {available_symbols[:10]}")
                    logger.info(f"Looking for: {self.subscriptions}")
                    self._logged_symbols = True

                found_count = 0
                for symbol, price in all_mids.items():
                    if symbol in self.subscriptions:
                        found_count += 1
                        try:
                            # Store to Redis
                            self.cache.set_price(
                                symbol,
                                float(price),
                                datetime.now().isoformat()
                            )

                            logger.info(f"Updated {symbol}: ${price}")
                        except Exception as e:
                            logger.error(f"Failed to store price for {symbol}: {e}")

                if found_count == 0:
                    logger.warning(f"No matching symbols found! Available: {available_symbols[:5]}")
                else:
                    logger.info(f"Successfully updated {found_count} symbols")

        except Exception as e:
            # Check if it's a rate limit error
            if hasattr(e, 'args') and len(e.args) > 0 and e.args[0] == 429:
                logger.warning("Rate limit hit (429), backing off...")
                time.sleep(10)  # Wait 10 seconds before reconnecting
            else:
                logger.error(f"Failed to fetch prices: {e}", exc_info=True)

    def stop(self):
        """Gracefully shutdown WebSocket connection"""
        logger.info("Stopping WebSocket client...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=5)

        log_agent_activity("scout", "info",
            "WebSocket client stopped")
