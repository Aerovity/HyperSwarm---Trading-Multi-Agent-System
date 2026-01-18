"use client"

import { useState } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { tradingPairs } from "@/lib/mock-data"
import { useDemoContext } from "@/lib/demo-context"
import { Zap, Shield, CheckCircle, XCircle, Loader2, HelpCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"

export function TradeExecution() {
  const { addPosition, addLog } = useDemoContext()
  const [selectedPair, setSelectedPair] = useState("")
  const [positionSize, setPositionSize] = useState([50000])
  const [guardianApproved, setGuardianApproved] = useState(false)
  const [isChecking, setIsChecking] = useState(false)
  const [riskScore, setRiskScore] = useState<number | null>(null)
  const [isExecuting, setIsExecuting] = useState(false)

  const handleCheckRisk = async () => {
    if (!selectedPair) return
    setIsChecking(true)

    // Log that guardian is checking
    addLog({
      timestamp: new Date(),
      agent: "guardian",
      message: `Analyzing risk for ${selectedPair} trade ($${positionSize[0].toLocaleString()})`,
      type: "info",
    })

    // Simulate Guardian agent checking risk
    await new Promise((resolve) => setTimeout(resolve, 1500))
    const score = Math.floor(Math.random() * 40) + 60 // Score between 60-100
    setRiskScore(score)
    setGuardianApproved(score >= 70)
    setIsChecking(false)

    // Log the result
    addLog({
      timestamp: new Date(),
      agent: "guardian",
      message: score >= 70
        ? `Trade approved with risk score ${score}/100`
        : `Trade blocked - risk score ${score}/100 below threshold`,
      type: score >= 70 ? "success" : "warning",
    })
  }

  const handleExecute = async () => {
    setIsExecuting(true)

    // Simulate execution delay
    await new Promise((resolve) => setTimeout(resolve, 1000))

    // Create random entry spread
    const entrySpread = Math.random() * 0.2 + 0.05

    // Add the position
    addPosition({
      pair: selectedPair,
      entrySpread,
      currentSpread: entrySpread,
      pnl: 0,
      pnlPercent: 0,
      riskLevel: riskScore && riskScore >= 80 ? "low" : riskScore && riskScore >= 70 ? "medium" : "high",
      size: positionSize[0],
      entryTime: new Date(),
    })

    // Log the execution
    addLog({
      timestamp: new Date(),
      agent: "executor",
      message: `Executed pair trade: ${selectedPair} with size $${positionSize[0].toLocaleString()}`,
      type: "success",
    })

    // Reset form
    setSelectedPair("")
    setRiskScore(null)
    setGuardianApproved(false)
    setIsExecuting(false)
  }

  return (
    <GlassCard data-tour="trade">
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
            <Tooltip>
              <TooltipTrigger className="flex items-center gap-1 text-sm font-medium">
                Guardian Risk Assessment
                <HelpCircle className="w-3 h-3 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-[220px]">
                AI risk manager that analyzes your trade before execution. Scores 70+ are approved, below 70 are blocked for safety.
              </TooltipContent>
            </Tooltip>
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
          disabled={!guardianApproved || !selectedPair || isExecuting}
          className={cn(
            "w-full haptic-press font-medium h-12",
            guardianApproved && !isExecuting
              ? "bg-white hover:bg-white/90 text-black"
              : "bg-secondary text-muted-foreground cursor-not-allowed",
          )}
        >
          {isExecuting ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Executing...
            </>
          ) : (
            <>
              <Zap className="w-4 h-4 mr-2" />
              Execute Pair Trade
            </>
          )}
        </Button>

        {!guardianApproved && selectedPair && (
          <p className="text-xs text-center text-muted-foreground">Guardian approval required before execution</p>
        )}
      </div>
    </GlassCard>
  )
}
