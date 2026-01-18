"""
REST API views for Orchestrator Agent.
Main chat endpoint that coordinates all agents via LangChain.
"""

import logging
import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

from .utils.agent import get_orchestrator_agent
from .utils.logger import log_agent_activity
from .utils.redis_cache import cache

logger = logging.getLogger(__name__)


@api_view(['POST'])
def chat(request):
    """
    POST /api/orchestrator/chat

    Main chat endpoint for AI orchestrator.
    Coordinates Scout, Guardian, Executor, and Onboarder agents via LangChain.

    Request body:
        message: str - User message
        conversation_id: str (optional) - Conversation ID for context
        user_address: str (optional) - User wallet address

    Returns:
        conversation_id: str
        message: str - Agent response in markdown format
        status: str - 'completed', 'error'
    """
    try:
        # Extract request data
        user_message = request.data.get('message', '').strip()
        conversation_id = request.data.get('conversation_id', f"conv_{int(time.time())}")
        user_address = request.data.get('user_address', settings.DEFAULT_USER_ADDRESS)

        if not user_message:
            return Response({
                'error': 'Message is required'
            }, status=400)

        # Log incoming request
        log_agent_activity(
            "orchestrator",
            "info",
            f"Chat request: {user_message[:100]}",
            {"conversation_id": conversation_id}
        )

        # Get or create agent
        agent = get_orchestrator_agent()

        # Execute agent
        try:
            result = agent.invoke({"input": user_message})
            agent_response = result.get('output', 'Sorry, I encountered an error processing your request.')

            # Log successful response
            log_agent_activity(
                "orchestrator",
                "success",
                "Chat response generated",
                {
                    "conversation_id": conversation_id,
                    "response_length": len(agent_response)
                }
            )

            return Response({
                'conversation_id': conversation_id,
                'message': agent_response,
                'status': 'completed'
            })

        except Exception as agent_error:
            logger.error(f"Agent execution error: {agent_error}")
            log_agent_activity(
                "orchestrator",
                "error",
                f"Agent error: {str(agent_error)}",
                {"conversation_id": conversation_id}
            )

            # Return friendly error message
            return Response({
                'conversation_id': conversation_id,
                'message': "❌ Sorry, I encountered an error processing your request. Please try again or rephrase your message.",
                'status': 'error',
                'error': str(agent_error)
            }, status=500)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=500)


@api_view(['GET'])
def agent_logs(request):
    """
    GET /api/agent/logs

    Get orchestrator agent activity logs.
    """
    try:
        limit = int(request.query_params.get('limit', 50))
        logs = cache.get_logs(limit=limit)
        return Response(logs)
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
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

        # Check if agent is initialized
        agent = get_orchestrator_agent()

        return Response({
            'status': 'healthy',
            'service': 'orchestrator_agent',
            'redis': 'connected',
            'langchain': 'ready',
            'demo_mode': settings.DEMO_MODE,
            'model': settings.ANTHROPIC_MODEL,
            'tools_count': len(agent.tools) if agent else 0
        })
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
