'use client';

import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { AuthGuard } from "@/components/auth-guard"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <SidebarProvider>
        {/* Changed bg-slate-950 to bg-background to sync with sidebar */}
        <div className="flex min-h-screen w-full bg-background text-foreground">
          <AppSidebar />
          
          <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
            {/* Muted the header border and background */}
            <header className="flex h-14 items-center gap-4 border-b border-border bg-background/95 backdrop-blur px-6 shrink-0">
              <SidebarTrigger className="text-muted-foreground hover:text-foreground" />
              <h1 className="font-medium text-sm text-muted-foreground tracking-wide uppercase">SiteScout Intelligence</h1>
            </header>
            
            <div className="flex-1 overflow-auto bg-background">
              {children}
            </div>
          </main>
        </div>
      </SidebarProvider>
    </AuthGuard>
  )
}