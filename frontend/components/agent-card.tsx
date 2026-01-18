"use client"

import { useState, useEffect } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { cn } from "@/lib/utils"
import type { Agent } from "@/types"
import { Search, ArrowUpDown, Zap, Shield } from "lucide-react"

const agentIcons = {
  scout: Search,
  onboarder: ArrowUpDown,
  executor: Zap,
  guardian: Shield,
}

interface AgentCardProps {
  agent: Agent
  compact?: boolean
}

export function AgentCard({ agent, compact = false }: AgentCardProps) {
  const Icon = agentIcons[agent.type]
  const [timeAgoText, setTimeAgoText] = useState("Just now")
  const [mounted, setMounted] = useState(false)

  // Fix hydration - only calculate time on client
  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return

    const updateTimeAgo = () => {
      const seconds = Math.floor((Date.now() - agent.lastActionTime.getTime()) / 1000)
      if (seconds < 60) {
        setTimeAgoText(`${seconds}s ago`)
      } else {
        const minutes = Math.floor(seconds / 60)
        if (minutes < 60) {
          setTimeAgoText(`${minutes}m ago`)
        } else {
          const hours = Math.floor(minutes / 60)
          setTimeAgoText(`${hours}h ago`)
        }
      }
    }

    updateTimeAgo()
    const interval = setInterval(updateTimeAgo, 1000)

    return () => clearInterval(interval)
  }, [agent.lastActionTime, mounted])

  if (compact) {
    return (
      <GlassCard className="relative overflow-hidden p-3">
        {/* Status indicator pulse */}
        {agent.status === "active" && (
          <div className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full animate-pulse-glow bg-[#30D158]" />
        )}

        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-white/10 shrink-0">
            <Icon className="w-4 h-4 text-white" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              <h3 className="font-medium text-sm">{agent.name}</h3>
              <span
                className={cn(
                  "px-1.5 py-0.5 rounded text-[10px] font-medium capitalize",
                  agent.status === "active" && "bg-[#30D158]/20 text-[#30D158]",
                  agent.status === "idle" && "bg-white/10 text-muted-foreground",
                  agent.status === "processing" && "bg-white/20 text-white",
                )}
              >
                {agent.status}
              </span>
            </div>
            <p className="text-[10px] text-muted-foreground/60">
              {mounted ? timeAgoText : "Just now"}
            </p>
          </div>
        </div>
      </GlassCard>
    )
  }

  return (
    <GlassCard className="relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300">
      {/* Status indicator pulse - kept green for active */}
      {agent.status === "active" && (
        <div className="absolute top-4 right-4 w-2 h-2 rounded-full animate-pulse-glow bg-[#30D158]" />
      )}

      <div className="absolute -top-20 -right-20 w-40 h-40 rounded-full opacity-10 blur-3xl transition-opacity group-hover:opacity-20 bg-white" />

      <div className="relative flex items-start gap-4">
        <div className="w-12 h-12 rounded-lg flex items-center justify-center bg-white/10">
          <Icon className="w-6 h-6 text-white" />
        </div>

        <div className="flex-1 min-w-0">
          {/* Name and status */}
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold">{agent.name}</h3>
            <span
              className={cn(
                "px-2 py-0.5 rounded text-xs font-medium capitalize",
                agent.status === "active" && "bg-[#30D158]/20 text-[#30D158]",
                agent.status === "idle" && "bg-white/10 text-muted-foreground",
                agent.status === "processing" && "bg-white/20 text-white",
              )}
            >
              {agent.status}
            </span>
          </div>

          {/* Last action */}
          <p className="text-sm text-muted-foreground truncate mb-1">{agent.lastAction}</p>

          <p className="text-xs text-muted-foreground/60">
            {mounted ? timeAgoText : "Just now"}
          </p>
        </div>
      </div>
    </GlassCard>
  )
}
