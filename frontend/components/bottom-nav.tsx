"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Home, Zap, Activity, Settings } from "lucide-react"

const navItems = [
  { href: "/dashboard", label: "Home", icon: Home },
  { href: "/trade", label: "Trade", icon: Zap },
  { href: "/logs", label: "Activity", icon: Activity },
  { href: "/settings", label: "Settings", icon: Settings },
]

export function BottomNav() {
  const pathname = usePathname()

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 h-16 border-t border-border bg-background/95 backdrop-blur-xl">
      <div className="flex items-center justify-around h-full px-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href ||
            (item.href === "/dashboard" && pathname === "/")
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg transition-all duration-200",
                "min-w-[64px]",
                isActive && "text-foreground",
                !isActive && "text-muted-foreground"
              )}
            >
              <div
                className={cn(
                  "p-1.5 rounded-lg transition-all duration-200",
                  isActive && "bg-foreground/10"
                )}
              >
                <Icon className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
