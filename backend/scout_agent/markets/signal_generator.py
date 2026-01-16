"""
Signal generator for pair trading opportunities.
Analyzes market data and generates trading signals.
"""

import logging
from typing import List, Optional
from datetime import datetime

from django.conf import settings
from .utils.redis_cache import RedisCache
from .utils.calculations import (
    calculate_zscore,
    calculate_correlation,
    calculate_spread,
    identify_mean_reversion,
    calculate_confidence
)
from .utils.logger import log_agent_activity

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Analyzes market data and generates trading signals.
    """

    def __init__(self):
        """Initialize signal generator"""
        self.cache = RedisCache()
        self.zscore_threshold = settings.SIGNAL_CONFIG['ZSCORE_THRESHOLD']
        self.correlation_threshold = settings.SIGNAL_CONFIG['CORRELATION_THRESHOLD']
        self.min_confidence = settings.SIGNAL_CONFIG['MIN_CONFIDENCE']

        # Define trading pairs (Hyperliquid uses simple symbol names)
        self.pairs = [
            ("BTC", "ETH"),
            ("BTC", "SOL"),
            ("BTC", "AVAX"),
            ("BTC", "MATIC"),
            ("ETH", "SOL"),
            ("ETH", "AVAX"),
            ("ETH", "MATIC"),
            ("SOL", "AVAX"),
            ("SOL", "MATIC"),
            ("AVAX", "MATIC"),
        ]

    def analyze_markets(self) -> List[dict]:
        """
        Analyze all pairs and generate signals.

        Returns:
            List of signal dictionaries
        """
        signals = []

        for pair1, pair2 in self.pairs:
            try:
                signal = self._analyze_pair(pair1, pair2)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Failed to analyze {pair1}/{pair2}: {e}")
                log_agent_activity("scout", "error",
                    f"Failed to analyze {pair1}/{pair2}: {str(e)}")

        return signals

    def _analyze_pair(self, asset1: str, asset2: str) -> Optional[dict]:
        """
        Analyze single pair for trading opportunity.

        Returns:
            Signal dictionary or None if no signal
        """
        # Get price histories
        history1 = self.cache.get_price_history(asset1, limit=50)
        history2 = self.cache.get_price_history(asset2, limit=50)

        # Need at least 50 data points
        if len(history1) < 50 or len(history2) < 50:
            return None

        try:
            # Calculate spread
            current_prices1 = self.cache.get_price(asset1)
            current_prices2 = self.cache.get_price(asset2)

            if not current_prices1 or not current_prices2:
                return None

            price1 = current_prices1['price']
            price2 = current_prices2['price']

            spread = calculate_spread(price1, price2, normalize=True)

            # Extract prices from history dicts
            prices1 = [h.get('price') for h in history1 if h.get('price') is not None]
            prices2 = [h.get('price') for h in history2 if h.get('price') is not None]

            if len(prices1) < 50 or len(prices2) < 50:
                return None

            # Calculate z-score of spread
            spread_history = [
                calculate_spread(p1, p2, normalize=True)
                for p1, p2 in zip(prices1, prices2)
            ]

            zscore = calculate_zscore(spread_history, window=20)

            # Calculate correlation
            correlation = calculate_correlation(prices1, prices2, window=50)

            # Check if signal threshold met
            is_signal, signal_type = identify_mean_reversion(
                zscore,
                self.zscore_threshold
            )

            if not is_signal:
                return None

            # Calculate confidence
            confidence, confidence_label = calculate_confidence(zscore, correlation)

            # Check minimum confidence
            if confidence < self.min_confidence:
                return None

            # Generate signal
            signal = {
                "id": f"signal_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "pair": f"{asset1}/{asset2}",
                "zscore": round(zscore, 4),
                "correlation": round(correlation, 4),
                "entry_spread": round(spread, 6),
                "signal_type": signal_type,
                "confidence": round(confidence, 4),
                "confidence_label": confidence_label,
                "status": "pending"
            }

            # Log signal
            log_agent_activity("scout", "success",
                f"Signal detected: {signal['pair']} at {zscore:.2f}σ - {confidence_label} confidence",
                data={"signal": signal}
            )

            # Store to Redis
            self.cache.set_signal(signal['id'], signal)

            return signal

        except Exception as e:
            logger.error(f"Error analyzing {asset1}/{asset2}: {e}")
            return None
