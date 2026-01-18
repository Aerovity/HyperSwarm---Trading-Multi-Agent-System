"use client"

import { createContext, useContext, useState, ReactNode } from "react"
import type { Position, ActivityLog } from "@/types"
import { mockPositions, mockActivityLogs } from "@/lib/mock-data"

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface DemoContextType {
  positions: Position[]
  activityLogs: ActivityLog[]
  addPosition: (position: Omit<Position, "id">) => void
  closePosition: (id: string) => void
  addLog: (log: Omit<ActivityLog, "id">) => void
  // Trading mode state
  tradingMode: "manual" | "ai"
  setTradingMode: (mode: "manual" | "ai") => void
  // Chat state for AI mode
  chatMessages: ChatMessage[]
  addChatMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => void
  clearChatMessages: () => void
}

const DemoContext = createContext<DemoContextType | null>(null)

export function DemoProvider({ children }: { children: ReactNode }) {
  const [positions, setPositions] = useState<Position[]>(mockPositions)
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>(mockActivityLogs)
  const [tradingMode, setTradingMode] = useState<"manual" | "ai">("manual")
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])

  const addPosition = (position: Omit<Position, "id">) => {
    const newPosition: Position = {
      ...position,
      id: `pos-${Date.now()}`,
    }
    setPositions((prev) => [newPosition, ...prev])
  }

  const closePosition = (id: string) => {
    setPositions((prev) => prev.filter((p) => p.id !== id))
  }

  const addLog = (log: Omit<ActivityLog, "id">) => {
    const newLog: ActivityLog = {
      ...log,
      id: `log-${Date.now()}`,
    }
    setActivityLogs((prev) => [newLog, ...prev])
  }

  const addChatMessage = (message: Omit<ChatMessage, "id" | "timestamp">) => {
    const newMessage: ChatMessage = {
      ...message,
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    }
    setChatMessages((prev) => [...prev, newMessage])
  }

  const clearChatMessages = () => {
    setChatMessages([])
  }

  return (
    <DemoContext.Provider
      value={{
        positions,
        activityLogs,
        addPosition,
        closePosition,
        addLog,
        tradingMode,
        setTradingMode,
        chatMessages,
        addChatMessage,
        clearChatMessages,
      }}
    >
      {children}
    </DemoContext.Provider>
  )
}

export function useDemoContext() {
  const context = useContext(DemoContext)
  if (!context) {
    throw new Error("useDemoContext must be used within a DemoProvider")
  }
  return context
}
