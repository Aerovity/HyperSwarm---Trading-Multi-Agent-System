"""
Tests for transaction management and demo mode.
"""

from django.test import TestCase, override_settings
from bridge.utils.redis_cache import RedisCache
from bridge.utils.json_storage import JSONStorage
from datetime import datetime
import time


class TransactionManagementTests(TestCase):
    """Test transaction tracking and storage"""

    def setUp(self):
        """Set up test cache and storage"""
        self.cache = RedisCache()
        self.storage = JSONStorage()
        self.cache.client.flushdb()

    def tearDown(self):
        """Clean up Redis"""
        self.cache.client.flushdb()

    def test_set_and_get_transaction(self):
        """Test transaction storage and retrieval"""
        tx_data = {
            'transaction_id': 'test_tx_001',
            'route_id': 'route_123',
            'user_wallet': '0x123',
            'status': 'pending',
            'from_chain': '137',
            'to_chain': '998',
        }

        self.cache.set_transaction('test_tx_001', tx_data)
        retrieved = self.cache.get_transaction('test_tx_001')

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['transaction_id'], 'test_tx_001')
        self.assertEqual(retrieved['status'], 'pending')

    def test_update_transaction(self):
        """Test transaction updates"""
        tx_data = {
            'transaction_id': 'test_tx_002',
            'status': 'pending',
        }

        self.cache.set_transaction('test_tx_002', tx_data)

        # Update status
        self.cache.update_transaction('test_tx_002', {
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        })

        retrieved = self.cache.get_transaction('test_tx_002')
        self.assertEqual(retrieved['status'], 'completed')
        self.assertIn('completed_at', retrieved)

    def test_get_recent_transactions(self):
        """Test retrieving recent transactions"""
        # Add multiple transactions
        for i in range(5):
            tx_data = {
                'transaction_id': f'test_tx_{i}',
                'status': 'pending',
            }
            self.cache.set_transaction(f'test_tx_{i}', tx_data)

        recent = self.cache.get_recent_transactions(limit=3)

        self.assertEqual(len(recent), 3)
        # Should be in reverse order (newest first)
        self.assertEqual(recent[0]['transaction_id'], 'test_tx_4')

    def test_transaction_persistence_to_json(self):
        """Test transaction persistence to JSON file"""
        tx_data = {
            'transaction_id': 'test_tx_persistent',
            'status': 'completed',
            'timestamp': datetime.now().isoformat()
        }

        self.storage.append('bridge_transactions.json', tx_data, max_items=10)

        # Read back from JSON
        data = self.storage.read('bridge_transactions.json')

        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['transaction_id'], 'test_tx_persistent')


class QuoteCachingTests(TestCase):
    """Test quote caching with TTL"""

    def setUp(self):
        """Set up test cache"""
        self.cache = RedisCache()
        self.cache.client.flushdb()

    def tearDown(self):
        """Clean up Redis"""
        self.cache.client.flushdb()

    def test_quote_caching_with_ttl(self):
        """Test quote is cached with TTL"""
        quote_data = {
            'route_id': 'route_test',
            'from_chain': '137',
            'to_chain': '998',
            'estimated_time': 180,
        }

        self.cache.set_quote('route_test', quote_data, ttl=2)

        # Should be retrievable immediately
        retrieved = self.cache.get_quote('route_test')
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['route_id'], 'route_test')

        # Wait for TTL to expire
        time.sleep(3)

        # Should be gone
        retrieved = self.cache.get_quote('route_test')
        self.assertIsNone(retrieved)

    def test_quote_rolling_window(self):
        """Test quote rolling window"""
        # Add multiple quotes
        for i in range(5):
            quote_data = {'route_id': f'route_{i}'}
            self.cache.set_quote(f'route_{i}', quote_data, ttl=60)

        # Check rolling window list exists
        recent_ids = self.cache.client.lrange('quotes:recent', 0, -1)
        self.assertGreater(len(recent_ids), 0)
