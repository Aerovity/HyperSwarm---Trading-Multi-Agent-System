import { Header } from "@/components/header"
import { AgentStatusPanel } from "@/components/agent-status-panel"
import { MarketScanner } from "@/components/market-scanner"
import { PositionMonitor } from "@/components/position-monitor"

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Agent Status - compact row */}
        <AgentStatusPanel />

        {/* Market Scanner - full width */}
        <MarketScanner />

        {/* Position Monitor */}
        <PositionMonitor />
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
