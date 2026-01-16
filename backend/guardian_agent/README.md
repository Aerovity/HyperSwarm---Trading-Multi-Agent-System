# Guardian Agent Service - HyperSwarm DeFi Trading System

**Fourth of 4 backend services** for the HyperSwarm multi-agent DeFi trading system.

## Overview

The Guardian Agent is the **risk management and trade approval** service. It's the ONLY agent that uses LLM reasoning (Claude API) for intelligent decision making.

## Features

- **Pure Python Risk Calculator**: Deterministic math functions (no LLM)
- **LLM Trade Approval**: Claude API for nuanced risk decisions
- **Hyperliquid Integration**: Real-time positions and account state
- **Portfolio Health Scoring**: 0-100 health score based on multiple factors
- **Risk Alerts**: Real-time monitoring and alerting
- **Demo Mode**: Fully functional testing without API keys

## Architecture

```
Django REST Framework
├── Risk Calculator (Pure Python)
├── Approval Engine (Claude API)
├── Hyperliquid Client (Positions/Balance)
├── Redis Cache (DB 2)
├── JSON Storage (Persistence)
└── REST API Endpoints
```

## Tech Stack

- **Backend**: Django 5.0.1, Django REST Framework
- **Caching**: Redis 5.0.1 with hiredis (DB 2)
- **LLM**: Anthropic Claude API
- **Data**: Hyperliquid Python SDK
- **Math**: NumPy
- **Testing**: Django TestCase, coverage

## Quick Start

### Prerequisites

- Python 3.10+
- Redis server running
- Anthropic API key (for production)

### Installation

```bash
# Navigate to guardian agent
cd backend/guardian_agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY for production

# Create data directory
mkdir -p data

# Run migrations
python manage.py migrate

# Start the service
python manage.py runserver 8003
```

### Start Redis

```bash
# Linux/Mac
redis-server

# Or verify Redis is running
redis-cli ping
# Should return: PONG
```

### Verify Installation

```bash
# Check API health
curl http://localhost:8003/api/health

# Run tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## API Endpoints

### Health & Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check (Redis + Anthropic) |
| `/api/agent/logs` | GET | Activity logs for frontend |

### Portfolio & Positions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portfolio/state` | GET | Portfolio state by address |
| `/api/positions` | GET | Open positions with PnL |
| `/api/risk/metrics` | GET | Detailed risk metrics |

### Trade Approval (LLM-Powered)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/trade/approve` | POST | **LLM-powered trade approval** |
| `/api/alerts` | GET | Risk alerts |

## Trade Approval Flow

```
Scout Signal → POST /api/trade/approve
                    │
                    ▼
         ┌─────────────────────┐
         │  check_risk_limits  │  ← Pure Python (deterministic)
         │  - Max 3 positions  │
         │  - Max 3x leverage  │
         │  - Max 30% per pos  │
         │  - Min 20% liq dist │
         │  - Min 0.7 confid   │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Claude API Call    │  ← LLM reasoning
         │  (nuanced decision) │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Response:          │
         │  - decision         │
         │  - risk_score       │
         │  - reasoning        │
         │  - concerns         │
         └─────────────────────┘
```

## Risk Rules

The Guardian enforces these rules:

| Rule | Limit | Description |
|------|-------|-------------|
| Max Positions | 3 | Maximum concurrent positions |
| Max Leverage | 3.0x | Maximum portfolio leverage |
| Max Position Size | 30% | Maximum % of portfolio per position |
| Min Liquidation Distance | 20% | Minimum distance to liquidation |
| Min Signal Confidence | 0.7 | Minimum signal confidence to trade |

## Configuration

### Environment Variables

```bash
# Anthropic/Claude (required for production)
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Demo mode (set to false for production)
DEMO_MODE=true

# Redis (Guardian uses DB 2)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=2

# Risk Limits
MAX_POSITIONS=3
MAX_LEVERAGE=3.0
MAX_POSITION_PCT=0.30
MIN_LIQUIDATION_DISTANCE=0.20
MIN_SIGNAL_CONFIDENCE=0.7
```

## Demo Mode

When `DEMO_MODE=true`:
- Returns mock portfolio/positions data
- Skips Claude API calls
- Uses rule-based approval decisions
- Perfect for development and testing

## Testing

```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test tests.test_risk_calculator
python manage.py test tests.test_approval_engine
python manage.py test tests.test_redis_cache
python manage.py test tests.test_api

# With coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

## Project Structure

```
guardian_agent/
├── manage.py
├── requirements.txt
├── .env.example
├── data/                          # JSON persistence
├── guardian/                      # Django project
│   ├── settings.py
│   └── urls.py
├── risk/                          # Django app
│   ├── views.py                   # REST API endpoints
│   ├── urls.py
│   └── utils/
│       ├── risk_calculator.py     # Pure Python math (NO LLM)
│       ├── approval_engine.py     # Claude API integration
│       ├── hyperliquid_client.py  # Position/balance data
│       ├── redis_cache.py         # Redis operations
│       ├── json_storage.py        # JSON persistence
│       └── logger.py              # Activity logging
└── tests/
    ├── test_risk_calculator.py
    ├── test_approval_engine.py
    ├── test_redis_cache.py
    └── test_api.py
```

## Integration with Other Agents

### From Scout Agent (Port 8001)

Scout sends trade signals to Guardian for approval:

```python
# Scout calls Guardian to approve trade
response = requests.post('http://localhost:8003/api/trade/approve', json={
    'trade_proposal': {
        'pair': 'BTC/ETH',
        'zscore': 2.5,
        'size': 2500,
        'confidence': 0.85,
    },
    'portfolio_state': {...},
    'market_conditions': {...},
})

if response.json()['decision'] == 'approve':
    # Proceed with trade execution
    pass
```

### From Executor Agent (Port 8004 - Future)

Executor will request approval before executing trades.

## Health Score Calculation

The health score (0-100) is calculated from:

| Factor | Weight | Best | Worst |
|--------|--------|------|-------|
| Liquidation Distance | 40% | >50% | 0% |
| Leverage | 30% | <2x | >5x |
| Position Count | 15% | 0-3 | >5 |
| Margin Usage | 15% | <50% | >80% |

## Troubleshooting

### Redis Connection Failed

```bash
# Check if Redis is running
redis-cli ping

# Start Redis
redis-server
```

### Claude API Errors

```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Use demo mode for testing
export DEMO_MODE=true
```

### Tests Failing

```bash
# Ensure Redis is running
redis-cli ping

# Clear Redis data
redis-cli -n 2 FLUSHDB

# Run tests with verbosity
python manage.py test --verbosity=2
```

## Performance

- **API Response**: < 10ms (cached reads)
- **Redis Operations**: < 5ms (hiredis)
- **LLM Approval**: ~1-2s (Claude API)
- **Demo Mode Approval**: < 50ms

## License

MIT

---

**Built for the HyperSwarm DeFi Trading System Hackathon**
