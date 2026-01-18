"""
Redis cache manager for Orchestrator Agent.
Stores conversation state and activity logs.
"""

import redis
import json
import logging
from typing import Optional, List, Dict
from django.conf import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache for conversations and logs"""

    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT} DB{settings.REDIS_DB}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def set_conversation(self, conversation_id: str, data: dict, ttl: int = None):
        """Store conversation data"""
        try:
            key = f"conversation:{conversation_id}"
            ttl = ttl or settings.CONVERSATION_CACHE_TTL
            self.client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to set conversation {conversation_id}: {e}")

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Get conversation data"""
        try:
            data = self.client.get(f"conversation:{conversation_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            return None

    def log_activity(self, log_entry: dict):
        """Log agent activity with rolling window"""
        try:
            self.client.lpush("logs:agent", json.dumps(log_entry))
            # Keep last LOG_WINDOW_SIZE items
            self.client.ltrim("logs:agent", 0, settings.LOG_WINDOW_SIZE - 1)
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

    def get_logs(self, limit: int = 50) -> List[dict]:
        """Get recent agent logs"""
        try:
            logs = self.client.lrange("logs:agent", 0, limit - 1)
            return [json.loads(log) for log in logs]
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return []


# Singleton instance
cache = RedisCache()
