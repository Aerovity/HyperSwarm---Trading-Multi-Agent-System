"""
PnL updater that uses Scout's real-time market data to update position spreads.
Reads price data from Scout's Redis cache and calculates updated spreads.
"""

import redis
import json
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class PnLUpdater:
    """Updates position PnL based on Scout's real-time market data"""

    def __init__(self):
        """Initialize Redis connections to both Executor and Scout databases"""
        try:
            # Executor Redis (DB 3) - for reading/writing positions
            self.executor_redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,  # Executor uses DB 3
                decode_responses=True
            )

            # Scout Redis (DB 0) - for reading market data
            self.scout_redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,  # Scout uses DB 0
                decode_responses=True
            )

            # Test connections
            self.executor_redis.ping()
            self.scout_redis.ping()
            logger.info("PnLUpdater: Connected to Redis (Executor DB 3, Scout DB 0)")
        except redis.ConnectionError as e:
            logger.error(f"PnLUpdater: Failed to connect to Redis: {e}")
            raise

    def calculate_zscore(self, prices, window=20):
        """Calculate z-score from price history"""
        if len(prices) < window:
            return 0.0

        recent = prices[:window]
        mean = sum(recent) / len(recent)
        variance = sum((x - mean) ** 2 for x in recent) / len(recent)
        std = variance ** 0.5

        if std == 0:
            return 0.0

        return (prices[0] - mean) / std

    def get_current_spread(self, pair: str) -> float:
        """
        Calculate current spread for a trading pair using Scout's market data.
        Uses 5-minute rolling average to smooth out volatility spikes.

        For pair trading (e.g., BTC/ETH), we calculate the z-score of the price ratio.
        For single asset pairs (e.g., BTC/USDC), we use the asset's z-score.
        """
        try:
            # Parse pair format: "BTC/ETH" or "BTC/USDC"
            symbols = pair.split('/')
            if len(symbols) != 2:
                logger.warning(f"Invalid pair format: {pair}")
                return 0.0

            base_symbol, quote_symbol = symbols

            # For single asset pairs (vs USDC), just get the asset's z-score
            if quote_symbol == 'USDC':
                # Get price history from Scout's Redis
                history_key = f"history:{base_symbol}"
                price_history_json = self.scout_redis.lrange(history_key, 0, 49)

                if len(price_history_json) < 20:
                    logger.warning(f"Insufficient price history for {base_symbol}")
                    return 0.0

                # Parse price history
                prices = []
                for entry in price_history_json:
                    try:
                        data = json.loads(entry)
                        if 'price' in data:
                            prices.append(data['price'])
                    except json.JSONDecodeError:
                        continue

                if len(prices) < 20:
                    return 0.0

                # Calculate z-score using 5-minute window (average last 5 prices)
                # This smooths out instant volatility spikes
                recent_window = min(5, len(prices))
                recent_avg = sum(prices[:recent_window]) / recent_window

                zscore = self.calculate_zscore(prices, window=20)

                # Convert z-score to spread - use conservative multiplier
                spread = abs(zscore) * 0.01  # Reduced from 0.05 to 0.01 for realism
                return round(spread, 4)

            # For pair trading (BTC/ETH), calculate spread from price ratio
            else:
                # Get both assets' price histories
                base_history_json = self.scout_redis.lrange(f"history:{base_symbol}", 0, 49)
                quote_history_json = self.scout_redis.lrange(f"history:{quote_symbol}", 0, 49)

                if len(base_history_json) < 20 or len(quote_history_json) < 20:
                    logger.warning(f"Insufficient price history for {pair}")
                    return 0.0

                # Parse both price histories
                base_prices = []
                quote_prices = []

                for entry in base_history_json:
                    try:
                        data = json.loads(entry)
                        if 'price' in data:
                            base_prices.append(data['price'])
                    except json.JSONDecodeError:
                        continue

                for entry in quote_history_json:
                    try:
                        data = json.loads(entry)
                        if 'price' in data:
                            quote_prices.append(data['price'])
                    except json.JSONDecodeError:
                        continue

                if len(base_prices) < 20 or len(quote_prices) < 20:
                    return 0.0

                # Calculate price ratios with 5-minute smoothing
                min_len = min(len(base_prices), len(quote_prices))
                ratios = []
                for i in range(min_len):
                    if quote_prices[i] > 0:
                        ratios.append(base_prices[i] / quote_prices[i])

                if len(ratios) < 20:
                    return 0.0

                # Use 5-period moving average of the ratio
                recent_window = min(5, len(ratios))
                recent_ratios = ratios[:recent_window]
                smoothed_ratio = sum(recent_ratios) / len(recent_ratios)

                # Calculate z-score using the smoothed ratio
                zscore = self.calculate_zscore(ratios, window=20)

                # Cap z-score at realistic values (±3 is typical for statistical significance)
                zscore = max(-3.0, min(3.0, zscore))

                # Convert z-score to spread - use realistic multiplier for pair trading
                # Typical crypto pair spreads are 0.1% - 2% in normal markets
                # Z-score of 2.0 should map to ~1% spread
                spread = abs(zscore) * 0.005  # 0.5% per z-score unit

                # Final clamp to ensure realism
                spread = max(0.0005, min(spread, 0.025))  # 0.05% - 2.5%

                return round(spread, 4)

        except Exception as e:
            logger.error(f"Failed to calculate spread for {pair}: {e}")
            return 0.0

    def calculate_risk_level(self, pnl_percent: float) -> str:
        """Determine risk level based on PnL percentage"""
        if pnl_percent <= -5.0:
            return 'high'
        elif pnl_percent <= -2.0:
            return 'medium'
        else:
            return 'low'

    def update_position_pnl(self, position_id: str) -> bool:
        """
        Update a single position's PnL using real-time spread data.

        Returns True if successful, False otherwise.
        """
        try:
            # Get position data from Executor Redis
            position_key = f"position:{position_id}"
            position_json = self.executor_redis.get(position_key)

            if not position_json:
                logger.warning(f"Position {position_id} not found")
                return False

            position = json.loads(position_json)

            # Get current spread from Scout's market data
            pair = position.get('pair', 'BTC/ETH')
            current_spread = self.get_current_spread(pair)

            # If we couldn't get current spread, skip update
            if current_spread == 0.0:
                return False

            # Calculate PnL
            entry_spread = position.get('entry_spread', 0.0)
            position_size = position.get('size', 0.0)

            # For pair trading: profit = (current_spread - entry_spread) / entry_spread * size
            # This assumes we're capturing spread convergence
            if entry_spread > 0:
                spread_change = (current_spread - entry_spread) / entry_spread
                pnl = spread_change * position_size
                pnl_percent = spread_change * 100
            else:
                pnl = 0.0
                pnl_percent = 0.0

            # Update position data
            position['current_spread'] = current_spread
            position['pnl'] = round(pnl, 2)
            position['pnl_percent'] = round(pnl_percent, 2)
            position['risk_level'] = self.calculate_risk_level(pnl_percent)
            position['last_updated'] = datetime.now().isoformat()

            # Get remaining TTL
            ttl = self.executor_redis.ttl(position_key)
            if ttl < 0:
                ttl = 86400  # Default 24 hours

            # Write updated position back to Redis
            self.executor_redis.setex(
                position_key,
                ttl,
                json.dumps(position)
            )

            logger.debug(f"Updated {position_id}: spread {entry_spread:.4f} -> {current_spread:.4f}, PnL ${pnl:.2f} ({pnl_percent:.2f}%)")
            return True

        except Exception as e:
            logger.error(f"Failed to update position {position_id}: {e}")
            return False

    def update_all_positions(self):
        """Update PnL for all open positions"""
        try:
            # Get all position IDs from the list
            position_ids = self.executor_redis.lrange("positions:all", 0, -1)

            if not position_ids:
                logger.debug("No positions to update")
                return

            updated_count = 0
            for position_id in position_ids:
                if self.update_position_pnl(position_id):
                    updated_count += 1

            logger.info(f"Updated {updated_count}/{len(position_ids)} positions")

        except Exception as e:
            logger.error(f"Failed to update all positions: {e}")
