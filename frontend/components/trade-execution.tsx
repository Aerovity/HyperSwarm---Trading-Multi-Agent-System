"use client"

import { useState } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { tradingPairs } from "@/lib/mock-data"
import { Zap, Shield, CheckCircle, XCircle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export function TradeExecution() {
  const [selectedPair, setSelectedPair] = useState("")
  const [positionSize, setPositionSize] = useState([50000])
  const [guardianApproved, setGuardianApproved] = useState(false)
  const [isChecking, setIsChecking] = useState(false)
  const [riskScore, setRiskScore] = useState<number | null>(null)

  const handleCheckRisk = async () => {
    if (!selectedPair) return
    setIsChecking(true)
    // Simulate Guardian agent checking risk
    await new Promise((resolve) => setTimeout(resolve, 1500))
    const score = Math.floor(Math.random() * 40) + 60 // Score between 60-100
    setRiskScore(score)
    setGuardianApproved(score >= 70)
    setIsChecking(false)
  }

  const handleExecute = () => {
    // Mock execution
    alert(`Executing pair trade: ${selectedPair} with size $${positionSize[0].toLocaleString()}`)
  }

  return (
    <GlassCard>
      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-5 h-5 text-white" />
        <h3 className="font-semibold">Trade Execution</h3>
      </div>

      <div className="space-y-5">
        {/* Pair Selection */}
        <div>
          <label className="text-sm text-muted-foreground mb-2 block">Trading Pair</label>
          <Select
            value={selectedPair}
            onValueChange={(v) => {
              setSelectedPair(v)
              setRiskScore(null)
              setGuardianApproved(false)
            }}
          >
            <SelectTrigger className="w-full bg-secondary/50 border-white/10">
              <SelectValue placeholder="Select pair" />
            </SelectTrigger>
            <SelectContent className="bg-secondary border-white/10">
              {tradingPairs.map((pair) => (
                <SelectItem key={pair} value={pair}>
                  {pair}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Position Size */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-muted-foreground">Position Size</label>
            <span className="font-mono text-sm">${positionSize[0].toLocaleString()}</span>
          </div>
          <Slider
            value={positionSize}
            onValueChange={setPositionSize}
            max={200000}
            min={10000}
            step={5000}
            className="py-2"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>$10K</span>
            <span>$200K</span>
          </div>
        </div>

        {/* Guardian Risk Assessment */}
        <div className="p-4 rounded-lg bg-secondary/30 border border-white/5">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-4 h-4 text-[#30D158]" />
            <span className="text-sm font-medium">Guardian Risk Assessment</span>
          </div>

          {riskScore !== null ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Risk Score</span>
                <span className={cn("font-bold text-lg", riskScore >= 70 ? "text-[#30D158]" : "text-[#FF453A]")}>
                  {riskScore}/100
                </span>
              </div>
              <div
                className={cn(
                  "flex items-center gap-2 text-sm",
                  guardianApproved ? "text-[#30D158]" : "text-[#FF453A]",
                )}
              >
                {guardianApproved ? (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Approved for execution
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4" />
                    High risk - Execution blocked
                  </>
                )}
              </div>
            </div>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={handleCheckRisk}
              disabled={!selectedPair || isChecking}
              className="w-full border-white/20 hover:bg-white/5 bg-transparent"
            >
              {isChecking ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing Risk...
                </>
              ) : (
                "Request Risk Assessment"
              )}
            </Button>
          )}
        </div>

        <Button
          onClick={handleExecute}
          disabled={!guardianApproved || !selectedPair}
          className={cn(
            "w-full haptic-press font-medium h-12",
            guardianApproved
              ? "bg-white hover:bg-white/90 text-black"
              : "bg-secondary text-muted-foreground cursor-not-allowed",
          )}
        >
          <Zap className="w-4 h-4 mr-2" />
          Execute Pair Trade
        </Button>

        {!guardianApproved && selectedPair && (
          <p className="text-xs text-center text-muted-foreground">Guardian approval required before execution</p>
        )}
      </div>
    </GlassCard>
  )
}
