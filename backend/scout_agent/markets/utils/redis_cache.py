"""
High-performance Redis cache manager for real-time data.
Implements rolling windows with sub-millisecond read/write operations.
"""

import redis
import json
import logging
from typing import Any, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """High-performance Redis cache for real-time data"""

    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def set_price(self, symbol: str, price: float, timestamp: str):
        """
        Store current price with timestamp.

        Also adds to time series for historical calculations.
        """
        try:
            key = f"price:{symbol}"
            data = {"price": price, "timestamp": timestamp}
            self.client.set(key, json.dumps(data))

            # Also add to time series for history (store as dict for timestamp)
            history_entry = json.dumps({"price": price, "timestamp": timestamp})
            self.client.lpush(f"history:{symbol}", history_entry)
            # Keep last PRICE_HISTORY_SIZE items (rolling window)
            self.client.ltrim(f"history:{symbol}", 0, settings.PRICE_HISTORY_SIZE - 1)
        except Exception as e:
            logger.error(f"Failed to set price for {symbol}: {e}")

    def get_price(self, symbol: str) -> Optional[dict]:
        """Get current price"""
        try:
            data = self.client.get(f"price:{symbol}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None

    def get_price_history(self, symbol: str, limit: int = 50) -> List[dict]:
        """Get recent price history"""
        try:
            prices = self.client.lrange(f"history:{symbol}", 0, limit - 1)
            history = []
            for p in prices:
                try:
                    # Try to parse as JSON (new format with timestamp)
                    history.append(json.loads(p))
                except (json.JSONDecodeError, TypeError):
                    # Fallback for old format (just price as float)
                    history.append({"price": float(p), "timestamp": ""})
            return history
        except Exception as e:
            logger.error(f"Failed to get price history for {symbol}: {e}")
            return []

    def set_signal(self, signal_id: str, signal_data: dict, ttl: int = 86400):
        """
        Store signal with TTL (24 hours default).

        Also adds to rolling window list for recent signals.
        """
        try:
            key = f"signal:{signal_id}"
            self.client.setex(key, ttl, json.dumps(signal_data))

            # Add to rolling window list
            self.client.lpush("signals:recent", signal_id)
            # Keep last SIGNAL_WINDOW_SIZE items
            self.client.ltrim("signals:recent", 0, settings.SIGNAL_WINDOW_SIZE - 1)
        except Exception as e:
            logger.error(f"Failed to set signal {signal_id}: {e}")

    def get_recent_signals(self, limit: int = 20) -> list:
        """Get recent signals from rolling window"""
        try:
            signal_ids = self.client.lrange("signals:recent", 0, limit - 1)
            signals = []

            for sid in signal_ids:
                data = self.client.get(f"signal:{sid}")
                if data:
                    signals.append(json.loads(data))

            return signals
        except Exception as e:
            logger.error(f"Failed to get recent signals: {e}")
            return []

    def log_activity(self, log_entry: dict):
        """Log agent activity with rolling window"""
        try:
            self.client.lpush("logs:agent", json.dumps(log_entry))
            # Keep last LOG_WINDOW_SIZE items
            self.client.ltrim("logs:agent", 0, settings.LOG_WINDOW_SIZE - 1)
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

    def get_logs(self, limit: int = 50) -> list:
        """Get recent agent logs"""
        try:
            logs = self.client.lrange("logs:agent", 0, limit - 1)
            return [json.loads(log) for log in logs]
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return []
