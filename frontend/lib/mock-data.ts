import type { Agent, MarketData, Position, ActivityLog } from "@/types"

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

// Generate spread history for charts
export function generateSpreadHistory(hours = 24): { time: string; spread: number; zScore: number }[] {
  const data = []
  const now = Date.now()
  const interval = (hours * 60 * 60 * 1000) / 48

  for (let i = 48; i >= 0; i--) {
    const time = new Date(now - i * interval)
    // Use deterministic sine waves instead of Math.random() to prevent hydration errors
    // This creates realistic-looking variation without randomness
    const basePattern = Math.sin(i / 5) * 0.05
    const microPattern = Math.sin(i / 2.3) * 0.01  // Secondary wave for variation
    const zScoreBase = Math.sin(i / 4) * 2
    const zScoreVariation = Math.cos(i / 3.7) * 0.3  // Secondary wave for z-score

    data.push({
      time: time.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      spread: 0.1 + basePattern + microPattern,
      zScore: zScoreBase + zScoreVariation,
    })
  }

  return data
}
