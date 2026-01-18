"use client"

import { useState, useEffect } from "react"
import { useDemoContext } from "@/lib/demo-context"
import { useTheme } from "@/lib/theme-context"
import { cn } from "@/lib/utils"
import { CheckCircle2, Circle, ChevronDown, ChevronUp, Trophy, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Mission {
  id: string
  label: string
  check: () => boolean
}

export function MissionTracker() {
  const { positions, activityLogs } = useDemoContext()
  const { theme } = useTheme()
  const [collapsed, setCollapsed] = useState(false)
  const [completedMissions, setCompletedMissions] = useState<Set<string>>(new Set())
  const [mounted, setMounted] = useState(false)

  const missions: Mission[] = [
    {
      id: "view-market",
      label: "View market opportunities",
      check: () => true, // Always complete on dashboard
    },
    {
      id: "execute-trade",
      label: "Execute your first trade",
      check: () => positions.length > 0 || activityLogs.some((log) => log.agent === "executor"),
    },
    {
      id: "close-position",
      label: "Close a position",
      check: () => activityLogs.some((log) => log.message.includes("Closed position")),
    },
    {
      id: "customize-theme",
      label: "Customize your theme",
      check: () => theme !== "dark",
    },
  ]

  useEffect(() => {
    setMounted(true)
    // Load completed missions from localStorage
    const saved = localStorage.getItem("hyperswarm-missions")
    if (saved) {
      setCompletedMissions(new Set(JSON.parse(saved)))
    }
  }, [])

  // Check missions and update completed state
  useEffect(() => {
    if (!mounted) return

    const newCompleted = new Set(completedMissions)
    let hasChanges = false

    missions.forEach((mission) => {
      if (!newCompleted.has(mission.id) && mission.check()) {
        newCompleted.add(mission.id)
        hasChanges = true
      }
    })

    if (hasChanges) {
      setCompletedMissions(newCompleted)
      localStorage.setItem("hyperswarm-missions", JSON.stringify([...newCompleted]))
    }
  }, [positions, activityLogs, theme, mounted])

  if (!mounted) return null

  const completedCount = missions.filter((m) => completedMissions.has(m.id)).length
  const allComplete = completedCount === missions.length
  const progress = (completedCount / missions.length) * 100

  return (
    <div className="p-3">
      <div className="glass rounded-lg overflow-hidden">
        {/* Header */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors"
        >
          <div className="flex items-center gap-2">
            {allComplete ? (
              <Trophy className="w-4 h-4 text-[#30D158]" />
            ) : (
              <Sparkles className="w-4 h-4 text-white/70" />
            )}
            <span className="text-sm font-medium">
              {allComplete ? "All Complete!" : "Getting Started"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {completedCount}/{missions.length}
            </span>
            {collapsed ? (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronUp className="w-4 h-4 text-muted-foreground" />
            )}
          </div>
        </button>

        {/* Progress bar */}
        <div className="h-1 bg-white/5">
          <div
            className="h-full bg-[#30D158] transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Mission list */}
        {!collapsed && (
          <div className="p-3 space-y-2">
            {missions.map((mission) => {
              const isComplete = completedMissions.has(mission.id)

              return (
                <div
                  key={mission.id}
                  className={cn(
                    "flex items-center gap-2 text-sm transition-all duration-300",
                    isComplete && "opacity-60"
                  )}
                >
                  {isComplete ? (
                    <CheckCircle2 className="w-4 h-4 text-[#30D158] shrink-0" />
                  ) : (
                    <Circle className="w-4 h-4 text-muted-foreground shrink-0" />
                  )}
                  <span className={cn(isComplete && "line-through")}>{mission.label}</span>
                </div>
              )
            })}

            {allComplete && (
              <div className="pt-2 mt-2 border-t border-white/10">
                <p className="text-xs text-[#30D158] text-center">
                  You're all set! Happy trading!
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
