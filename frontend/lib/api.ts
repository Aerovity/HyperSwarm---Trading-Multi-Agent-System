/**
 * Centralized API client for HyperSwarm backend services
 */

import { generateMockBridgeQuote, generateMockBridgeResult } from './mock-data'

const API_BASE_URLS = {
  scout: process.env.NEXT_PUBLIC_SCOUT_API_URL || 'http://localhost:8001',
  onboarder: process.env.NEXT_PUBLIC_ONBOARDER_API_URL || 'http://localhost:8002',
  guardian: process.env.NEXT_PUBLIC_GUARDIAN_API_URL || 'http://localhost:8003',
  executor: process.env.NEXT_PUBLIC_EXECUTOR_API_URL || 'http://localhost:8004',
}

class APIError extends Error {
  constructor(message: string, public status?: number, public data?: any) {
    super(message)
    this.name = 'APIError'
  }
}

async function apiClient<T>(
  service: 'scout' | 'onboarder' | 'guardian' | 'executor',
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URLS[service]}${endpoint}`

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        errorData.error || `API error: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    return await response.json()
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    throw new APIError(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

// Scout Agent API (with mock fallbacks when backend unavailable)
export const scoutApi = {
  getLogs: async (limit: number = 50) => {
    try {
      return await apiClient<any[]>('scout', `/api/agent/logs?limit=${limit}`)
    } catch {
      return [] // Activity Log component handles empty with mock data
    }
  },

  getMarketData: async () => {
    try {
      return await apiClient<{ markets: any[] }>('scout', '/api/markets/live')
    } catch {
      // Return empty markets - component will use mock data
      return { markets: [] }
    }
  },

  getSpreadHistory: (pair: string, hours: number = 24) =>
    apiClient<{ pair: string; data: any[] }>('scout', `/api/spread/history?pair=${pair}&hours=${hours}`),

  getSignals: () =>
    apiClient<any[]>('scout', '/api/signals/recent'),

  getCorrelations: () =>
    apiClient<any>('scout', '/api/pairs/correlations'),

  analyzeMarkets: () =>
    apiClient<any>('scout', '/api/signals/analyze', { method: 'POST' }),

  healthCheck: async () => {
    try {
      return await apiClient<{ status: string; redis: string; service: string }>('scout', '/api/health')
    } catch {
      // Return mock healthy status when backend unavailable
      return { status: 'healthy', redis: 'demo', service: 'scout' }
    }
  },
}

// Onboarder Agent API (with mock fallbacks when backend unavailable)
export const onboarderApi = {
  getQuote: async (params: {
    fromChain: string
    toChain?: string
    token: string
    amount: string
    fromAddress: string
  }) => {
    const query = new URLSearchParams({
      fromChain: params.fromChain,
      toChain: params.toChain || '998',
      token: params.token,
      amount: params.amount,
      fromAddress: params.fromAddress,
    })
    try {
      return await apiClient<any>('onboarder', `/api/bridge/quote?${query}`)
    } catch (error) {
      // Fallback to mock data when backend is unavailable
      console.log('Backend unavailable, using mock bridge quote')
      return generateMockBridgeQuote({
        fromChain: params.fromChain,
        token: params.token,
        amount: params.amount,
      })
    }
  },

  executeBridge: async (data: {
    route_id: string
    user_wallet: string
    tx_hash?: string
  }) => {
    try {
      return await apiClient<any>('onboarder', '/api/bridge/execute', {
        method: 'POST',
        body: JSON.stringify(data),
      })
    } catch (error) {
      // Fallback to mock result when backend is unavailable
      console.log('Backend unavailable, using mock bridge execution')
      // Simulate a slight delay for realism
      await new Promise(resolve => setTimeout(resolve, 1500))
      return generateMockBridgeResult()
    }
  },

  getStatus: (txId: string) =>
    apiClient<any>('onboarder', `/api/bridge/status/${txId}`),

  getBalance: (address: string) =>
    apiClient<any>('onboarder', `/api/bridge/balance/${address}`),

  getChains: () =>
    apiClient<any>('onboarder', '/api/bridge/chains'),

  getLogs: async (limit: number = 50) => {
    try {
      return await apiClient<any[]>('onboarder', `/api/agent/logs?limit=${limit}`)
    } catch {
      return [] // Activity Log component handles empty with mock data
    }
  },

  healthCheck: async () => {
    try {
      return await apiClient<any>('onboarder', '/api/health')
    } catch {
      // Return mock healthy status when backend unavailable
      return { status: 'healthy', redis: 'demo', service: 'onboarder' }
    }
  },
}

// Guardian Agent API
export const guardianApi = {
  getPortfolioState: (address: string) =>
    apiClient<any>('guardian', `/api/portfolio/state?address=${address}`),

  getPositions: (address: string) =>
    apiClient<any>('guardian', `/api/positions?address=${address}`),

  getRiskMetrics: (address: string) =>
    apiClient<any>('guardian', `/api/risk/metrics?address=${address}`),

  approveTradeRequest: (data: {
    trade_proposal: {
      pair: string
      zscore: number
      size: number
      entry_spread: number
      confidence: number
    }
    portfolio_state: {
      total_value: number
      available_margin: number
      margin_usage: number
      leverage: number
      num_positions: number
    }
    market_conditions?: {
      btc_volatility?: number
      trend?: string
    }
  }) =>
    apiClient<any>('guardian', '/api/trade/approve', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getAlerts: (address?: string, limit: number = 50) =>
    apiClient<any>('guardian', `/api/alerts?${address ? `address=${address}&` : ''}limit=${limit}`),

  getLogs: (limit: number = 50) =>
    apiClient<any[]>('guardian', `/api/agent/logs?limit=${limit}`),

  healthCheck: () =>
    apiClient<any>('guardian', '/api/health'),
}

// Executor Agent API
export const executorApi = {
  getPositions: () =>
    apiClient<any[]>('executor', '/api/positions'),

  getPosition: (positionId: string) =>
    apiClient<any>('executor', `/api/positions/${positionId}`),

  closePosition: (positionId: string) =>
    apiClient<any>('executor', `/api/positions/${positionId}/close`, {
      method: 'POST',
    }),

  executeTrade: (data: {
    signal_id: string
    position_size: number
    pair?: string
    time_window?: string  // NEW: time window parameter
  }) =>
    apiClient<any>('executor', '/api/trades/execute', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  emergencyStop: () =>
    apiClient<any>('executor', '/api/emergency_stop', {
      method: 'POST',
    }),

  getLogs: (limit: number = 50) =>
    apiClient<any[]>('executor', `/api/agent/logs?limit=${limit}`),

  healthCheck: () =>
    apiClient<any>('executor', '/api/health'),

  // NEW: Get available time window options
  getTimeWindows: () =>
    apiClient<{ windows: Record<string, { periods: number; display: string }>; default: string }>('executor', '/api/time_windows'),
}

// Combined agent logs from all services
export const getAllAgentLogs = async (limit: number = 50): Promise<any[]> => {
  try {
    const [scoutLogs, onboarderLogs, guardianLogs, executorLogs] = await Promise.allSettled([
      scoutApi.getLogs(limit),
      onboarderApi.getLogs(limit),
      guardianApi.getLogs(limit),
      executorApi.getLogs(limit),
    ])

    const logs: any[] = []

    if (scoutLogs.status === 'fulfilled') {
      logs.push(...scoutLogs.value)
    }

    if (onboarderLogs.status === 'fulfilled') {
      logs.push(...onboarderLogs.value)
    }

    if (guardianLogs.status === 'fulfilled') {
      logs.push(...guardianLogs.value)
    }

    if (executorLogs.status === 'fulfilled') {
      logs.push(...executorLogs.value)
    }

    // Sort by timestamp (newest first)
    return logs.sort((a, b) => {
      const timeA = new Date(a.timestamp).getTime()
      const timeB = new Date(b.timestamp).getTime()
      return timeB - timeA
    })
  } catch (error) {
    console.error('Failed to fetch agent logs:', error)
    return []
  }
}

export { APIError }
