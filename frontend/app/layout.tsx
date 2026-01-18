import type React from "react"
import type { Metadata, Viewport } from "next"
import { Analytics } from "@vercel/analytics/next"
import { DemoProvider } from "@/lib/demo-context"
import { ThemeProvider } from "@/lib/theme-context"
import { TooltipProvider } from "@/components/ui/tooltip"
import "./globals.css"

export const metadata: Metadata = {
  title: "HyperSwarm | DeFi Trading Dashboard",
  description: "AI-powered multi-agent DeFi trading platform on Hyperliquid",
  generator: "v0.app",
  manifest: "/manifest.json",
}

export const viewport: Viewport = {
  themeColor: "#0A0A0A",
  width: "device-width",
  initialScale: 1,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased min-h-screen bg-background">
        <ThemeProvider>
          <DemoProvider>
            <TooltipProvider>
              {children}
            </TooltipProvider>
          </DemoProvider>
        </ThemeProvider>
        <Analytics />
      </body>
    </html>
  )
}
