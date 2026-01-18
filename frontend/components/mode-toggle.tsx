"use client"

import { Switch } from "@/components/ui/switch"
import { Bot, User } from "lucide-react"
import { cn } from "@/lib/utils"

interface ModeToggleProps {
  mode: "manual" | "ai"
  onChange: (mode: "manual" | "ai") => void
  label?: string
}

export function ModeToggle({ mode, onChange, label = "Enable AI Trading" }: ModeToggleProps) {
  const isAI = mode === "ai"

  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 border border-white/5">
      <div className="flex items-center gap-2">
        {isAI ? (
          <Bot className="w-4 h-4 text-[#30D158]" />
        ) : (
          <User className="w-4 h-4 text-muted-foreground" />
        )}
        <span className={cn(
          "text-sm font-medium transition-colors",
          isAI ? "text-[#30D158]" : "text-muted-foreground"
        )}>
          {label}
        </span>
      </div>
      <Switch
        checked={isAI}
        onCheckedChange={(checked) => onChange(checked ? "ai" : "manual")}
        className="data-[state=checked]:bg-[#30D158]"
      />
    </div>
  )
}
