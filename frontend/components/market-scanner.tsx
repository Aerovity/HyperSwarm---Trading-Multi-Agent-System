"use client"

import { useState, useMemo, useEffect } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { mockMarketData, generateSpreadHistory } from "@/lib/mock-data"
import { scoutApi } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Search, TrendingUp, TrendingDown, Sparkles } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts"

export function MarketScanner() {
  const [selectedPair, setSelectedPair] = useState("BTC/ETH")
  const [marketData, setMarketData] = useState(mockMarketData)
  const [isLoading, setIsLoading] = useState(false)
  const [spreadHistory, setSpreadHistory] = useState(generateSpreadHistory(24))

  // Fetch real spread history from Scout Agent
  useEffect(() => {
    const fetchSpreadHistory = async () => {
      try {
        const data = await scoutApi.getSpreadHistory(selectedPair, 24)
        if (data.data && data.data.length > 0) {
          setSpreadHistory(data.data)
        } else {
          // Fallback to mock data if API returns empty
          setSpreadHistory(generateSpreadHistory(24))
        }
      } catch (error) {
        console.error('Failed to fetch spread history:', error)
        // Fallback to mock data on error
        setSpreadHistory(generateSpreadHistory(24))
      }
    }

    // Fetch immediately when pair changes
    fetchSpreadHistory()

    // Poll every 10 seconds for updates
    const interval = setInterval(fetchSpreadHistory, 10000)

    return () => clearInterval(interval)
  }, [selectedPair])

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
    <GlassCard className="col-span-full lg:col-span-2">
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
                <th className="text-right pb-3 font-medium">Z-Score</th>
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
                <Tooltip
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
                  stroke="#FFFFFF"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: "#FFFFFF" }}
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
