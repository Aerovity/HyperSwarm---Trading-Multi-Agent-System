"use client"

import { useState, useEffect } from "react"
import { AgentCard } from "@/components/agent-card"
import { mockAgents } from "@/lib/mock-data"
import { scoutApi, onboarderApi, guardianApi, executorApi } from "@/lib/api"
import type { Agent } from "@/types"
import { cn } from "@/lib/utils"

interface AgentStatusPanelProps {
  compact?: boolean
}

export function AgentStatusPanel({ compact = false }: AgentStatusPanelProps) {
  const [agents, setAgents] = useState<Agent[]>(mockAgents)
  const [mounted, setMounted] = useState(false)

  // Fix hydration issue - only run on client
  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return

    const checkAgentHealth = async () => {
      try {
        // Check health of all 4 agents in parallel
        const [scoutHealth, onboarderHealth, guardianHealth, executorHealth] = await Promise.allSettled([
          scoutApi.healthCheck(),
          onboarderApi.healthCheck(),
          guardianApi.healthCheck(),
          executorApi.healthCheck(),
        ])

        // Update agent statuses based on health checks
        setAgents((prevAgents) =>
          prevAgents.map((agent) => {
            if (agent.type === 'scout' && scoutHealth.status === 'fulfilled') {
              return {
                ...agent,
                status: scoutHealth.value.status === 'healthy' ? 'active' : 'idle',
                lastAction: `Redis: ${scoutHealth.value.redis}`,
                lastActionTime: new Date(),
              } as Agent
            }

            if (agent.type === 'onboarder' && onboarderHealth.status === 'fulfilled') {
              return {
                ...agent,
                status: onboarderHealth.value.status === 'healthy' ? 'active' : 'idle',
                lastAction: `Redis: ${onboarderHealth.value.redis}`,
                lastActionTime: new Date(),
              } as Agent
            }

            if (agent.type === 'guardian' && guardianHealth.status === 'fulfilled') {
              return {
                ...agent,
                status: guardianHealth.value.status === 'healthy' ? 'active' : 'idle',
                lastAction: `Redis: ${guardianHealth.value.redis}, Claude: ${guardianHealth.value.anthropic || 'N/A'}`,
                lastActionTime: new Date(),
              } as Agent
            }

            if (agent.type === 'executor' && executorHealth.status === 'fulfilled') {
              return {
                ...agent,
                status: executorHealth.value.status === 'healthy' ? 'active' : 'idle',
                lastAction: `Redis: ${executorHealth.value.redis}`,
                lastActionTime: new Date(),
              } as Agent
            }

            return agent
          })
        )
      } catch (error) {
        console.error('Failed to check agent health:', error)
        // Keep using mock data on error
      }
    }

    // Initial check
    checkAgentHealth()

    // Poll every 10 seconds
    const interval = setInterval(checkAgentHealth, 10000)

    return () => clearInterval(interval)
  }, [mounted])

  const activeCount = agents.filter((a) => a.status === "active").length

  return (
    <section data-tour="agents" className={cn(compact && "h-full flex flex-col")}>
      <div className="flex items-center justify-between mb-3 flex-shrink-0">
        <h2 className={cn("font-semibold", compact ? "text-sm" : "text-lg")}>Agent Status</h2>
        <span className="text-xs text-muted-foreground">
          {activeCount}/{agents.length} Active
        </span>
      </div>

      <div className={cn(
        "grid gap-3",
        compact
          ? "grid-cols-2 flex-1"
          : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
      )}>
        {agents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} compact={compact} />
        ))}
      </div>
    </section>
  )
}
