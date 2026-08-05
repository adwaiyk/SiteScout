'use client';

import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { AuthGuard } from "@/components/auth-guard"
import { useTheme } from "@/context/theme-context"
import { Sun, Moon } from "lucide-react"

function ThemeToggleButton() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      id="theme-toggle-btn"
      onClick={toggleTheme}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className={[
        "ml-auto flex items-center justify-center",
        "h-8 w-8 rounded-lg border border-border",
        "bg-card text-muted-foreground",
        "hover:bg-accent hover:text-accent-foreground",
        "transition-all duration-200 ease-in-out",
        "focus:outline-none focus:ring-2 focus:ring-ring/50",
        "active:scale-95",
      ].join(" ")}
    >
      <span
        className="transition-transform duration-300 ease-in-out"
        style={{ transform: isDark ? "rotate(0deg)" : "rotate(180deg)" }}
      >
        {isDark ? (
          <Sun className="h-4 w-4" />
        ) : (
          <Moon className="h-4 w-4" />
        )}
      </span>
    </button>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <SidebarProvider>
        <div className="flex min-h-screen w-full bg-background text-foreground">
          <AppSidebar />

          <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
            <header className="flex h-14 items-center gap-4 border-b border-border bg-background/95 backdrop-blur px-6 shrink-0">
              <SidebarTrigger className="text-muted-foreground hover:text-foreground" />
              <h1 className="font-medium text-sm text-muted-foreground tracking-wide uppercase">
                SiteScout Intelligence
              </h1>
              <ThemeToggleButton />
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