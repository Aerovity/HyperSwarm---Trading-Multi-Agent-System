"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { X, ArrowRight, ArrowLeft, Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"

interface TourStep {
  target: string
  title: string
  description: string
  position: "top" | "bottom" | "left" | "right"
}

const tourSteps: TourStep[] = [
  {
    target: "body",
    title: "Welcome to HyperSwarm!",
    description: "Let's take a quick tour of your AI-powered trading dashboard. This will only take a minute.",
    position: "bottom",
  },
  {
    target: "[data-tour='sidebar']",
    title: "Navigation",
    description: "Use the sidebar to navigate between Dashboard, Trade, Activity Logs, and Settings.",
    position: "right",
  },
  {
    target: "[data-tour='agents']",
    title: "Your AI Agents",
    description: "These are your trading agents. Scout finds opportunities, Guardian manages risk, Executor handles trades, and Onboarder bridges assets.",
    position: "bottom",
  },
  {
    target: "[data-tour='market']",
    title: "Market Scanner",
    description: "Scout Agent monitors markets here. Watch for Z-Score signals - below -2 suggests buying opportunities, above +2 suggests selling.",
    position: "bottom",
  },
  {
    target: "[data-tour='trade']",
    title: "Execute Trades",
    description: "Head to the Trade page to execute pair trades. Guardian will assess risk before any trade is approved.",
    position: "bottom",
  },
]

export function OnboardingTour() {
  const [isOpen, setIsOpen] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Check if user has completed the tour
    const hasCompletedTour = localStorage.getItem("hyperswarm-tour-completed")
    if (!hasCompletedTour) {
      // Small delay to let the page render
      const timer = setTimeout(() => setIsOpen(true), 1000)
      return () => clearTimeout(timer)
    }
  }, [])

  const handleNext = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      completeTour()
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const completeTour = () => {
    localStorage.setItem("hyperswarm-tour-completed", "true")
    setIsOpen(false)
  }

  const skipTour = () => {
    localStorage.setItem("hyperswarm-tour-completed", "true")
    setIsOpen(false)
  }

  if (!mounted || !isOpen) return null

  const step = tourSteps[currentStep]
  const isFirstStep = currentStep === 0
  const isLastStep = currentStep === tourSteps.length - 1

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm" />

      {/* Tour Modal */}
      <div
        className={cn(
          "fixed z-[101] w-[90vw] max-w-md p-6 rounded-xl",
          "bg-card border border-white/10 shadow-2xl",
          // Center for welcome step, otherwise position near content
          isFirstStep && "top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2",
          !isFirstStep && "top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 lg:top-[30%] lg:left-[50%]"
        )}
      >
        {/* Close button */}
        <button
          onClick={skipTour}
          className="absolute top-4 right-4 text-muted-foreground hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Step indicator */}
        <div className="flex items-center gap-1 mb-4">
          {tourSteps.map((_, index) => (
            <div
              key={index}
              className={cn(
                "h-1 rounded-full transition-all duration-300",
                index === currentStep ? "w-6 bg-white" : "w-2 bg-white/20"
              )}
            />
          ))}
        </div>

        {/* Content */}
        <div className="space-y-3">
          {isFirstStep && (
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-white to-white/60 flex items-center justify-center mb-4">
              <Sparkles className="w-6 h-6 text-black" />
            </div>
          )}
          <h3 className="text-xl font-semibold">{step.title}</h3>
          <p className="text-muted-foreground leading-relaxed">{step.description}</p>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between mt-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={skipTour}
            className="text-muted-foreground hover:text-white"
          >
            Skip tour
          </Button>

          <div className="flex items-center gap-2">
            {!isFirstStep && (
              <Button
                variant="outline"
                size="sm"
                onClick={handlePrev}
                className="border-white/20"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Back
              </Button>
            )}
            <Button
              size="sm"
              onClick={handleNext}
              className="bg-white text-black hover:bg-white/90"
            >
              {isLastStep ? (
                "Get Started"
              ) : (
                <>
                  Next
                  <ArrowRight className="w-4 h-4 ml-1" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </>
  )
}
