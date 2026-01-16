"""
REST API views for Onboarder Agent.
Handles bridge quotes, execution, status checking, and balance verification.
"""

import random
import time
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import logging

from .utils.lifi_client import lifi_client
from .utils.route_calculator import (
    calculate_route_cost,
    estimate_route_time,
    format_route_steps,
    extract_transaction_request,
    get_route_summary,
)
from .utils.hyperliquid_client import hyperliquid_client
from .utils.redis_cache import RedisCache
from .utils.json_storage import JSONStorage
from .utils.logger import log_agent_activity

logger = logging.getLogger(__name__)

# Initialize cache and storage
cache = RedisCache()
storage = JSONStorage()


@api_view(['GET'])
def get_bridge_quote(request):
    """
    GET /api/bridge/quote
    Get best bridge route from LI.FI.

    Query params:
        fromChain: Source chain ID (e.g., 137)
        toChain: Destination chain ID (e.g., 998)
        token: Token symbol (e.g., USDC)
        amount: Amount in base units
        fromAddress: User wallet address
    """
    try:
        # Extract query parameters
        from_chain = request.query_params.get('fromChain')
        to_chain = request.query_params.get('toChain', settings.DESTINATION_CHAIN)
        token = request.query_params.get('token', 'USDC')
        amount = request.query_params.get('amount')
        from_address = request.query_params.get('fromAddress')

        # Validate required params
        if not all([from_chain, amount, from_address]):
            return Response({
                'error': 'Missing required parameters: fromChain, amount, fromAddress'
            }, status=400)

        # Demo mode - return mock quote
        if settings.DEMO_MODE:
            route_id = f"demo_route_{int(datetime.now().timestamp())}"
            mock_quote = {
                'route_id': route_id,
                'from_chain': from_chain,
                'to_chain': to_chain,
                'token': token,
                'amount': amount,
                'estimated_time': 180,  # 3 minutes
                'total_cost': round(float(amount) * 0.001, 2),  # 0.1% fee
                'steps': [
                    {'chain': f'Chain {from_chain}', 'action': 'approve'},
                    {'chain': f'Chain {from_chain}', 'action': 'bridge'},
                    {'chain': f'Chain {to_chain}', 'action': 'receive'},
                ],
                'cached_at': datetime.now().isoformat(),
                'demo_mode': True,
                'transaction_request': {
                    'to': '0x1234567890123456789012345678901234567890',
                    'data': '0xdemo',
                    'value': '0',
                    'chainId': from_chain,
                }
            }

            # Cache the quote
            cache.set_quote(route_id, mock_quote, ttl=settings.QUOTE_CACHE_TTL)

            log_agent_activity(
                'onboarder',
                'info',
                f"Generated demo quote: {token} from chain {from_chain} to {to_chain}",
                {'route_id': route_id, 'amount': amount}
            )

            return Response(mock_quote)

        # Real LI.FI API call
        # Get token addresses (for now using USDC as default)
        # In production, you'd query LI.FI tokens endpoint
        token_addresses = {
            '137': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',  # USDC on Polygon
            '42161': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',  # USDC on Arbitrum
            '8453': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',  # USDC on Base
            '10': '0x7F5c764cBc14f9669B88837ca1490cCa17c31607',  # USDC on Optimism
        }

        from_token = token_addresses.get(from_chain, token)
        to_token = token  # Use symbol for destination

        quote = lifi_client.get_quote(
            from_chain_id=from_chain,
            to_chain_id=to_chain,
            from_token=from_token,
            to_token=to_token,
            from_amount=amount,
            from_address=from_address,
        )

        if not quote:
            return Response({'error': 'Failed to get quote from LI.FI'}, status=503)

        # Generate route ID
        route_id = f"route_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"

        # Format response
        formatted_quote = {
            'route_id': route_id,
            'from_chain': from_chain,
            'to_chain': to_chain,
            'token': token,
            'amount': amount,
            'estimated_time': estimate_route_time(quote),
            'total_cost': calculate_route_cost(quote),
            'steps': format_route_steps(quote),
            'cached_at': datetime.now().isoformat(),
            'transaction_request': extract_transaction_request(quote),
            'raw_quote': quote,  # Include full LI.FI response
        }

        # Cache the quote
        cache.set_quote(route_id, formatted_quote, ttl=settings.QUOTE_CACHE_TTL)

        log_agent_activity(
            'onboarder',
            'success',
            f"Generated quote: {token} from chain {from_chain} to {to_chain}",
            {'route_id': route_id, 'cost': formatted_quote['total_cost']}
        )

        return Response(formatted_quote)

    except Exception as e:
        logger.error(f"Error in get_bridge_quote: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def execute_bridge(request):
    """
    POST /api/bridge/execute
    Store bridge transaction after user signs in frontend.

    Body:
        route_id: Quote/route ID from get_bridge_quote
        user_wallet: User's wallet address
        tx_hash: Transaction hash after user signs (optional in demo mode)
    """
    try:
        data = request.data
        route_id = data.get('route_id')
        user_wallet = data.get('user_wallet')
        tx_hash = data.get('tx_hash')

        if not route_id or not user_wallet:
            return Response({
                'error': 'Missing required fields: route_id, user_wallet'
            }, status=400)

        # Get quote from cache
        quote = cache.get_quote(route_id)
        if not quote:
            return Response({'error': 'Quote not found or expired'}, status=404)

        # Generate transaction ID
        tx_id = f"bridge_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"

        # Demo mode - simulate execution
        if settings.DEMO_MODE:
            time.sleep(3)  # Simulate processing time

            tx_data = {
                'transaction_id': tx_id,
                'route_id': route_id,
                'user_wallet': user_wallet,
                'tx_hash': f"0xdemo{random.randint(100000, 999999)}{'0' * 58}",
                'status': 'completed',
                'substatus': 'COMPLETED',
                'from_chain': quote['from_chain'],
                'to_chain': quote['to_chain'],
                'token': quote['token'],
                'amount': quote['amount'],
                'started_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat(),
                'estimated_completion': datetime.now().isoformat(),
                'demo_mode': True,
            }

            cache.set_transaction(tx_id, tx_data)
            storage.append('bridge_transactions.json', tx_data, max_items=500)

            log_agent_activity(
                'onboarder',
                'success',
                f"Demo bridge completed: {quote['token']} to chain {quote['to_chain']}",
                {'transaction_id': tx_id}
            )

            return Response(tx_data)

        # Real execution - store transaction for tracking
        if not tx_hash:
            return Response({
                'error': 'tx_hash required for real bridge execution'
            }, status=400)

        estimated_completion = datetime.now() + timedelta(seconds=quote['estimated_time'])

        tx_data = {
            'transaction_id': tx_id,
            'route_id': route_id,
            'user_wallet': user_wallet,
            'tx_hash': tx_hash,
            'status': 'pending',
            'substatus': 'WAIT_SOURCE_CONFIRMATIONS',
            'from_chain': quote['from_chain'],
            'to_chain': quote['to_chain'],
            'token': quote['token'],
            'amount': quote['amount'],
            'started_at': datetime.now().isoformat(),
            'estimated_completion': estimated_completion.isoformat(),
        }

        # Store in both Redis and JSON
        cache.set_transaction(tx_id, tx_data)
        storage.append('bridge_transactions.json', tx_data, max_items=500)

        log_agent_activity(
            'onboarder',
            'info',
            f"Bridge initiated: {quote['token']} from chain {quote['from_chain']} to {quote['to_chain']}",
            {'transaction_id': tx_id, 'tx_hash': tx_hash}
        )

        return Response(tx_data)

    except Exception as e:
        logger.error(f"Error in execute_bridge: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def get_bridge_status(request, tx_id):
    """
    GET /api/bridge/status/{tx_id}
    Get bridge transaction status from LI.FI or cache.
    """
    try:
        # Get from cache first
        tx_data = cache.get_transaction(tx_id)

        if not tx_data:
            return Response({'error': 'Transaction not found'}, status=404)

        # If demo mode or already completed, return cached data
        if tx_data.get('demo_mode') or tx_data['status'] in ['completed', 'failed']:
            return Response(tx_data)

        # Poll LI.FI for real transaction status
        tx_hash = tx_data.get('tx_hash')
        from_chain = tx_data.get('from_chain')

        status_data = lifi_client.get_status(
            tx_hash=tx_hash,
            from_chain_id=from_chain
        )

        if status_data:
            # Update transaction with latest status
            updates = {
                'status': status_data.get('status', 'pending').lower(),
                'substatus': status_data.get('substatus', ''),
                'last_updated': datetime.now().isoformat(),
            }

            # Check if completed
            if status_data.get('status') == 'DONE':
                updates['status'] = 'completed'
                updates['completed_at'] = datetime.now().isoformat()

                log_agent_activity(
                    'onboarder',
                    'success',
                    f"Bridge completed: tx {tx_id}",
                    {'transaction_id': tx_id}
                )

            elif status_data.get('status') == 'FAILED':
                updates['status'] = 'failed'

                log_agent_activity(
                    'onboarder',
                    'error',
                    f"Bridge failed: tx {tx_id}",
                    {'transaction_id': tx_id}
                )

            # Update cache and storage
            cache.update_transaction(tx_id, updates)
            tx_data.update(updates)

        return Response(tx_data)

    except Exception as e:
        logger.error(f"Error in get_bridge_status: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def get_user_balance(request, address):
    """
    GET /api/bridge/balance/{address}
    Check Hyperliquid balance for address.
    """
    try:
        balance = hyperliquid_client.get_user_balance(address)

        if balance is None:
            return Response({
                'error': 'Failed to fetch balance from Hyperliquid'
            }, status=503)

        log_agent_activity(
            'onboarder',
            'info',
            f"Balance checked for {address[:8]}...: ${balance['withdrawable']:.2f}",
            {'address': address}
        )

        return Response(balance)

    except Exception as e:
        logger.error(f"Error in get_user_balance: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def get_supported_chains(request):
    """
    GET /api/bridge/chains
    Get list of supported chains for bridging.
    """
    try:
        if settings.DEMO_MODE:
            # Return mock chains in demo mode
            chains = [
                {'id': '137', 'name': 'Polygon', 'logo': 'polygon.svg'},
                {'id': '42161', 'name': 'Arbitrum', 'logo': 'arbitrum.svg'},
                {'id': '8453', 'name': 'Base', 'logo': 'base.svg'},
                {'id': '10', 'name': 'Optimism', 'logo': 'optimism.svg'},
                {'id': '998', 'name': 'Hyperliquid', 'logo': 'hyperliquid.svg'},
            ]
        else:
            # Fetch from LI.FI
            chains = lifi_client.get_chains()

        return Response({'chains': chains})

    except Exception as e:
        logger.error(f"Error in get_supported_chains: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def agent_logs(request):
    """
    GET /api/agent/logs?limit=50
    Get onboarder agent activity logs.
    """
    try:
        limit = int(request.query_params.get('limit', 50))
        logs = cache.get_logs(limit=limit)
        return Response(logs)

    except Exception as e:
        logger.error(f"Error in agent_logs: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def health_check(request):
    """
    GET /api/health
    Health check endpoint.
    """
    try:
        # Check Redis connection
        cache.client.ping()

        # Check LI.FI API (in demo mode skip this)
        lifi_status = "demo_mode" if settings.DEMO_MODE else "connected"

        return Response({
            'status': 'healthy',
            'service': 'onboarder_agent',
            'redis': 'connected',
            'lifi': lifi_status,
            'demo_mode': settings.DEMO_MODE,
        })

    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
