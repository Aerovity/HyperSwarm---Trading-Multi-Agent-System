"use client"

import { useTheme, Theme } from "@/lib/theme-context"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Moon, Sun, Zap, Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"

const themes: { value: Theme; label: string; icon: React.ReactNode; description: string }[] = [
  {
    value: "dark",
    label: "Dark",
    icon: <Moon className="w-4 h-4" />,
    description: "Default dark mode",
  },
  {
    value: "light",
    label: "Light",
    icon: <Sun className="w-4 h-4" />,
    description: "Clean light mode",
  },
  {
    value: "neon",
    label: "Neon",
    icon: <Zap className="w-4 h-4" />,
    description: "Cyberpunk vibes",
  },
  {
    value: "retro",
    label: "Retro",
    icon: <Sparkles className="w-4 h-4" />,
    description: "Synthwave style",
  },
]

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme()

  const currentTheme = themes.find((t) => t.value === theme) || themes[0]

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 gap-2 px-2 hover:bg-secondary/80"
        >
          {currentTheme.icon}
          <span className="hidden sm:inline text-xs">{currentTheme.label}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        {themes.map((t) => (
          <DropdownMenuItem
            key={t.value}
            onClick={() => setTheme(t.value)}
            className={cn(
              "flex items-center gap-2 cursor-pointer",
              theme === t.value && "bg-secondary"
            )}
          >
            {t.icon}
            <div className="flex flex-col">
              <span className="text-sm">{t.label}</span>
              <span className="text-xs text-muted-foreground">{t.description}</span>
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
