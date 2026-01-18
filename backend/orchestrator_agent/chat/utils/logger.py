"""
Activity logging utility for Orchestrator Agent.
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


def log_agent_activity(
    agent: str,
    level: str,
    message: str,
    metadata: Dict[str, Any] = None
):
    """
    Log agent activity to console and Redis.

    Args:
        agent: Agent name ("orchestrator")
        level: Log level ("info", "success", "warning", "error")
        message: Log message
        metadata: Additional metadata dictionary
    """
    log_entry = {
        "agent": agent,
        "level": level,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }

    # Log to console
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(f"[{agent.upper()}] {message}")

    # Store in Redis (optional)
    try:
        from .redis_cache import cache
        cache.log_activity(log_entry)
    except Exception as e:
        logger.error(f"Failed to log to Redis: {e}")

    return log_entry
