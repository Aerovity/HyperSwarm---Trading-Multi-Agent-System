"use client"

import { useState, useMemo, useEffect } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { mockMarketData, generateSpreadHistory } from "@/lib/mock-data"
import { scoutApi } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Search, TrendingUp, TrendingDown, Sparkles, HelpCircle } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine } from "recharts"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { useTheme, Theme } from "@/lib/theme-context"

// Chart line colors per theme
const chartLineColors: Record<Theme, string> = {
  dark: "#FFFFFF",
  light: "#1d1d1f",
  neon: "#00ffff",
  retro: "#ffd700",
}

export function MarketScanner() {
  const { theme } = useTheme()
  const [selectedPair, setSelectedPair] = useState("BTC/ETH")
  const [marketData, setMarketData] = useState(mockMarketData)
  const [isLoading, setIsLoading] = useState(false)
  const [spreadHistory, setSpreadHistory] = useState(() => generateSpreadHistory("BTC/ETH", 24))

  // Get chart line color based on current theme
  const chartLineColor = chartLineColors[theme]

  // Get current Z-Score for selected pair from market data
  const currentZScore = marketData.find(m => m.pair === selectedPair)?.zScore

  // Generate spread history when pair changes
  useEffect(() => {
    const fetchSpreadHistory = async () => {
      try {
        const data = await scoutApi.getSpreadHistory(selectedPair, 24)
        if (data.data && data.data.length > 0) {
          setSpreadHistory(data.data)
        } else {
          // Fallback to mock data if API returns empty - use pair-specific data
          setSpreadHistory(generateSpreadHistory(selectedPair, 24, currentZScore))
        }
      } catch (error) {
        console.error('Failed to fetch spread history:', error)
        // Fallback to mock data on error - use pair-specific data
        setSpreadHistory(generateSpreadHistory(selectedPair, 24, currentZScore))
      }
    }

    // Fetch immediately when pair changes
    fetchSpreadHistory()

    return () => {}
  }, [selectedPair, currentZScore])

  // Live update effect - add new data point every 3 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setSpreadHistory(prev => {
        if (prev.length === 0) return prev

        // Remove oldest point
        const newData = [...prev.slice(1)]

        // Add new point with slight variation from last
        const lastZ = newData[newData.length - 1]?.zScore || 0
        // Small random walk, biased towards current Z-Score if available
        const targetZ = currentZScore ?? lastZ
        const drift = (targetZ - lastZ) * 0.1 // Drift towards target
        const noise = (Math.random() - 0.5) * 0.2 // Small random noise
        const newZ = Math.max(-3, Math.min(3, lastZ + drift + noise))

        newData.push({
          time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
          spread: 0.1 + newZ * 0.02,
          zScore: newZ,
        })

        return newData
      })
    }, 3000) // Update every 3 seconds

    return () => clearInterval(interval)
  }, [currentZScore])

  // Fetch real market data from Scout Agent
  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        setIsLoading(true)
        const data = await scoutApi.getMarketData()

        // If API returns data, use it; otherwise fallback to mock data
        if (data.markets && data.markets.length > 0) {
          setMarketData(data.markets)
        } else {
          // Use mock data if API returns empty
          setMarketData(mockMarketData)
        }
      } catch (error) {
        console.error('Failed to fetch market data:', error)
        // Fallback to mock data on error
        setMarketData(mockMarketData)
      } finally {
        setIsLoading(false)
      }
    }

    // Initial fetch
    fetchMarketData()

    // Poll every 5 seconds for updates
    const interval = setInterval(fetchMarketData, 5000)

    return () => clearInterval(interval)
  }, [])

  const getZScoreColor = (zScore: number) => {
    if (zScore <= -2) return "text-[#30D158]"
    if (zScore >= 2) return "text-[#FF453A]"
    return "text-white"
  }

  const getZScoreBg = (zScore: number) => {
    if (zScore <= -2) return "bg-[#30D158]/20"
    if (zScore >= 2) return "bg-[#FF453A]/20"
    return "bg-white/10"
  }

  const formatPrice = (price: number) => {
    if (price >= 1000) return price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    if (price >= 1) return price.toFixed(2)
    return price.toFixed(5)
  }

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `$${(volume / 1e9).toFixed(1)}B`
    if (volume >= 1e6) return `$${(volume / 1e6).toFixed(0)}M`
    return `$${volume.toLocaleString()}`
  }

  return (
    <GlassCard className="col-span-full lg:col-span-2" data-tour="market">
      <div className="flex items-center gap-2 mb-4">
        <Search className="w-5 h-5 text-white" />
        <h3 className="font-semibold">Live Market Scanner</h3>
        <span className="text-xs text-muted-foreground ml-auto">
          {isLoading ? 'Loading...' : 'Scout Agent View'}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Price Feed Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-muted-foreground text-xs uppercase">
                <th className="text-left pb-3 font-medium">Pair</th>
                <th className="text-right pb-3 font-medium">Price</th>
                <th className="text-right pb-3 font-medium">24h</th>
                <th className="text-right pb-3 font-medium">
                  <Tooltip>
                    <TooltipTrigger className="flex items-center gap-1 justify-end">
                      Z-Score
                      <HelpCircle className="w-3 h-3 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-[200px]">
                      Statistical measure of price deviation. Below -2σ = oversold (buy signal). Above +2σ = overbought (sell signal).
                    </TooltipContent>
                  </Tooltip>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {marketData.map((market) => (
                <tr
                  key={market.pair}
                  onClick={() => setSelectedPair(market.pair)}
                  className={cn(
                    "cursor-pointer transition-colors",
                    selectedPair === market.pair ? "bg-white/5" : "hover:bg-white/5",
                  )}
                >
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{market.pair}</span>
                      {Math.abs(market.zScore) >= 2 && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#30D158]/20 text-[#30D158] flex items-center gap-1">
                          <Sparkles className="w-3 h-3" />
                          Opportunity
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">Vol: {formatVolume(market.volume24h)}</span>
                  </td>
                  <td className="py-3 text-right font-mono">${formatPrice(market.price)}</td>
                  <td className="py-3 text-right">
                    <span
                      className={cn(
                        "flex items-center justify-end gap-1",
                        market.change24h >= 0 ? "text-[#30D158]" : "text-[#FF453A]",
                      )}
                    >
                      {market.change24h >= 0 ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : (
                        <TrendingDown className="w-3 h-3" />
                      )}
                      {Math.abs(market.change24h).toFixed(2)}%
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    <span
                      className={cn(
                        "px-2 py-1 rounded-lg font-mono text-xs",
                        getZScoreBg(market.zScore),
                        getZScoreColor(market.zScore),
                      )}
                    >
                      {market.zScore >= 0 ? "+" : ""}
                      {market.zScore.toFixed(1)}σ
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Spread Chart */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium">{selectedPair} Spread History</span>
            <span className="text-xs text-muted-foreground">24h</span>
          </div>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={spreadHistory}>
                <XAxis
                  dataKey="time"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#8E8E93", fontSize: 10 }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#8E8E93", fontSize: 10 }}
                  domain={[-3, 3]}
                  ticks={[-2, 0, 2]}
                />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: "#1C1C1E",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "8px",
                    color: "#fff",
                  }}
                  labelStyle={{ color: "#8E8E93" }}
                />
                <ReferenceLine y={2} stroke="#FF453A" strokeDasharray="3 3" strokeOpacity={0.5} />
                <ReferenceLine y={-2} stroke="#30D158" strokeDasharray="3 3" strokeOpacity={0.5} />
                <ReferenceLine y={0} stroke="#8E8E93" strokeOpacity={0.3} />
                <Line
                  type="monotone"
                  dataKey="zScore"
                  stroke={chartLineColor}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: chartLineColor }}
                  isAnimationActive={true}
                  animationDuration={300}
                  animationEasing="ease-in-out"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-4 mt-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-[#30D158]" /> Long Signal (-2σ)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-[#FF453A]" /> Short Signal (+2σ)
            </span>
          </div>
        </div>
      </div>
    </GlassCard>
  )
}
