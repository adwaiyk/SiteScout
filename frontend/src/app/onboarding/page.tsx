"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import {
  Loader2,
  Globe2,
  BarChart3,
  FolderKanban,
  Zap,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  CheckCircle2,
  MapPin,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";

// ---------- Step Data ----------
const FEATURES = [
  {
    icon: Globe2,
    title: "Feasibility Scanner",
    desc: "Click anywhere on the interactive map to instantly analyze solar and wind potential using real NASA climate data.",
    color: "from-blue-500 to-cyan-500",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
  },
  {
    icon: FolderKanban,
    title: "Project Management",
    desc: "Save scanned sites into organized projects. Track multiple deployments across different regions.",
    color: "from-indigo-500 to-purple-500",
    bg: "bg-indigo-500/10",
    text: "text-indigo-400",
  },
  {
    icon: BarChart3,
    title: "ML-Powered Analytics",
    desc: "Get capacity factor predictions, energy yield estimates, and infrastructure proximity reports — all powered by machine learning.",
    color: "from-emerald-500 to-green-500",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
  },
];

export default function OnboardingPage() {
  const [step, setStep] = useState(0);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  // Skip onboarding if already completed
  useEffect(() => {
    if (mounted && localStorage.getItem("onboarding_complete") === "true") {
      router.replace("/dashboard");
    }
  }, [mounted, router]);

  const handleComplete = () => {
    localStorage.setItem("onboarding_complete", "true");
    router.replace("/dashboard");
  };

  const handleSkip = () => {
    localStorage.setItem("onboarding_complete", "true");
    router.replace("/dashboard");
  };

  if (!mounted || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  const firstName = user?.name?.split(" ")[0] || "there";

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/3 pointer-events-none" />
      <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-blue-500/5 blur-[150px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 h-64 w-64 rounded-full bg-indigo-500/5 blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between p-6 md:px-10">
        <div className="flex items-center gap-2.5 font-semibold text-lg">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-600/25">
            <Sparkles className="size-4" />
          </div>
          <span className="tracking-tight">SiteScout</span>
        </div>
        <Button variant="ghost" size="sm" onClick={handleSkip} className="text-muted-foreground hover:text-foreground">
          Skip setup
        </Button>
      </header>

      {/* Main content */}
      <div className="relative z-10 flex flex-col items-center justify-center px-6 pb-12" style={{ minHeight: 'calc(100vh - 80px)' }}>
        <div className="w-full max-w-2xl">
          {/* Step indicator */}
          <div className="flex items-center justify-center gap-2 mb-10">
            {[0, 1, 2].map((s) => (
              <button
                key={s}
                onClick={() => setStep(s)}
                className={`h-2 rounded-full transition-all duration-500 ${
                  s === step ? "w-8 bg-primary" : s < step ? "w-2 bg-primary/50" : "w-2 bg-muted"
                }`}
                aria-label={`Go to step ${s + 1}`}
              />
            ))}
          </div>

          {/* ===== STEP 0: Welcome ===== */}
          {step === 0 && (
            <div className="text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Animated welcome icon */}
              <div className="mx-auto relative">
                <div className="h-20 w-20 mx-auto rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-xl shadow-blue-600/20">
                  <span className="text-3xl">👋</span>
                </div>
                <div className="absolute -inset-4 rounded-3xl bg-blue-500/10 blur-xl -z-10" />
              </div>

              <div className="space-y-3">
                <h1 className="text-4xl font-bold tracking-tight">
                  Welcome, {firstName}!
                </h1>
                <p className="text-lg text-muted-foreground max-w-md mx-auto leading-relaxed">
                  You&apos;re now part of SiteScout — the AI-powered platform for renewable energy site intelligence.
                </p>
              </div>

              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-sm font-medium">
                <CheckCircle2 className="h-4 w-4" />
                Account created successfully
              </div>

              <div className="pt-2">
                <Button size="lg" onClick={() => setStep(1)} className="h-12 px-8 font-medium shadow-lg shadow-primary/20">
                  Let&apos;s get started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* ===== STEP 1: Feature Tour ===== */}
          {step === 1 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">What you can do</h2>
                <p className="text-muted-foreground">
                  Here&apos;s a quick look at SiteScout&apos;s core capabilities
                </p>
              </div>

              <div className="grid gap-4">
                {FEATURES.map((feat, i) => (
                  <div
                    key={feat.title}
                    className="group flex items-start gap-4 p-5 rounded-xl border border-border bg-card/50 backdrop-blur-sm hover:bg-card hover:shadow-lg hover:shadow-black/5 transition-all duration-300"
                    style={{ animationDelay: `${i * 100}ms` }}
                  >
                    <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${feat.bg} transition-transform duration-300 group-hover:scale-110`}>
                      <feat.icon className={`h-6 w-6 ${feat.text}`} />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-foreground mb-1">{feat.title}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">{feat.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-between pt-2">
                <Button variant="ghost" onClick={() => setStep(0)} className="gap-2">
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Button>
                <Button onClick={() => setStep(2)} className="gap-2 shadow-lg shadow-primary/20">
                  Next
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* ===== STEP 2: Get Started CTAs ===== */}
          {step === 2 && (
            <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Ready to explore?</h2>
                <p className="text-muted-foreground">
                  Pick your first action to dive into the platform
                </p>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                {/* Scan action */}
                <button
                  onClick={handleComplete}
                  className="group relative p-6 rounded-xl border border-border bg-card/50 backdrop-blur-sm hover:bg-card hover:shadow-xl hover:shadow-black/5 transition-all duration-300 text-left overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="relative z-10 space-y-4">
                    <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-blue-500/10">
                      <MapPin className="h-7 w-7 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg mb-1">Scan a Location</h3>
                      <p className="text-sm text-muted-foreground">
                        Open the Map Scanner and click anywhere to analyze solar & wind potential.
                      </p>
                    </div>
                    <div className="flex items-center gap-1.5 text-sm font-medium text-blue-400 group-hover:gap-2.5 transition-all duration-200">
                      Open Scanner
                      <ArrowRight className="h-4 w-4" />
                    </div>
                  </div>
                </button>

                {/* Create project action */}
                <button
                  onClick={handleComplete}
                  className="group relative p-6 rounded-xl border border-border bg-card/50 backdrop-blur-sm hover:bg-card hover:shadow-xl hover:shadow-black/5 transition-all duration-300 text-left overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="relative z-10 space-y-4">
                    <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-indigo-500/10">
                      <Plus className="h-7 w-7 text-indigo-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg mb-1">Create a Project</h3>
                      <p className="text-sm text-muted-foreground">
                        Set up your first project workspace to organize site evaluations.
                      </p>
                    </div>
                    <div className="flex items-center gap-1.5 text-sm font-medium text-indigo-400 group-hover:gap-2.5 transition-all duration-200">
                      Create Project
                      <ArrowRight className="h-4 w-4" />
                    </div>
                  </div>
                </button>
              </div>

              <div className="flex justify-between items-center pt-2">
                <Button variant="ghost" onClick={() => setStep(1)} className="gap-2">
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Button>
                <Button onClick={handleComplete} className="gap-2 font-medium shadow-lg shadow-primary/20">
                  <Zap className="h-4 w-4" />
                  Go to Dashboard
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
