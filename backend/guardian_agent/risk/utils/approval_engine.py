"""
Trade approval engine using Claude API for intelligent risk reasoning.
Combines deterministic risk checks with LLM analysis for nuanced decisions.
Now supports RL-based policy for learned risk assessment!

This is the KEY DIFFERENTIATOR - contextual AI decision making!
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from anthropic import Anthropic
from django.conf import settings

from .risk_calculator import check_risk_limits, calculate_health_score

logger = logging.getLogger(__name__)


class ApprovalEngine:
    """Trade approval engine with LLM-powered reasoning and RL policy support"""

    def __init__(self):
        """Initialize Claude client and RL policy"""
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.ANTHROPIC_MODEL
        self.client = None

        # Initialize Claude client if API key is available
        if self.api_key:
            try:
                self.client = Anthropic(api_key=self.api_key)
                logger.info(f"Anthropic client initialized with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")

        # Default risk rules
        self.risk_limits = settings.RISK_LIMITS

        # RL Policy (lazy loaded)
        self._rl_policy = None
        self._rl_state_encoder = None
        self._use_rl = getattr(settings, 'USE_RL_POLICY', False)

    def _load_rl_policy(self):
        """Lazy load RL policy when needed"""
        if self._rl_policy is not None:
            return True

        if not self._use_rl:
            return False

        try:
            from .rl.policy import PolicyWrapper
            from .rl.state_encoder import StateEncoder

            model_path = getattr(settings, 'RL_MODEL_PATH', './data/models/guardian_ppo_latest')

            # Check if model exists
            if not Path(model_path).exists() and not Path(f"{model_path}.zip").exists():
                logger.warning(f"RL model not found at {model_path}, falling back to rules")
                return False

            self._rl_policy = PolicyWrapper.load(model_path)
            self._rl_state_encoder = StateEncoder()
            logger.info(f"RL policy loaded from {model_path}")
            return True

        except ImportError as e:
            logger.warning(f"RL dependencies not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load RL policy: {e}")
            return False

    def _rl_approve(
        self,
        trade_proposal: Dict,
        portfolio_state: Dict,
        market_conditions: Dict,
    ) -> Optional[Dict]:
        """
        Get approval decision from RL policy.

        Returns None if RL is not available or fails.
        """
        if not self._load_rl_policy():
            return None

        try:
            import pandas as pd
            import numpy as np

            # Build portfolio state dict
            portfolio = {
                'account_value': portfolio_state.get('total_value', 10000),
                'current_leverage': portfolio_state.get('leverage', 0),
                'margin_usage': portfolio_state.get('margin_usage', 0) / 100,
                'num_positions': portfolio_state.get('num_positions', 0),
                'liquidation_distance': portfolio_state.get('liquidation_distance', 100) / 100,
                'health_score': calculate_health_score(
                    portfolio_state.get('leverage', 0),
                    portfolio_state.get('num_positions', 0),
                    portfolio_state.get('margin_usage', 0) / 100,
                    portfolio_state.get('liquidation_distance', 100) / 100,
                ),
            }

            # Build trade proposal dict
            trade = {
                'size': trade_proposal.get('size', 0),
                'leverage': portfolio_state.get('leverage', 1.0),
                'confidence': trade_proposal.get('confidence', 0.5),
                'z_score': trade_proposal.get('zscore', 0),
                'account_value': portfolio_state.get('total_value', 10000),
            }

            # Build market data (use dummy values if not available)
            market_data = pd.Series({
                'rsi_14': 50,
                'macd': 0,
                'macd_signal': 0,
                'macd_diff': 0,
                'bb_position': 0,
                'atr_normalized': market_conditions.get('btc_volatility', 2) / 100,
                'adx': 25,
                'volume_ratio': 1.0,
                'momentum_1h': 0,
                'momentum_4h': 0,
                'momentum_24h': 0,
                'returns': 0,
                'stoch_k': 50,
                'stoch_d': 50,
            })

            # Encode state
            state = self._rl_state_encoder.encode(
                portfolio, trade, market_data, already_normalized=False
            )

            # Get prediction
            deterministic = getattr(settings, 'RL_DETERMINISTIC', True)
            action, probs, value = self._rl_policy.predict_with_probs(state.reshape(1, -1))

            # Map action to decision
            action_map = {
                0: ('reject', 'high'),
                1: ('approve', 'medium'),  # approve with warning
                2: ('approve', 'low'),
            }
            decision, risk_level = action_map.get(action, ('reject', 'high'))

            # Calculate risk score from probabilities
            # Higher approve probability = higher risk score (safer)
            risk_score = int((probs[1] * 0.7 + probs[2] * 1.0) * 100)

            return {
                'decision': decision,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'reasoning': f"RL policy decision (action={action}, confidence={probs[action]:.2f})",
                'concerns': [],
                'source': 'rl_policy',
                'action_probs': {
                    'reject': float(probs[0]),
                    'approve_warning': float(probs[1]),
                    'approve': float(probs[2]),
                },
            }

        except Exception as e:
            logger.error(f"RL policy prediction failed: {e}")
            return None

    def approve_trade_with_llm_reasoning(
        self,
        trade_proposal: Dict,
        portfolio_state: Dict,
        market_conditions: Dict
    ) -> Dict:
        """
        Use Claude to make nuanced risk decisions with reasoning.
        This is where AI shines - contextual decision making!

        Args:
            trade_proposal: Dict with keys:
                - pair: str (e.g., "BTC/ETH")
                - zscore: float (signal z-score)
                - size: float (position size in USD)
                - entry_spread: float
                - confidence: float (0.0 to 1.0)

            portfolio_state: Dict with keys:
                - total_value: float
                - available_margin: float
                - margin_usage: float (percentage)
                - leverage: float
                - num_positions: int
                - liquidation_distance: float (percentage)

            market_conditions: Dict with keys:
                - btc_volatility: float (24h volatility %)
                - trend: str ("bullish", "bearish", "neutral")

        Returns:
            Dict with keys:
                - decision: str ("approve" or "reject")
                - risk_score: int (0-100, 100 = safest)
                - reasoning: str (2-3 sentence explanation)
                - concerns: List[str]
                - rule_violations: List[str]
                - approval_id: str
                - timestamp: str
        """
        # Generate approval ID
        approval_id = f"approval_{int(datetime.now().timestamp())}_{hash(str(trade_proposal)) % 10000}"
        timestamp = datetime.now().isoformat()

        # First, run deterministic rule checks
        passes_rules, violations = check_risk_limits(
            proposed_trade={
                'size': trade_proposal.get('size', 0),
                'leverage': portfolio_state.get('leverage', 1.0),
                'confidence': trade_proposal.get('confidence', 0),
            },
            portfolio_state={
                'account_value': portfolio_state.get('total_value', 0),
                'num_positions': portfolio_state.get('num_positions', 0),
                'current_leverage': portfolio_state.get('leverage', 0),
                'liquidation_distance': portfolio_state.get('liquidation_distance', 1.0),
            },
            risk_limits=self.risk_limits
        )

        # Try RL policy first if enabled
        if self._use_rl:
            rl_result = self._rl_approve(trade_proposal, portfolio_state, market_conditions)
            if rl_result is not None:
                # Apply safety net: reject if rule violations exist
                fallback_to_rules = getattr(settings, 'RL_FALLBACK_TO_RULES', True)
                if fallback_to_rules and not passes_rules:
                    rl_result['decision'] = 'reject'
                    rl_result['rule_violations'] = violations
                    rl_result['reasoning'] += f" Overridden by rule violations: {', '.join(violations[:2])}"

                rl_result['approval_id'] = approval_id
                rl_result['timestamp'] = timestamp
                rl_result['rule_violations'] = violations
                logger.info(f"RL policy decision: {rl_result['decision']} for {trade_proposal.get('pair')}")
                return rl_result

        # If demo mode or no client, return based on rule checks
        if settings.DEMO_MODE or not self.client:
            return self._generate_demo_response(
                trade_proposal,
                portfolio_state,
                passes_rules,
                violations,
                approval_id,
                timestamp
            )

        # Build prompt and call Claude
        try:
            prompt = self._build_approval_prompt(
                trade_proposal,
                portfolio_state,
                market_conditions,
                violations
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse LLM response
            result = self._parse_llm_response(response.content[0].text)
            result['rule_violations'] = violations
            result['approval_id'] = approval_id
            result['timestamp'] = timestamp

            logger.info(f"Trade approval decision: {result['decision']} for {trade_proposal.get('pair')}")
            return result

        except Exception as e:
            logger.error(f"LLM approval failed: {e}")
            # Fallback to rule-based decision
            return self._generate_demo_response(
                trade_proposal,
                portfolio_state,
                passes_rules,
                violations,
                approval_id,
                timestamp
            )

    def _build_approval_prompt(
        self,
        trade_proposal: Dict,
        portfolio_state: Dict,
        market_conditions: Dict,
        rule_violations: list
    ) -> str:
        """Build structured prompt for Claude analysis"""

        violations_text = ""
        if rule_violations:
            violations_text = f"\n\nRULE VIOLATIONS DETECTED:\n" + "\n".join(f"- {v}" for v in rule_violations)

        prompt = f"""You are the Guardian Agent, an expert risk manager for a DeFi trading system.

TRADE PROPOSAL:
- Pair: {trade_proposal.get('pair', 'UNKNOWN')}
- Signal Z-Score: {trade_proposal.get('zscore', 0)}
- Position Size: ${trade_proposal.get('size', 0):,.2f}
- Entry Spread: {trade_proposal.get('entry_spread', 0)}
- Signal Confidence: {trade_proposal.get('confidence', 0)}

CURRENT PORTFOLIO STATE:
- Total Value: ${portfolio_state.get('total_value', 0):,.2f}
- Available Margin: ${portfolio_state.get('available_margin', 0):,.2f}
- Used Margin: {portfolio_state.get('margin_usage', 0):.1f}%
- Current Leverage: {portfolio_state.get('leverage', 0):.2f}x
- Open Positions: {portfolio_state.get('num_positions', 0)}
- Liquidation Distance: {portfolio_state.get('liquidation_distance', 0):.1f}%

MARKET CONDITIONS:
- BTC 24h Volatility: {market_conditions.get('btc_volatility', 0):.1f}%
- Overall Market Trend: {market_conditions.get('trend', 'neutral')}
{violations_text}

RISK RULES TO ENFORCE:
1. Maximum 3 concurrent positions
2. Maximum 3x leverage
3. Maximum 30% of portfolio per position
4. Minimum 20% liquidation distance
5. Only trade high-confidence signals (confidence > 0.7)

TASK:
Decide whether to APPROVE or REJECT this trade. Consider:
- Is the signal strong enough? (z-score > 2.0 preferred)
- Can the portfolio handle this position?
- Is liquidation risk acceptable?
- Are we over-concentrated in any pair?
- Is market volatility too high right now?

Respond in JSON format ONLY (no other text):
{{
    "decision": "approve" or "reject",
    "risk_score": 0-100 (100 = safest),
    "reasoning": "2-3 sentence explanation of your decision",
    "concerns": ["list", "of", "any", "concerns"]
}}"""

        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse structured response from Claude"""
        try:
            # Try to extract JSON from response
            # Handle case where response might have markdown code blocks
            text = response_text.strip()
            if text.startswith("```"):
                # Remove markdown code blocks
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            result = json.loads(text)

            # Validate and normalize response
            return {
                'decision': result.get('decision', 'reject').lower(),
                'risk_score': int(result.get('risk_score', 50)),
                'reasoning': result.get('reasoning', 'No reasoning provided'),
                'concerns': result.get('concerns', []),
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.error(f"Response text: {response_text}")
            return {
                'decision': 'reject',
                'risk_score': 50,
                'reasoning': 'Failed to parse LLM response, rejecting for safety',
                'concerns': ['LLM response parsing failed'],
            }

    def _generate_demo_response(
        self,
        trade_proposal: Dict,
        portfolio_state: Dict,
        passes_rules: bool,
        violations: list,
        approval_id: str,
        timestamp: str
    ) -> Dict:
        """Generate demo response based on rule checks"""

        confidence = trade_proposal.get('confidence', 0)
        zscore = abs(trade_proposal.get('zscore', 0))
        leverage = portfolio_state.get('leverage', 0)

        if not passes_rules:
            # Reject due to rule violations
            return {
                'decision': 'reject',
                'risk_score': 25,
                'reasoning': f"Trade rejected due to risk rule violations: {', '.join(violations[:2])}. "
                             f"Please adjust position size or wait for better conditions.",
                'concerns': violations,
                'rule_violations': violations,
                'approval_id': approval_id,
                'timestamp': timestamp,
            }

        # Calculate risk score based on factors
        risk_score = 100

        # Penalize low confidence
        if confidence < 0.8:
            risk_score -= 20

        # Penalize weak signal
        if zscore < 2.5:
            risk_score -= 15

        # Penalize high leverage
        if leverage > 2.0:
            risk_score -= int((leverage - 2.0) * 20)

        risk_score = max(0, min(100, risk_score))

        concerns = []
        if confidence < 0.85:
            concerns.append(f"Signal confidence ({confidence:.2f}) is moderate")
        if zscore < 2.5:
            concerns.append(f"Z-score ({zscore:.2f}) is below preferred threshold of 2.5")
        if leverage > 2.0:
            concerns.append(f"Current leverage ({leverage:.2f}x) is elevated")

        return {
            'decision': 'approve',
            'risk_score': risk_score,
            'reasoning': f"Trade approved. Signal confidence of {confidence:.2f} meets minimum threshold. "
                         f"Z-score of {zscore:.2f} indicates a valid mean reversion opportunity. "
                         f"Portfolio can accommodate this position within risk limits.",
            'concerns': concerns,
            'rule_violations': [],
            'approval_id': approval_id,
            'timestamp': timestamp,
        }


# Singleton instance
approval_engine = ApprovalEngine()


def approve_trade(
    trade_proposal: Dict,
    portfolio_state: Dict,
    market_conditions: Dict
) -> Dict:
    """
    Convenience function for trade approval.
    Combines deterministic rule checks with LLM reasoning.
    """
    return approval_engine.approve_trade_with_llm_reasoning(
        trade_proposal, portfolio_state, market_conditions
    )
