import { Header } from "@/components/header"
import { TradeExecution } from "@/components/trade-execution"
import { BridgeWidget } from "@/components/bridge-widget"

export default function TradePage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Trade Execution & Bridge Widget */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TradeExecution />
          <BridgeWidget />
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
