# Onboarder Agent

Cross-chain bridge agent for HyperSwarm - enables users to bridge assets from multiple chains to Hyperliquid via LI.FI.

## Overview

The Onboarder Agent is part of the HyperSwarm multi-agent DeFi system. It handles:
- Bridge quote generation from LI.FI
- Transaction execution coordination
- Status tracking and polling
- Hyperliquid balance verification

## Features

- **LI.FI Integration**: Get best routes for cross-chain bridges
- **Multi-Chain Support**: Bridge from Polygon, Arbitrum, Base, Optimism to Hyperliquid
- **Real-time Tracking**: Poll transaction status until completion
- **Demo Mode**: Fully functional simulation for testing without real transactions
- **Dual Storage**: Redis for hot cache (30s TTL), JSON for persistence
- **Rate Limiting**: Built-in API throttling
- **Agent Logging**: Activity logs for frontend monitoring

## Tech Stack

- **Django 5.0** + Django REST Framework
- **Redis** - Real-time caching
- **LI.FI REST API** - Cross-chain routing
- **Hyperliquid Python SDK** - Balance checking
- **Python 3.10+**

## Quick Start

### Prerequisites

- Python 3.10+
- Redis server running on localhost:6379
- uv package manager (optional but recommended)

### Installation

```bash
cd backend/onboarder_agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env and set your values (especially LIFI_API_KEY for production)
```

### Environment Variables

Create a `.env` file with:

```bash
# LI.FI Configuration
LIFI_API_URL=https://li.quest/v1
LIFI_API_KEY=                      # Optional, for higher rate limits
LIFI_INTEGRATOR=hyperswarm-hackathon

# Hyperliquid Configuration
HYPERLIQUID_API_URL=https://api.hyperliquid-testnet.xyz

# Service Configuration
ONBOARDER_PORT=8002
DEBUG=True
DEMO_MODE=true                     # Set to false for production

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1                         # Use different DB from Scout Agent

# Cache Settings
QUOTE_CACHE_TTL=30                 # Seconds
POLL_INTERVAL=5                    # Seconds between status checks
```

### Running the Service

#### Demo Mode (Recommended for Testing)

```bash
# Start with demo mode
export DEMO_MODE=true
python manage.py runserver 8002
```

Demo mode:
- Simulates LI.FI bridge execution
- 3-second completion time
- No real API calls for execution
- Perfect for frontend development

#### Production Mode

```bash
# Start with real LI.FI API
export DEMO_MODE=false
export LIFI_API_KEY=your_api_key_here
python manage.py runserver 8002
```

### Running Tests

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report

# Run specific test module
python manage.py test tests.test_api
python manage.py test tests.test_routes
```

## API Endpoints

### 1. Get Bridge Quote

**GET** `/api/bridge/quote`

Get best bridge route from LI.FI.

**Query Parameters:**
- `fromChain` (required): Source chain ID (e.g., `137` for Polygon)
- `toChain` (optional): Destination chain ID (default: `998` for Hyperliquid)
- `token` (required): Token symbol (e.g., `USDC`)
- `amount` (required): Amount in smallest unit (e.g., `1000000` for 1 USDC)
- `fromAddress` (required): User's wallet address

**Response:**
```json
{
  "route_id": "route_1737036000_1234",
  "from_chain": "137",
  "to_chain": "998",
  "token": "USDC",
  "amount": "1000000",
  "estimated_time": 180,
  "total_cost": 2.50,
  "steps": [...],
  "cached_at": "2025-01-16T10:00:00Z",
  "transaction_request": {
    "to": "0x1234...",
    "data": "0xabcd...",
    "value": "0",
    "chainId": "137"
  }
}
```

### 2. Execute Bridge

**POST** `/api/bridge/execute`

Store bridge transaction (frontend handles wallet signing).

**Body:**
```json
{
  "route_id": "route_1737036000_1234",
  "user_wallet": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "tx_hash": "0xabcd..." // Optional in demo mode
}
```

**Response:**
```json
{
  "transaction_id": "bridge_1737036010_5678",
  "status": "pending",
  "estimated_completion": "2025-01-16T10:05:00Z"
}
```

### 3. Get Bridge Status

**GET** `/api/bridge/status/{tx_id}`

Poll transaction status.

**Response:**
```json
{
  "transaction_id": "bridge_1737036010_5678",
  "status": "completed",
  "substatus": "COMPLETED",
  "from_chain": "137",
  "to_chain": "998",
  "started_at": "2025-01-16T10:00:00Z",
  "completed_at": "2025-01-16T10:03:15Z"
}
```

### 4. Get User Balance

**GET** `/api/bridge/balance/{address}`

Check Hyperliquid balance for address.

**Response:**
```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "withdrawable": 13104.51,
  "account_value": 13109.48,
  "total_margin_used": 4.97
}
```

### 5. Get Supported Chains

**GET** `/api/bridge/chains`

List supported chains for bridging.

**Response:**
```json
{
  "chains": [
    {"id": "137", "name": "Polygon"},
    {"id": "42161", "name": "Arbitrum"},
    {"id": "998", "name": "Hyperliquid"}
  ]
}
```

### 6. Get Agent Logs

**GET** `/api/agent/logs?limit=50`

Retrieve agent activity logs.

### 7. Health Check

**GET** `/api/health`

Check service health.

## Architecture

### Data Flow

1. **Quote Request** → LI.FI API → Cache (30s) → Frontend
2. **Execute Bridge** → Store in Redis + JSON → Return tx_id
3. **Status Polling** → LI.FI API → Update cache → Return status
4. **Balance Check** → Hyperliquid API → Return balance

### Storage Strategy

- **Redis (Hot)**: Real-time quotes (TTL: 30s), recent transactions, activity logs
- **JSON (Cold)**: Persistent transaction history, full activity log archive

### Rate Limiting

Built-in rate limiter prevents API abuse:
- Default: 10 calls per second
- Configurable via `RATE_LIMIT_CALLS` and `RATE_LIMIT_PERIOD`

## Project Structure

```
onboarder_agent/
├── manage.py
├── requirements.txt
├── .env.example
├── data/                          # JSON storage
│   ├── bridge_quotes.json
│   ├── bridge_transactions.json
│   └── agent_logs.json
├── onboarder/                     # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── bridge/                        # Main Django app
│   ├── views.py                   # REST API endpoints
│   ├── urls.py
│   ├── utils/
│   │   ├── lifi_client.py         # LI.FI API wrapper
│   │   ├── route_calculator.py    # Route math functions
│   │   ├── hyperliquid_client.py  # Balance checker
│   │   ├── redis_cache.py         # Redis manager
│   │   ├── json_storage.py        # JSON storage
│   │   └── logger.py              # Activity logger
└── tests/
    ├── test_lifi_client.py
    ├── test_routes.py
    ├── test_transactions.py
    └── test_api.py
```

## Frontend Integration

The frontend is already integrated! See [frontend/lib/api.ts](../../frontend/lib/api.ts) for the API client.

### Example Usage

```typescript
import { onboarderApi } from '@/lib/api'

// Get bridge quote
const quote = await onboarderApi.getQuote({
  fromChain: '137',
  token: 'USDC',
  amount: '1000000',
  fromAddress: userAddress,
})

// Execute bridge
const result = await onboarderApi.executeBridge({
  route_id: quote.route_id,
  user_wallet: userAddress,
})

// Poll status
const status = await onboarderApi.getStatus(result.transaction_id)
```

## Troubleshooting

### Redis Connection Error

```
Failed to connect to Redis: Error 111 connecting to localhost:6379
```

**Solution**: Start Redis server
```bash
redis-server
# or on macOS with Homebrew
brew services start redis
```

### LI.FI Rate Limit

```
LI.FI API error 429: Too Many Requests
```

**Solution**:
1. Get API key from [LI.FI](https://li.fi)
2. Set `LIFI_API_KEY` in `.env`
3. Or increase `RATE_LIMIT_PERIOD` to slow down requests

### Chain Not Supported

```
Failed to get quote from LI.FI
```

**Solution**: Hyperliquid (chain ID 998) may not be supported by LI.FI yet. Use demo mode for testing.

## Development

### Adding New Endpoints

1. Add view function in `bridge/views.py`
2. Add URL pattern in `bridge/urls.py`
3. Add tests in `tests/test_api.py`

### Adding New Chains

Update `SOURCE_CHAINS` in `.env`:
```bash
SOURCE_CHAINS=137,42161,8453,10,1  # Add chain ID 1 for Ethereum
```

## Integration with Scout Agent

The Onboarder Agent works with the Scout Agent to check if users have sufficient funds before executing trades:

```python
from bridge.utils.hyperliquid_client import hyperliquid_client

# Check if user needs to bridge funds
has_funds, available = hyperliquid_client.check_sufficient_funds(
    address="0x...",
    required_amount=1000.0
)

if not has_funds:
    # Suggest bridging from source chain
    log_agent_activity('onboarder', 'info',
        f"User needs ${required - available:.2f} more for trade")
```

## Contributing

When adding features:
1. Write tests first (TDD)
2. Follow Scout Agent patterns for consistency
3. Update this README
4. Use type hints in Python
5. Log all agent activities

## License

MIT License - Part of HyperSwarm Project

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/hyperswarm/issues)
- Docs: [HyperSwarm Docs](https://hyperswarm.dev)
