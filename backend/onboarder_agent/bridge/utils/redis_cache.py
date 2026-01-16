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
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT} DB {settings.REDIS_DB}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def set_quote(self, quote_id: str, quote_data: dict, ttl: int = 30):
        """
        Store bridge quote with TTL.

        Args:
            quote_id: Unique quote identifier
            quote_data: Quote data dictionary
            ttl: Time to live in seconds (default 30)
        """
        try:
            key = f"quote:{quote_id}"
            self.client.setex(key, ttl, json.dumps(quote_data))

            # Add to rolling window list
            self.client.lpush("quotes:recent", quote_id)
            self.client.ltrim("quotes:recent", 0, settings.QUOTE_WINDOW_SIZE - 1)
        except Exception as e:
            logger.error(f"Failed to set quote {quote_id}: {e}")

    def get_quote(self, quote_id: str) -> Optional[dict]:
        """Get quote by ID"""
        try:
            data = self.client.get(f"quote:{quote_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get quote {quote_id}: {e}")
            return None

    def set_transaction(self, tx_id: str, tx_data: dict):
        """
        Store bridge transaction.

        Args:
            tx_id: Transaction identifier
            tx_data: Transaction data dictionary
        """
        try:
            key = f"transaction:{tx_id}"
            self.client.set(key, json.dumps(tx_data))

            # Add to rolling window list
            self.client.lpush("transactions:recent", tx_id)
            self.client.ltrim("transactions:recent", 0, settings.TRANSACTION_WINDOW_SIZE - 1)
        except Exception as e:
            logger.error(f"Failed to set transaction {tx_id}: {e}")

    def get_transaction(self, tx_id: str) -> Optional[dict]:
        """Get transaction by ID"""
        try:
            data = self.client.get(f"transaction:{tx_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get transaction {tx_id}: {e}")
            return None

    def update_transaction(self, tx_id: str, updates: dict):
        """
        Update transaction with new data.

        Args:
            tx_id: Transaction identifier
            updates: Fields to update
        """
        try:
            tx_data = self.get_transaction(tx_id)
            if tx_data:
                tx_data.update(updates)
                self.client.set(f"transaction:{tx_id}", json.dumps(tx_data))
        except Exception as e:
            logger.error(f"Failed to update transaction {tx_id}: {e}")

    def get_recent_transactions(self, limit: int = 20) -> list:
        """Get recent transactions from rolling window"""
        try:
            tx_ids = self.client.lrange("transactions:recent", 0, limit - 1)
            transactions = []

            for tx_id in tx_ids:
                data = self.get_transaction(tx_id)
                if data:
                    transactions.append(data)

            return transactions
        except Exception as e:
            logger.error(f"Failed to get recent transactions: {e}")
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
