"""
High-performance Redis cache manager for Guardian Agent.
Uses Redis DB 2 (Scout=0, Onboarder=1).
Provides caching for portfolio state, risk metrics, approvals, and alerts.
"""

import redis
import json
import logging
from typing import Any, Optional, List, Dict
from django.conf import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache for Guardian Agent data"""

    def __init__(self):
        """Initialize Redis connection to DB 2"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,  # DB 2
                decode_responses=True
            )
            self.client.ping()
            logger.info(f"Connected to Redis DB {settings.REDIS_DB}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

        # Window sizes from settings
        self.approval_window = getattr(settings, 'APPROVAL_WINDOW_SIZE', 100)
        self.alert_window = getattr(settings, 'ALERT_WINDOW_SIZE', 200)
        self.log_window = getattr(settings, 'LOG_WINDOW_SIZE', 100)

    # Portfolio state caching
    def set_portfolio_state(self, address: str, state: Dict, ttl: int = 60):
        """
        Cache portfolio state with TTL.

        Args:
            address: User's wallet address
            state: Portfolio state dict
            ttl: Time to live in seconds (default 60)
        """
        try:
            key = f"portfolio:{address}"
            self.client.setex(key, ttl, json.dumps(state))
            logger.debug(f"Cached portfolio state for {address}")
        except Exception as e:
            logger.error(f"Failed to cache portfolio state: {e}")

    def get_portfolio_state(self, address: str) -> Optional[Dict]:
        """
        Get cached portfolio state.

        Args:
            address: User's wallet address

        Returns:
            Portfolio state dict or None if not cached
        """
        try:
            key = f"portfolio:{address}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get portfolio state: {e}")
            return None

    # Risk metrics caching
    def set_risk_metrics(self, address: str, metrics: Dict, ttl: int = 30):
        """
        Cache risk metrics with short TTL.

        Args:
            address: User's wallet address
            metrics: Risk metrics dict
            ttl: Time to live in seconds (default 30)
        """
        try:
            key = f"risk:{address}"
            self.client.setex(key, ttl, json.dumps(metrics))
        except Exception as e:
            logger.error(f"Failed to cache risk metrics: {e}")

    def get_risk_metrics(self, address: str) -> Optional[Dict]:
        """
        Get cached risk metrics.

        Args:
            address: User's wallet address

        Returns:
            Risk metrics dict or None
        """
        try:
            key = f"risk:{address}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get risk metrics: {e}")
            return None

    # Trade approvals with rolling window
    def set_approval(self, approval_id: str, approval_data: Dict, ttl: int = 86400):
        """
        Store trade approval decision.

        Args:
            approval_id: Unique approval ID
            approval_data: Approval decision data
            ttl: Time to live in seconds (default 24h)
        """
        try:
            # Store approval data
            key = f"approval:{approval_id}"
            self.client.setex(key, ttl, json.dumps(approval_data))

            # Add to rolling window
            self.client.lpush("approvals:recent", approval_id)
            self.client.ltrim("approvals:recent", 0, self.approval_window - 1)

            logger.debug(f"Stored approval {approval_id}")
        except Exception as e:
            logger.error(f"Failed to store approval: {e}")

    def get_approval(self, approval_id: str) -> Optional[Dict]:
        """
        Get approval by ID.

        Args:
            approval_id: Unique approval ID

        Returns:
            Approval data dict or None
        """
        try:
            key = f"approval:{approval_id}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get approval: {e}")
            return None

    def get_recent_approvals(self, limit: int = 20) -> List[Dict]:
        """
        Get recent approval decisions.

        Args:
            limit: Maximum number of approvals to return

        Returns:
            List of approval dicts
        """
        try:
            approval_ids = self.client.lrange("approvals:recent", 0, limit - 1)
            approvals = []

            for approval_id in approval_ids:
                approval = self.get_approval(approval_id)
                if approval:
                    approvals.append(approval)

            return approvals
        except Exception as e:
            logger.error(f"Failed to get recent approvals: {e}")
            return []

    # Risk alerts with rolling window
    def add_alert(self, alert: Dict):
        """
        Add risk alert to rolling window.

        Args:
            alert: Alert dict with id, severity, message, etc.
        """
        try:
            # Store alert data
            alert_id = alert.get('id', f"alert_{len(alert)}")
            key = f"alert:{alert_id}"
            self.client.setex(key, 86400, json.dumps(alert))  # 24h TTL

            # Add to rolling window
            self.client.lpush("alerts:recent", alert_id)
            self.client.ltrim("alerts:recent", 0, self.alert_window - 1)

            logger.debug(f"Added alert {alert_id}")
        except Exception as e:
            logger.error(f"Failed to add alert: {e}")

    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """
        Get recent risk alerts.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of alert dicts
        """
        try:
            alert_ids = self.client.lrange("alerts:recent", 0, limit - 1)
            alerts = []

            for alert_id in alert_ids:
                key = f"alert:{alert_id}"
                data = self.client.get(key)
                if data:
                    alerts.append(json.loads(data))

            return alerts
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []

    def clear_alerts(self, address: Optional[str] = None):
        """
        Clear alerts (all or for specific address).

        Args:
            address: Optional address to filter by
        """
        try:
            if address:
                # Clear alerts for specific address
                alert_ids = self.client.lrange("alerts:recent", 0, -1)
                for alert_id in alert_ids:
                    key = f"alert:{alert_id}"
                    data = self.client.get(key)
                    if data:
                        alert = json.loads(data)
                        if alert.get('address') == address:
                            self.client.delete(key)
                            self.client.lrem("alerts:recent", 0, alert_id)
            else:
                # Clear all alerts
                self.client.delete("alerts:recent")
                keys = self.client.keys("alert:*")
                if keys:
                    self.client.delete(*keys)

            logger.info(f"Cleared alerts for {address or 'all'}")
        except Exception as e:
            logger.error(f"Failed to clear alerts: {e}")

    # Activity logging
    def log_activity(self, log_entry: Dict):
        """
        Log agent activity with rolling window.

        Args:
            log_entry: Log entry dict
        """
        try:
            self.client.lpush("logs:agent", json.dumps(log_entry))
            self.client.ltrim("logs:agent", 0, self.log_window - 1)
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

    def get_logs(self, limit: int = 50) -> List[Dict]:
        """
        Get recent activity logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List of log entry dicts
        """
        try:
            logs = self.client.lrange("logs:agent", 0, limit - 1)
            return [json.loads(log) for log in logs]
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return []


# Singleton instance
_cache_instance = None


def get_cache() -> RedisCache:
    """Get or create Redis cache singleton"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance
