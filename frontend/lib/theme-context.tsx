"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"

export type Theme = "dark" | "light" | "neon" | "retro"

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  highContrast: boolean
  setHighContrast: (enabled: boolean) => void
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "dark",
  setTheme: () => {},
  highContrast: false,
  setHighContrast: () => {},
})

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("dark")
  const [highContrast, setHighContrastState] = useState(false)
  const [mounted, setMounted] = useState(false)

  // Load theme and high contrast from localStorage on mount
  useEffect(() => {
    setMounted(true)
    const savedTheme = localStorage.getItem("hyperswarm-theme") as Theme | null
    if (savedTheme && ["dark", "light", "neon", "retro"].includes(savedTheme)) {
      setThemeState(savedTheme)
    }
    const savedHighContrast = localStorage.getItem("hyperswarm-high-contrast")
    if (savedHighContrast === "true") {
      setHighContrastState(true)
    }
  }, [])

  // Apply theme class to document
  useEffect(() => {
    if (!mounted) return

    const root = document.documentElement
    // Remove all theme classes
    root.classList.remove("dark", "theme-dark", "theme-light", "theme-neon", "theme-retro", "high-contrast")

    // Add the new theme class
    if (theme === "dark") {
      root.classList.add("dark", "theme-dark")
    } else {
      root.classList.add(`theme-${theme}`)
    }

    // Add high contrast class if enabled
    if (highContrast) {
      root.classList.add("high-contrast")
    }
  }, [theme, highContrast, mounted])

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
    localStorage.setItem("hyperswarm-theme", newTheme)
  }

  const setHighContrast = (enabled: boolean) => {
    setHighContrastState(enabled)
    localStorage.setItem("hyperswarm-high-contrast", enabled.toString())
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, highContrast, setHighContrast }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}
