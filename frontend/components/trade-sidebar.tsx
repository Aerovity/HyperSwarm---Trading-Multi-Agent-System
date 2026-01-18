"use client"

import { useDemoContext } from "@/lib/demo-context"
import { TradeExecution } from "@/components/trade-execution"
import { BridgeWidget } from "@/components/bridge-widget"
import { AIChatInterface } from "@/components/ai-chat-interface"
import { ModeToggle } from "@/components/mode-toggle"

export function TradeSidebar() {
  const { tradingMode, setTradingMode } = useDemoContext()

  return (
    <aside className="w-[320px] flex-shrink-0 border-r border-white/5 bg-background/80 backdrop-blur-xl flex flex-col overflow-hidden">
      {/* Mode Toggle Header */}
      <div className="px-3 py-3 border-b border-white/5 flex-shrink-0">
        <ModeToggle
          mode={tradingMode}
          onChange={setTradingMode}
          label="Enable AI Trading"
        />
      </div>

      {/* Scrollable Content - using native scroll */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
        {tradingMode === "manual" ? (
          <>
            <TradeExecution />
            <BridgeWidget />
          </>
        ) : (
          <AIChatInterface />
        )}
      </div>
    </aside>
  )
}
