"""
REST API views for Executor Agent service.
"""
import logging
import time
import json
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

from .utils.redis_cache import RedisCache
from .utils.logger import log_agent_activity

logger = logging.getLogger(__name__)

# Initialize cache
cache = RedisCache()
redis_client = cache.client  # Direct Redis client access

@api_view(['GET'])
def health_check(request):
    """GET /api/health - Health check endpoint."""
    try:
        cache.client.ping()
        redis_status = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "disconnected"

    status = "healthy" if redis_status == "connected" else "unhealthy"

    return Response({
        'status': status,
        'service': 'executor_agent',
        'redis': redis_status,
        'demo_mode': settings.DEMO_MODE,
    }, status=200 if status == "healthy" else 503)

@api_view(['GET'])
def agent_logs(request):
    """GET /api/agent/logs - Activity logs."""
    try:
        limit = int(request.query_params.get('limit', 50))
        logs = cache.get_logs(limit=limit)
        return Response(logs)
    except Exception as e:
        logger.error(f"Error in agent_logs: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def list_positions(request):
    """GET /api/positions - List all positions."""
    try:
        positions = cache.get_all_positions()
        return Response(positions)
    except Exception as e:
        logger.error(f"Error in list_positions: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def get_position(request, position_id):
    """GET /api/positions/:id - Get position details."""
    try:
        position = cache.get_position(position_id)
        if not position:
            return Response({'error': 'Position not found'}, status=404)
        return Response(position)
    except Exception as e:
        logger.error(f"Error in get_position: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def close_position(request, position_id):
    """POST /api/positions/:id/close - Close a position."""
    try:
        position = cache.get_position(position_id)
        if not position:
            return Response({'error': 'Position not found'}, status=404)

        # TODO: Implement position closing logic
        log_agent_activity("executor", "info", f"Manual close requested for position {position_id}")

        return Response({'status': 'closing', 'position_id': position_id})
    except Exception as e:
        logger.error(f"Error in close_position: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def execute_trade(request):
    """POST /api/trades/execute - Execute trade."""
    try:
        signal_id = request.data.get('signal_id')
        position_size = request.data.get('position_size')
        pair = request.data.get('pair', 'BTC/ETH')  # Default pair

        if not signal_id or not position_size:
            return Response({'error': 'Missing required fields'}, status=400)

        # Create demo position with realistic entry spread
        position_id = f"pos_{int(time.time() * 1000)}"

        # Use realistic entry spread based on typical pair trading ranges
        # Most crypto pair trades have spreads between 0.1% - 2%
        import random
        entry_spread = round(random.uniform(0.001, 0.02), 4)  # 0.1% - 2%

        position_data = {
            'position_id': position_id,
            'signal_id': signal_id,
            'pair': pair,
            'size': position_size,
            'position_size': position_size,
            'entry_spread': entry_spread,
            'current_spread': entry_spread,
            'entry_time': datetime.now().isoformat(),
            'status': 'open',
            'pnl': 0.0,
            'pnl_percent': 0.0,
            'risk_level': 'low',
        }

        # Store position in Redis
        redis_client.setex(
            f"position:{position_id}",
            86400,  # 24 hour expiry
            json.dumps(position_data)
        )

        # Add position ID to the list of all positions
        redis_client.lpush("positions:all", position_id)
        # Keep list manageable (max 100 positions)
        redis_client.ltrim("positions:all", 0, 99)

        log_agent_activity("executor", "success", f"Position opened: {position_id} for {pair}")

        return Response({
            'status': 'submitted',
            'position_id': position_id,
            'signal_id': signal_id,
            'position_size': position_size,
            'pair': pair
        })
    except Exception as e:
        logger.error(f"Error in execute_trade: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def emergency_stop(request):
    """POST /api/emergency_stop - Close all positions."""
    try:
        log_agent_activity("executor", "warning", "Emergency stop activated")
        # TODO: Implement emergency stop logic
        return Response({'status': 'all_positions_closed' if settings.DEMO_MODE else 'closing'})
    except Exception as e:
        logger.error(f"Error in emergency_stop: {e}")
        return Response({'error': str(e)}, status=500)
