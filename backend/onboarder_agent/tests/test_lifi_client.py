"""
Tests for LI.FI client integration.
"""

from django.test import TestCase
from bridge.utils.lifi_client import LiFiClient, RateLimiter
from django.conf import settings
import time


class RateLimiterTests(TestCase):
    """Test rate limiting functionality"""

    def test_rate_limiter_allows_initial_calls(self):
        """Test that initial calls are allowed"""
        limiter = RateLimiter(calls=5, period=1)

        start = time.time()
        for i in range(5):
            limiter.wait_if_needed()
        elapsed = time.time() - start

        # Should complete almost instantly
        self.assertLess(elapsed, 0.5)

    def test_rate_limiter_throttles_excess_calls(self):
        """Test that excess calls are throttled"""
        limiter = RateLimiter(calls=2, period=1)

        start = time.time()
        for i in range(3):
            limiter.wait_if_needed()
        elapsed = time.time() - start

        # Third call should be delayed by ~1 second
        self.assertGreater(elapsed, 0.9)


class LiFiClientTests(TestCase):
    """Test LI.FI API client"""

    def setUp(self):
        """Set up test client"""
        self.client = LiFiClient()

    def test_client_initialization(self):
        """Test client initializes with correct settings"""
        self.assertEqual(self.client.api_url, settings.LIFI['API_URL'])
        self.assertEqual(self.client.integrator, settings.LIFI['INTEGRATOR'])
        self.assertIsNotNone(self.client.session)

    def test_get_chains_returns_list(self):
        """Test get_chains returns a list"""
        if settings.DEMO_MODE:
            self.skipTest("Skipping API test in demo mode")

        chains = self.client.get_chains()
        self.assertIsInstance(chains, list)

    def test_get_quote_with_invalid_chain(self):
        """Test get_quote with invalid chain returns None"""
        if settings.DEMO_MODE:
            self.skipTest("Skipping API test in demo mode")

        quote = self.client.get_quote(
            from_chain_id='99999',  # Invalid chain
            to_chain_id='137',
            from_token='USDC',
            to_token='USDC',
            from_amount='1000000',
            from_address='0x0000000000000000000000000000000000000000'
        )

        # Should return None on error
        self.assertIsNone(quote)
