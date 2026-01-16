"""
Integration tests for REST API endpoints.
"""

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from risk.utils.redis_cache import get_cache


class HealthCheckTests(TestCase):
    """Test health check endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.cache = get_cache()
        self.cache.client.flushdb()

    def tearDown(self):
        self.cache.client.flushdb()

    def test_health_check_healthy(self):
        """Test /api/health returns healthy when Redis connected"""
        response = self.client.get('/api/health')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'guardian_agent')
        self.assertEqual(data['redis'], 'connected')


class AgentLogsTests(TestCase):
    """Test agent logs endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.cache = get_cache()
        self.cache.client.flushdb()

        # Add test log
        self.cache.log_activity({
            'id': 'test_log_1',
            'timestamp': '2025-01-16T10:00:00Z',
            'agent': 'guardian',
            'type': 'info',
            'message': 'Test log message',
        })

    def tearDown(self):
        self.cache.client.flushdb()

    def test_get_logs(self):
        """Test /api/agent/logs returns logs"""
        response = self.client.get('/api/agent/logs')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['agent'], 'guardian')

    def test_get_logs_with_limit(self):
        """Test /api/agent/logs with limit parameter"""
        # Add more logs
        for i in range(10):
            self.cache.log_activity({
                'id': f'log_{i}',
                'agent': 'guardian',
                'message': f'Log {i}',
            })

        response = self.client.get('/api/agent/logs?limit=5')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data), 5)


@override_settings(DEMO_MODE=True)
class PortfolioStateTests(TestCase):
    """Test portfolio state endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.cache = get_cache()
        self.cache.client.flushdb()

    def tearDown(self):
        self.cache.client.flushdb()

    def test_portfolio_state_requires_address(self):
        """Test /api/portfolio/state requires address parameter"""
        response = self.client.get('/api/portfolio/state')

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_portfolio_state_demo_mode(self):
        """Test /api/portfolio/state returns demo data"""
        response = self.client.get('/api/portfolio/state?address=0x1234')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('account_value', data)
        self.assertIn('health_score', data)
        self.assertIn('effective_leverage', data)


@override_settings(DEMO_MODE=True)
class PositionsTests(TestCase):
    """Test positions endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.cache = get_cache()
        self.cache.client.flushdb()

    def tearDown(self):
        self.cache.client.flushdb()

    def test_positions_requires_address(self):
        """Test /api/positions requires address parameter"""
        response = self.client.get('/api/positions')

        self.assertEqual(response.status_code, 400)

    def test_positions_demo_mode(self):
        """Test /api/positions returns demo positions"""
        response = self.client.get('/api/positions?address=0x1234')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('positions', data)
        self.assertIn('total_positions', data)
        self.assertIsInstance(data['positions'], list)


@override_settings(DEMO_MODE=True)
class RiskMetricsTests(TestCase):
    """Test risk metrics endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.cache = get_cache()
        self.cache.client.flushdb()

    def tearDown(self):
        self.cache.client.flushdb()

    def test_risk_metrics_requires_address(self):
        """Test /api/risk/metrics requires address parameter"""
        response = self.client.get('/api/risk/metrics')

        self.assertEqual(response.status_code, 400)

    def test_risk_metrics_demo_mode(self):
        """Test /api/risk/metrics returns demo metrics"""
        response = self.client.get('/api/risk/metrics?address=0x1234')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('health_score', data)
        self.assertIn('margin_usage', data)
        self.assertIn('effective_leverage', data)
        self.assertIn('risk_breakdown', data)


@override_settings(DEMO_MODE=True)
class TradeApprovalTests(TestCase):
    """Test trade approval endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.cache = get_cache()
        self.cache.client.flushdb()

    def tearDown(self):
        self.cache.client.flushdb()

    def test_approve_valid_trade(self):
        """Test POST /api/trade/approve with valid trade"""
        response = self.client.post('/api/trade/approve', {
            'trade_proposal': {
                'pair': 'BTC/ETH',
                'zscore': 2.5,
                'size': 2500,
                'entry_spread': 0.015,
                'confidence': 0.85,
            },
            'portfolio_state': {
                'total_value': 10000,
                'available_margin': 7500,
                'margin_usage': 25,
                'leverage': 1.5,
                'num_positions': 1,
                'liquidation_distance': 40,
            },
            'market_conditions': {
                'btc_volatility': 3.5,
                'trend': 'neutral',
            },
        }, format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('decision', data)
        self.assertIn(data['decision'], ['approve', 'reject'])
        self.assertIn('approval_id', data)
        self.assertIn('reasoning', data)

    def test_approve_missing_pair(self):
        """Test POST /api/trade/approve without required pair"""
        response = self.client.post('/api/trade/approve', {
            'trade_proposal': {},
            'portfolio_state': {},
            'market_conditions': {},
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_approve_stores_in_cache(self):
        """Test that approval is stored in cache"""
        response = self.client.post('/api/trade/approve', {
            'trade_proposal': {
                'pair': 'BTC/ETH',
                'zscore': 2.5,
                'size': 2500,
                'confidence': 0.85,
            },
            'portfolio_state': {
                'total_value': 10000,
                'num_positions': 1,
                'leverage': 1.5,
                'liquidation_distance': 40,
            },
            'market_conditions': {'btc_volatility': 3.5, 'trend': 'neutral'},
        }, format='json')

        data = response.json()
        approval_id = data['approval_id']

        # Check it's in cache
        cached = self.cache.get_approval(approval_id)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['decision'], data['decision'])


class AlertsTests(TestCase):
    """Test alerts endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.cache = get_cache()
        self.cache.client.flushdb()

        # Add test alert
        self.cache.add_alert({
            'id': 'alert_1',
            'severity': 'warning',
            'type': 'leverage_warning',
            'message': 'High leverage detected',
            'address': '0x1234',
            'acknowledged': False,
        })

    def tearDown(self):
        self.cache.client.flushdb()

    def test_get_alerts(self):
        """Test GET /api/alerts returns alerts"""
        response = self.client.get('/api/alerts')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('alerts', data)
        self.assertIn('unacknowledged_count', data)
        self.assertEqual(len(data['alerts']), 1)

    def test_get_alerts_filtered_by_address(self):
        """Test GET /api/alerts filtered by address"""
        # Add alert for different address
        self.cache.add_alert({
            'id': 'alert_2',
            'severity': 'info',
            'address': '0x5678',
        })

        response = self.client.get('/api/alerts?address=0x1234')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should only return alerts for 0x1234
        self.assertEqual(len(data['alerts']), 1)
        self.assertEqual(data['alerts'][0]['address'], '0x1234')
