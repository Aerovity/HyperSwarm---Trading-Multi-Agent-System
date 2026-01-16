"use client"

import { useState, useEffect } from "react"
import { AgentCard } from "@/components/agent-card"
import { mockAgents } from "@/lib/mock-data"
import { scoutApi, onboarderApi } from "@/lib/api"
import type { Agent } from "@/types"

export function AgentStatusPanel() {
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
        // Check health of both agents in parallel
        const [scoutHealth, onboarderHealth] = await Promise.allSettled([
          scoutApi.healthCheck(),
          onboarderApi.healthCheck(),
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
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Agent Status</h2>
        <span className="text-sm text-muted-foreground">
          {activeCount}/{agents.length} Active
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {agents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </section>
  )
}
