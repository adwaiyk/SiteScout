"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { useTheme } from "@/context/theme-context";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Globe2,
  BarChart3,
  Zap,
  Shield,
  Loader2,
  Sun,
  Moon,
  TrendingUp,
  Brain,
  Leaf,
} from "lucide-react";

const FEATURES = [
  {
    icon: Globe2,
    title: "GIS-Powered Scanning",
    desc: "Click anywhere on the map to analyze solar and wind potential using real-time NASA POWER data and OSM infrastructure.",
    gradient: "from-teal-500/20 to-cyan-500/20",
    iconColor: "text-teal-500",
  },
  {
    icon: BarChart3,
    title: "ML Yield Predictions",
    desc: "XGBoost models predict capacity factors, energy output, with SHAP explainability for every factor.",
    gradient: "from-amber-500/20 to-orange-500/20",
    iconColor: "text-amber-500",
  },
  {
    icon: Shield,
    title: "Land-Use Screening",
    desc: "Automatic conflict detection flags restricted zones, protected areas, and infrastructure proximity.",
    gradient: "from-emerald-500/20 to-green-500/20",
    iconColor: "text-emerald-500",
  },
  {
    icon: TrendingUp,
    title: "Pareto Optimization",
    desc: "NSGA-II multi-objective optimization reveals trade-offs across energy, environment, and cost.",
    gradient: "from-violet-500/20 to-purple-500/20",
    iconColor: "text-violet-500",
  },
  {
    icon: Brain,
    title: "AI Narratives",
    desc: "LLM-generated plain-English investment summaries grounded in real computed data.",
    gradient: "from-rose-500/20 to-pink-500/20",
    iconColor: "text-rose-500",
  },
  {
    icon: Leaf,
    title: "Financial Analysis",
    desc: "25-year NPV, LCOE, IRR, payback analysis with degradation modeling and P10/P50/P90 bands.",
    gradient: "from-sky-500/20 to-blue-500/20",
    iconColor: "text-sky-500",
  },
];

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      id="landing-theme-toggle"
      onClick={toggleTheme}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="flex items-center justify-center h-9 w-9 rounded-lg border border-border bg-card/50 backdrop-blur-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-all duration-200 active:scale-95"
    >
      <span className="transition-transform duration-300" style={{ transform: isDark ? "rotate(0deg)" : "rotate(180deg)" }}>
        {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </span>
    </button>
  );
}

export default function LandingPage() {
  const [mounted, setMounted] = useState(false);
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isLoading, isAuthenticated, router]);

  if (!mounted || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/5 pointer-events-none" />

      {/* Grid texture */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: "80px 80px",
        }}
      />

      {/* Glow orbs */}
      <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-primary/8 blur-[150px] animate-pulse pointer-events-none" />
      <div className="absolute bottom-1/3 right-1/4 h-64 w-64 rounded-full bg-chart-2/8 blur-[120px] animate-pulse pointer-events-none" style={{ animationDelay: "2s" }} />
      <div className="absolute top-1/2 left-1/2 h-48 w-48 rounded-full bg-chart-5/5 blur-[100px] animate-pulse pointer-events-none" style={{ animationDelay: "4s" }} />

      {/* Top bar with theme toggle */}
      <header className="relative z-20 flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Zap className="h-4 w-4" />
          </div>
          <span className="font-semibold text-sm text-foreground">SiteScout</span>
        </div>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Button asChild variant="ghost" size="sm" className="text-sm">
            <Link href="/login">Sign In</Link>
          </Button>
        </div>
      </header>

      {/* Hero */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-[calc(100vh-80px)] p-6 text-center">
        <div className="max-w-5xl mx-auto space-y-12">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-sm font-medium text-primary">
            <Zap className="h-3.5 w-3.5" />
            Solar & Wind Deployment Intelligence
          </div>

          {/* Headline */}
          <div className="space-y-6">
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1]">
              Deploy Renewables{" "}
              <br />
              <span className="bg-gradient-to-r from-primary via-chart-1 to-chart-5 bg-clip-text text-transparent">
                With Confidence.
              </span>
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              SiteScout uses multi-objective optimization and spatial AI to help planners discover, evaluate, and select optimal locations for solar and wind infrastructure.
            </p>
          </div>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild size="lg" className="h-13 px-8 text-base font-medium shadow-xl shadow-primary/25 bg-primary hover:bg-primary/90">
              <Link href="/signup">
                Get Started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="h-13 px-8 text-base border-border hover:bg-accent">
              <Link href="/login">Sign in to Dashboard</Link>
            </Button>
          </div>

          {/* Feature grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-8 max-w-4xl mx-auto">
            {FEATURES.map((feat, i) => (
              <div
                key={feat.title}
                className="group p-5 rounded-xl border border-border bg-card/30 backdrop-blur-sm hover:bg-card/60 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300 text-left hover:-translate-y-0.5"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br ${feat.gradient} mb-3 transition-transform duration-300 group-hover:scale-110`}>
                  <feat.icon className={`h-5 w-5 ${feat.iconColor}`} />
                </div>
                <h3 className="font-semibold text-sm mb-1 text-foreground">{feat.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>

          {/* Bottom tagline */}
          <p className="text-xs text-muted-foreground pt-6">
            Built for the Infosys Springboard Internship 2026 · Powered by NASA POWER, OpenStreetMap, XGBoost & NSGA-II
          </p>
        </div>
      </div>
    </div>
  );
}