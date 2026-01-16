"""
Tests for approval engine with mocked Claude API.
"""

from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from risk.utils.approval_engine import ApprovalEngine, approve_trade


class ApprovalEngineTests(TestCase):
    """Test approval engine with mocked LLM"""

    def setUp(self):
        """Set up test fixtures"""
        self.valid_trade = {
            'pair': 'BTC/ETH',
            'zscore': 2.5,
            'size': 2500,
            'entry_spread': 0.015,
            'confidence': 0.85,
        }

        self.portfolio_state = {
            'total_value': 10000,
            'available_margin': 7500,
            'margin_usage': 25.0,
            'leverage': 1.5,
            'num_positions': 1,
            'liquidation_distance': 40.0,
        }

        self.market_conditions = {
            'btc_volatility': 3.5,
            'trend': 'neutral',
        }

    @override_settings(DEMO_MODE=True)
    def test_demo_mode_approve_valid_trade(self):
        """Test approval of valid trade in demo mode"""
        engine = ApprovalEngine()

        result = engine.approve_trade_with_llm_reasoning(
            self.valid_trade, self.portfolio_state, self.market_conditions
        )

        self.assertEqual(result['decision'], 'approve')
        self.assertIn('approval_id', result)
        self.assertIn('reasoning', result)
        self.assertIn('risk_score', result)
        self.assertIsInstance(result['concerns'], list)

    @override_settings(DEMO_MODE=True)
    def test_demo_mode_reject_low_confidence(self):
        """Test rejection of low confidence signal in demo mode"""
        engine = ApprovalEngine()

        low_conf_trade = {**self.valid_trade, 'confidence': 0.5}

        result = engine.approve_trade_with_llm_reasoning(
            low_conf_trade, self.portfolio_state, self.market_conditions
        )

        self.assertEqual(result['decision'], 'reject')
        self.assertTrue(any('confidence' in v for v in result['rule_violations']))

    @override_settings(DEMO_MODE=True)
    def test_demo_mode_reject_max_positions(self):
        """Test rejection when max positions reached in demo mode"""
        engine = ApprovalEngine()

        full_portfolio = {
            **self.portfolio_state,
            'num_positions': 3,  # At maximum
        }

        result = engine.approve_trade_with_llm_reasoning(
            self.valid_trade, full_portfolio, self.market_conditions
        )

        self.assertEqual(result['decision'], 'reject')
        self.assertTrue(any('max_positions' in v for v in result['rule_violations']))

    @override_settings(DEMO_MODE=True)
    def test_demo_mode_reject_high_leverage(self):
        """Test rejection when leverage would exceed limit"""
        engine = ApprovalEngine()

        # Large trade that would push leverage over 3x
        large_trade = {**self.valid_trade, 'size': 8000}
        high_lev_portfolio = {
            **self.portfolio_state,
            'leverage': 2.5,  # Already high
        }

        result = engine.approve_trade_with_llm_reasoning(
            large_trade, high_lev_portfolio, self.market_conditions
        )

        self.assertEqual(result['decision'], 'reject')
        self.assertTrue(any('leverage' in v for v in result['rule_violations']))

    @override_settings(DEMO_MODE=True)
    def test_approval_has_required_fields(self):
        """Test that approval response has all required fields"""
        engine = ApprovalEngine()

        result = engine.approve_trade_with_llm_reasoning(
            self.valid_trade, self.portfolio_state, self.market_conditions
        )

        required_fields = ['decision', 'risk_score', 'reasoning', 'concerns',
                          'rule_violations', 'approval_id', 'timestamp']

        for field in required_fields:
            self.assertIn(field, result, f"Missing field: {field}")

    @override_settings(DEMO_MODE=True)
    def test_risk_score_in_valid_range(self):
        """Test that risk score is between 0 and 100"""
        engine = ApprovalEngine()

        result = engine.approve_trade_with_llm_reasoning(
            self.valid_trade, self.portfolio_state, self.market_conditions
        )

        self.assertGreaterEqual(result['risk_score'], 0)
        self.assertLessEqual(result['risk_score'], 100)

    @override_settings(DEMO_MODE=True)
    def test_convenience_function(self):
        """Test the approve_trade convenience function"""
        result = approve_trade(
            self.valid_trade, self.portfolio_state, self.market_conditions
        )

        self.assertIn('decision', result)
        self.assertIn(result['decision'], ['approve', 'reject'])


class PromptBuildingTests(TestCase):
    """Test prompt building for LLM"""

    def setUp(self):
        self.engine = ApprovalEngine()

    def test_prompt_contains_trade_info(self):
        """Test prompt includes trade proposal info"""
        trade = {'pair': 'BTC/ETH', 'zscore': 2.5, 'size': 2500,
                 'entry_spread': 0.015, 'confidence': 0.85}
        portfolio = {'total_value': 10000, 'available_margin': 7500,
                    'margin_usage': 25, 'leverage': 1.5,
                    'num_positions': 1, 'liquidation_distance': 40}
        market = {'btc_volatility': 3.5, 'trend': 'neutral'}

        prompt = self.engine._build_approval_prompt(trade, portfolio, market, [])

        self.assertIn('BTC/ETH', prompt)
        self.assertIn('2.5', prompt)  # z-score
        self.assertIn('0.85', prompt)  # confidence

    def test_prompt_contains_violations(self):
        """Test prompt includes rule violations when present"""
        trade = {'pair': 'BTC/ETH', 'zscore': 2.5, 'size': 2500,
                 'entry_spread': 0.015, 'confidence': 0.85}
        portfolio = {'total_value': 10000, 'available_margin': 7500,
                    'margin_usage': 25, 'leverage': 1.5,
                    'num_positions': 1, 'liquidation_distance': 40}
        market = {'btc_volatility': 3.5, 'trend': 'neutral'}
        violations = ['max_positions_exceeded: 3/3 positions']

        prompt = self.engine._build_approval_prompt(trade, portfolio, market, violations)

        self.assertIn('RULE VIOLATIONS', prompt)
        self.assertIn('max_positions_exceeded', prompt)


class ResponseParsingTests(TestCase):
    """Test LLM response parsing"""

    def setUp(self):
        self.engine = ApprovalEngine()

    def test_parse_valid_json(self):
        """Test parsing valid JSON response"""
        response = '{"decision": "approve", "risk_score": 30, "reasoning": "Good trade", "concerns": []}'

        result = self.engine._parse_llm_response(response)

        self.assertEqual(result['decision'], 'approve')
        self.assertEqual(result['risk_score'], 30)
        self.assertEqual(result['reasoning'], 'Good trade')

    def test_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code block"""
        response = '''```json
{"decision": "reject", "risk_score": 70, "reasoning": "Too risky", "concerns": ["high leverage"]}
```'''

        result = self.engine._parse_llm_response(response)

        self.assertEqual(result['decision'], 'reject')
        self.assertEqual(result['risk_score'], 70)

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns safe default"""
        response = 'This is not JSON'

        result = self.engine._parse_llm_response(response)

        self.assertEqual(result['decision'], 'reject')
        self.assertIn('failed to parse', result['reasoning'].lower())
