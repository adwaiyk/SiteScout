"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Globe2,
  BarChart3,
  Zap,
  Shield,
  Loader2,
} from "lucide-react";

const FEATURES = [
  {
    icon: Globe2,
    title: "GIS-Powered Scanning",
    desc: "Click anywhere on the map to analyze solar and wind potential using real-time NASA POWER data.",
    gradient: "from-blue-500/20 to-cyan-500/20",
    iconColor: "text-blue-400",
  },
  {
    icon: BarChart3,
    title: "ML Yield Predictions",
    desc: "Machine learning models predict capacity factors, annual energy output, and LCOE estimates.",
    gradient: "from-indigo-500/20 to-purple-500/20",
    iconColor: "text-indigo-400",
  },
  {
    icon: Shield,
    title: "Land-Use Screening",
    desc: "Automatic conflict detection flags restricted zones, protected areas, and infrastructure proximity.",
    gradient: "from-emerald-500/20 to-green-500/20",
    iconColor: "text-emerald-400",
  },
];

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
      {/* Animated background */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-blue-950/20 pointer-events-none" />
      
      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: "80px 80px",
        }}
      />

      {/* Floating glow orbs */}
      <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-blue-500/8 blur-[150px] animate-pulse pointer-events-none" />
      <div
        className="absolute bottom-1/3 right-1/4 h-64 w-64 rounded-full bg-indigo-500/8 blur-[120px] animate-pulse pointer-events-none"
        style={{ animationDelay: "2s" }}
      />
      <div
        className="absolute top-1/2 left-1/2 h-48 w-48 rounded-full bg-cyan-500/5 blur-[100px] animate-pulse pointer-events-none"
        style={{ animationDelay: "4s" }}
      />

      {/* Hero */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen p-6 text-center">
        <div className="max-w-4xl mx-auto space-y-12">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-sm font-medium text-primary">
            <Zap className="h-3.5 w-3.5" />
            SiteScout
          </div>

          {/* Title */}
          <div className="space-y-6">
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight">
              Deploy Renewables{" "}
              <br />
              <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
                With Confidence.
              </span>
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              SiteScout uses multi-objective optimization and spatial AI to help planners discover, evaluate, and select the optimal locations for solar and wind infrastructure.
            </p>
          </div>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild size="lg" className="h-13 px-8 text-base font-medium shadow-xl shadow-primary/20">
              <Link href="/signup">
                Get Started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="h-13 px-8 text-base">
              <Link href="/login">Sign in to Dashboard</Link>
            </Button>
          </div>

          {/* Feature cards */}
          <div className="grid sm:grid-cols-3 gap-4 pt-8 max-w-3xl mx-auto">
            {FEATURES.map((feat, i) => (
              <div
                key={feat.title}
                className="group p-5 rounded-xl border border-border bg-card/30 backdrop-blur-sm hover:bg-card/60 hover:shadow-lg hover:shadow-black/5 transition-all duration-300 text-left"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br ${feat.gradient} mb-3 transition-transform duration-300 group-hover:scale-110`}>
                  <feat.icon className={`h-5 w-5 ${feat.iconColor}`} />
                </div>
                <h3 className="font-semibold text-sm mb-1">{feat.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}