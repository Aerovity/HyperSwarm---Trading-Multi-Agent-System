"use client"

import { useState, useEffect } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { sourceChains } from "@/lib/mock-data"
import { ArrowRight, Loader2, CheckCircle2, Clock, DollarSign, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { onboarderApi } from "@/lib/api"

type BridgeStatus = "idle" | "loading" | "success" | "error"

interface BridgeQuote {
  route_id: string
  from_chain: string
  to_chain: string
  token: string
  amount: string
  estimated_time: number
  total_cost: number
  transaction_request?: any
}

export function BridgeWidget() {
  const [sourceChain, setSourceChain] = useState("")
  const [amount, setAmount] = useState("")
  const [status, setStatus] = useState<BridgeStatus>("idle")
  const [quote, setQuote] = useState<BridgeQuote | null>(null)
  const [isLoadingQuote, setIsLoadingQuote] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Mock wallet address (in production, get from wallet connection)
  const userAddress = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

  // Fetch quote when amount and chain change
  useEffect(() => {
    const fetchQuote = async () => {
      if (!sourceChain || !amount || parseFloat(amount) <= 0) {
        setQuote(null)
        return
      }

      setIsLoadingQuote(true)
      setError(null)

      try {
        // Convert USDC to smallest unit (6 decimals)
        const amountInSmallestUnit = (parseFloat(amount) * 1_000_000).toString()

        const quoteData = await onboarderApi.getQuote({
          fromChain: sourceChain,
          token: 'USDC',
          amount: amountInSmallestUnit,
          fromAddress: userAddress,
        })

        setQuote(quoteData)
      } catch (err) {
        console.error('Failed to fetch quote:', err)
        setError('Failed to get bridge quote')
        setQuote(null)
      } finally {
        setIsLoadingQuote(false)
      }
    }

    // Debounce quote fetching
    const timeoutId = setTimeout(fetchQuote, 500)
    return () => clearTimeout(timeoutId)
  }, [sourceChain, amount, userAddress])

  const handleBridge = async () => {
    if (!quote) return

    setStatus("loading")
    setError(null)

    try {
      // Execute bridge (in demo mode, no tx_hash needed)
      const result = await onboarderApi.executeBridge({
        route_id: quote.route_id,
        user_wallet: userAddress,
      })

      setStatus("success")
      setTimeout(() => {
        setStatus("idle")
        setAmount("")
        setQuote(null)
      }, 3000)
    } catch (err) {
      console.error('Bridge failed:', err)
      setError('Bridge execution failed')
      setStatus("error")
    }
  }

  const estimatedFee = quote ? `$${quote.total_cost.toFixed(2)}` : "$0.00"
  const estimatedTime = quote
    ? `~${Math.ceil(quote.estimated_time / 60)} min`
    : "~2-5 min"

  return (
    <GlassCard glow={status === "success" ? "green" : "none"}>
      <div className="flex items-center gap-2 mb-4">
        <ArrowRight className="w-5 h-5 text-white" />
        <h3 className="font-semibold">Cross-Chain Onboarding</h3>
      </div>

      {status === "success" ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="w-16 h-16 rounded-lg bg-[#30D158]/20 flex items-center justify-center mb-4 animate-in zoom-in duration-300">
            <CheckCircle2 className="w-8 h-8 text-[#30D158]" />
          </div>
          <h4 className="font-semibold text-lg mb-1">Bridge Successful!</h4>
          <p className="text-sm text-muted-foreground">Your USDC is now available on Hyperliquid</p>
        </div>
      ) : status === "error" ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="w-16 h-16 rounded-lg bg-[#FF453A]/20 flex items-center justify-center mb-4">
            <AlertCircle className="w-8 h-8 text-[#FF453A]" />
          </div>
          <h4 className="font-semibold text-lg mb-1">Bridge Failed</h4>
          <p className="text-sm text-muted-foreground mb-4">{error || 'An error occurred'}</p>
          <Button
            onClick={() => setStatus("idle")}
            variant="outline"
            className="border-white/10"
          >
            Try Again
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Source Chain */}
          <div>
            <label className="text-sm text-muted-foreground mb-2 block">Source Chain</label>
            <Select value={sourceChain} onValueChange={setSourceChain}>
              <SelectTrigger className="w-full bg-secondary/50 border-white/10">
                <SelectValue placeholder="Select chain" />
              </SelectTrigger>
              <SelectContent className="bg-secondary border-white/10">
                {sourceChains.map((chain) => (
                  <SelectItem key={chain.id} value={chain.id}>
                    <span className="flex items-center gap-2">
                      <span>{chain.icon}</span>
                      {chain.name}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Amount Input */}
          <div>
            <label className="text-sm text-muted-foreground mb-2 block">Amount (USDC)</label>
            <div className="relative">
              <Input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="bg-secondary/50 border-white/10 pr-16 text-lg font-mono"
              />
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 -translate-y-1/2 text-xs text-white hover:text-white hover:bg-white/10"
                onClick={() => setAmount("1000")}
              >
                MAX
              </Button>
            </div>
          </div>

          {/* Estimates */}
          <div className="flex items-center justify-between text-sm text-muted-foreground py-3 border-t border-white/5">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-white" />
              <span>{isLoadingQuote ? 'Calculating...' : estimatedTime}</span>
            </div>
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-white" />
              <span>Fee: {isLoadingQuote ? '...' : estimatedFee}</span>
            </div>
          </div>

          {error && status !== "error" && (
            <div className="text-xs text-[#FF453A] bg-[#FF453A]/10 px-3 py-2 rounded-lg">
              {error}
            </div>
          )}

          <Button
            onClick={handleBridge}
            disabled={!sourceChain || !amount || status === "loading" || !quote || isLoadingQuote}
            className={cn(
              "w-full haptic-press font-medium",
              "bg-white text-black",
              "hover:bg-white/90 transition-opacity",
              "disabled:opacity-50 disabled:cursor-not-allowed",
            )}
          >
            {status === "loading" ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Bridging...
              </>
            ) : isLoadingQuote ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Getting Quote...
              </>
            ) : (
              <>
                Bridge to Hyperliquid
                <ArrowRight className="w-4 h-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      )}
    </GlassCard>
  )
}
