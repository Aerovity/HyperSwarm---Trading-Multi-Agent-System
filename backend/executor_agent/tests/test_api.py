"""
API endpoint tests.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from trading.utils.redis_cache import RedisCache

class APITests(TestCase):
    """Test REST API endpoints"""

    def setUp(self):
        """Set up test client and Redis data"""
        self.client = APIClient()
        self.cache = RedisCache()
        self.cache.client.flushdb()

    def tearDown(self):
        """Clean up Redis"""
        self.cache.client.flushdb()

    def test_health_check_endpoint(self):
        """Test /api/health returns health status"""
        response = self.client.get('/api/health')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')

    def test_agent_logs_endpoint(self):
        """Test /api/agent/logs returns logs"""
        response = self.client.get('/api/agent/logs')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_list_positions_endpoint(self):
        """Test /api/positions returns positions"""
        response = self.client.get('/api/positions')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
