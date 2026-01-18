"use client"

import { ReactNode } from "react"
import { AppSidebar } from "@/components/app-sidebar"
import { BottomNav } from "@/components/bottom-nav"
import { OnboardingTour } from "@/components/onboarding-tour"

interface AppLayoutProps {
  children: ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen">
      {/* Desktop Sidebar */}
      <AppSidebar />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-h-screen pb-16 lg:pb-0">
        {children}
      </main>

      {/* Mobile Bottom Navigation */}
      <BottomNav />

      {/* Onboarding Tour */}
      <OnboardingTour />
    </div>
  )
}
