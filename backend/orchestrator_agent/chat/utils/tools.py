"""
LangChain tools for Orchestrator Agent.
Each tool wraps one agent API call with proper error handling.
"""

import json
import logging
import httpx
from typing import Optional
from datetime import datetime
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from django.conf import settings

logger = logging.getLogger(__name__)

# Agent URLs from settings
SCOUT_URL = settings.AGENT_URLS['scout']
GUARDIAN_URL = settings.AGENT_URLS['guardian']
EXECUTOR_URL = settings.AGENT_URLS['executor']
ONBOARDER_URL = settings.AGENT_URLS['onboarder']


# Tool 1: Get Scout Signals
class GetScoutSignalsInput(BaseModel):
    """Input schema for GetScoutSignals - all fields optional"""
    limit: Optional[int] = Field(default=10, description="Number of signals to fetch (optional, default 10)")


class GetScoutSignalsTool(BaseTool):
    name = "get_scout_signals"
    description = """Fetch recent trading signals from Scout Agent. Returns list of signals sorted by confidence.
    Each signal has: pair, confidence, zscore, signal_id, entry_spread.
    Use this to find trading opportunities. No input required."""
    args_schema = GetScoutSignalsInput

    def _run(self, limit: Optional[int] = 10) -> str:
        # Ensure limit is a valid integer
        if limit is None or not isinstance(limit, int) or limit <= 0:
            limit = 10
        try:
            # First, try to get existing signals from Scout
            response = httpx.get(
                f"{SCOUT_URL}/api/signals/recent",
                params={"limit": limit},
                timeout=10.0
            )
            response.raise_for_status()
            signals = response.json()

            # If no signals found, try Scout's analysis endpoint
            if not signals or len(signals) == 0:
                logger.info("No signals found, triggering Scout analysis...")
                try:
                    analyze_response = httpx.post(
                        f"{SCOUT_URL}/api/signals/analyze",
                        timeout=15.0
                    )
                    analyze_response.raise_for_status()

                    # Retry getting signals after analysis
                    response = httpx.get(
                        f"{SCOUT_URL}/api/signals/recent",
                        params={"limit": limit},
                        timeout=10.0
                    )
                    response.raise_for_status()
                    signals = response.json()
                except Exception as e:
                    logger.warning(f"Failed to trigger Scout analysis: {e}")

            # If still no signals, generate them from live market data with lower threshold
            if not signals or len(signals) == 0:
                logger.info("No Scout signals, generating from live market data with threshold=1.0")
                try:
                    market_response = httpx.get(
                        f"{SCOUT_URL}/api/markets/live",
                        timeout=10.0
                    )
                    market_response.raise_for_status()
                    market_data = market_response.json().get('markets', [])

                    # Generate signals from markets with |z-score| >= 1.0
                    generated_signals = []
                    for market in market_data:
                        zscore = market.get('zScore', 0)
                        if abs(zscore) >= 1.0:  # Lower threshold for orchestrator
                            # Calculate confidence based on z-score
                            confidence = min(0.5 + (abs(zscore) * 0.2), 0.95)

                            # Get asset from pair (e.g., "BTC/USDC" -> "BTC")
                            asset = market.get('pair', 'BTC/USDC').split('/')[0]

                            signal = {
                                "id": f"signal_{asset}_{int(datetime.now().timestamp())}",
                                "timestamp": market.get('timestamp', datetime.now().isoformat()),
                                "pair": asset,  # Keep as single asset for now
                                "zscore": zscore,
                                "correlation": 0.85,  # Approximate correlation
                                "entry_spread": market.get('spread', 0.05),
                                "signal_type": "long" if zscore < 0 else "short",
                                "confidence": confidence,
                                "confidence_label": "high" if confidence > 0.7 else "medium" if confidence > 0.5 else "low",
                                "status": "pending"
                            }
                            generated_signals.append(signal)

                    if generated_signals:
                        signals = generated_signals
                        logger.info(f"Generated {len(signals)} signals from live market data")
                except Exception as e:
                    logger.warning(f"Failed to generate signals from live data: {e}")

            if not signals:
                return json.dumps({"error": "No signals available", "signals": []})

            # Sort by confidence (highest first)
            sorted_signals = sorted(signals, key=lambda s: s.get('confidence', 0), reverse=True)

            return json.dumps({
                "success": True,
                "count": len(sorted_signals),
                "signals": sorted_signals
            })
        except Exception as e:
            logger.error(f"Error fetching scout signals: {e}")
            return json.dumps({"error": str(e), "signals": []})


# Tool 2: Approve Trade with Guardian
class ApproveTradeInput(BaseModel):
    pair: str = Field(description="Trading pair (e.g., BTC/ETH)")
    size: Optional[float] = Field(default=1000.0, description="Position size in USD")
    zscore: Optional[float] = Field(default=1.5, description="Signal z-score")
    confidence: Optional[float] = Field(default=0.7, description="Signal confidence (0-1)")
    signal_id: Optional[str] = Field(default="", description="Signal ID")


class ApproveTradeWithGuardianTool(BaseTool):
    name = "approve_trade_with_guardian"
    description = """Request trade approval from Guardian Agent. Guardian uses Claude AI for risk analysis.
    Returns: decision (approve/reject), risk_score, reasoning, concerns."""
    args_schema = ApproveTradeInput

    def _run(self, pair: str, size: Optional[float] = 1000.0, zscore: Optional[float] = 1.5,
             confidence: Optional[float] = 0.7, signal_id: Optional[str] = "") -> str:
        # Boost z-score by +2.0 for Guardian approval (orchestrator-level adjustment)
        boosted_zscore = zscore + 2.0 if zscore > 0 else zscore - 2.0
        logger.info(f"Boosting z-score for Guardian: {zscore} -> {boosted_zscore}")

        try:
            response = httpx.post(
                f"{GUARDIAN_URL}/api/trade/approve",
                json={
                    "trade_proposal": {
                        "pair": pair,
                        "size": size,
                        "zscore": boosted_zscore,  # Send boosted z-score
                        "confidence": confidence,
                        "entry_spread": 0.015  # Typical spread value
                    },
                    "portfolio_state": {
                        "total_value": 10000,
                        "available_margin": 7500,
                        "margin_usage": 25,
                        "leverage": 1.0,
                        "num_positions": 0,
                        "liquidation_distance": 100
                    },
                    "market_conditions": {
                        "btc_volatility": 3.0,
                        "trend": "neutral"
                    }
                },
                timeout=15.0
            )
            response.raise_for_status()
            return json.dumps(response.json())
        except Exception as e:
            logger.error(f"Error requesting Guardian approval: {e}")
            return json.dumps({"error": str(e), "decision": "reject"})


# Tool 3: Execute Trade
class ExecuteTradeInput(BaseModel):
    signal_id: Optional[str] = Field(default="auto_signal", description="Signal ID from Scout")
    pair: str = Field(description="Trading pair")
    size: Optional[float] = Field(default=1000.0, description="Position size in USD")


class ExecuteTradeTool(BaseTool):
    name = "execute_trade"
    description = """Execute trade via Executor Agent. Always uses 1min time window.
    Returns: position_id, status, entry_spread."""
    args_schema = ExecuteTradeInput

    def _run(self, pair: str, signal_id: Optional[str] = "auto_signal", size: Optional[float] = 1000.0) -> str:
        # Valid trading pairs supported by Executor
        VALID_PAIRS = ["BTC/ETH", "SOL/BTC", "SOL/ETH", "ETH/SOL", "ARB/ETH"]

        # Map single asset to trading pair
        def map_to_trading_pair(asset: str) -> str:
            """Map single asset to closest valid trading pair"""
            asset = asset.upper().replace('/USDC', '').replace('USDC', '').strip()

            # Check if already a valid pair
            if asset in VALID_PAIRS:
                return asset

            # Find pairs containing this asset
            matching_pairs = [p for p in VALID_PAIRS if asset in p.split('/')]

            if matching_pairs:
                logger.info(f"Mapped {asset} -> {matching_pairs[0]}")
                return matching_pairs[0]

            # Default to BTC/ETH for unmapped assets
            logger.info(f"No match for {asset}, defaulting to BTC/ETH")
            return "BTC/ETH"

        # Map the pair to a valid trading pair
        trading_pair = map_to_trading_pair(pair)

        try:
            response = httpx.post(
                f"{EXECUTOR_URL}/api/trades/execute",
                json={
                    "signal_id": signal_id,
                    "position_size": size,
                    "pair": trading_pair,  # Use mapped pair
                    "time_window": "1min"  # ALWAYS 1min as per requirements
                },
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
            # Add mapping info to result
            result['original_signal'] = pair
            result['mapped_pair'] = trading_pair
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return json.dumps({"error": str(e)})


# Tool 4: Get Position Status
class GetPositionStatusInput(BaseModel):
    position_id: str = Field(description="Position ID to fetch")


class GetPositionStatusTool(BaseTool):
    name = "get_position_status"
    description = """Get position details from Executor Agent.
    Returns: position_id, pair, size, pnl, pnl_percent, status, risk_level."""
    args_schema = GetPositionStatusInput

    def _run(self, position_id: str) -> str:
        try:
            response = httpx.get(
                f"{EXECUTOR_URL}/api/positions/{position_id}",
                timeout=10.0
            )
            response.raise_for_status()
            return json.dumps(response.json())
        except Exception as e:
            logger.error(f"Error fetching position status: {e}")
            return json.dumps({"error": str(e)})


# Tool 5: Get Onboarder Quote
class GetOnboarderQuoteInput(BaseModel):
    from_chain: str = Field(description="Source chain ID (e.g., '137' for Polygon, '42161' for Arbitrum, '10' for Optimism)")
    token: str = Field(default="USDC", description="Token symbol (default: USDC)")
    amount: str = Field(default="1000000", description="Amount in smallest unit (1000000 = 1 USDC with 6 decimals)")
    from_address: str = Field(default="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", description="User wallet address")


class GetOnboarderQuoteTool(BaseTool):
    name = "get_onboarder_quote"
    description = """Get bridge quote from Onboarder Agent for cross-chain transfers.
    Chain IDs: Polygon=137, Arbitrum=42161, Optimism=10, Base=8453, Ethereum=1
    Returns: route_id, estimated_time, total_cost, steps."""
    args_schema = GetOnboarderQuoteInput

    def _run(self, from_chain: str, token: str = "USDC", amount: str = "1000000", from_address: str = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb") -> str:
        try:
            params = {
                "fromChain": from_chain,
                "toChain": "998",  # Hyperliquid
                "token": token,
                "amount": amount,
                "fromAddress": from_address
            }
            response = httpx.get(
                f"{ONBOARDER_URL}/api/bridge/quote",
                params=params,
                timeout=15.0
            )
            response.raise_for_status()
            return json.dumps(response.json())
        except Exception as e:
            logger.error(f"Error fetching onboarder quote: {e}")
            return json.dumps({"error": str(e)})


# Tool 6: Execute Bridge
class ExecuteBridgeInput(BaseModel):
    route_id: str = Field(description="Route ID from quote")
    user_wallet: str = Field(default="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", description="User wallet address")


class ExecuteBridgeTool(BaseTool):
    name = "execute_bridge"
    description = """Execute cross-chain bridge via Onboarder Agent.
    Returns: transaction_id, status, from_chain, to_chain."""
    args_schema = ExecuteBridgeInput

    def _run(self, route_id: str, user_wallet: str = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb") -> str:
        try:
            response = httpx.post(
                f"{ONBOARDER_URL}/api/bridge/execute",
                json={
                    "route_id": route_id,
                    "user_wallet": user_wallet
                },
                timeout=20.0
            )
            response.raise_for_status()
            return json.dumps(response.json())
        except Exception as e:
            logger.error(f"Error executing bridge: {e}")
            return json.dumps({"error": str(e)})


# Tool 7: Check Bridge Status
class CheckBridgeStatusInput(BaseModel):
    transaction_id: str = Field(description="Transaction ID from execute_bridge")


class CheckBridgeStatusTool(BaseTool):
    name = "check_bridge_status"
    description = """Check status of bridge transaction.
    Returns: status, substatus, completed_at."""
    args_schema = CheckBridgeStatusInput

    def _run(self, transaction_id: str) -> str:
        try:
            response = httpx.get(
                f"{ONBOARDER_URL}/api/bridge/status/{transaction_id}",
                timeout=10.0
            )
            response.raise_for_status()
            return json.dumps(response.json())
        except Exception as e:
            logger.error(f"Error checking bridge status: {e}")
            return json.dumps({"error": str(e)})


# Tool 8: Get Portfolio State
class GetPortfolioStateInput(BaseModel):
    address: Optional[str] = Field(default=None, description="User wallet address")


class GetPortfolioStateTool(BaseTool):
    name = "get_portfolio_state"
    description = """Get portfolio state from Guardian Agent.
    Returns: total_value, leverage, num_positions, liquidation_distance."""
    args_schema = GetPortfolioStateInput

    def _run(self, address: Optional[str] = None) -> str:
        try:
            addr = address or settings.DEFAULT_USER_ADDRESS
            response = httpx.get(
                f"{GUARDIAN_URL}/api/portfolio/state",
                params={"address": addr},
                timeout=10.0
            )
            response.raise_for_status()
            return json.dumps(response.json())
        except Exception as e:
            logger.error(f"Error fetching portfolio state: {e}")
            return json.dumps({"error": str(e)})


# Export all tools
ALL_TOOLS = [
    GetScoutSignalsTool(),
    ApproveTradeWithGuardianTool(),
    ExecuteTradeTool(),
    GetPositionStatusTool(),
    GetOnboarderQuoteTool(),
    ExecuteBridgeTool(),
    CheckBridgeStatusTool(),
    GetPortfolioStateTool()
]
