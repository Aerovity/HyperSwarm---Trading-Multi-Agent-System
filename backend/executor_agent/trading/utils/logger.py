"""
Agent activity logger with dual-write strategy.
Writes to Redis (hot) and JSON (cold storage) for speed + durability.
"""

from datetime import datetime
from typing import Literal, Optional
import logging

from .redis_cache import RedisCache
from .json_storage import JSONStorage

logger = logging.getLogger(__name__)

AgentType = Literal["scout", "onboarder", "executor", "guardian"]
LogType = Literal["info", "success", "warning", "error"]

# Initialize cache and storage instances
cache = RedisCache()
storage = JSONStorage()


def log_agent_activity(
    agent: AgentType,
    log_type: LogType,
    message: str,
    data: Optional[dict] = None
):
    """
    Log agent activity to Redis (hot) and JSON (cold storage).

    Redis: Real-time logs for frontend (rolling 100)
    JSON: Historical archive (rolling 1000)

    Args:
        agent: Agent identifier
        log_type: Log level (info/success/warning/error)
        message: Human-readable message
        data: Optional additional data
    """
    try:
        log_entry = {
            "id": f"{agent}_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "type": log_type,
            "message": message,
        }

        if data:
            log_entry["data"] = data

        # Write to both Redis (fast) and JSON (persistent)
        cache.log_activity(log_entry)
        storage.append('agent_logs.json', log_entry, max_items=1000)

        logger.debug(f"Logged {agent} activity: {message}")
    except Exception as e:
        logger.error(f"Failed to log agent activity: {e}")
