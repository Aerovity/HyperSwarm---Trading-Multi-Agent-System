"use client"

import { useDemoContext } from "@/lib/demo-context"
import { TradeExecution } from "@/components/trade-execution"
import { BridgeWidget } from "@/components/bridge-widget"
import { AIChatInterface } from "@/components/ai-chat-interface"
import { ModeToggle } from "@/components/mode-toggle"
import { GlassCard } from "@/components/ui/glass-card"
import { ScrollArea } from "@/components/ui/scroll-area"

export function TradePanel() {
  const { tradingMode, setTradingMode } = useDemoContext()

  return (
    <GlassCard className="h-full flex flex-col p-0 overflow-hidden">
      {/* Mode Toggle at top */}
      <div className="p-3 border-b border-white/5 flex-shrink-0">
        <ModeToggle
          mode={tradingMode}
          onChange={setTradingMode}
          label="Enable AI Trading"
        />
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden">
        {tradingMode === "manual" ? (
          <ScrollArea className="h-full">
            <div className="p-3 space-y-3">
              <TradeExecution />
              <BridgeWidget />
            </div>
          </ScrollArea>
        ) : (
          <div className="h-full p-3">
            <AIChatInterface />
          </div>
        )}
      </div>
    </GlassCard>
  )
}
