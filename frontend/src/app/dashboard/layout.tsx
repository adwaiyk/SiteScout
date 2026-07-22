'use client';

import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-slate-950">
        {/* The Custom SiteScout Sidebar */}
        <AppSidebar />
        
        {/* Main Content Area */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Top Header for Sidebar Trigger and Context */}
          <header className="flex h-14 items-center gap-4 border-b border-slate-800 bg-slate-900/50 px-6 shrink-0">
            <SidebarTrigger className="text-slate-300 hover:text-white" />
            <h1 className="font-semibold text-lg text-slate-200">SiteScout Intelligence Platform</h1>
          </header>
          
          {/* The actual page content (Map Scanner or My Projects) */}
          <div className="flex-1 overflow-auto bg-slate-900">
            {children}
          </div>
        </main>
      </div>
    </SidebarProvider>
  )
}