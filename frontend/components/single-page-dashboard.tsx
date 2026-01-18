"use client"

import { useState } from "react"
import dynamic from "next/dynamic"
import { TradeSidebar } from "@/components/trade-sidebar"
import { MarketScannerTable } from "@/components/market-scanner-table"
import { AgentStatusPanel } from "@/components/agent-status-panel"
import { ActivityLogComponent } from "@/components/activity-log"
import { PositionMonitor } from "@/components/position-monitor"
import { Header } from "@/components/header"
import { GlassCard } from "@/components/ui/glass-card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { tradingPairs } from "@/lib/mock-data"

// Dynamic import for TradingChart to avoid SSR issues with Lightweight Charts
const TradingChart = dynamic(
  () => import("@/components/trading-chart").then((mod) => mod.TradingChart),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex items-center justify-center bg-secondary/20 animate-pulse">
        <span className="text-muted-foreground text-sm">Loading chart...</span>
      </div>
    ),
  }
)

export function SinglePageDashboard() {
  const [selectedPair, setSelectedPair] = useState("BTC/ETH")

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background">
      {/* Header */}
      <Header />

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Trade Panel (full height, scrollable) */}
        <TradeSidebar />

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden p-4 gap-4">
          {/* Top Row - Chart + Market Scanner */}
          <section className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-5 gap-4">
            {/* Chart - 60% width (3/5 cols) */}
            <div className="lg:col-span-3 min-h-[250px]">
              <GlassCard className="h-full flex flex-col p-0 overflow-hidden">
                {/* Chart Header */}
                <div className="flex items-center justify-between p-3 border-b border-white/5 flex-shrink-0">
                  <Select value={selectedPair} onValueChange={setSelectedPair}>
                    <SelectTrigger className="w-[140px] bg-secondary/50 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-secondary border-white/10">
                      {tradingPairs.map((pair) => (
                        <SelectItem key={pair} value={pair}>
                          {pair}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="w-2 h-2 rounded-full bg-[#30D158] animate-pulse" />
                    Live
                  </div>
                </div>
                {/* Chart */}
                <div className="flex-1 min-h-0">
                  <TradingChart pair={selectedPair} chartType="candlestick" />
                </div>
              </GlassCard>
            </div>

            {/* Market Scanner - 40% width (2/5 cols) */}
            <div className="lg:col-span-2 min-h-[250px]">
              <MarketScannerTable
                selectedPair={selectedPair}
                onPairSelect={setSelectedPair}
              />
            </div>
          </section>

          {/* Agent Status - Horizontal Strip */}
          <section className="flex-shrink-0">
            <GlassCard className="p-3">
              <AgentStatusPanel compact horizontal />
            </GlassCard>
          </section>

          {/* Bottom Row - Position Monitor + Activity Log (scrollable) */}
          <section className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[65%_35%] gap-4">
            {/* Position Monitor - Left (scrollable) */}
            <div className="min-h-0 overflow-auto">
              <PositionMonitor />
            </div>

            {/* Activity Log - Right (scrollable) */}
            <div className="min-h-0 overflow-auto">
              <ActivityLogComponent />
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}
