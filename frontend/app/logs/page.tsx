"use client"

import { useState, useMemo } from "react"
import { Header } from "@/components/header"
import { GlassCard } from "@/components/ui/glass-card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useDemoContext } from "@/lib/demo-context"
import { cn } from "@/lib/utils"
import { Activity, Search, ArrowUpDown, Zap, Shield, Filter } from "lucide-react"

const agentIcons = {
  scout: Search,
  onboarder: ArrowUpDown,
  executor: Zap,
  guardian: Shield,
}

const agentFilters = [
  { id: "all", label: "All" },
  { id: "scout", label: "Scout" },
  { id: "onboarder", label: "Onboarder" },
  { id: "executor", label: "Executor" },
  { id: "guardian", label: "Guardian" },
]

const typeFilters = [
  { id: "all", label: "All Types" },
  { id: "success", label: "Success" },
  { id: "warning", label: "Warning" },
  { id: "error", label: "Error" },
  { id: "info", label: "Info" },
]

export default function LogsPage() {
  const { activityLogs } = useDemoContext()
  const [agentFilter, setAgentFilter] = useState("all")
  const [typeFilter, setTypeFilter] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")

  const filteredLogs = useMemo(() => {
    return activityLogs.filter((log) => {
      // Agent filter
      if (agentFilter !== "all" && log.agent !== agentFilter) return false

      // Type filter
      if (typeFilter !== "all" && log.type !== typeFilter) return false

      // Search filter
      if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }

      return true
    })
  }, [activityLogs, agentFilter, typeFilter, searchQuery])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    })
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-6 space-y-6">
        <GlassCard>
          <div className="flex items-center gap-2 mb-6">
            <Activity className="w-5 h-5 text-white" />
            <h3 className="font-semibold text-lg">Activity Logs</h3>
            <span className="text-xs text-muted-foreground ml-auto">
              {filteredLogs.length} entries
            </span>
          </div>

          {/* Agent Filter Tabs */}
          <div className="flex flex-wrap gap-2 mb-4">
            {agentFilters.map((filter) => (
              <Button
                key={filter.id}
                variant="ghost"
                size="sm"
                onClick={() => setAgentFilter(filter.id)}
                className={cn(
                  "rounded-full px-4",
                  agentFilter === filter.id
                    ? "bg-white/10 text-white"
                    : "text-muted-foreground hover:text-white hover:bg-white/5"
                )}
              >
                {filter.label}
              </Button>
            ))}
          </div>

          {/* Search and Type Filter */}
          <div className="flex flex-col sm:flex-row gap-3 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-secondary/50 border-white/10"
              />
            </div>
            <div className="flex gap-2">
              {typeFilters.map((filter) => (
                <Button
                  key={filter.id}
                  variant="ghost"
                  size="sm"
                  onClick={() => setTypeFilter(filter.id)}
                  className={cn(
                    "text-xs",
                    typeFilter === filter.id
                      ? "bg-white/10 text-white"
                      : "text-muted-foreground hover:text-white hover:bg-white/5",
                    filter.id === "success" && typeFilter === filter.id && "text-[#30D158]",
                    filter.id === "warning" && typeFilter === filter.id && "text-yellow-500",
                    filter.id === "error" && typeFilter === filter.id && "text-[#FF453A]"
                  )}
                >
                  {filter.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Log Entries */}
          <div className="space-y-2 max-h-[calc(100vh-400px)] overflow-y-auto pr-2">
            {filteredLogs.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <Filter className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm">No logs match your filters</p>
              </div>
            ) : (
              filteredLogs.map((log, index) => {
                const Icon = agentIcons[log.agent]

                return (
                  <div
                    key={log.id}
                    className={cn(
                      "flex items-start gap-3 p-3 rounded-lg transition-all duration-300",
                      "hover:bg-white/5",
                      index === 0 && "animate-in slide-in-from-top-2"
                    )}
                  >
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 bg-white/10">
                      <Icon className="w-4 h-4 text-white" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm capitalize text-white">
                          {log.agent}
                        </span>
                        <span className="text-xs text-muted-foreground font-mono">
                          {formatTime(log.timestamp)}
                        </span>
                        <span
                          className={cn(
                            "text-[10px] px-1.5 py-0.5 rounded uppercase font-medium",
                            log.type === "success" && "bg-[#30D158]/20 text-[#30D158]",
                            log.type === "warning" && "bg-yellow-500/20 text-yellow-500",
                            log.type === "error" && "bg-[#FF453A]/20 text-[#FF453A]",
                            log.type === "info" && "bg-white/10 text-white/70"
                          )}
                        >
                          {log.type}
                        </span>
                      </div>
                      <p
                        className={cn(
                          "text-sm mt-0.5",
                          log.type === "success" && "text-[#30D158]",
                          log.type === "warning" && "text-white/80",
                          log.type === "error" && "text-[#FF453A]",
                          log.type === "info" && "text-foreground/80"
                        )}
                      >
                        {log.message}
                      </p>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </GlassCard>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 mt-8">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>HyperSwarm v1.0.0</span>
            <span>Connected to Hyperliquid Testnet</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
