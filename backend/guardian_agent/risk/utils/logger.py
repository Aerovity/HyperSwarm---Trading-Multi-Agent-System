"""
Agent activity logger with dual-write strategy for Guardian Agent.
Writes to Redis (hot) and JSON (cold storage) for speed + durability.
"""

from datetime import datetime
from typing import Literal, Optional
import logging

from .redis_cache import get_cache
from .json_storage import get_storage

logger = logging.getLogger(__name__)

AgentType = Literal["scout", "onboarder", "executor", "guardian"]
LogType = Literal["info", "success", "warning", "error"]


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
        agent: Agent identifier ("guardian" for this service)
        log_type: Log level (info/success/warning/error)
        message: Human-readable message
        data: Optional additional context data
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

        # Write to Redis (fast, for real-time display)
        try:
            cache = get_cache()
            cache.log_activity(log_entry)
        except Exception as e:
            logger.warning(f"Failed to log to Redis: {e}")

        # Write to JSON (persistent archive)
        try:
            storage = get_storage()
            storage.append('agent_logs.json', log_entry, max_items=1000)
        except Exception as e:
            logger.warning(f"Failed to log to JSON: {e}")

        logger.debug(f"Logged {agent} activity: {message}")

    except Exception as e:
        logger.error(f"Failed to log agent activity: {e}")


def log_trade_approval(
    approval_id: str,
    decision: str,
    trade_pair: str,
    reasoning: str,
    risk_score: int
):
    """
    Log trade approval decision.

    Args:
        approval_id: Unique approval identifier
        decision: "approve" or "reject"
        trade_pair: Trading pair (e.g., "BTC/ETH")
        reasoning: Explanation of decision
        risk_score: Risk score 0-100
    """
    log_type = "success" if decision == "approve" else "warning"
    action = "approved" if decision == "approve" else "rejected"
    message = f"Trade {action} for {trade_pair} (risk score: {risk_score})"

    log_agent_activity(
        agent="guardian",
        log_type=log_type,
        message=message,
        data={
            "approval_id": approval_id,
            "decision": decision,
            "pair": trade_pair,
            "risk_score": risk_score,
            "reasoning": reasoning,
        }
    )


def log_risk_alert(
    severity: str,
    alert_type: str,
    message: str,
    address: Optional[str] = None,
    data: Optional[dict] = None
):
    """
    Log risk alert.

    Args:
        severity: "info", "warning", "error", "critical"
        alert_type: Type of alert (e.g., "leverage_warning", "liquidation_risk")
        message: Alert message
        address: Optional user wallet address
        data: Optional additional data
    """
    log_type_map = {
        "info": "info",
        "warning": "warning",
        "error": "error",
        "critical": "error",
    }

    log_agent_activity(
        agent="guardian",
        log_type=log_type_map.get(severity, "warning"),
        message=f"[{alert_type.upper()}] {message}",
        data={
            "severity": severity,
            "alert_type": alert_type,
            "address": address,
            **(data or {}),
        }
    )
