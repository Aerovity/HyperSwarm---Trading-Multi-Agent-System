"""
Generates text lessons from decision outcomes.

The Reflector analyzes past decisions and their outcomes to generate
human-readable lessons that inform future decisions.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class Reflector:
    """Generates text lessons from decision outcomes."""

    def generate_lesson(self, decision: Dict, outcome: Dict) -> str:
        """
        Generate a text lesson from decision + outcome.

        Args:
            decision: Dict with pair, decision, context (zscore, confidence, etc.)
            outcome: Dict with pnl, entry_price, exit_price, etc.

        Returns:
            Human-readable lesson string
        """
        pair = decision.get('pair', 'UNKNOWN')
        action = decision.get('decision', 'unknown')
        context = decision.get('context', {})

        zscore = context.get('zscore', 0)
        conf = context.get('confidence', 0)
        leverage = context.get('leverage', 0)
        volatility = context.get('volatility', 0)

        pnl = outcome.get('pnl', 0)
        pnl_pct = pnl * 100

        if action == 'approve':
            return self._generate_approval_lesson(
                pair, zscore, conf, leverage, volatility, pnl, pnl_pct
            )
        else:
            return self._generate_rejection_lesson(
                pair, zscore, conf, leverage, volatility, pnl, pnl_pct
            )

    def _generate_approval_lesson(
        self,
        pair: str,
        zscore: float,
        conf: float,
        leverage: float,
        volatility: float,
        pnl: float,
        pnl_pct: float
    ) -> str:
        """Generate lesson for an approved trade."""
        # Format z-score string
        z_str = f"z={abs(zscore):.1f}" if zscore else ""
        conf_str = f"conf={conf:.2f}" if conf else ""
        params = ", ".join(filter(None, [z_str, conf_str]))

        if pnl > 0:
            # Profitable approved trade - good decision
            lesson = f"Approved {pair}"
            if params:
                lesson += f" with {params}"
            lesson += f" -> +{pnl_pct:.1f}% profit."

            # Add insight
            if conf >= 0.8:
                lesson += " High confidence pays off."
            elif zscore and abs(zscore) >= 2.5:
                lesson += " Strong z-score was reliable."
            else:
                lesson += " Good decision."

        else:
            # Losing approved trade - learn from mistake
            lesson = f"Approved {pair}"
            if params:
                lesson += f" with {params}"
            lesson += f" -> {pnl_pct:.1f}% loss."

            # Add insight based on what might have gone wrong
            if conf < 0.75:
                lesson += " Consider: confidence was below 0.75."
            elif zscore and abs(zscore) < 2.0:
                lesson += " Consider: z-score was weak."
            elif leverage > 2.5:
                lesson += " Consider: leverage was high."
            elif volatility and volatility > 3.0:
                lesson += " Consider: volatility was elevated."
            else:
                lesson += " Review conditions for this pair."

        return lesson

    def _generate_rejection_lesson(
        self,
        pair: str,
        zscore: float,
        conf: float,
        leverage: float,
        volatility: float,
        pnl: float,
        pnl_pct: float
    ) -> str:
        """Generate lesson for a rejected trade (counterfactual)."""
        z_str = f"z={abs(zscore):.1f}" if zscore else ""
        conf_str = f"conf={conf:.2f}" if conf else ""
        params = ", ".join(filter(None, [z_str, conf_str]))

        if pnl < 0:
            # Trade would have lost money - good rejection
            lesson = f"Rejected {pair}"
            if params:
                lesson += f" with {params}"
            lesson += f". Trade would have lost {abs(pnl_pct):.1f}%."

            # Add insight
            if conf < 0.7:
                lesson += " Low confidence rejection was correct."
            elif zscore and abs(zscore) < 2.0:
                lesson += " Weak signal rejection was correct."
            else:
                lesson += " Good rejection!"

        else:
            # Trade would have been profitable - missed opportunity
            lesson = f"Rejected {pair}"
            if params:
                lesson += f" with {params}"
            lesson += f". Missed +{pnl_pct:.1f}% opportunity."

            # Add insight
            if conf >= 0.75:
                lesson += " Consider loosening criteria for this pair."
            elif zscore and abs(zscore) >= 2.0:
                lesson += " Signal was stronger than assessed."
            else:
                lesson += " Review rejection criteria."

        return lesson

    def summarize_pair(self, pair: str, decisions: List[Dict], outcomes: List[Dict]) -> str:
        """
        Generate summary statistics for a pair.

        Args:
            pair: Trading pair
            decisions: List of decision dicts
            outcomes: List of outcome dicts

        Returns:
            Summary string like "BTC/ETH: 10 trades, 7 wins (70%), avg PnL: +1.2%"
        """
        if not decisions or not outcomes:
            return f"{pair}: No trading history."

        total = len(outcomes)
        wins = sum(1 for o in outcomes if o.get('pnl', 0) > 0)
        total_pnl = sum(o.get('pnl', 0) for o in outcomes)
        avg_pnl = total_pnl / total if total > 0 else 0
        win_rate = wins / total * 100 if total > 0 else 0

        return f"{pair}: {total} trades, {wins} wins ({win_rate:.0f}%), avg PnL: {avg_pnl*100:+.1f}%"

    def identify_patterns(self, pair: str, decisions: List[Dict], outcomes: List[Dict]) -> List[str]:
        """
        Identify patterns from historical data.

        Args:
            pair: Trading pair
            decisions: List of decision dicts
            outcomes: List of outcome dicts

        Returns:
            List of pattern observations
        """
        patterns = []

        if len(decisions) < 5:
            return patterns

        # Group by confidence ranges
        high_conf_wins = 0
        high_conf_total = 0
        low_conf_wins = 0
        low_conf_total = 0

        for dec, out in zip(decisions, outcomes):
            conf = dec.get('context', {}).get('confidence', 0)
            pnl = out.get('pnl', 0)

            if conf >= 0.8:
                high_conf_total += 1
                if pnl > 0:
                    high_conf_wins += 1
            elif conf < 0.7:
                low_conf_total += 1
                if pnl > 0:
                    low_conf_wins += 1

        # Analyze confidence patterns
        if high_conf_total >= 3:
            high_conf_rate = high_conf_wins / high_conf_total
            if high_conf_rate >= 0.7:
                patterns.append(f"{pair} performs well with confidence >= 0.8 ({high_conf_rate*100:.0f}% win rate)")

        if low_conf_total >= 3:
            low_conf_rate = low_conf_wins / low_conf_total
            if low_conf_rate <= 0.4:
                patterns.append(f"{pair} underperforms with confidence < 0.7 ({low_conf_rate*100:.0f}% win rate)")

        # Analyze z-score patterns
        high_z_wins = 0
        high_z_total = 0

        for dec, out in zip(decisions, outcomes):
            zscore = abs(dec.get('context', {}).get('zscore', 0))
            pnl = out.get('pnl', 0)

            if zscore >= 2.5:
                high_z_total += 1
                if pnl > 0:
                    high_z_wins += 1

        if high_z_total >= 3:
            high_z_rate = high_z_wins / high_z_total
            if high_z_rate >= 0.7:
                patterns.append(f"Strong z-scores (>= 2.5) are reliable for {pair}")

        return patterns
