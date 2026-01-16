"""
REST API views for Scout Agent service.
Optimized for sub-10ms response times using Redis cache.
"""

import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .utils.redis_cache import RedisCache
from .utils.calculations import calculate_zscore, calculate_correlation
from .signal_generator import SignalGenerator

logger = logging.getLogger(__name__)

# Initialize cache (singleton for performance)
cache = RedisCache()
generator = SignalGenerator()


@api_view(['GET'])
def live_markets(request):
    """
    GET /api/markets/live

    Returns current prices and z-scores for all tracked pairs.
    Optimized: Reads from Redis cache (sub-ms response).
    """
    try:
        # Hyperliquid uses simple symbol names
        symbols = ["BTC", "ETH", "SOL", "AVAX", "MATIC"]
        market_data = []

        for symbol in symbols:
            price_data = cache.get_price(symbol)
            if price_data:
                # Calculate real-time z-score
                history = cache.get_price_history(symbol, limit=20)
                if len(history) >= 20:
                    try:
                        # Extract prices from history dicts
                        prices = [h.get('price') for h in history if h.get('price') is not None]

                        if len(prices) >= 20:
                            zscore = calculate_zscore(prices, window=20)

                            # Calculate 24h change
                            history_24h = cache.get_price_history(symbol, limit=288)  # ~24h at 5min intervals
                            change_24h = 0.0
                            if len(history_24h) >= 2:
                                old_price = history_24h[-1].get('price', price_data["price"])
                                current_price = price_data["price"]
                                change_24h = ((current_price - old_price) / old_price) * 100 if old_price > 0 else 0.0

                            # Format pair name for frontend: BTC -> BTC/USDC
                            pair_name = f"{symbol}/USDC"

                            # Calculate approximate volume (mock for now, can be enhanced)
                            volume_24h = price_data["price"] * 1000000 * (2 + abs(zscore) * 0.5)

                            market_data.append({
                                "pair": pair_name,
                                "price": price_data["price"],
                                "timestamp": price_data["timestamp"],
                                "zScore": round(zscore, 4),
                                "change24h": round(change_24h, 2),
                                "spread": round(abs(zscore) * 0.05, 3),
                                "volume24h": int(volume_24h)
                            })
                    except Exception as e:
                        logger.error(f"Failed to calculate z-score for {symbol}: {e}")

        return Response({"markets": market_data})
    except Exception as e:
        logger.error(f"Error in live_markets: {e}")
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def recent_signals(request):
    """
    GET /api/signals/recent

    Returns last 20 signals from Redis rolling window.
    Optimized: Direct Redis read, no JSON parsing.
    """
    try:
        limit = int(request.query_params.get('limit', 20))
        signals = cache.get_recent_signals(limit=limit)
        return Response(signals)
    except Exception as e:
        logger.error(f"Error in recent_signals: {e}")
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def pair_correlations(request):
    """
    GET /api/pairs/correlations

    Returns correlation matrix for all tracked assets.
    """
    try:
        symbols = ["BTC", "ETH", "SOL", "AVAX", "MATIC"]
        matrix = {}

        for s1 in symbols:
            for s2 in symbols:
                if s1 != s2:
                    h1 = cache.get_price_history(s1, limit=50)
                    h2 = cache.get_price_history(s2, limit=50)

                    if len(h1) >= 50 and len(h2) >= 50:
                        try:
                            # Extract prices from history dicts
                            prices1 = [h.get('price') for h in h1 if h.get('price') is not None]
                            prices2 = [h.get('price') for h in h2 if h.get('price') is not None]

                            if len(prices1) >= 50 and len(prices2) >= 50:
                                corr = calculate_correlation(prices1, prices2, window=50)
                                pair_key = f"{s1}/{s2}"
                                matrix[pair_key] = round(corr, 4)
                        except Exception as e:
                            logger.error(f"Failed to calculate correlation for {s1}/{s2}: {e}")

        return Response({"correlations": matrix})
    except Exception as e:
        logger.error(f"Error in pair_correlations: {e}")
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def agent_logs(request):
    """
    GET /api/agent/logs

    Returns recent agent activity logs for frontend display.
    Optimized: Redis read with 50-log limit.
    """
    try:
        limit = int(request.query_params.get('limit', 50))
        logs = cache.get_logs(limit=limit)
        return Response(logs)
    except Exception as e:
        logger.error(f"Error in agent_logs: {e}")
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
def analyze_and_signal(request):
    """
    POST /api/signals/analyze

    Trigger signal generation analysis.
    Returns any new signals detected.
    """
    try:
        signals = generator.analyze_markets()
        return Response({
            "signals_detected": len(signals),
            "signals": signals
        })
    except Exception as e:
        logger.error(f"Error in analyze_and_signal: {e}")
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def spread_history(request):
    """
    GET /api/spread/history?pair=BTC/ETH&hours=24

    Returns historical z-score data for a trading pair.
    Used for frontend spread history charts.
    """
    try:
        pair = request.query_params.get('pair', 'BTC/ETH')
        hours = int(request.query_params.get('hours', 24))

        # Extract base symbol from pair format: BTC/ETH -> BTC, BTC/USDC -> BTC
        symbols = pair.split('/')
        if len(symbols) < 1:
            return Response({"error": "Invalid pair format"}, status=400)

        base_symbol = symbols[0]  # Just use "BTC", "ETH", etc.

        # Get historical data from Redis
        history = cache.get_price_history(base_symbol, limit=min(hours * 12, 288))

        if not history or len(history) < 20:
            return Response({"error": "Insufficient historical data"}, status=404)

        # Calculate z-scores for each historical point
        spread_data = []
        for i in range(len(history)):
            if i < 19:  # Need at least 20 points for z-score calculation
                continue

            window = history[max(0, i-19):i+1]
            try:
                # Extract prices from history dicts
                prices = [h.get('price') for h in window if h.get('price') is not None]

                if len(prices) >= 20:
                    zscore = calculate_zscore(prices, window=20)
                    timestamp = history[i].get('timestamp', '')

                    # Format time for display
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%I:%M %p')
                    except:
                        time_str = timestamp

                    spread_data.append({
                        "time": time_str,
                        "zScore": round(zscore, 2),
                        "spread": round(abs(zscore) * 0.05, 3)  # Approximate spread from z-score
                    })
            except Exception as e:
                logger.error(f"Failed to calculate z-score for index {i}: {e}")
                continue

        return Response({
            "pair": pair,
            "data": spread_data[-48:] if len(spread_data) > 48 else spread_data  # Return last 48 points (24h at 5min intervals)
        })
    except Exception as e:
        logger.error(f"Error in spread_history: {e}")
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def health_check(request):
    """
    GET /api/health

    Health check endpoint.
    """
    try:
        # Check Redis connection
        cache.client.ping()

        return Response({
            "status": "healthy",
            "redis": "connected",
            "service": "scout_agent"
        })
    except Exception as e:
        return Response({
            "status": "unhealthy",
            "error": str(e)
        }, status=503)
