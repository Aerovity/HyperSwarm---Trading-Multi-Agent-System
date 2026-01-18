"""
Text-based memory for Guardian agent decisions and lessons.

Uses Redis DB 3 for real-time storage with JSON file backup.
Memory updates after every decision for continuous learning.
"""

import json
import logging
import redis
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from django.conf import settings

from .reflector import Reflector

logger = logging.getLogger(__name__)


class ReflexionMemory:
    """Text-based memory for Guardian agent decisions and lessons."""

    def __init__(self, redis_db: int = 3, data_dir: str = None):
        """
        Initialize reflexion memory.

        Args:
            redis_db: Redis database number (default 3, separate from main cache)
            data_dir: Directory for JSON backups (default ./data/reflexion)
        """
        # Redis connection
        try:
            self.redis = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=redis_db,
                decode_responses=True
            )
            self.redis.ping()
            logger.info(f"Reflexion memory connected to Redis DB {redis_db}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis for reflexion: {e}")
            self.redis = None

        # JSON backup directory
        if data_dir is None:
            base_dir = Path(settings.BASE_DIR) if hasattr(settings, 'BASE_DIR') else Path('.')
            data_dir = base_dir / 'data' / 'reflexion'
        else:
            data_dir = Path(data_dir)

        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Reflector for lesson generation
        self.reflector = Reflector()

        # Configuration
        self.max_lessons_per_pair = 50
        self.max_decisions_window = 1000

    def store_decision(
        self,
        approval_id: str,
        pair: str,
        decision: str,
        reasoning: str,
        context: Dict
    ) -> bool:
        """
        Store decision immediately after making it.

        Args:
            approval_id: Unique approval ID
            pair: Trading pair (e.g., "BTC/ETH")
            decision: "approve" or "reject"
            reasoning: LLM reasoning for the decision
            context: Dict with zscore, confidence, leverage, volatility, etc.

        Returns:
            True if stored successfully
        """
        timestamp = datetime.now().isoformat()

        decision_record = {
            'approval_id': approval_id,
            'pair': pair,
            'timestamp': timestamp,
            'decision': decision,
            'reasoning': reasoning,
            'context': context,
        }

        try:
            # Store in Redis
            if self.redis:
                # Hash for decision details
                key = f"decisions:{approval_id}"
                self.redis.hset(key, mapping={
                    'pair': pair,
                    'timestamp': timestamp,
                    'decision': decision,
                    'reasoning': reasoning,
                    'context': json.dumps(context),
                })
                # 7 day TTL for decisions
                self.redis.expire(key, 604800)

                # Add to pair's decision list (for context building)
                pair_key = f"decisions_by_pair:{pair}"
                self.redis.lpush(pair_key, approval_id)
                self.redis.ltrim(pair_key, 0, self.max_decisions_window - 1)

                # Add to global recent decisions list
                self.redis.lpush("decisions:recent", approval_id)
                self.redis.ltrim("decisions:recent", 0, self.max_decisions_window - 1)

            # JSON backup (append-only)
            self._append_to_jsonl('decisions.jsonl', decision_record)

            logger.debug(f"Stored decision {approval_id} for {pair}: {decision}")
            return True

        except Exception as e:
            logger.error(f"Failed to store decision: {e}")
            return False

    def record_outcome(
        self,
        approval_id: str,
        pnl: float,
        details: Dict = None
    ) -> Optional[str]:
        """
        Record trade outcome and trigger lesson generation.

        Args:
            approval_id: Approval ID to link outcome to
            pnl: Profit/loss as decimal (e.g., 0.025 = +2.5%)
            details: Optional dict with entry_price, exit_price, etc.

        Returns:
            Generated lesson string, or None if failed
        """
        timestamp = datetime.now().isoformat()
        details = details or {}

        try:
            # Get the original decision
            decision = self.get_decision(approval_id)
            if not decision:
                logger.warning(f"No decision found for approval_id {approval_id}")
                return None

            pair = decision.get('pair', 'UNKNOWN')

            # Store outcome in Redis
            outcome_record = {
                'approval_id': approval_id,
                'timestamp': timestamp,
                'pnl': pnl,
                **details
            }

            if self.redis:
                key = f"outcomes:{approval_id}"
                self.redis.hset(key, mapping={
                    'timestamp': timestamp,
                    'pnl': str(pnl),
                    'details': json.dumps(details),
                })
                self.redis.expire(key, 604800)  # 7 day TTL

            # Generate lesson from decision + outcome
            lesson = self.reflector.generate_lesson(decision, outcome_record)

            # Store lesson
            self._store_lesson(pair, lesson, approval_id)

            # Update pair statistics
            self._update_pair_stats(pair, decision['decision'], pnl)

            # JSON backup
            outcome_record['lesson'] = lesson
            self._append_to_jsonl('outcomes.jsonl', outcome_record)

            logger.info(f"Recorded outcome for {approval_id}: PnL={pnl:.2%}, lesson generated")
            return lesson

        except Exception as e:
            logger.error(f"Failed to record outcome: {e}")
            return None

    def get_decision(self, approval_id: str) -> Optional[Dict]:
        """Get a stored decision by approval_id."""
        try:
            if self.redis:
                key = f"decisions:{approval_id}"
                data = self.redis.hgetall(key)
                if data:
                    return {
                        'approval_id': approval_id,
                        'pair': data.get('pair'),
                        'timestamp': data.get('timestamp'),
                        'decision': data.get('decision'),
                        'reasoning': data.get('reasoning'),
                        'context': json.loads(data.get('context', '{}')),
                    }
            return None
        except Exception as e:
            logger.error(f"Failed to get decision: {e}")
            return None

    def get_lessons_for_pair(self, pair: str, limit: int = 5) -> List[str]:
        """
        Get most recent lessons for a trading pair.

        Args:
            pair: Trading pair (e.g., "BTC/ETH")
            limit: Maximum number of lessons to return

        Returns:
            List of lesson strings, most recent first
        """
        try:
            if self.redis:
                key = f"lessons:{pair}"
                lessons = self.redis.lrange(key, 0, limit - 1)
                return lessons
            return []
        except Exception as e:
            logger.error(f"Failed to get lessons for {pair}: {e}")
            return []

    def get_pair_statistics(self, pair: str) -> Dict:
        """
        Get aggregate stats: win_rate, avg_pnl, total_trades.

        Args:
            pair: Trading pair

        Returns:
            Dict with total, wins, losses, avg_pnl, win_rate
        """
        try:
            if self.redis:
                key = f"stats:{pair}"
                data = self.redis.hgetall(key)
                if data:
                    total = int(data.get('total', 0))
                    wins = int(data.get('wins', 0))
                    losses = int(data.get('losses', 0))
                    total_pnl = float(data.get('total_pnl', 0))

                    return {
                        'total': total,
                        'wins': wins,
                        'losses': losses,
                        'avg_pnl': total_pnl / total if total > 0 else 0,
                        'win_rate': wins / total if total > 0 else 0,
                    }
            return {'total': 0, 'wins': 0, 'losses': 0, 'avg_pnl': 0, 'win_rate': 0}
        except Exception as e:
            logger.error(f"Failed to get stats for {pair}: {e}")
            return {'total': 0, 'wins': 0, 'losses': 0, 'avg_pnl': 0, 'win_rate': 0}

    def get_reflexion_context(self, pair: str) -> str:
        """
        Build text context for LLM prompt.

        Args:
            pair: Trading pair

        Returns:
            Formatted string with stats and lessons for the prompt
        """
        stats = self.get_pair_statistics(pair)
        lessons = self.get_lessons_for_pair(pair, limit=3)

        return self._format_context(stats, lessons)

    def _format_context(self, stats: Dict, lessons: List[str]) -> str:
        """Format stats and lessons into prompt context."""
        if stats['total'] == 0 and not lessons:
            return "No prior experience with this pair."

        lines = []

        # Stats summary
        if stats['total'] > 0:
            win_pct = stats['win_rate'] * 100
            avg_pnl_pct = stats['avg_pnl'] * 100
            lines.append(
                f"- Stats: {stats['total']} trades, {stats['wins']} wins "
                f"({win_pct:.0f}%), avg PnL: {avg_pnl_pct:+.1f}%"
            )

        # Recent lessons
        for lesson in lessons:
            lines.append(f"- Lesson: {lesson}")

        # Pattern detection
        if stats['total'] >= 3:
            if stats['win_rate'] >= 0.7:
                lines.append("- Pattern: This pair has been performing well")
            elif stats['win_rate'] <= 0.3:
                lines.append("- Pattern: This pair has been underperforming - extra caution advised")

        return "\n".join(lines) if lines else "No prior experience with this pair."

    def _store_lesson(self, pair: str, lesson: str, approval_id: str):
        """Store a lesson in Redis."""
        try:
            if self.redis:
                key = f"lessons:{pair}"
                # Store with timestamp prefix for ordering
                timestamped_lesson = f"[{datetime.now().strftime('%H:%M')}] {lesson}"
                self.redis.lpush(key, timestamped_lesson)
                self.redis.ltrim(key, 0, self.max_lessons_per_pair - 1)

                # Also store in lessons.json for persistence
                self._save_lessons_json(pair, timestamped_lesson)
        except Exception as e:
            logger.error(f"Failed to store lesson: {e}")

    def _update_pair_stats(self, pair: str, decision: str, pnl: float):
        """Update aggregate statistics for a pair."""
        try:
            if self.redis:
                key = f"stats:{pair}"

                # Get current stats
                current = self.redis.hgetall(key)
                total = int(current.get('total', 0))
                wins = int(current.get('wins', 0))
                losses = int(current.get('losses', 0))
                total_pnl = float(current.get('total_pnl', 0))

                # Update based on outcome
                if decision == 'approve':
                    total += 1
                    total_pnl += pnl
                    if pnl > 0:
                        wins += 1
                    else:
                        losses += 1
                else:
                    # For rejections, we track counterfactuals
                    # pnl here represents what would have happened
                    total += 1
                    if pnl < 0:
                        # Rejected a losing trade = good decision
                        wins += 1
                    else:
                        # Rejected a winning trade = missed opportunity
                        losses += 1

                # Store updated stats
                self.redis.hset(key, mapping={
                    'total': str(total),
                    'wins': str(wins),
                    'losses': str(losses),
                    'total_pnl': str(total_pnl),
                })
        except Exception as e:
            logger.error(f"Failed to update pair stats: {e}")

    def _append_to_jsonl(self, filename: str, record: Dict):
        """Append a record to a JSONL file."""
        try:
            filepath = self.data_dir / filename
            with open(filepath, 'a') as f:
                f.write(json.dumps(record) + '\n')
        except Exception as e:
            logger.error(f"Failed to append to {filename}: {e}")

    def _save_lessons_json(self, pair: str, lesson: str):
        """Save lessons to organized JSON file."""
        try:
            filepath = self.data_dir / 'lessons.json'

            # Load existing lessons
            if filepath.exists():
                with open(filepath, 'r') as f:
                    lessons_data = json.load(f)
            else:
                lessons_data = {}

            # Add new lesson
            if pair not in lessons_data:
                lessons_data[pair] = []
            lessons_data[pair].insert(0, lesson)

            # Trim to max
            lessons_data[pair] = lessons_data[pair][:self.max_lessons_per_pair]

            # Save
            with open(filepath, 'w') as f:
                json.dump(lessons_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save lessons JSON: {e}")

    def clear_pair_memory(self, pair: str):
        """Clear all memory for a specific pair (for testing)."""
        try:
            if self.redis:
                self.redis.delete(f"lessons:{pair}")
                self.redis.delete(f"stats:{pair}")
                self.redis.delete(f"decisions_by_pair:{pair}")
            logger.info(f"Cleared memory for {pair}")
        except Exception as e:
            logger.error(f"Failed to clear memory for {pair}: {e}")


# Singleton instance
_memory_instance = None


def get_reflexion_memory() -> ReflexionMemory:
    """Get or create ReflexionMemory singleton."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = ReflexionMemory()
    return _memory_instance
