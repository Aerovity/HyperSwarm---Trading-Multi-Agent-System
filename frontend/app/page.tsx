import { Header } from "@/components/header"
import { AgentStatusPanel } from "@/components/agent-status-panel"
import { BridgeWidget } from "@/components/bridge-widget"
import { MarketScanner } from "@/components/market-scanner"
import { PositionMonitor } from "@/components/position-monitor"
import { TradeExecution } from "@/components/trade-execution"
import { ActivityLogComponent } from "@/components/activity-log"

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Agent Status */}
        <AgentStatusPanel />

        {/* Main Trading Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Market Scanner - spans 2 cols */}
          <MarketScanner />

          {/* Bridge Widget */}
          <BridgeWidget />
        </div>

        {/* Position Monitor */}
        <PositionMonitor />

        {/* Trade Execution & Activity Log */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <TradeExecution />
          <div className="lg:col-span-2">
            <ActivityLogComponent />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 mt-8">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>HyperSwarm v1.0.0</span>
            <span>Connected to Hyperliquid Testnet</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
