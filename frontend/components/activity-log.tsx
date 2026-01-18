"use client"

import { useRef, useState, useEffect } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { cn } from "@/lib/utils"
import { Activity, Search, ArrowUpDown, Zap, Shield } from "lucide-react"
import { useDemoContext } from "@/lib/demo-context"

const agentIcons = {
  scout: Search,
  onboarder: ArrowUpDown,
  executor: Zap,
  guardian: Shield,
}

export function ActivityLogComponent() {
  const { activityLogs } = useDemoContext()
  const scrollRef = useRef<HTMLDivElement>(null)
  const [mounted, setMounted] = useState(false)

  // Fix hydration - only render timestamps on client
  useEffect(() => {
    setMounted(true)
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
    <GlassCard className="col-span-full h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4 shrink-0">
        <Activity className="w-5 h-5 text-white" />
        <h3 className="font-semibold">Agent Activity Log</h3>
        <span className="text-xs text-muted-foreground ml-auto">Real-time</span>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-2 pr-2">
        {activityLogs.map((log, index) => {
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
                  <span className="text-xs text-muted-foreground font-mono">
                    {mounted ? formatTime(log.timestamp) : "--:--:--"}
                  </span>
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
