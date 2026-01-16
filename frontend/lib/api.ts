/**
 * Centralized API client for HyperSwarm backend services
 */

const API_BASE_URLS = {
  scout: process.env.NEXT_PUBLIC_SCOUT_API_URL || 'http://localhost:8001',
  onboarder: process.env.NEXT_PUBLIC_ONBOARDER_API_URL || 'http://localhost:8002',
}

class APIError extends Error {
  constructor(message: string, public status?: number, public data?: any) {
    super(message)
    this.name = 'APIError'
  }
}

async function apiClient<T>(
  service: 'scout' | 'onboarder',
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

// Scout Agent API
export const scoutApi = {
  getLogs: (limit: number = 50) =>
    apiClient<any[]>('scout', `/api/agent/logs?limit=${limit}`),

  getMarketData: () =>
    apiClient<{ markets: any[] }>('scout', '/api/markets/live'),

  getSpreadHistory: (pair: string, hours: number = 24) =>
    apiClient<{ pair: string; data: any[] }>('scout', `/api/spread/history?pair=${pair}&hours=${hours}`),

  getSignals: () =>
    apiClient<any[]>('scout', '/api/signals/recent'),

  getCorrelations: () =>
    apiClient<any>('scout', '/api/pairs/correlations'),

  analyzeMarkets: () =>
    apiClient<any>('scout', '/api/signals/analyze', { method: 'POST' }),

  healthCheck: () =>
    apiClient<{ status: string; redis: string; service: string }>('scout', '/api/health'),
}

// Onboarder Agent API
export const onboarderApi = {
  getQuote: (params: {
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
    return apiClient<any>('onboarder', `/api/bridge/quote?${query}`)
  },

  executeBridge: (data: {
    route_id: string
    user_wallet: string
    tx_hash?: string
  }) =>
    apiClient<any>('onboarder', '/api/bridge/execute', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getStatus: (txId: string) =>
    apiClient<any>('onboarder', `/api/bridge/status/${txId}`),

  getBalance: (address: string) =>
    apiClient<any>('onboarder', `/api/bridge/balance/${address}`),

  getChains: () =>
    apiClient<any>('onboarder', '/api/bridge/chains'),

  getLogs: (limit: number = 50) =>
    apiClient<any[]>('onboarder', `/api/agent/logs?limit=${limit}`),

  healthCheck: () =>
    apiClient<any>('onboarder', '/api/health'),
}

// Combined agent logs from all services
export const getAllAgentLogs = async (limit: number = 50): Promise<any[]> => {
  try {
    const [scoutLogs, onboarderLogs] = await Promise.allSettled([
      scoutApi.getLogs(limit),
      onboarderApi.getLogs(limit),
    ])

    const logs: any[] = []

    if (scoutLogs.status === 'fulfilled') {
      logs.push(...scoutLogs.value)
    }

    if (onboarderLogs.status === 'fulfilled') {
      logs.push(...onboarderLogs.value)
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
