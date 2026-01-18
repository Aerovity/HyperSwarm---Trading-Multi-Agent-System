"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Home, Zap, Activity, Settings, ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { MissionTracker } from "@/components/mission-tracker"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/trade", label: "Trade", icon: Zap },
  { href: "/logs", label: "Activity", icon: Activity },
  { href: "/settings", label: "Settings", icon: Settings },
]

export function AppSidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      data-tour="sidebar"
      className={cn(
        "hidden lg:flex flex-col h-screen sticky top-0 border-r border-border bg-background/80 backdrop-blur-xl transition-all duration-300",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div className={cn(
        "flex items-center h-16 px-4 border-b border-border",
        collapsed ? "justify-center" : "gap-2"
      )}>
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-foreground to-foreground/60 flex items-center justify-center">
          <span className="text-background font-bold text-sm">HS</span>
        </div>
        {!collapsed && (
          <span className="font-semibold text-lg">HyperSwarm</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href ||
            (item.href === "/dashboard" && pathname === "/")
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                "hover:bg-foreground/10",
                isActive && "bg-foreground/10 text-foreground",
                !isActive && "text-muted-foreground hover:text-foreground",
                collapsed && "justify-center px-2"
              )}
            >
              <Icon className="w-5 h-5 shrink-0" />
              {!collapsed && (
                <span className="font-medium">{item.label}</span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Mission Tracker - only show when expanded */}
      {!collapsed && <MissionTracker />}

      {/* Collapse Toggle */}
      <div className="p-3 border-t border-border">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "w-full hover:bg-foreground/10",
            collapsed ? "px-2" : "justify-start"
          )}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4 mr-2" />
              Collapse
            </>
          )}
        </Button>
      </div>
    </aside>
  )
}
