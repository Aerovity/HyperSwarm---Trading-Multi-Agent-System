"use client"

import type React from "react"

import { cn } from "@/lib/utils"
import { forwardRef } from "react"

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  glow?: "green" | "blue" | "none"
}

const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, glow = "none", children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "glass rounded-lg p-6 transition-all duration-300",
          glow === "green" && "shadow-[0_0_30px_rgba(48,209,88,0.15)]",
          glow === "blue" && "shadow-[0_0_30px_rgba(255,255,255,0.1)]",
          className,
        )}
        {...props}
      >
        {children}
      </div>
    )
  },
)
GlassCard.displayName = "GlassCard"

export { GlassCard }
