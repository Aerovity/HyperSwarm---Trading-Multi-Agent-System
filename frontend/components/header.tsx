"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Wallet, Wifi, ChevronDown } from "lucide-react"

export function Header() {
  const [isConnected, setIsConnected] = useState(false)
  const [address, setAddress] = useState("")

  const handleConnect = () => {
    // Mock wallet connection
    setIsConnected(true)
    setAddress("0x1234...5678")
  }

  return (
    <header className="sticky top-0 z-50 glass border-b border-white/5">
      <div className="px-2 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl font-semibold tracking-tight">HyperSwarm</span>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {/* Network indicator */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 text-sm">
            <Wifi className="w-3.5 h-3.5 text-[#30D158]" />
            <span className="text-muted-foreground">Hyperliquid Testnet</span>
          </div>

          {/* Wallet button */}
          {isConnected ? (
            <Button
              variant="outline"
              className="haptic-press bg-secondary/50 border-white/20 hover:bg-secondary/80 gap-2"
            >
              <div className="w-2 h-2 rounded-full bg-[#30D158]" />
              <span className="font-mono text-sm">{address}</span>
              <ChevronDown className="w-4 h-4 text-white" />
            </Button>
          ) : (
            <Button
              onClick={handleConnect}
              className="haptic-press bg-white hover:bg-white/90 text-black font-medium gap-2"
            >
              <Wallet className="w-4 h-4" />
              Connect Wallet
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}
