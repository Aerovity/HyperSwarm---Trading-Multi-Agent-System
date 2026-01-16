"use client"

import { useEffect, useState, useRef } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import type { ActivityLog } from "@/types"
import { cn } from "@/lib/utils"
import { Activity, Search, ArrowUpDown, Zap, Shield } from "lucide-react"

const agentIcons = {
  scout: Search,
  onboarder: ArrowUpDown,
  executor: Zap,
  guardian: Shield,
}

export function ActivityLogComponent() {
  const [logs, setLogs] = useState<ActivityLog[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)

  // Fetch real logs from Scout and Onboarder Agent APIs
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        // Fetch from both agents in parallel
        const [scoutResponse, onboarderResponse] = await Promise.allSettled([
          fetch('http://localhost:8001/api/agent/logs'),
          fetch('http://localhost:8002/api/agent/logs'),
        ])

        const allLogs: ActivityLog[] = []

        // Process Scout logs
        if (scoutResponse.status === 'fulfilled' && scoutResponse.value.ok) {
          const scoutData = await scoutResponse.value.json()
          const scoutLogs = scoutData.map((log: any) => ({
            id: log.id,
            timestamp: new Date(log.timestamp),
            agent: log.agent,
            message: log.message,
            type: log.type,
          }))
          allLogs.push(...scoutLogs)
        }

        // Process Onboarder logs
        if (onboarderResponse.status === 'fulfilled' && onboarderResponse.value.ok) {
          const onboarderData = await onboarderResponse.value.json()
          const onboarderLogs = onboarderData.map((log: any) => ({
            id: log.id,
            timestamp: new Date(log.timestamp),
            agent: log.agent,
            message: log.message,
            type: log.type,
          }))
          allLogs.push(...onboarderLogs)
        }

        // Sort by timestamp (newest first)
        allLogs.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())

        setLogs(allLogs)
      } catch (error) {
        console.error('Failed to fetch agent logs:', error)
        // Fallback to empty array, keep UI functional
        setLogs([])
      }
    }

    // Poll every 2 seconds for real-time updates
    const interval = setInterval(fetchLogs, 2000)
    fetchLogs() // Initial fetch

    return () => clearInterval(interval)
  }, [])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    })
  }

  return (
    <GlassCard className="col-span-full">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-white" />
        <h3 className="font-semibold">Agent Activity Log</h3>
        <span className="text-xs text-muted-foreground ml-auto">Real-time</span>
      </div>

      <div ref={scrollRef} className="h-[280px] overflow-y-auto space-y-2 pr-2">
        {logs.map((log, index) => {
          const Icon = agentIcons[log.agent]

          return (
            <div
              key={log.id}
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg transition-all duration-300",
                "hover:bg-white/5",
                index === 0 && "animate-in slide-in-from-top-2",
              )}
            >
              <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 bg-white/10">
                <Icon className="w-4 h-4 text-white" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm capitalize text-white">{log.agent}</span>
                  <span className="text-xs text-muted-foreground font-mono">{formatTime(log.timestamp)}</span>
                </div>
                <p
                  className={cn(
                    "text-sm mt-0.5",
                    log.type === "success" && "text-[#30D158]",
                    log.type === "warning" && "text-white/80",
                    log.type === "error" && "text-[#FF453A]",
                    log.type === "info" && "text-foreground/80",
                  )}
                >
                  {log.message}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </GlassCard>
  )
}
