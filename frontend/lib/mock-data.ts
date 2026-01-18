import type { Agent, MarketData, Position, ActivityLog } from "@/types"
import type { CandlestickData, Time } from "lightweight-charts"

// Base prices for different trading pairs
export const basePrices: Record<string, number> = {
  "BTC/USDC": 97500,
  "ETH/USDC": 3420,
  "SOL/USDC": 178,
  "BTC/ETH": 28.5,
  "SOL/BTC": 0.00183,
  "ARB/USDC": 0.89,
}

// Track last prices for live updates
const lastPrices: Record<string, number> = {}

// Generate mock candlestick data for Lightweight Charts
export function generateMockCandlestickData(
  pair: string,
  count: number = 100
): CandlestickData[] {
  const basePrice = basePrices[pair] || 100
  const data: CandlestickData[] = []
  const now = Math.floor(Date.now() / 1000)
  const interval = 60 // 1-minute candles

  let currentPrice = basePrice * (0.98 + Math.random() * 0.04) // Start within 2% of base

  for (let i = count; i >= 0; i--) {
    const time = (now - i * interval) as Time

    // Generate OHLC with realistic variation
    const volatility = basePrice * 0.002 // 0.2% volatility per candle
    const open = currentPrice
    const change = (Math.random() - 0.5) * 2 * volatility
    const close = open + change
    const high = Math.max(open, close) + Math.random() * volatility * 0.5
    const low = Math.min(open, close) - Math.random() * volatility * 0.5

    data.push({ time, open, high, low, close })
    currentPrice = close
  }

  // Store last price for live updates
  lastPrices[pair] = currentPrice

  return data
}

// Generate a new candle for live updates
export function generateNewCandle(pair: string = "BTC/USDC"): CandlestickData {
  const basePrice = basePrices[pair] || 97500
  const now = Math.floor(Date.now() / 1000) as Time

  // Get or initialize last price
  if (!lastPrices[pair]) {
    lastPrices[pair] = basePrice
  }

  const volatility = basePrice * 0.001
  const open = lastPrices[pair]
  const change = (Math.random() - 0.5) * 2 * volatility
  const close = open + change
  const high = Math.max(open, close) + Math.random() * volatility * 0.3
  const low = Math.min(open, close) - Math.random() * volatility * 0.3

  lastPrices[pair] = close

  return { time: now, open, high, low, close }
}

export const mockAgents: Agent[] = [
  {
    id: "1",
    name: "Scout",
    type: "scout",
    status: "active",
    lastAction: "Scanning BTC/ETH spread",
    lastActionTime: new Date(Date.now() - 30000),
  },
  {
    id: "2",
    name: "Onboarder",
    type: "onboarder",
    status: "idle",
    lastAction: "Bridged 500 USDC from Polygon",
    lastActionTime: new Date(Date.now() - 300000),
  },
  {
    id: "3",
    name: "Executor",
    type: "executor",
    status: "processing",
    lastAction: "Executing SOL/BTC pair trade",
    lastActionTime: new Date(Date.now() - 10000),
  },
  {
    id: "4",
    name: "Guardian",
    type: "guardian",
    status: "active",
    lastAction: "Risk assessment complete",
    lastActionTime: new Date(Date.now() - 60000),
  },
]

export const mockMarketData: MarketData[] = [
  { pair: "BTC/USDC", price: 97542.3, change24h: 2.34, zScore: -1.8, spread: 0.05, volume24h: 2340000000 },
  { pair: "ETH/USDC", price: 3421.5, change24h: -1.22, zScore: 0.5, spread: 0.08, volume24h: 890000000 },
  { pair: "SOL/USDC", price: 178.92, change24h: 5.67, zScore: -2.3, spread: 0.12, volume24h: 456000000 },
  { pair: "BTC/ETH", price: 28.52, change24h: 3.56, zScore: 2.1, spread: 0.15, volume24h: 123000000 },
  { pair: "SOL/BTC", price: 0.00183, change24h: 3.33, zScore: -0.8, spread: 0.18, volume24h: 67000000 },
  { pair: "ARB/USDC", price: 0.892, change24h: -2.45, zScore: 1.2, spread: 0.22, volume24h: 34000000 },
]

export const mockPositions: Position[] = [
  {
    id: "1",
    pair: "BTC/ETH",
    entrySpread: 0.12,
    currentSpread: 0.15,
    pnl: 2340.5,
    pnlPercent: 4.68,
    riskLevel: "low",
    size: 50000,
    entryTime: new Date(Date.now() - 7200000),
  },
  {
    id: "2",
    pair: "SOL/BTC",
    entrySpread: 0.22,
    currentSpread: 0.18,
    pnl: -890.25,
    pnlPercent: -1.78,
    riskLevel: "medium",
    size: 50000,
    entryTime: new Date(Date.now() - 3600000),
  },
  {
    id: "3",
    pair: "ETH/SOL",
    entrySpread: 0.08,
    currentSpread: 0.1,
    pnl: 1567.8,
    pnlPercent: 3.14,
    riskLevel: "low",
    size: 50000,
    entryTime: new Date(Date.now() - 1800000),
  },
]

export const mockActivityLogs: ActivityLog[] = [
  {
    id: "1",
    timestamp: new Date(Date.now() - 5000),
    agent: "scout",
    message: "Detected BTC/ETH spread at 2.3σ - Opportunity flagged",
    type: "success",
  },
  {
    id: "2",
    timestamp: new Date(Date.now() - 15000),
    agent: "guardian",
    message: "Risk assessment passed for SOL/BTC position",
    type: "info",
  },
  {
    id: "3",
    timestamp: new Date(Date.now() - 30000),
    agent: "executor",
    message: "Executed pair trade: Long ETH, Short BTC @ 28.52",
    type: "success",
  },
  {
    id: "4",
    timestamp: new Date(Date.now() - 60000),
    agent: "scout",
    message: "Monitoring 6 trading pairs across Hyperliquid",
    type: "info",
  },
  {
    id: "5",
    timestamp: new Date(Date.now() - 120000),
    agent: "onboarder",
    message: "Bridge transaction confirmed - 500 USDC received",
    type: "success",
  },
  {
    id: "6",
    timestamp: new Date(Date.now() - 180000),
    agent: "guardian",
    message: "Portfolio risk level: LOW - All positions healthy",
    type: "info",
  },
  {
    id: "7",
    timestamp: new Date(Date.now() - 240000),
    agent: "scout",
    message: "SOL/USDC Z-score reached -2.3σ - Extreme deviation",
    type: "warning",
  },
  {
    id: "8",
    timestamp: new Date(Date.now() - 300000),
    agent: "executor",
    message: "Position closed: +$1,234.50 profit on ARB/ETH",
    type: "success",
  },
]

export const sourceChains = [
  { id: "polygon", name: "Polygon", icon: "🟣" },
  { id: "arbitrum", name: "Arbitrum", icon: "🔵" },
  { id: "base", name: "Base", icon: "🔷" },
  { id: "optimism", name: "Optimism", icon: "🔴" },
  { id: "ethereum", name: "Ethereum", icon: "⟠" },
]

export const tradingPairs = ["BTC/ETH", "SOL/BTC", "ETH/SOL", "ARB/ETH", "SOL/ETH"]

// Mock bridge quote generator for when backend is unavailable
export function generateMockBridgeQuote(params: {
  fromChain: string
  token: string
  amount: string
}) {
  const amountNum = parseFloat(params.amount) / 1_000_000 // Convert from smallest unit
  return {
    route_id: `mock-${Date.now()}`,
    from_chain: params.fromChain,
    to_chain: 'hyperliquid',
    token: params.token,
    amount: params.amount,
    estimated_time: 180, // 3 minutes
    total_cost: amountNum * 0.001, // 0.1% fee
  }
}

export function generateMockBridgeResult() {
  return {
    status: 'success',
    tx_id: `mock-tx-${Date.now()}`,
    message: 'Bridge executed successfully (demo mode)',
  }
}

// Generate spread history for charts - unique per trading pair
export function generateSpreadHistory(
  pair: string = "BTC/ETH",
  hours = 24,
  currentZScore?: number
): { time: string; spread: number; zScore: number }[] {
  // Use pair name to create unique seed
  const seed = pair.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)

  const data = []
  const now = Date.now()
  const interval = (hours * 60 * 60 * 1000) / 48

  // Create pair-specific parameters from seed
  const phase = (seed % 100) * 0.1
  const amplitude = 1.2 + (seed % 30) * 0.05
  const frequency1 = 3 + (seed % 5)
  const frequency2 = 2 + (seed % 3)

  for (let i = 48; i >= 0; i--) {
    const time = new Date(now - i * interval)

    // Use deterministic sine waves with pair-specific parameters
    const zScoreBase = Math.sin((i + phase) / frequency1) * amplitude
    const zScoreVariation = Math.cos((i + phase * 0.5) / frequency2) * 0.4
    const microVariation = Math.sin((i + phase) / 1.7) * 0.15

    const zScore = zScoreBase + zScoreVariation + microVariation
    const spread = 0.1 + zScore * 0.02

    data.push({
      time: time.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      spread,
      zScore: Math.max(-3, Math.min(3, zScore)), // Clamp to ±3
    })
  }

  // If currentZScore provided, smoothly transition last few points to match
  if (currentZScore !== undefined && data.length > 0) {
    const lastIndex = data.length - 1
    // Blend last 3 points towards the current Z-Score for smooth transition
    for (let i = 0; i < 3 && lastIndex - i >= 0; i++) {
      const blendFactor = 1 - (i * 0.3)
      const original = data[lastIndex - i].zScore
      data[lastIndex - i].zScore = original * (1 - blendFactor) + currentZScore * blendFactor
    }
  }

  return data
}
