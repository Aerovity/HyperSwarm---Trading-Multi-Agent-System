"use client"

import { useState, useEffect } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { mockMarketData } from "@/lib/mock-data"
import { scoutApi } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Search, TrendingUp, TrendingDown, Sparkles, HelpCircle } from "lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import type { MarketData } from "@/types"

interface MarketScannerTableProps {
  selectedPair?: string
  onPairSelect?: (pair: string) => void
}

export function MarketScannerTable({ selectedPair, onPairSelect }: MarketScannerTableProps) {
  const [marketData, setMarketData] = useState<MarketData[]>(mockMarketData)
  const [isLoading, setIsLoading] = useState(false)

  // Fetch real market data from Scout Agent
  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        setIsLoading(true)
        const data = await scoutApi.getMarketData()

        if (data.markets && data.markets.length > 0) {
          setMarketData(data.markets)
        } else {
          setMarketData(mockMarketData)
        }
      } catch (error) {
        console.error('Failed to fetch market data:', error)
        setMarketData(mockMarketData)
      } finally {
        setIsLoading(false)
      }
    }

    fetchMarketData()
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
    <GlassCard className="h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4 flex-shrink-0">
        <Search className="w-5 h-5 text-white" />
        <h3 className="font-semibold">Live Market Scanner</h3>
        <span className="text-xs text-muted-foreground ml-auto">
          {isLoading ? 'Loading...' : 'Scout Agent'}
        </span>
      </div>

      <div className="overflow-auto flex-1">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-background/90 backdrop-blur-sm">
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
                onClick={() => onPairSelect?.(market.pair)}
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
    </GlassCard>
  )
}
