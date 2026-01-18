"use client"

import { Header } from "@/components/header"
import { GlassCard } from "@/components/ui/glass-card"
import { Switch } from "@/components/ui/switch"
import { useTheme, Theme } from "@/lib/theme-context"
import { cn } from "@/lib/utils"
import { Settings, Moon, Sun, Zap, Sparkles, Eye } from "lucide-react"

const themes: { id: Theme; label: string; icon: typeof Moon; description: string }[] = [
  { id: "dark", label: "Dark", icon: Moon, description: "Default dark theme" },
  { id: "light", label: "Light", icon: Sun, description: "Clean light theme" },
  { id: "neon", label: "Neon", icon: Zap, description: "Cyberpunk vibes" },
  { id: "retro", label: "Retro", icon: Sparkles, description: "Golden classics" },
]

export default function SettingsPage() {
  const { theme, setTheme, highContrast, setHighContrast } = useTheme()

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-6 space-y-6 max-w-2xl">
        {/* Page Title */}
        <div className="flex items-center gap-2">
          <Settings className="w-6 h-6" />
          <h1 className="text-2xl font-semibold">Settings</h1>
        </div>

        {/* Appearance Section */}
        <GlassCard>
          <h2 className="text-lg font-semibold mb-4">Appearance</h2>

          {/* Theme Selection */}
          <div className="space-y-3">
            <label className="text-sm text-muted-foreground">Theme</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {themes.map((t) => {
                const Icon = t.icon
                const isActive = theme === t.id

                return (
                  <button
                    key={t.id}
                    onClick={() => setTheme(t.id)}
                    className={cn(
                      "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all duration-200",
                      isActive
                        ? "border-foreground bg-foreground/10"
                        : "border-border hover:border-foreground/30 hover:bg-foreground/5"
                    )}
                  >
                    <div
                      className={cn(
                        "w-10 h-10 rounded-lg flex items-center justify-center",
                        isActive ? "bg-foreground text-background" : "bg-foreground/10"
                      )}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-sm font-medium">{t.label}</span>
                    <span className="text-[10px] text-muted-foreground">{t.description}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* High Contrast Toggle */}
          <div className="mt-6 pt-6 border-t border-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-foreground/10 flex items-center justify-center">
                  <Eye className="w-5 h-5" />
                </div>
                <div>
                  <span className="font-medium">High Contrast Mode</span>
                  <p className="text-xs text-muted-foreground">
                    Increases visibility for better accessibility
                  </p>
                </div>
              </div>
              <Switch
                checked={highContrast}
                onCheckedChange={setHighContrast}
              />
            </div>
          </div>
        </GlassCard>

        {/* Trading Preferences (Coming Soon) */}
        <GlassCard>
          <h2 className="text-lg font-semibold mb-4">Trading Preferences</h2>

          <div className="space-y-4 opacity-50">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium">Demo Mode</span>
                <p className="text-xs text-muted-foreground">
                  Trade with simulated data
                </p>
              </div>
              <Switch checked={true} disabled />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium">Risk Level</span>
                <p className="text-xs text-muted-foreground">
                  Coming soon
                </p>
              </div>
              <span className="text-sm text-muted-foreground">Balanced</span>
            </div>
          </div>
        </GlassCard>

        {/* Notifications (Coming Soon) */}
        <GlassCard>
          <h2 className="text-lg font-semibold mb-4">Notifications</h2>
          <p className="text-sm text-muted-foreground">
            Notification settings coming soon.
          </p>
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
