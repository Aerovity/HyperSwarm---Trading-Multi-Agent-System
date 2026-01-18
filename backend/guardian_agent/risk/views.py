"""
REST API views for Guardian Agent.
Handles portfolio state, risk metrics, trade approval, and alerts.
"""

import logging
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

from .utils.hyperliquid_client import (
    hyperliquid_client,
    get_demo_user_state,
    get_demo_positions,
)
from .utils.risk_calculator import (
    calculate_portfolio_value,
    calculate_portfolio_leverage,
    calculate_health_score,
    calculate_liquidation_distance,
    calculate_margin_usage,
    calculate_position_pnl,
    calculate_position_risk_level,
    calculate_concentration_risk,
)
from .utils.approval_engine import approval_engine
from .utils.redis_cache import get_cache
from .utils.logger import (
    log_agent_activity,
    log_trade_approval,
    log_risk_alert,
)
from .utils.reflexion import ReflexionMemory

logger = logging.getLogger(__name__)


@api_view(['GET'])
def health_check(request):
    """
    GET /api/health - Health check endpoint.
    Polled by frontend every 10 seconds.
    """
    try:
        # Check Redis connection
        cache = get_cache()
        cache.client.ping()
        redis_status = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "disconnected"

    # Check Anthropic API availability
    if settings.DEMO_MODE:
        anthropic_status = "demo_mode"
    elif settings.ANTHROPIC_API_KEY:
        anthropic_status = "connected"
    else:
        anthropic_status = "no_api_key"

    status = "healthy" if redis_status == "connected" else "unhealthy"

    return Response({
        'status': status,
        'service': 'guardian_agent',
        'redis': redis_status,
        'anthropic': anthropic_status,
        'demo_mode': settings.DEMO_MODE,
    }, status=200 if status == "healthy" else 503)


@api_view(['GET'])
def agent_logs(request):
    """
    GET /api/agent/logs - Activity logs for frontend display.
    Polled by frontend every 2 seconds.
    """
    try:
        limit = int(request.query_params.get('limit', 50))
        cache = get_cache()
        logs = cache.get_logs(limit=limit)
        return Response(logs)
    except Exception as e:
        logger.error(f"Error in agent_logs: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def portfolio_state(request):
    """
    GET /api/portfolio/state - Current portfolio state.

    Query Parameters:
        address (required): User wallet address
    """
    address = request.query_params.get('address')
    if not address:
        return Response({'error': 'address parameter is required'}, status=400)

    try:
        # Check cache first
        cache = get_cache()
        cached_state = cache.get_portfolio_state(address)
        if cached_state:
            return Response(cached_state)

        # Fetch from Hyperliquid (or use demo data)
        if settings.DEMO_MODE:
            state = get_demo_user_state(address)
        else:
            state = hyperliquid_client.get_user_state(address)

        if not state:
            return Response({'error': 'Failed to fetch portfolio state'}, status=503)

        # Calculate additional metrics
        positions = state.get('positions', [])
        account_value = state.get('account_value', 0)
        total_margin_used = state.get('total_margin_used', 0)

        # Calculate health score
        leverage = state.get('leverage', 0)
        margin_usage = total_margin_used / account_value if account_value > 0 else 0

        # Estimate liquidation distance (simplified)
        # In real scenario, this would be calculated from actual liquidation prices
        liq_distance = max(0, 1 - (leverage / 5))  # Rough estimate

        health_score = calculate_health_score(
            liquidation_distance=liq_distance,
            leverage=leverage,
            num_positions=len(positions),
            margin_usage=margin_usage,
        )

        # Build response
        response_data = {
            'address': address,
            'account_value': account_value,
            'available_margin': state.get('available_margin', 0),
            'total_margin_used': total_margin_used,
            'withdrawable': state.get('withdrawable', 0),
            'num_positions': len(positions),
            'total_position_value': calculate_portfolio_value(positions),
            'effective_leverage': leverage,
            'health_score': health_score,
            'last_updated': datetime.now().isoformat(),
        }

        # Cache the result
        cache.set_portfolio_state(address, response_data, ttl=60)

        log_agent_activity(
            "guardian", "info",
            f"Portfolio state fetched for {address[:10]}...",
            data={"health_score": health_score, "leverage": leverage}
        )

        return Response(response_data)

    except Exception as e:
        logger.error(f"Error in portfolio_state: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def get_positions(request):
    """
    GET /api/positions - Current open positions.

    Query Parameters:
        address (required): User wallet address
    """
    address = request.query_params.get('address')
    if not address:
        return Response({'error': 'address parameter is required'}, status=400)

    try:
        # Fetch positions
        if settings.DEMO_MODE:
            positions = get_demo_positions(address)
        else:
            positions = hyperliquid_client.get_positions(address)

        # Enrich positions with additional data
        enriched_positions = []
        total_unrealized_pnl = 0

        for pos in positions:
            entry_price = pos.get('entry_price', 0)
            mark_price = pos.get('mark_price', entry_price)
            size = abs(pos.get('size', 0))
            is_long = pos.get('is_long', True)
            leverage = pos.get('leverage', 1.0)
            liquidation_price = pos.get('liquidation_price', 0)

            # Calculate PnL
            pnl_usd, pnl_pct = calculate_position_pnl(
                entry_price=entry_price,
                current_price=mark_price,
                size=size,
                is_long=is_long
            )

            # Calculate liquidation distance
            if liquidation_price > 0:
                liq_distance = abs(mark_price - liquidation_price) / mark_price
            else:
                liq_distance = 1.0

            # Determine risk level
            risk_level = calculate_position_risk_level(
                leverage=leverage,
                liquidation_distance=liq_distance,
                pnl_percent=pnl_pct
            )

            enriched_positions.append({
                'symbol': pos.get('symbol'),
                'side': 'long' if is_long else 'short',
                'size': size,
                'entry_price': entry_price,
                'mark_price': mark_price,
                'unrealized_pnl': pnl_usd,
                'unrealized_pnl_pct': pnl_pct,
                'leverage': leverage,
                'margin_used': pos.get('margin_used', 0),
                'liquidation_price': liquidation_price,
                'liquidation_distance': liq_distance,
                'risk_level': risk_level,
            })

            total_unrealized_pnl += pnl_usd

        return Response({
            'positions': enriched_positions,
            'total_positions': len(enriched_positions),
            'total_unrealized_pnl': total_unrealized_pnl,
            'last_updated': datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Error in get_positions: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def risk_metrics(request):
    """
    GET /api/risk/metrics - Detailed risk metrics.

    Query Parameters:
        address (required): User wallet address
    """
    address = request.query_params.get('address')
    if not address:
        return Response({'error': 'address parameter is required'}, status=400)

    try:
        # Check cache first
        cache = get_cache()
        cached_metrics = cache.get_risk_metrics(address)
        if cached_metrics:
            return Response(cached_metrics)

        # Fetch state
        if settings.DEMO_MODE:
            state = get_demo_user_state(address)
        else:
            state = hyperliquid_client.get_user_state(address)

        if not state:
            return Response({'error': 'Failed to fetch user state'}, status=503)

        positions = state.get('positions', [])
        account_value = state.get('account_value', 0)
        total_margin_used = state.get('total_margin_used', 0)
        leverage = state.get('leverage', 0)

        # Calculate metrics
        margin_usage = calculate_margin_usage(
            total_margin_used, account_value
        ) if account_value > 0 else 0

        # Estimate liquidation distance
        liq_distance = max(0, 1 - (leverage / 5))

        # Health score
        health_score = calculate_health_score(
            liquidation_distance=liq_distance,
            leverage=leverage,
            num_positions=len(positions),
            margin_usage=margin_usage,
        )

        # Position concentration
        concentration = calculate_concentration_risk(positions)

        # Risk breakdown
        risk_breakdown = {
            'leverage_risk': 'high' if leverage > 2.5 else ('medium' if leverage > 1.5 else 'low'),
            'concentration_risk': 'high' if any(v > 0.5 for v in concentration.values()) else 'low',
            'margin_risk': 'high' if margin_usage > 0.7 else ('medium' if margin_usage > 0.5 else 'low'),
            'liquidation_risk': 'high' if liq_distance < 0.2 else ('medium' if liq_distance < 0.35 else 'low'),
        }

        # Generate recommendations
        recommendations = []
        if leverage > 2.5:
            recommendations.append("Consider reducing leverage to lower risk")
        if any(v > 0.5 for v in concentration.values()):
            high_conc = [k for k, v in concentration.items() if v > 0.5]
            recommendations.append(f"High concentration in {', '.join(high_conc)} - consider diversifying")
        if margin_usage > 0.7:
            recommendations.append("Margin usage is high - consider closing some positions")
        if liq_distance < 0.2:
            recommendations.append("Close to liquidation - reduce position size urgently")

        metrics = {
            'address': address,
            'health_score': health_score,
            'margin_usage': margin_usage,
            'effective_leverage': leverage,
            'liquidation_distance': liq_distance,
            'position_concentration': concentration,
            'risk_breakdown': risk_breakdown,
            'recommendations': recommendations,
            'last_calculated': datetime.now().isoformat(),
        }

        # Cache metrics
        cache.set_risk_metrics(address, metrics, ttl=30)

        return Response(metrics)

    except Exception as e:
        logger.error(f"Error in risk_metrics: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def approve_trade(request):
    """
    POST /api/trade/approve - LLM-powered trade approval.
    This is the KEY endpoint that uses Claude for intelligent reasoning.

    Request Body:
        trade_proposal: {pair, zscore, size, entry_spread, confidence}
        portfolio_state: {total_value, available_margin, margin_usage, leverage, num_positions, liquidation_distance}
        market_conditions: {btc_volatility, trend}
    """
    try:
        data = request.data

        trade_proposal = data.get('trade_proposal', {})
        portfolio_state = data.get('portfolio_state', {})
        market_conditions = data.get('market_conditions', {})

        # Validate required fields
        if not trade_proposal.get('pair'):
            return Response({'error': 'trade_proposal.pair is required'}, status=400)

        # Call approval engine (uses Claude API in production, demo response in demo mode)
        result = approval_engine.approve_trade_with_llm_reasoning(
            trade_proposal=trade_proposal,
            portfolio_state=portfolio_state,
            market_conditions=market_conditions
        )

        # Store approval in cache
        cache = get_cache()
        cache.set_approval(result['approval_id'], result)

        # Log the decision
        log_trade_approval(
            approval_id=result['approval_id'],
            decision=result['decision'],
            trade_pair=trade_proposal.get('pair', 'UNKNOWN'),
            reasoning=result.get('reasoning', ''),
            risk_score=result.get('risk_score', 50),
        )

        return Response(result)

    except Exception as e:
        logger.error(f"Error in approve_trade: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def get_alerts(request):
    """
    GET /api/alerts - Risk alerts.

    Query Parameters:
        address (optional): Filter by user address
        limit (optional): Maximum alerts to return (default 50)
    """
    try:
        address = request.query_params.get('address')
        limit = int(request.query_params.get('limit', 50))

        cache = get_cache()
        alerts = cache.get_alerts(limit=limit)

        # Filter by address if provided
        if address:
            alerts = [a for a in alerts if a.get('address') == address]

        # Count unacknowledged
        unacknowledged = sum(1 for a in alerts if not a.get('acknowledged', False))

        return Response({
            'alerts': alerts,
            'unacknowledged_count': unacknowledged,
        })

    except Exception as e:
        logger.error(f"Error in get_alerts: {e}")
        return Response({'error': str(e)}, status=500)


# Singleton reflexion memory for outcome recording
_reflexion_memory = None


def get_reflexion_memory() -> ReflexionMemory:
    """Get or create ReflexionMemory singleton."""
    global _reflexion_memory
    if _reflexion_memory is None:
        _reflexion_memory = ReflexionMemory()
    return _reflexion_memory


@api_view(['POST'])
def record_trade_outcome(request):
    """
    POST /api/trade/outcome - Record the outcome of a trade.
    Triggers lesson generation for reflexion learning.

    Request Body:
        approval_id (required): The approval ID of the trade
        pnl (required): Profit/loss as decimal (e.g., 0.025 = +2.5%)
        entry_price (optional): Entry price of the trade
        exit_price (optional): Exit price of the trade
    """
    try:
        data = request.data

        approval_id = data.get('approval_id')
        pnl = data.get('pnl')
        entry_price = data.get('entry_price')
        exit_price = data.get('exit_price')

        if not approval_id:
            return Response({'error': 'approval_id is required'}, status=400)

        if pnl is None:
            return Response({'error': 'pnl is required'}, status=400)

        try:
            pnl = float(pnl)
        except (ValueError, TypeError):
            return Response({'error': 'pnl must be a number'}, status=400)

        # Record outcome and generate lesson
        memory = get_reflexion_memory()
        details = {}
        if entry_price is not None:
            details['entry_price'] = entry_price
        if exit_price is not None:
            details['exit_price'] = exit_price

        lesson = memory.record_outcome(
            approval_id=approval_id,
            pnl=pnl,
            details=details
        )

        if lesson is None:
            return Response({
                'status': 'warning',
                'message': f'No decision found for approval_id {approval_id}. Outcome not recorded.',
            }, status=404)

        # Log the outcome
        log_agent_activity(
            "guardian", "info",
            f"Trade outcome recorded: {approval_id}, PnL: {pnl*100:+.2f}%",
            data={"approval_id": approval_id, "pnl": pnl, "lesson": lesson}
        )

        return Response({
            'status': 'recorded',
            'approval_id': approval_id,
            'pnl': pnl,
            'lesson': lesson,
        })

    except Exception as e:
        logger.error(f"Error in record_trade_outcome: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def get_reflexion_stats(request):
    """
    GET /api/reflexion/stats - Get reflexion learning statistics for a pair.

    Query Parameters:
        pair (required): Trading pair (e.g., "BTC/ETH")
    """
    try:
        pair = request.query_params.get('pair')
        if not pair:
            return Response({'error': 'pair parameter is required'}, status=400)

        memory = get_reflexion_memory()
        stats = memory.get_pair_statistics(pair)
        lessons = memory.get_lessons_for_pair(pair, limit=10)
        context = memory.get_reflexion_context(pair)

        return Response({
            'pair': pair,
            'stats': stats,
            'lessons': lessons,
            'context': context,
        })

    except Exception as e:
        logger.error(f"Error in get_reflexion_stats: {e}")
        return Response({'error': str(e)}, status=500)
