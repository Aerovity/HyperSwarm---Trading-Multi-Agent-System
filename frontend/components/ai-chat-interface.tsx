"use client"

import { useState, useRef, useEffect } from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { TextShimmer } from "@/components/ui/text-shimmer"
import { useDemoContext } from "@/lib/demo-context"
import { orchestratorApi } from "@/lib/api"
import { Bot, User, Send, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import ReactMarkdown from 'react-markdown'

export function AIChatInterface() {
  const { chatMessages, addChatMessage } = useDemoContext()
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string>()
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

    try {
      // Call real orchestrator API
      const response = await orchestratorApi.chat({
        message: userMessage,
        conversation_id: conversationId,
        user_address: "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb" // Demo address
      })

      // Update conversation ID
      setConversationId(response.conversation_id)

      // Add AI response
      addChatMessage({
        role: "assistant",
        content: response.message,
      })
    } catch (error) {
      console.error("Chat error:", error)
      // Add error message
      addChatMessage({
        role: "assistant",
        content: "❌ Sorry, I encountered an error. Please make sure the orchestrator backend is running on port 8005.",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Render message content with markdown support
  const renderContent = (content: string) => {
    return (
      <div className="prose prose-sm prose-invert max-w-none">
        <ReactMarkdown
          components={{
            h1: ({ children }) => <h1 className="text-lg font-bold mt-2 mb-1">{children}</h1>,
            h2: ({ children }) => <h2 className="text-base font-bold mt-2 mb-1">{children}</h2>,
            h3: ({ children }) => <h3 className="text-sm font-bold mt-1 mb-1">{children}</h3>,
            p: ({ children }) => <p className="my-1">{children}</p>,
            ul: ({ children }) => <ul className="list-disc list-inside my-1">{children}</ul>,
            li: ({ children }) => (
              <li className="flex items-start gap-2">
                <span className="text-[#30D158] mt-0.5">•</span>
                <span className="flex-1">{children}</span>
              </li>
            ),
            strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
            em: ({ children }) => <em className="italic">{children}</em>,
            code: ({ children }) => (
              <code className="bg-black/30 px-1 py-0.5 rounded text-xs">{children}</code>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    )
  }

  return (
    <GlassCard className="h-full flex flex-col p-0 overflow-hidden">
      {/* Chat Messages */}
      <ScrollArea ref={scrollRef} className="flex-1 min-h-0 p-4">
        <div className="space-y-4 pb-4">
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
                <TextShimmer duration={1.2} className="text-sm">
                  Processing your request...
                </TextShimmer>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="flex-shrink-0 p-4 border-t border-white/5 bg-black/20">
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
