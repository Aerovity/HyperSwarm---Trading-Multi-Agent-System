"""
Route calculation utilities - pure math functions, NO LLM.
Calculates costs, times, and compares bridge routes.
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_route_cost(route: Dict) -> float:
    """
    Calculate total cost of a route (fees + gas).

    Args:
        route: LI.FI route object

    Returns:
        Total cost in USD
    """
    try:
        total_cost = 0.0

        # Sum all fee costs
        if 'feeCosts' in route:
            for fee in route['feeCosts']:
                if 'amountUSD' in fee:
                    total_cost += float(fee['amountUSD'])

        # Add gas costs
        if 'gasCosts' in route:
            for gas in route['gasCosts']:
                if 'amountUSD' in gas:
                    total_cost += float(gas['amountUSD'])

        return round(total_cost, 4)

    except Exception as e:
        logger.error(f"Failed to calculate route cost: {e}")
        return 0.0


def estimate_route_time(route: Dict) -> int:
    """
    Estimate route completion time in seconds.

    Args:
        route: LI.FI route object

    Returns:
        Estimated time in seconds
    """
    try:
        # LI.FI provides estimate in seconds
        if 'estimate' in route and 'executionDuration' in route['estimate']:
            return int(route['estimate']['executionDuration'])

        # Fallback: estimate based on number of steps
        # Assume 2 minutes per step (conservative estimate)
        if 'steps' in route:
            num_steps = len(route['steps'])
            return num_steps * 120

        # Default fallback
        return 300  # 5 minutes

    except Exception as e:
        logger.error(f"Failed to estimate route time: {e}")
        return 300


def compare_routes(routes: List[Dict]) -> Optional[Dict]:
    """
    Find the cheapest route from a list.

    Args:
        routes: List of LI.FI route objects

    Returns:
        Cheapest route or None if list is empty
    """
    try:
        if not routes:
            return None

        cheapest = None
        min_cost = float('inf')

        for route in routes:
            cost = calculate_route_cost(route)
            if cost < min_cost:
                min_cost = cost
                cheapest = route

        return cheapest

    except Exception as e:
        logger.error(f"Failed to compare routes: {e}")
        return routes[0] if routes else None


def format_route_steps(route: Dict) -> List[Dict]:
    """
    Format route steps for frontend display.

    Args:
        route: LI.FI route object

    Returns:
        List of formatted step dicts
    """
    try:
        formatted_steps = []

        if 'steps' not in route:
            return []

        for i, step in enumerate(route['steps']):
            formatted_step = {
                'step_number': i + 1,
                'action': step.get('type', 'unknown'),
                'tool': step.get('tool', 'unknown'),
                'from_chain': step.get('action', {}).get('fromChainId', ''),
                'to_chain': step.get('action', {}).get('toChainId', ''),
                'from_token': step.get('action', {}).get('fromToken', {}).get('symbol', ''),
                'to_token': step.get('action', {}).get('toToken', {}).get('symbol', ''),
                'from_amount': step.get('estimate', {}).get('fromAmount', '0'),
                'to_amount': step.get('estimate', {}).get('toAmount', '0'),
            }
            formatted_steps.append(formatted_step)

        return formatted_steps

    except Exception as e:
        logger.error(f"Failed to format route steps: {e}")
        return []


def extract_transaction_request(route: Dict) -> Optional[Dict]:
    """
    Extract transaction request data from route for wallet signing.

    Args:
        route: LI.FI route object

    Returns:
        Transaction request dict or None
    """
    try:
        if 'transactionRequest' in route:
            tx_req = route['transactionRequest']
            return {
                'to': tx_req.get('to'),
                'data': tx_req.get('data'),
                'value': tx_req.get('value', '0'),
                'from': tx_req.get('from'),
                'chainId': tx_req.get('chainId'),
                'gasLimit': tx_req.get('gasLimit'),
                'gasPrice': tx_req.get('gasPrice'),
            }

        # Check if it's in the first step
        if 'steps' in route and route['steps']:
            step = route['steps'][0]
            if 'transactionRequest' in step:
                tx_req = step['transactionRequest']
                return {
                    'to': tx_req.get('to'),
                    'data': tx_req.get('data'),
                    'value': tx_req.get('value', '0'),
                    'from': tx_req.get('from'),
                    'chainId': tx_req.get('chainId'),
                    'gasLimit': tx_req.get('gasLimit'),
                    'gasPrice': tx_req.get('gasPrice'),
                }

        return None

    except Exception as e:
        logger.error(f"Failed to extract transaction request: {e}")
        return None


def get_route_summary(route: Dict) -> Dict:
    """
    Get human-readable summary of a route.

    Args:
        route: LI.FI route object

    Returns:
        Summary dict with key info
    """
    try:
        return {
            'from_chain': route.get('fromChainId', 'unknown'),
            'to_chain': route.get('toChainId', 'unknown'),
            'from_token': route.get('fromToken', {}).get('symbol', 'unknown'),
            'to_token': route.get('toToken', {}).get('symbol', 'unknown'),
            'from_amount': route.get('fromAmount', '0'),
            'to_amount': route.get('toAmount', '0'),
            'cost_usd': calculate_route_cost(route),
            'estimated_time_seconds': estimate_route_time(route),
            'tool': route.get('steps', [{}])[0].get('tool', 'unknown') if route.get('steps') else 'unknown',
        }

    except Exception as e:
        logger.error(f"Failed to get route summary: {e}")
        return {}
