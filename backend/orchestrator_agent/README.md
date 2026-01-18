# Orchestrator Agent - HyperSwarm DeFi

AI-powered orchestrator for autonomous trading and cross-chain bridging.

## Overview

The Orchestrator Agent is a LangChain-powered AI that coordinates all 4 HyperSwarm agents:
- **Scout Agent**: Market monitoring and signal generation
- **Guardian Agent**: Risk management and trade approval
- **Executor Agent**: Trade execution and position management
- **Onboarder Agent**: Cross-chain bridging via LI.FI

## Features

✅ **Autonomous Trading**: "Do a trade with $2500" → Picks best signal → Guardian approval → Execute
✅ **Cross-Chain Bridging**: "Bridge 1000 USDC from Polygon" → Get quote → Execute → Track status
✅ **Markdown Responses**: Beautiful formatting with emojis (🚀 ✅ ⏳ ❌ 💰 📊)
✅ **Status Updates**: Real-time progress at each step
✅ **Guardian Retry**: Max 3 attempts if trade rejected
✅ **Always 1min window**: Consistent execution timeframe

## Installation

```bash
cd backend/orchestrator_agent
pip install -r requirements.txt
```

## Configuration

Copy `.env` file and configure:

```bash
# Anthropic API (reuse from Guardian)
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=4

# Agent URLs
SCOUT_URL=http://localhost:8001
GUARDIAN_URL=http://localhost:8003
EXECUTOR_URL=http://localhost:8004
ONBOARDER_URL=http://localhost:8002
```

## Running

```bash
# Start server
python manage.py runserver 8005

# Health check
curl http://localhost:8005/api/health
```

## API Endpoints

### POST /api/orchestrator/chat
Main chat endpoint for AI orchestrator.

**Request:**
```json
{
  "message": "Do a trade with $2500",
  "conversation_id": "conv_123",
  "user_address": "0x742d35..."
}
```

**Response:**
```json
{
  "conversation_id": "conv_123",
  "message": "🤖 **Starting Trade Execution**\n\n✅ Found BTC/ETH signal...",
  "status": "completed"
}
```

### GET /api/agent/logs
Get orchestrator activity logs.

### GET /api/health
Health check endpoint.

## Example Conversations

### Autonomous Trading
```
User: "Do a trade with $2500"

Orchestrator:
🤖 **Starting Trade Execution with $2500**

**Step 1: Market Analysis** ⏳
Analyzing Scout signals...
✅ Found **BTC/ETH** signal (confidence: 87%, z-score: 2.4)

**Why this pair?**
Highest confidence signal showing strong mean reversion opportunity.

**Step 2: Risk Assessment** ⏳
Requesting Guardian approval...
✅ **APPROVED** by Guardian (Risk Score: 78/100)

**Step 3: Trade Execution** ⏳
Executing trade via Executor...
✅ **Trade Executed Successfully!**

💰 **Position Summary:**
- Pair: BTC/ETH
- Size: $2,500
- Position ID: pos_123456
- Entry Spread: 0.0145
- Time Window: 1min

📊 Check Position Monitor for live PnL updates!
```

### Cross-Chain Bridging
```
User: "Bridge 1000 USDC from Polygon"

Orchestrator:
🌉 **Starting Cross-Chain Bridge**

**Step 1: Getting Quote** ⏳
Fetching bridge route from Polygon to Hyperliquid...
✅ Quote received

💰 **Bridge Details:**
- Amount: 1000 USDC
- From: Polygon
- To: Hyperliquid
- Estimated Time: ~180 seconds
- Fee: $2.50

**Step 2: Executing Bridge** ⏳
Processing transaction...
✅ **Bridge Executed!**

Transaction ID: bridge_123456
Status: Completed

🎉 Funds arriving on Hyperliquid shortly!
```

## Architecture

```
User Message
    ↓
LangChain Agent (Claude)
    ↓
Tool Selection & Execution
    ↓
┌─────────────┬──────────────┬──────────────┬──────────────┐
│ Scout Tools │ Guardian Tools│ Executor Tools│ Onboarder Tools│
└─────────────┴──────────────┴──────────────┴──────────────┘
    ↓
Markdown Response with Status Updates
```

## Tools Available

1. **get_scout_signals**: Fetch trading signals
2. **approve_trade_with_guardian**: Request risk approval
3. **execute_trade**: Execute trade (always 1min window)
4. **get_position_status**: Get position details
5. **get_onboarder_quote**: Get bridge quote
6. **execute_bridge**: Execute cross-chain bridge
7. **check_bridge_status**: Check bridge transaction status
8. **get_portfolio_state**: Get portfolio metrics

## Development

### Testing

```bash
# Unit tests
python manage.py test

# Manual testing
curl -X POST http://localhost:8005/api/orchestrator/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Do a trade with $1000"}'
```

### Debugging

Set `DEBUG=True` and `verbose=True` in agent.py to see tool calls.

## Hackathon Notes

Built for Hyperliquid London Hackathon (3-day sprint).

**What makes this impressive:**
- Multi-agent coordination via LangChain
- Claude-powered intelligent conversation
- Production-ready error handling
- Beautiful markdown UX with emojis
- Real integration with Hyperliquid + LI.FI

## License

MIT
