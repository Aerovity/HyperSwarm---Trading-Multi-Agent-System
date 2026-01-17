"use client"

import { GlassCard } from "@/components/ui/glass-card"
import { mockPositions } from "@/lib/mock-data"
import { executorApi } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Activity, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { useState, useEffect } from "react"

export function PositionMonitor() {
  const [isMounted, setIsMounted] = useState(false)
  const [positions, setPositions] = useState(mockPositions)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  // Fetch positions from Executor agent
  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const executorPositions = await executorApi.getPositions()

        // If API returns positions, use them; otherwise fallback to mock
        if (executorPositions && executorPositions.length > 0) {
          // Transform Executor API positions to match frontend format
          const transformedPositions = executorPositions.map((pos: any) => ({
            id: pos.position_id || pos.id,
            pair: pos.pair || 'BTC/ETH',
            timeWindow: pos.time_window || '5min',  // NEW: time window
            entrySpread: pos.entry_spread || 0,
            currentSpread: pos.current_spread || pos.entry_spread || 0,
            size: pos.size || pos.position_size || 0,
            pnl: pos.pnl || 0,
            pnlPercent: pos.pnl_percent || 0,
            riskLevel: pos.risk_level || 'low',
            entryTime: pos.entry_time ? new Date(pos.entry_time) : new Date(),
            status: pos.status || 'open',  // NEW: position status
            windowExpiresAt: pos.window_expires_at ? new Date(pos.window_expires_at) : null,  // NEW: expiration time
          }))
          setPositions(transformedPositions)
        }
      } catch (error) {
        console.error('Failed to fetch positions from Executor:', error)
        // Keep using mock data on error
      }
    }

    fetchPositions()
    // Poll every 5 seconds for updates
    const interval = setInterval(fetchPositions, 5000)

    return () => clearInterval(interval)
  }, [])

  const totalPnL = positions.reduce((sum, p) => sum + p.pnl, 0)
  const totalPnLPercent = positions.length > 0
    ? positions.reduce((sum, p) => sum + p.pnlPercent, 0) / positions.length
    : 0

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
              ${Math.abs(totalPnL).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div
              className={cn(
                "flex items-center gap-1 text-sm mt-1",
                totalPnLPercent >= 0 ? "text-[#30D158]" : "text-[#FF453A]",
              )}
            >
              {totalPnLPercent >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              {Math.abs(totalPnLPercent).toFixed(2)}%
            </div>

            {/* Liquidation Health */}
            <div className="mt-4 pt-4 border-t border-white/10">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground">Liquidation Health</span>
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
          <table className="w-full text-sm">
            <thead>
              <tr className="text-muted-foreground text-xs uppercase">
                <th className="text-left pb-3 font-medium">Pair</th>
                <th className="text-right pb-3 font-medium">Window</th>
                <th className="text-right pb-3 font-medium">Entry Spread</th>
                <th className="text-right pb-3 font-medium">Current Spread</th>
                <th className="text-right pb-3 font-medium">Size</th>
                <th className="text-right pb-3 font-medium">Current Value</th>
                <th className="text-right pb-3 font-medium">Risk</th>
                <th className="text-right pb-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {positions.length > 0 ? (
                positions.map((position) => (
                  <tr key={position.id} className="hover:bg-white/5 transition-colors">
                    <td className="py-3">
                      <span className="font-medium">{position.pair}</span>
                      <span className="block text-xs text-muted-foreground">
                        {isMounted
                          ? position.entryTime.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
                          : "--:-- --"}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <span className="text-xs text-muted-foreground">{position.timeWindow || '5min'}</span>
                    </td>
                    <td className="py-3 text-right font-mono">{position.entrySpread.toFixed(4)}</td>
                    <td className="py-3 text-right font-mono">{position.currentSpread.toFixed(4)}</td>
                    <td className="py-3 text-right font-mono">${position.size.toLocaleString()}</td>
                    <td className="py-3 text-right">
                      <span className={cn("font-medium", position.pnl >= 0 ? "text-[#30D158]" : "text-[#FF453A]")}>
                        ${position.pnl >= 0
                          ? (position.size + position.pnl).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                          : Math.abs(position.pnl).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                        }
                      </span>
                      <span
                        className={cn(
                          "block text-xs",
                          position.pnl >= 0 ? "text-[#30D158]/70" : "text-[#FF453A]/70",
                        )}
                      >
                        {((Math.abs(position.pnl) / position.size) * 100).toFixed(2)}%
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
                      <span
                        className={cn(
                          "px-2 py-1 rounded-lg text-xs font-medium capitalize",
                          position.status === 'settled' ? "bg-blue-500/20 text-blue-400" : "bg-green-500/20 text-green-400"
                        )}
                      >
                        {position.status || 'open'}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-muted-foreground">
                    No active positions
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </GlassCard>
  )
}
