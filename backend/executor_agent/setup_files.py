#!/usr/bin/env python3
"""
Quick setup script to generate all Executor Agent files.
Run this to create all necessary implementation files at once.
"""
import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\House Computer\Desktop\HyperSwarm\backend\executor_agent")

# File contents dictionary
files = {
    "trading/urls.py": '''"""
URL patterns for trading API endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health', views.health_check, name='health_check'),
    path('agent/logs', views.agent_logs, name='agent_logs'),
    path('positions', views.list_positions, name='list_positions'),
    path('positions/<str:position_id>', views.get_position, name='get_position'),
    path('positions/<str:position_id>/close', views.close_position, name='close_position'),
    path('trades/execute', views.execute_trade, name='execute_trade'),
    path('emergency_stop', views.emergency_stop, name='emergency_stop'),
]
''',

    "trading/views.py": '''"""
REST API views for Executor Agent service.
"""
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

from .utils.redis_cache import RedisCache
from .utils.logger import log_agent_activity

logger = logging.getLogger(__name__)

# Initialize cache
cache = RedisCache()

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

        if not signal_id or not position_size:
            return Response({'error': 'Missing required fields'}, status=400)

        # TODO: Implement trade execution logic
        log_agent_activity("executor", "info", f"Trade execution requested for signal {signal_id}")

        return Response({
            'status': 'demo_mode' if settings.DEMO_MODE else 'executing',
            'signal_id': signal_id,
            'position_size': position_size
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
''',

    "tests/__init__.py": "# Tests package",

    "tests/test_trade_calculations.py": '''"""
Unit tests for trade_calculator.py
"""
from django.test import TestCase
from trading.utils.trade_calculator import (
    calculate_position_size,
    calculate_leverage,
    split_twap_order,
    calculate_take_profit_spread,
    calculate_stop_loss_spread,
    calculate_spread,
    calculate_position_pnl,
)

class TradeCalculatorTests(TestCase):
    """Test trade calculator functions"""

    def test_calculate_position_size(self):
        """Test position size calculation"""
        self.assertEqual(calculate_position_size(10000, 0.30), 3000)
        self.assertEqual(calculate_position_size(5000, 0.20), 1000)

        with self.assertRaises(ValueError):
            calculate_position_size(-100, 0.30)

    def test_calculate_leverage(self):
        """Test leverage calculation"""
        self.assertEqual(calculate_leverage(3000, 1000), 3.0)
        self.assertEqual(calculate_leverage(2000, 1000), 2.0)

        with self.assertRaises(ValueError):
            calculate_leverage(1000, -100)

    def test_split_twap_order(self):
        """Test TWAP order splitting"""
        chunks = split_twap_order(1.0, 5)
        self.assertEqual(len(chunks), 5)
        self.assertEqual(sum(chunks), 1.0)
        self.assertTrue(all(c == 0.2 for c in chunks))

        with self.assertRaises(ValueError):
            split_twap_order(-1, 5)

    def test_calculate_spread(self):
        """Test spread calculation"""
        self.assertAlmostEqual(calculate_spread(110, 100, True), 0.1)
        self.assertEqual(calculate_spread(110, 100, False), 10)

        with self.assertRaises(ValueError):
            calculate_spread(100, 0)

    def test_calculate_position_pnl(self):
        """Test PnL calculation"""
        pnl = calculate_position_pnl(
            entry_spread=2.0,
            current_spread=1.0,
            long_size=0.1,
            short_size=1.0,
            long_entry_price=50000,
            short_entry_price=3000,
            long_current_price=51000,
            short_current_price=2900
        )
        # Long: 0.1 * (51000 - 50000) = 100
        # Short: 1.0 * (3000 - 2900) = 100
        # Total = 200
        self.assertEqual(pnl, 200)
''',

    "tests/test_risk_controls.py": '''"""
Unit tests for risk_controls.py
"""
from django.test import TestCase
from trading.utils.risk_controls import (
    validate_max_positions,
    validate_position_size,
    validate_leverage,
    validate_portfolio_value,
    validate_all_risk_controls,
)

class RiskControlsTests(TestCase):
    """Test risk control functions"""

    def test_validate_max_positions(self):
        """Test max positions validation"""
        self.assertTrue(validate_max_positions(2, 3))
        self.assertFalse(validate_max_positions(3, 3))

    def test_validate_position_size(self):
        """Test position size validation"""
        self.assertTrue(validate_position_size(3000, 10000, 0.30))
        self.assertFalse(validate_position_size(4000, 10000, 0.30))
        self.assertFalse(validate_position_size(1000, -100, 0.30))

    def test_validate_leverage(self):
        """Test leverage validation"""
        self.assertTrue(validate_leverage(2.5, 3.0))
        self.assertFalse(validate_leverage(3.5, 3.0))

    def test_validate_portfolio_value(self):
        """Test portfolio value validation"""
        self.assertTrue(validate_portfolio_value(1000, 100))
        self.assertFalse(validate_portfolio_value(50, 100))

    def test_validate_all_risk_controls(self):
        """Test all risk controls together"""
        passed, msg = validate_all_risk_controls(
            position_size=3000,
            portfolio_value=10000,
            leverage=2.5,
            current_positions=2
        )
        self.assertTrue(passed)
        self.assertEqual(msg, "All risk controls passed")

        passed, msg = validate_all_risk_controls(
            position_size=4000,
            portfolio_value=10000,
            leverage=2.5,
            current_positions=2
        )
        self.assertFalse(passed)
        self.assertIn("allocation limit", msg)
''',

    "tests/test_api.py": '''"""
API endpoint tests.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from trading.utils.redis_cache import RedisCache

class APITests(TestCase):
    """Test REST API endpoints"""

    def setUp(self):
        """Set up test client and Redis data"""
        self.client = APIClient()
        self.cache = RedisCache()
        self.cache.client.flushdb()

    def tearDown(self):
        """Clean up Redis"""
        self.cache.client.flushdb()

    def test_health_check_endpoint(self):
        """Test /api/health returns health status"""
        response = self.client.get('/api/health')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')

    def test_agent_logs_endpoint(self):
        """Test /api/agent/logs returns logs"""
        response = self.client.get('/api/agent/logs')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_list_positions_endpoint(self):
        """Test /api/positions returns positions"""
        response = self.client.get('/api/positions')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
''',
}

# Create all files
for file_path, content in files.items():
    full_path = BASE_DIR / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {file_path}")

# Extend redis_cache.py with position/trade methods
redis_cache_addition = '''
    def get_all_positions(self):
        """Get all positions"""
        try:
            position_ids = self.client.lrange("positions:all", 0, -1)
            positions = []
            for pid in position_ids:
                pos = self.client.get(f"position:{pid}")
                if pos:
                    import json
                    positions.append(json.loads(pos))
            return positions
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to get positions: {e}")
            return []

    def get_position(self, position_id: str):
        """Get specific position"""
        try:
            import json
            data = self.client.get(f"position:{position_id}")
            return json.loads(data) if data else None
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to get position: {e}")
            return None
'''

# Append to redis_cache.py
redis_cache_path = BASE_DIR / "trading/utils/redis_cache.py"
with open(redis_cache_path, 'a', encoding='utf-8') as f:
    f.write(redis_cache_addition)

print("\\nAll files created successfully!")
print("Setup complete. Run 'python manage.py test' to verify.")
