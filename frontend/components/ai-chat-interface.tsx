"use client"

import { useState, useRef, useEffect } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useDemoContext } from "@/lib/demo-context"
import { Bot, User, Send, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export function AIChatInterface() {
  const { chatMessages, addChatMessage } = useDemoContext()
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      const scrollContainer = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [chatMessages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput("")

    // Add user message
    addChatMessage({ role: "user", content: userMessage })

    setIsLoading(true)

    // Simulate AI response (founder will add real orchestrator logic later)
    await new Promise((resolve) => setTimeout(resolve, 1500))

    // Mock AI response based on user input
    let responseContent = "I'm the AI trading orchestrator. I coordinate between Scout, Guardian, and Executor agents to find and execute optimal trades.\n\n"

    if (userMessage.toLowerCase().includes("trade") || userMessage.toLowerCase().includes("buy") || userMessage.toLowerCase().includes("sell")) {
      responseContent += "- Analyzing market conditions via Scout Agent\n- Checking risk parameters with Guardian\n- Ready to execute when approved"
    } else if (userMessage.toLowerCase().includes("risk") || userMessage.toLowerCase().includes("safe")) {
      responseContent += "- Current portfolio risk: LOW\n- Guardian monitoring all positions\n- All stop-losses in place"
    } else if (userMessage.toLowerCase().includes("market") || userMessage.toLowerCase().includes("opportunity")) {
      responseContent += "- Scout detected 2 opportunities\n- BTC/ETH spread at -2.1σ (buy signal)\n- SOL/USDC showing momentum"
    } else {
      responseContent += "- Trade execution ready\n- Risk management active\n- Market scanning operational"
    }

    addChatMessage({
      role: "assistant",
      content: responseContent,
    })

    setIsLoading(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Render message content with bullet point support
  const renderContent = (content: string) => {
    return content.split("\n").map((line, i) => {
      const isBullet = line.startsWith("- ")
      return (
        <p key={i} className={cn(i > 0 && "mt-1")}>
          {isBullet ? (
            <span className="flex items-start gap-2">
              <span className="text-[#30D158] mt-0.5">•</span>
              <span>{line.slice(2)}</span>
            </span>
          ) : (
            line
          )}
        </p>
      )
    })
  }

  return (
    <GlassCard className="h-full flex flex-col p-0 overflow-hidden min-h-[400px]">
      {/* Chat Messages */}
      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        <div className="space-y-4">
          {chatMessages.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm font-medium">AI Trading Orchestrator</p>
              <p className="text-xs mt-1 opacity-70">Ask me to analyze markets or execute trades</p>
            </div>
          )}

          {chatMessages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3",
                message.role === "user" ? "flex-row-reverse" : "flex-row"
              )}
            >
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center shrink-0",
                message.role === "user" ? "bg-white text-black" : "bg-[#30D158]/20"
              )}>
                {message.role === "user" ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Bot className="w-4 h-4 text-[#30D158]" />
                )}
              </div>

              <div className={cn(
                "max-w-[85%] rounded-lg p-3 text-sm",
                message.role === "user"
                  ? "bg-white text-black ml-auto"
                  : "bg-secondary/50"
              )}>
                {renderContent(message.content)}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#30D158]/20 flex items-center justify-center">
                <Bot className="w-4 h-4 text-[#30D158]" />
              </div>
              <div className="bg-secondary/50 rounded-lg p-3">
                <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t border-white/5">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Talk to the orchestrator..."
            className="flex-1 bg-secondary/50 border-white/10"
            disabled={isLoading}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="bg-white text-black hover:bg-white/90 disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </GlassCard>
  )
}
