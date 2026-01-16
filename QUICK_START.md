# HyperSwarm Quick Start Guide

## Prerequisites

1. **Redis** - Must be running
   ```bash
   # Check if Redis is running
   redis-cli ping
   # Should return: PONG

   # If not running, start it
   redis-server
   ```

2. **Python 3.10+**
   ```bash
   python --version
   ```

3. **Node.js 18+**
   ```bash
   node --version
   ```

## Start All Services

### 1. Start Scout Agent (Port 8001)

```bash
cd backend/scout_agent
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python manage.py runserver 8001
```

**Verify:** http://localhost:8001/api/health

### 2. Start Onboarder Agent (Port 8002)

```bash
cd backend/onboarder_agent
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python manage.py runserver 8002
```

**Verify:** http://localhost:8002/api/health

### 3. Start Frontend (Port 3000)

```bash
cd frontend
npm run dev
```

**Open:** http://localhost:3000

## Verify Everything Works

### Check Backend Health

```bash
# Scout Agent
curl http://localhost:8001/api/health

# Onboarder Agent
curl http://localhost:8002/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "scout_agent",  // or "onboarder_agent"
  "redis": "connected"
}
```

### Test Bridge Quote (Onboarder)

```bash
curl "http://localhost:8002/api/bridge/quote?fromChain=137&token=USDC&amount=1000000&fromAddress=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
```

Should return a quote with `route_id`, `estimated_time`, and `total_cost`.

### Check Frontend Integration

1. Open http://localhost:3000
2. **Activity Log** should show logs from both agents
3. **Bridge Widget** should fetch quotes when you:
   - Select a chain
   - Enter an amount
   - See real-time estimates

## Demo Mode vs Production Mode

### Demo Mode (Default - Recommended)

Both agents are configured with `DEMO_MODE=true` by default.

**Benefits:**
- No API keys needed
- Instant responses
- Perfect for frontend development
- Safe for hackathon demos

**What's simulated:**
- LI.FI bridge execution (3s delay)
- Market data (Scout Agent)
- Transaction status updates

### Production Mode

To use real APIs:

1. **Scout Agent:** Update WebSocket to real Hyperliquid
2. **Onboarder Agent:** Get LI.FI API key
   ```bash
   cd backend/onboarder_agent
   # Edit .env
   DEMO_MODE=false
   LIFI_API_KEY=your_api_key_here
   ```

## Running Tests

### Scout Agent Tests
```bash
cd backend/scout_agent
python manage.py test
```

### Onboarder Agent Tests
```bash
cd backend/onboarder_agent
python manage.py test
```

### Expected Results
- All tests should pass
- 85%+ code coverage
- No Redis connection errors

## Troubleshooting

### Redis Not Connected

**Error:** `Failed to connect to Redis: Error 111`

**Solution:**
```bash
redis-server
# Keep this running in a separate terminal
```

### Port Already in Use

**Error:** `Error: That port is already in use.`

**Solution:**
```bash
# Find process using port (Linux/Mac)
lsof -ti:8001 | xargs kill -9
lsof -ti:8002 | xargs kill -9

# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

### Python Module Not Found

**Error:** `ModuleNotFoundError: No module named 'django'`

**Solution:**
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Can't Fetch Logs

**Error:** `Failed to fetch agent logs`

**Check:**
1. Backend services are running
2. Ports 8001 and 8002 are accessible
3. No CORS errors in browser console

**Solution:**
```bash
# Check if services are up
curl http://localhost:8001/api/health
curl http://localhost:8002/api/health
```

## Development Workflow

### Making Backend Changes

1. Edit files in `backend/<agent>/`
2. Django auto-reloads on save
3. Test with curl or frontend
4. Run tests: `python manage.py test`

### Making Frontend Changes

1. Edit files in `frontend/`
2. Next.js hot-reloads automatically
3. Check browser for changes
4. Check console for errors

## Project Ports

- **3000** - Next.js Frontend
- **8001** - Scout Agent API
- **8002** - Onboarder Agent API
- **6379** - Redis (internal)

## Useful Commands

### View Logs in Real-Time

```bash
# Scout Agent
curl -s http://localhost:8001/api/agent/logs | python -m json.tool

# Onboarder Agent
curl -s http://localhost:8002/api/agent/logs | python -m json.tool

# Combined (from frontend API)
# Just open http://localhost:3000 and check Activity Log widget
```

### Clear Redis Cache

```bash
redis-cli FLUSHDB
```

### Reset Everything

```bash
# Stop all services (Ctrl+C in each terminal)

# Clear Redis
redis-cli FLUSHDB

# Clear JSON logs
rm backend/scout_agent/data/*.json
rm backend/onboarder_agent/data/*.json

# Restart services
```

## Next Steps

1. ✅ Scout Agent is running (market analysis)
2. ✅ Onboarder Agent is running (cross-chain bridging)
3. 🔜 Executor Agent (trade execution)
4. 🔜 Guardian Agent (risk management)
5. 🔜 LangGraph Orchestrator (AI coordination)

## Support

- **Code:** Browse `backend/` and `frontend/` directories
- **Docs:** Check individual README files
- **Tests:** See `tests/` directories for examples

---

**Status:** All systems ready for hackathon demo! 🚀
