"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Loader2, GalleryVerticalEnd, Eye, EyeOff, ArrowRight, Zap, Globe2, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [authLoading, isAuthenticated, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid email or password.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!mounted || authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (isAuthenticated) return null;

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {}
      <div className="flex flex-col gap-4 p-6 md:p-10 justify-center items-center relative overflow-hidden">
        {}
        <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/5 pointer-events-none" />
        
        <div className="w-full max-w-sm space-y-6 relative z-10">
          {}
          <div className="flex items-center gap-2.5 font-semibold text-lg">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-600/25">
              <GalleryVerticalEnd className="size-4" />
            </div>
            <span className="tracking-tight">SiteScout</span>
          </div>
          
          <div className="space-y-2">
            <h1 className="text-2xl font-bold tracking-tight">Welcome back</h1>
            <p className="text-sm text-muted-foreground">
              Sign in to access your deployment intelligence dashboard
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="login-email">Email</Label>
              <Input
                id="login-email"
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="h-10 transition-all duration-200 focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="login-password">Password</Label>
              </div>
              <div className="relative">
                <Input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="h-10 pr-10 transition-all duration-200 focus:ring-2 focus:ring-primary/20"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  tabIndex={-1}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            
            {error && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                <p className="text-sm font-medium text-destructive">{error}</p>
              </div>
            )}

            <Button type="submit" className="w-full h-10 font-medium transition-all duration-200" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign in
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </form>

          <div className="text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="font-medium text-foreground underline underline-offset-4 hover:text-primary transition-colors">
              Create account
            </Link>
          </div>
        </div>
      </div>

      {}
      <div className="relative hidden bg-muted lg:block overflow-hidden">
        {}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950" />
        
        {}
        <div className="absolute inset-0 opacity-[0.07]" style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }} />
        
        {}
        <div className="absolute top-1/4 left-1/4 h-64 w-64 rounded-full bg-blue-500/20 blur-[100px] animate-pulse" />
        <div className="absolute bottom-1/3 right-1/4 h-48 w-48 rounded-full bg-indigo-500/20 blur-[80px] animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 right-1/3 h-32 w-32 rounded-full bg-cyan-500/15 blur-[60px] animate-pulse" style={{ animationDelay: '2s' }} />
        
        {}
        <div className="absolute inset-0 flex flex-col justify-between p-10 text-white">
          {}
          <div className="flex-1 flex flex-col justify-center space-y-6">
            <div className="space-y-3">
              <h2 className="text-3xl font-bold tracking-tight">Spatial Intelligence,<br />Redefined.</h2>
              <p className="text-sm text-slate-400 max-w-md">
                Multi-objective optimization for renewable energy site selection, powered by real-time climate and infrastructure data.
              </p>
            </div>
            
            {}
            <div className="space-y-3 max-w-sm">
              {[
                { icon: Globe2, label: "GIS-Powered Site Scanning", desc: "NASA climate + infrastructure data" },
                { icon: BarChart3, label: "ML Yield Predictions", desc: "Solar & wind capacity forecasting" },
                { icon: Zap, label: "Infrastructure Analysis", desc: "Grid proximity & land-use screening" },
              ].map((feat, i) => (
                <div
                  key={feat.label}
                  className="flex items-start gap-3 p-3 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm transition-all duration-300 hover:bg-white/10"
                  style={{ animationDelay: `${i * 150}ms` }}
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-blue-500/20 text-blue-400">
                    <feat.icon className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">{feat.label}</p>
                    <p className="text-xs text-slate-500">{feat.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {}
          <blockquote className="space-y-2 border-t border-white/10 pt-6">
            <p className="text-sm text-slate-400 leading-relaxed">
              &ldquo;SiteScout optimizes our deployment selection pipeline, bringing multi-objective frontier intelligence to core planning processes.&rdquo;
            </p>
            <footer className="text-xs text-slate-600">Infosys AI Domain Platform</footer>
          </blockquote>
        </div>
      </div>
    </div>
  );
}