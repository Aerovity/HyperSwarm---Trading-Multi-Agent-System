"use client"

import { GlassCard } from "@/components/ui/glass-card"
import { useDemoContext } from "@/lib/demo-context"
import { cn } from "@/lib/utils"
import { Activity, TrendingUp, TrendingDown, AlertTriangle, X, HelpCircle } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { useState, useEffect } from "react"

export function PositionMonitor() {
  const { positions, closePosition, addLog } = useDemoContext()
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  const totalPnL = positions.reduce((sum, p) => sum + p.pnl, 0)
  const totalPnLPercent = positions.length > 0
    ? positions.reduce((sum, p) => sum + p.pnlPercent, 0) / positions.length
    : 0

  const handleClosePosition = (position: typeof positions[0]) => {
    closePosition(position.id)
    addLog({
      timestamp: new Date(),
      agent: "executor",
      message: `Closed position: ${position.pair} (${position.pnl >= 0 ? '+' : ''}$${position.pnl.toFixed(2)})`,
      type: position.pnl >= 0 ? "success" : "info",
    })
  }

  // Mock liquidation health (0-100, where 100 is fully safe)
  const liquidationHealth = 78

  const getRiskColor = (level: string) => {
    switch (level) {
      case "low":
        return "text-[#30D158]"
      case "medium":
        return "text-white"
      case "high":
        return "text-[#FF453A]"
      default:
        return "text-muted-foreground"
    }
  }

  const getRiskBg = (level: string) => {
    switch (level) {
      case "low":
        return "bg-[#30D158]/20"
      case "medium":
        return "bg-white/10"
      case "high":
        return "bg-[#FF453A]/20"
      default:
        return "bg-white/10"
    }
  }

  const getHealthColor = (health: number) => {
    if (health >= 70) return "#30D158"
    if (health >= 40) return "#FFFFFF"
    return "#FF453A"
  }

  return (
    <GlassCard className="col-span-full">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-white" />
        <h3 className="font-semibold">Position Monitor</h3>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Total PnL Card */}
        <div className="lg:col-span-1">
          <div className="glass rounded-lg p-4 h-full flex flex-col justify-center">
            <span className="text-sm text-muted-foreground mb-1">Total Portfolio PnL</span>
            <div
              className={cn("text-3xl font-bold tracking-tight", totalPnL >= 0 ? "text-[#30D158]" : "text-[#FF453A]")}
            >
              {totalPnL >= 0 ? "+" : ""}
              {totalPnL.toLocaleString("en-US", { style: "currency", currency: "USD" })}
            </div>
            <div
              className={cn(
                "flex items-center gap-1 text-sm mt-1",
                totalPnLPercent >= 0 ? "text-[#30D158]" : "text-[#FF453A]",
              )}
            >
              {totalPnLPercent >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              {totalPnLPercent >= 0 ? "+" : ""}
              {totalPnLPercent.toFixed(2)}%
            </div>

            {/* Liquidation Health */}
            <div className="mt-4 pt-4 border-t border-white/10">
              <div className="flex items-center justify-between mb-2">
                <Tooltip>
                  <TooltipTrigger className="flex items-center gap-1 text-xs text-muted-foreground">
                    Liquidation Health
                    <HelpCircle className="w-3 h-3" />
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-[200px]">
                    How safe your positions are from forced closure. Below 50% = danger zone. Below 25% = liquidation risk.
                  </TooltipContent>
                </Tooltip>
                <span className="text-xs font-medium" style={{ color: getHealthColor(liquidationHealth) }}>
                  {liquidationHealth}%
                </span>
              </div>
              <Progress
                value={liquidationHealth}
                className="h-2 bg-white/10"
                style={{
                  ["--progress-foreground" as string]: getHealthColor(liquidationHealth),
                }}
              />
              {liquidationHealth < 50 && (
                <div className="flex items-center gap-1 mt-2 text-xs text-white">
                  <AlertTriangle className="w-3 h-3" />
                  Consider reducing position size
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Positions Table */}
        <div className="lg:col-span-3 overflow-x-auto">
          {positions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-8 text-muted-foreground">
              <Activity className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-sm">No open positions</p>
              <p className="text-xs">Execute a trade to see it here</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-muted-foreground text-xs uppercase">
                  <th className="text-left pb-3 font-medium">Pair</th>
                  <th className="text-right pb-3 font-medium">
                    <Tooltip>
                      <TooltipTrigger className="flex items-center gap-1 justify-end">
                        Entry Spread
                        <HelpCircle className="w-3 h-3" />
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-[180px]">
                        The spread value when you opened this position
                      </TooltipContent>
                    </Tooltip>
                  </th>
                  <th className="text-right pb-3 font-medium">Current Spread</th>
                  <th className="text-right pb-3 font-medium">Size</th>
                  <th className="text-right pb-3 font-medium">PnL</th>
                  <th className="text-right pb-3 font-medium">
                    <Tooltip>
                      <TooltipTrigger className="flex items-center gap-1 justify-end">
                        Risk
                        <HelpCircle className="w-3 h-3" />
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-[180px]">
                        Position risk based on size, volatility, and market conditions
                      </TooltipContent>
                    </Tooltip>
                  </th>
                  <th className="text-right pb-3 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {positions.map((position) => (
                  <tr key={position.id} className="hover:bg-white/5 transition-colors">
                    <td className="py-3">
                      <span className="font-medium">{position.pair}</span>
                      <span className="block text-xs text-muted-foreground">
                        {isMounted
                          ? position.entryTime.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
                          : "--:-- --"}
                      </span>
                    </td>
                    <td className="py-3 text-right font-mono">{position.entrySpread.toFixed(4)}</td>
                    <td className="py-3 text-right font-mono">{position.currentSpread.toFixed(4)}</td>
                    <td className="py-3 text-right font-mono">${position.size.toLocaleString()}</td>
                    <td className="py-3 text-right">
                      <span className={cn("font-medium", position.pnl >= 0 ? "text-[#30D158]" : "text-[#FF453A]")}>
                        {position.pnl >= 0 ? "+" : ""}${position.pnl.toFixed(2)}
                      </span>
                      <span
                        className={cn(
                          "block text-xs",
                          position.pnlPercent >= 0 ? "text-[#30D158]/70" : "text-[#FF453A]/70",
                        )}
                      >
                        {position.pnlPercent >= 0 ? "+" : ""}
                        {position.pnlPercent.toFixed(2)}%
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <span
                        className={cn(
                          "px-2 py-1 rounded-lg text-xs font-medium capitalize",
                          getRiskBg(position.riskLevel),
                          getRiskColor(position.riskLevel),
                        )}
                      >
                        {position.riskLevel}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => handleClosePosition(position)}
                        className="w-7 h-7 ml-2 rounded-full border border-muted-foreground/50 flex items-center justify-center transition-all duration-200 hover:border-destructive hover:text-destructive hover:bg-destructive/10"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </GlassCard>
  )
}
