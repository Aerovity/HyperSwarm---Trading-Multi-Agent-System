"""
Redis integration tests.
Tests Redis cache operations with rolling windows.
"""

from django.test import TestCase
from markets.utils.redis_cache import RedisCache
import json


class RedisCacheTests(TestCase):
    """Test Redis cache operations"""

    def setUp(self):
        """Clear Redis before each test"""
        self.cache = RedisCache()
        self.cache.client.flushdb()

    def tearDown(self):
        """Clean up after each test"""
        self.cache.client.flushdb()

    def test_set_and_get_price(self):
        """Test storing and retrieving price data"""
        self.cache.set_price("BTC-USD", 50000.0, "2025-01-16T10:00:00Z")

        price_data = self.cache.get_price("BTC-USD")

        self.assertIsNotNone(price_data)
        self.assertEqual(price_data["price"], 50000.0)
        self.assertEqual(price_data["timestamp"], "2025-01-16T10:00:00Z")

    def test_price_history_rolling_window(self):
        """Test price history maintains rolling window"""
        # Add 150 prices
        for i in range(150):
            self.cache.set_price("ETH-USD", 3000 + i, f"2025-01-16T10:{i:02d}:00Z")

        history = self.cache.get_price_history("ETH-USD", limit=100)

        # Should only keep last 100 (PRICE_HISTORY_SIZE)
        self.assertEqual(len(history), 100)

    def test_signal_with_ttl(self):
        """Test signal storage with TTL"""
        signal_data = {
            "id": "signal_123",
            "pair": "BTC/ETH",
            "zscore": 2.5
        }

        self.cache.set_signal("signal_123", signal_data, ttl=60)

        # Signal should exist
        retrieved = self.cache.client.get("signal:signal_123")
        self.assertIsNotNone(retrieved)

    def test_recent_signals_rolling_window(self):
        """Test recent signals maintains rolling window"""
        # Add 50 signals
        for i in range(50):
            signal = {"id": f"signal_{i}", "value": i}
            self.cache.set_signal(f"signal_{i}", signal)

        signals = self.cache.get_recent_signals(limit=20)

        # Should return last 20
        self.assertEqual(len(signals), 20)

    def test_activity_logging(self):
        """Test agent activity logging"""
        log_entry = {
            "id": "log_123",
            "timestamp": "2025-01-16T10:00:00Z",
            "agent": "scout",
            "type": "info",
            "message": "Test log"
        }

        self.cache.log_activity(log_entry)

        logs = self.cache.get_logs(limit=10)

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["agent"], "scout")

    def test_logs_rolling_window(self):
        """Test logs maintains rolling window"""
        # Add 150 logs
        for i in range(150):
            log_entry = {
                "id": f"log_{i}",
                "timestamp": "2025-01-16T10:00:00Z",
                "agent": "scout",
                "type": "info",
                "message": f"Test message {i}"
            }
            self.cache.log_activity(log_entry)

        logs = self.cache.get_logs(limit=200)

        # Should only keep last 100 (LOG_WINDOW_SIZE)
        self.assertEqual(len(logs), 100)
