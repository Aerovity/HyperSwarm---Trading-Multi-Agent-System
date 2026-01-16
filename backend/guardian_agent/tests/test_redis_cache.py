"""
Tests for Redis cache operations.
"""

from django.test import TestCase
from risk.utils.redis_cache import RedisCache, get_cache


class RedisCacheTests(TestCase):
    """Test Redis cache operations"""

    def setUp(self):
        """Set up test fixtures"""
        self.cache = get_cache()
        self.cache.client.flushdb()

    def tearDown(self):
        """Clean up after tests"""
        self.cache.client.flushdb()

    def test_connection(self):
        """Test Redis connection works"""
        self.assertTrue(self.cache.client.ping())

    def test_portfolio_state_set_and_get(self):
        """Test setting and getting portfolio state"""
        address = "0x1234567890abcdef"
        state = {
            'account_value': 10000,
            'leverage': 2.0,
            'positions': [],
        }

        self.cache.set_portfolio_state(address, state)
        retrieved = self.cache.get_portfolio_state(address)

        self.assertEqual(retrieved['account_value'], 10000)
        self.assertEqual(retrieved['leverage'], 2.0)

    def test_portfolio_state_expires(self):
        """Test portfolio state TTL works"""
        address = "0x1234567890abcdef"
        state = {'account_value': 10000}

        self.cache.set_portfolio_state(address, state, ttl=1)

        # Should exist immediately
        self.assertIsNotNone(self.cache.get_portfolio_state(address))

        # Wait for expiration (in real test, use mock time)
        # For now, just verify TTL was set
        ttl = self.cache.client.ttl(f"portfolio:{address}")
        self.assertGreater(ttl, 0)

    def test_risk_metrics_set_and_get(self):
        """Test setting and getting risk metrics"""
        address = "0x1234567890abcdef"
        metrics = {
            'health_score': 85,
            'leverage': 1.5,
        }

        self.cache.set_risk_metrics(address, metrics)
        retrieved = self.cache.get_risk_metrics(address)

        self.assertEqual(retrieved['health_score'], 85)

    def test_approval_storage(self):
        """Test approval storage and retrieval"""
        approval_id = "approval_123"
        approval_data = {
            'decision': 'approve',
            'risk_score': 30,
            'reasoning': 'Good trade',
        }

        self.cache.set_approval(approval_id, approval_data)
        retrieved = self.cache.get_approval(approval_id)

        self.assertEqual(retrieved['decision'], 'approve')
        self.assertEqual(retrieved['risk_score'], 30)

    def test_recent_approvals_rolling_window(self):
        """Test recent approvals rolling window"""
        # Add multiple approvals
        for i in range(5):
            self.cache.set_approval(
                f"approval_{i}",
                {'decision': 'approve', 'index': i}
            )

        # Get recent approvals
        recent = self.cache.get_recent_approvals(limit=3)

        self.assertEqual(len(recent), 3)
        # Most recent should be first
        self.assertEqual(recent[0]['index'], 4)

    def test_alert_storage(self):
        """Test alert storage"""
        alert = {
            'id': 'alert_123',
            'severity': 'warning',
            'message': 'High leverage detected',
        }

        self.cache.add_alert(alert)
        alerts = self.cache.get_alerts(limit=10)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['severity'], 'warning')

    def test_alerts_rolling_window(self):
        """Test alerts rolling window"""
        # Add multiple alerts
        for i in range(10):
            self.cache.add_alert({
                'id': f'alert_{i}',
                'severity': 'info',
                'message': f'Alert {i}',
            })

        alerts = self.cache.get_alerts(limit=5)
        self.assertEqual(len(alerts), 5)

    def test_clear_all_alerts(self):
        """Test clearing all alerts"""
        for i in range(3):
            self.cache.add_alert({
                'id': f'alert_{i}',
                'severity': 'info',
            })

        self.cache.clear_alerts()
        alerts = self.cache.get_alerts()

        self.assertEqual(len(alerts), 0)

    def test_activity_logging(self):
        """Test activity logging"""
        log_entry = {
            'id': 'log_123',
            'timestamp': '2025-01-16T10:00:00Z',
            'agent': 'guardian',
            'type': 'info',
            'message': 'Test log',
        }

        self.cache.log_activity(log_entry)
        logs = self.cache.get_logs(limit=10)

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['agent'], 'guardian')

    def test_logs_rolling_window(self):
        """Test logs rolling window"""
        # Add more logs than window size
        for i in range(150):
            self.cache.log_activity({
                'id': f'log_{i}',
                'agent': 'guardian',
                'message': f'Log {i}',
            })

        # Should only keep LOG_WINDOW_SIZE (default 100)
        logs = self.cache.get_logs(limit=200)
        self.assertLessEqual(len(logs), 100)

    def test_get_nonexistent_portfolio(self):
        """Test getting non-existent portfolio returns None"""
        result = self.cache.get_portfolio_state("nonexistent")
        self.assertIsNone(result)

    def test_get_nonexistent_approval(self):
        """Test getting non-existent approval returns None"""
        result = self.cache.get_approval("nonexistent")
        self.assertIsNone(result)
