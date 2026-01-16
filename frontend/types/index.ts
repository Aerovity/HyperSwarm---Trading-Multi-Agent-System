export type AgentStatus = "active" | "idle" | "processing"

export interface Agent {
  id: string
  name: string
  type: "scout" | "onboarder" | "executor" | "guardian"
  status: AgentStatus
  lastAction: string
  lastActionTime: Date
}

export interface MarketData {
  pair: string
  price: number
  change24h: number
  zScore: number
  spread: number
  volume24h: number
}

export interface Position {
  id: string
  pair: string
  entrySpread: number
  currentSpread: number
  pnl: number
  pnlPercent: number
  riskLevel: "low" | "medium" | "high"
  size: number
  entryTime: Date
}

export interface ActivityLog {
  id: string
  timestamp: Date
  agent: "scout" | "onboarder" | "executor" | "guardian"
  message: string
  type: "info" | "success" | "warning" | "error"
}

export interface BridgeTransaction {
  sourceChain: string
  amount: number
  estimatedTime: string
  estimatedFee: number
  status: "pending" | "processing" | "success" | "failed"
}

export interface BridgeQuote {
  route_id: string
  from_chain: string
  to_chain: string
  token: string
  amount: string
  estimated_time: number
  total_cost: number
  steps: BridgeStep[]
  cached_at: string
  transaction_request?: TransactionRequest
  demo_mode?: boolean
}

export interface BridgeStep {
  step_number: number
  action: string
  tool: string
  from_chain: string
  to_chain: string
  from_token: string
  to_token: string
  from_amount: string
  to_amount: string
}

export interface TransactionRequest {
  to: string
  data: string
  value: string
  from?: string
  chainId?: string
  gasLimit?: string
  gasPrice?: string
}

export interface BridgeStatus {
  transaction_id: string
  route_id: string
  user_wallet: string
  tx_hash: string
  status: "pending" | "processing" | "confirming" | "completed" | "failed"
  substatus: string
  from_chain: string
  to_chain: string
  token: string
  amount: string
  started_at: string
  completed_at?: string
  estimated_completion: string
  demo_mode?: boolean
}

export interface HyperliquidBalance {
  address: string
  withdrawable: number
  account_value: number
  total_margin_used: number
  total_raw_usd: number
}

export interface Chain {
  id: string
  name: string
  logo?: string
}
