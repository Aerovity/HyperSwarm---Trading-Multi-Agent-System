"""
Tests for route calculation utilities.
"""

from django.test import TestCase
from bridge.utils.route_calculator import (
    calculate_route_cost,
    estimate_route_time,
    compare_routes,
    format_route_steps,
    extract_transaction_request,
    get_route_summary,
)


class RouteCalculatorTests(TestCase):
    """Test route calculation functions"""

    def test_calculate_route_cost(self):
        """Test route cost calculation with known fees"""
        route = {
            'feeCosts': [
                {'amountUSD': '1.50'},
                {'amountUSD': '0.30'},
            ],
            'gasCosts': [
                {'amountUSD': '0.20'},
            ]
        }

        cost = calculate_route_cost(route)
        self.assertEqual(cost, 2.0)

    def test_calculate_route_cost_no_fees(self):
        """Test route cost calculation with no fees"""
        route = {}
        cost = calculate_route_cost(route)
        self.assertEqual(cost, 0.0)

    def test_estimate_route_time_with_estimate(self):
        """Test time estimation with execution duration"""
        route = {
            'estimate': {
                'executionDuration': 300
            }
        }

        time_seconds = estimate_route_time(route)
        self.assertEqual(time_seconds, 300)

    def test_estimate_route_time_from_steps(self):
        """Test time estimation based on step count"""
        route = {
            'steps': [
                {'action': 'swap'},
                {'action': 'bridge'},
                {'action': 'swap'},
            ]
        }

        time_seconds = estimate_route_time(route)
        # Should be 3 steps * 120 seconds
        self.assertEqual(time_seconds, 360)

    def test_estimate_route_time_fallback(self):
        """Test time estimation fallback"""
        route = {}
        time_seconds = estimate_route_time(route)
        # Should return default 300 seconds
        self.assertEqual(time_seconds, 300)

    def test_compare_routes_finds_cheapest(self):
        """Test route comparison finds cheapest route"""
        routes = [
            {
                'feeCosts': [{'amountUSD': '5.00'}],
                'gasCosts': []
            },
            {
                'feeCosts': [{'amountUSD': '2.00'}],
                'gasCosts': []
            },
            {
                'feeCosts': [{'amountUSD': '3.50'}],
                'gasCosts': []
            },
        ]

        cheapest = compare_routes(routes)
        cost = calculate_route_cost(cheapest)
        self.assertEqual(cost, 2.0)

    def test_compare_routes_empty_list(self):
        """Test route comparison with empty list"""
        cheapest = compare_routes([])
        self.assertIsNone(cheapest)

    def test_format_route_steps(self):
        """Test route step formatting"""
        route = {
            'steps': [
                {
                    'type': 'swap',
                    'tool': 'uniswap',
                    'action': {
                        'fromChainId': '137',
                        'toChainId': '137',
                        'fromToken': {'symbol': 'USDC'},
                        'toToken': {'symbol': 'USDT'},
                    },
                    'estimate': {
                        'fromAmount': '1000000',
                        'toAmount': '999000',
                    }
                }
            ]
        }

        steps = format_route_steps(route)

        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]['action'], 'swap')
        self.assertEqual(steps[0]['tool'], 'uniswap')
        self.assertEqual(steps[0]['from_token'], 'USDC')
        self.assertEqual(steps[0]['to_token'], 'USDT')

    def test_extract_transaction_request(self):
        """Test transaction request extraction"""
        route = {
            'transactionRequest': {
                'to': '0x1234567890123456789012345678901234567890',
                'data': '0xabcdef',
                'value': '0',
                'from': '0x0987654321098765432109876543210987654321',
                'chainId': '137',
                'gasLimit': '200000',
            }
        }

        tx_req = extract_transaction_request(route)

        self.assertIsNotNone(tx_req)
        self.assertEqual(tx_req['to'], '0x1234567890123456789012345678901234567890')
        self.assertEqual(tx_req['chainId'], '137')

    def test_extract_transaction_request_from_step(self):
        """Test transaction request extraction from first step"""
        route = {
            'steps': [
                {
                    'transactionRequest': {
                        'to': '0x1111111111111111111111111111111111111111',
                        'data': '0x123456',
                        'value': '1000',
                    }
                }
            ]
        }

        tx_req = extract_transaction_request(route)

        self.assertIsNotNone(tx_req)
        self.assertEqual(tx_req['to'], '0x1111111111111111111111111111111111111111')

    def test_get_route_summary(self):
        """Test route summary generation"""
        route = {
            'fromChainId': '137',
            'toChainId': '42161',
            'fromToken': {'symbol': 'USDC'},
            'toToken': {'symbol': 'USDC'},
            'fromAmount': '1000000',
            'toAmount': '998000',
            'feeCosts': [{'amountUSD': '1.50'}],
            'steps': [{'tool': 'stargate'}],
            'estimate': {'executionDuration': 240}
        }

        summary = get_route_summary(route)

        self.assertEqual(summary['from_chain'], '137')
        self.assertEqual(summary['to_chain'], '42161')
        self.assertEqual(summary['from_token'], 'USDC')
        self.assertEqual(summary['cost_usd'], 1.5)
        self.assertEqual(summary['estimated_time_seconds'], 240)
        self.assertEqual(summary['tool'], 'stargate')
