"""
API endpoint tests.
Tests REST API endpoints with Django test framework.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from markets.utils.redis_cache import RedisCache


class APITests(TestCase):
    """Test REST API endpoints"""

    def setUp(self):
        """Set up test client and Redis data"""
        self.client = APIClient()
        self.cache = RedisCache()
        self.cache.client.flushdb()

        # Add test price data
        self.cache.set_price("BTC-USD", 50000.0, "2025-01-16T10:00:00Z")
        self.cache.set_price("ETH-USD", 3000.0, "2025-01-16T10:00:00Z")

        # Add price history
        for i in range(50):
            self.cache.client.lpush("history:BTC-USD", str(50000 + i))
            self.cache.client.lpush("history:ETH-USD", str(3000 + i))

        # Add test log
        log_entry = {
            "id": "log_1",
            "timestamp": "2025-01-16T10:00:00Z",
            "agent": "scout",
            "type": "info",
            "message": "Test log message"
        }
        self.cache.log_activity(log_entry)

    def tearDown(self):
        """Clean up Redis"""
        self.cache.client.flushdb()

    def test_live_markets_endpoint(self):
        """Test /api/markets/live returns market data"""
        response = self.client.get('/api/markets/live')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("markets", data)
        self.assertIsInstance(data["markets"], list)

    def test_recent_signals_endpoint(self):
        """Test /api/signals/recent returns signals"""
        response = self.client.get('/api/signals/recent')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_agent_logs_endpoint(self):
        """Test /api/agent/logs returns logs"""
        response = self.client.get('/api/agent/logs')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_pair_correlations_endpoint(self):
        """Test /api/pairs/correlations returns correlation matrix"""
        response = self.client.get('/api/pairs/correlations')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("correlations", data)

    def test_health_check_endpoint(self):
        """Test /api/health returns health status"""
        response = self.client.get('/api/health')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")

    def test_analyze_and_signal_endpoint(self):
        """Test /api/signals/analyze triggers analysis"""
        response = self.client.post('/api/signals/analyze')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("signals_detected", data)
        self.assertIn("signals", data)
