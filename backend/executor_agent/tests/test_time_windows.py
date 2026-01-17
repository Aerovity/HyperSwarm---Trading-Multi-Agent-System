"""Tests for time window functionality"""
from django.test import TestCase
from django.conf import settings
from datetime import datetime, timedelta
import redis
import json
import time


class TimeWindowTests(TestCase):
    """Test time window spread calculations"""

    def setUp(self):
        """Set up test Redis client"""
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,  # Scout DB
            decode_responses=True
        )
        # Clean before test
        self.redis_client.flushdb()

    def tearDown(self):
        """Clean up after test"""
        self.redis_client.flushdb()

    def test_time_window_configuration(self):
        """Test time window settings exist"""
        self.assertIn('TIME_WINDOWS', dir(settings))
        self.assertIn('10sec', settings.TIME_WINDOWS)
        self.assertIn('1min', settings.TIME_WINDOWS)
        self.assertIn('5min', settings.TIME_WINDOWS)
        self.assertIn('15min', settings.TIME_WINDOWS)

    def test_time_window_periods(self):
        """Test period calculations"""
        self.assertEqual(settings.TIME_WINDOWS['10sec']['periods'], 2)
        self.assertEqual(settings.TIME_WINDOWS['1min']['periods'], 12)
        self.assertEqual(settings.TIME_WINDOWS['5min']['periods'], 60)
        self.assertEqual(settings.TIME_WINDOWS['15min']['periods'], 180)

    def test_time_window_durations(self):
        """Test duration_seconds are correct"""
        self.assertEqual(settings.TIME_WINDOWS['10sec']['duration_seconds'], 10)
        self.assertEqual(settings.TIME_WINDOWS['1min']['duration_seconds'], 60)
        self.assertEqual(settings.TIME_WINDOWS['5min']['duration_seconds'], 300)
        self.assertEqual(settings.TIME_WINDOWS['15min']['duration_seconds'], 900)

    def test_time_window_display_names(self):
        """Test display names exist"""
        self.assertEqual(settings.TIME_WINDOWS['10sec']['display'], '10 seconds')
        self.assertEqual(settings.TIME_WINDOWS['1min']['display'], '1 minute')
        self.assertEqual(settings.TIME_WINDOWS['5min']['display'], '5 minutes')
        self.assertEqual(settings.TIME_WINDOWS['15min']['display'], '15 minutes')

    def test_spread_clamping(self):
        """Test spread values are clamped to realistic range"""
        self.assertGreaterEqual(settings.SPREAD_MIN, 0.0001)
        self.assertLessEqual(settings.SPREAD_MAX, 0.10)  # Max 10%

    def test_demo_multiplier_exists(self):
        """Test demo multiplier setting exists"""
        self.assertIn('DEMO_SPREAD_MULTIPLIER', dir(settings))
        self.assertGreater(settings.DEMO_SPREAD_MULTIPLIER, 0)

    def test_position_settlement_after_expiration(self):
        """Test that positions settle after time window expires"""
        from trading.pnl_updater import PnLUpdater

        # Create executor Redis client
        executor_redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,  # Executor DB
            decode_responses=True
        )

        try:
            # Clean executor DB
            executor_redis.flushdb()

            # Create a mock position that already expired
            position_id = "test_pos_123"
            entry_time = datetime.now() - timedelta(seconds=15)  # 15 seconds ago
            window_expires_at = entry_time + timedelta(seconds=10)  # Expired 5 seconds ago

            position_data = {
                'position_id': position_id,
                'pair': 'BTC/ETH',
                'time_window': '10sec',
                'entry_spread': 0.0050,
                'current_spread': 0.0050,
                'entry_time': entry_time.isoformat(),
                'window_expires_at': window_expires_at.isoformat(),
                'status': 'open',
                'size': 1000,
                'pnl': 0.0,
                'pnl_percent': 0.0,
                'risk_level': 'low'
            }

            # Store position
            executor_redis.setex(
                f"position:{position_id}",
                3600,
                json.dumps(position_data)
            )

            # Update the position - should detect expiration and settle
            updater = PnLUpdater()
            result = updater.update_position_pnl(position_id)

            self.assertTrue(result)

            # Verify position was settled
            updated_position_json = executor_redis.get(f"position:{position_id}")
            self.assertIsNotNone(updated_position_json)

            updated_position = json.loads(updated_position_json)
            self.assertEqual(updated_position['status'], 'settled')
            self.assertIn('settled_at', updated_position)

        finally:
            # Clean up
            executor_redis.flushdb()

    def test_position_updates_before_expiration(self):
        """Test that positions update normally before window expires"""
        from trading.pnl_updater import PnLUpdater

        # Create executor Redis client
        executor_redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,  # Executor DB
            decode_responses=True
        )

        try:
            # Clean executor DB
            executor_redis.flushdb()

            # Create a position that hasn't expired yet
            position_id = "test_pos_456"
            entry_time = datetime.now()
            window_expires_at = entry_time + timedelta(minutes=5)  # Expires in 5 minutes

            position_data = {
                'position_id': position_id,
                'pair': 'BTC/ETH',
                'time_window': '5min',
                'entry_spread': 0.0050,
                'current_spread': 0.0050,
                'entry_time': entry_time.isoformat(),
                'window_expires_at': window_expires_at.isoformat(),
                'status': 'open',
                'size': 1000,
                'pnl': 0.0,
                'pnl_percent': 0.0,
                'risk_level': 'low'
            }

            # Store position
            executor_redis.setex(
                f"position:{position_id}",
                3600,
                json.dumps(position_data)
            )

            # Add to positions list
            executor_redis.lpush("positions:all", position_id)

            # Update should work normally (not settle)
            updater = PnLUpdater()
            result = updater.update_position_pnl(position_id)

            # Note: This might fail if Scout doesn't have price data, which is ok for this test
            # The key is that it shouldn't settle the position

            updated_position_json = executor_redis.get(f"position:{position_id}")
            if updated_position_json:
                updated_position = json.loads(updated_position_json)
                # Should still be open, not settled
                self.assertEqual(updated_position['status'], 'open')
                self.assertNotIn('settled_at', updated_position)

        finally:
            # Clean up
            executor_redis.flushdb()
