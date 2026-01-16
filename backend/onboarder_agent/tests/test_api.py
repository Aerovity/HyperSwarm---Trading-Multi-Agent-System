"""
Tests for REST API endpoints.
"""

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from bridge.utils.redis_cache import RedisCache
from bridge.utils.json_storage import JSONStorage


class APIEndpointTests(TestCase):
    """Test REST API endpoints"""

    def setUp(self):
        """Set up test client and Redis data"""
        self.client = APIClient()
        self.cache = RedisCache()
        self.storage = JSONStorage()
        self.cache.client.flushdb()

        # Add test log
        log_entry = {
            "id": "onboarder_1",
            "timestamp": "2025-01-16T10:00:00Z",
            "agent": "onboarder",
            "type": "info",
            "message": "Test log message"
        }
        self.cache.log_activity(log_entry)

    def tearDown(self):
        """Clean up Redis"""
        self.cache.client.flushdb()

    @override_settings(DEMO_MODE=True)
    def test_bridge_quote_endpoint_demo_mode(self):
        """Test /api/bridge/quote in demo mode"""
        response = self.client.get('/api/bridge/quote', {
            'fromChain': '137',
            'toChain': '998',
            'token': 'USDC',
            'amount': '1000000',
            'fromAddress': '0x123'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('route_id', data)
        self.assertEqual(data['from_chain'], '137')
        self.assertEqual(data['to_chain'], '998')
        self.assertEqual(data['token'], 'USDC')
        self.assertTrue(data['demo_mode'])

    def test_bridge_quote_missing_params(self):
        """Test /api/bridge/quote with missing parameters"""
        response = self.client.get('/api/bridge/quote', {
            'fromChain': '137',
            # Missing amount and fromAddress
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    @override_settings(DEMO_MODE=True)
    def test_bridge_execute_endpoint_demo_mode(self):
        """Test /api/bridge/execute in demo mode"""
        # First get a quote
        quote_response = self.client.get('/api/bridge/quote', {
            'fromChain': '137',
            'toChain': '998',
            'token': 'USDC',
            'amount': '1000000',
            'fromAddress': '0x123'
        })

        route_id = quote_response.json()['route_id']

        # Execute bridge
        response = self.client.post('/api/bridge/execute', {
            'route_id': route_id,
            'user_wallet': '0x123',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('transaction_id', data)
        self.assertEqual(data['status'], 'completed')
        self.assertTrue(data.get('demo_mode'))

    def test_bridge_execute_missing_route(self):
        """Test /api/bridge/execute with missing route"""
        response = self.client.post('/api/bridge/execute', {
            'route_id': 'nonexistent',
            'user_wallet': '0x123',
        }, format='json')

        self.assertEqual(response.status_code, 404)

    @override_settings(DEMO_MODE=True)
    def test_bridge_status_endpoint(self):
        """Test /api/bridge/status/{tx_id}"""
        # Create a transaction first
        tx_data = {
            'transaction_id': 'test_tx_status',
            'status': 'completed',
            'from_chain': '137',
            'to_chain': '998',
            'demo_mode': True,
        }
        self.cache.set_transaction('test_tx_status', tx_data)

        response = self.client.get('/api/bridge/status/test_tx_status')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['transaction_id'], 'test_tx_status')
        self.assertEqual(data['status'], 'completed')

    def test_bridge_status_not_found(self):
        """Test /api/bridge/status with nonexistent transaction"""
        response = self.client.get('/api/bridge/status/nonexistent')

        self.assertEqual(response.status_code, 404)

    @override_settings(DEMO_MODE=True)
    def test_supported_chains_endpoint(self):
        """Test /api/bridge/chains"""
        response = self.client.get('/api/bridge/chains')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('chains', data)
        self.assertIsInstance(data['chains'], list)
        self.assertGreater(len(data['chains']), 0)

    def test_agent_logs_endpoint(self):
        """Test /api/agent/logs"""
        response = self.client.get('/api/agent/logs')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['agent'], 'onboarder')

    def test_agent_logs_with_limit(self):
        """Test /api/agent/logs with limit parameter"""
        response = self.client.get('/api/agent/logs?limit=5')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertLessEqual(len(data), 5)

    def test_health_check_endpoint(self):
        """Test /api/health"""
        response = self.client.get('/api/health')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'onboarder_agent')
        self.assertEqual(data['redis'], 'connected')
        self.assertIn('demo_mode', data)
