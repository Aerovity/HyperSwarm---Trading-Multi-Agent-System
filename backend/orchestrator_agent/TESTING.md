# Orchestrator Agent Test Suite

This document contains test cases for the Orchestrator Agent.

## Test 1: Health Check

**Request:**
```bash
curl http://localhost:8005/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "orchestrator_agent",
  "redis": "connected",
  "langchain": "ready",
  "demo_mode": true,
  "model": "claude-sonnet-4-20250514",
  "tools_count": 8
}
```

## Test 2: Simple Chat Test

**Request:**
```bash
curl -X POST http://localhost:8005/api/orchestrator/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, what can you do?"
  }'
```

**Expected:** Orchestrator introduces itself and explains capabilities.

## Test 3: Autonomous Trading Flow

**Request:**
```bash
curl -X POST http://localhost:8005/api/orchestrator/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Do a trade with $2500"
  }'
```

**Expected Steps:**
1. ✅ Calls `get_scout_signals` to fetch signals
2. ✅ Picks highest confidence signal
3. ✅ Calls `approve_trade_with_guardian` for risk approval
4. ✅ If approved: calls `execute_trade` with 1min window
5. ✅ Calls `get_position_status` to show results
6. ✅ Returns markdown response with:
   - Why the pair was chosen (highest confidence)
   - Trade execution confirmation
   - Position details (ID, pair, size, entry spread)

**Expected Response Format:**
```markdown
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

## Test 4: Cross-Chain Bridge Flow

**Request:**
```bash
curl -X POST http://localhost:8005/api/orchestrator/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Bridge 1000 USDC from Polygon"
  }'
```

**Expected Steps:**
1. ✅ Parses "Polygon" → chain ID "137"
2. ✅ Parses "1000 USDC" → amount "1000000000" (6 decimals)
3. ✅ Calls `get_onboarder_quote` with correct params
4. ✅ Calls `execute_bridge` with route_id
5. ✅ Calls `check_bridge_status` to verify completion
6. ✅ Returns markdown response with bridge details

**Expected Response Format:**
```markdown
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

## Test 5: Guardian Rejection & Retry

**Prerequisites:** Ensure Scout has multiple signals with varying confidence.

**Request:**
```bash
curl -X POST http://localhost:8005/api/orchestrator/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Do a trade with $10000"
  }'
```

**Expected:**
- If first signal rejected by Guardian → tries next signal
- Max 3 attempts
- If all 3 rejected → Returns friendly error message

## Test 6: Frontend Integration Test

**Steps:**
1. Open http://localhost:3000
2. Toggle "Enable AI Trading" to ON
3. Type: "Do a trade with $1500"
4. Send message

**Expected:**
- ✅ Loading shows TextShimmer animation: "Processing your request..."
- ✅ Response appears with proper markdown formatting
- ✅ Emojis display correctly (🤖 ✅ ⏳ 💰 📊)
- ✅ Headings are bold
- ✅ Lists are formatted with green bullets
- ✅ Code blocks have dark background

## Test 7: Conversation Context

**Request 1:**
```bash
curl -X POST http://localhost:8005/api/orchestrator/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What trading pairs are available?"
  }'
```

**Request 2 (same conversation):**
```bash
curl -X POST http://localhost:8005/api/orchestrator/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Execute a trade on the first one",
    "conversation_id": "[ID from response 1]"
  }'
```

**Expected:** Agent remembers context from previous message.

## Test 8: Error Handling

**Test 8a: No Signals Available**
- Stop Scout Agent
- Request: "Do a trade with $1000"
- Expected: Friendly error message

**Test 8b: Guardian Unavailable**
- Stop Guardian Agent
- Request: "Do a trade with $1000"
- Expected: Graceful error handling

**Test 8c: Invalid Input**
```bash
curl -X POST http://localhost:8005/api/orchestrator/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": ""
  }'
```
- Expected: 400 error "Message is required"

## Success Criteria

### ✅ Backend Tests
- [x] Health check returns healthy status
- [x] Chat endpoint accepts POST requests
- [x] LangChain agent initialized with 8 tools
- [x] Tools can call other agent APIs (Scout, Guardian, Executor, Onboarder)
- [x] Markdown responses formatted correctly
- [x] Emojis included in responses
- [x] Status updates at each step

### ✅ Frontend Tests
- [x] TextShimmer component renders during loading
- [x] Markdown rendered with ReactMarkdown
- [x] API calls orchestratorApi.chat()
- [x] Conversation ID maintained
- [x] Error handling for backend unavailable

### ✅ Flow Tests
- [x] Autonomous trading: Scout → Guardian → Executor → Position
- [x] Cross-chain bridge: Quote → Execute → Status
- [x] Guardian retry logic (max 3 attempts)
- [x] Always uses 1min time window
- [x] Explains why pair was chosen

## Performance Benchmarks

Expected response times:
- Health check: < 100ms
- Simple chat: < 2s
- Trading flow: 5-10s (depends on agent response times)
- Bridge flow: 3-8s

## Notes for Hackathon Demo

1. **Start all agents first:**
   - Scout (8001)
   - Onboarder (8002)
   - Guardian (8003)
   - Executor (8004)
   - Orchestrator (8005)

2. **Demo script:**
   - Show health checks for all agents
   - Toggle AI Trading mode in frontend
   - Say: "Do a trade with $2500"
   - Watch step-by-step execution
   - Show Position Monitor with live position
   - Say: "Bridge 500 USDC from Polygon"
   - Watch cross-chain flow

3. **Key talking points:**
   - Multi-agent coordination via LangChain
   - Claude-powered intelligent decision making
   - Guardian provides risk management with AI reasoning
   - Beautiful UX with markdown + emojis
   - Production-ready error handling
   - Real integration: Hyperliquid + LI.FI + Pear Protocol
