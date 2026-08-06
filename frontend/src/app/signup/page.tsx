"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import {
  Loader2,
  GalleryVerticalEnd,
  Eye,
  EyeOff,
  ArrowRight,
  ArrowLeft,
  Check,
  Shield,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function getPasswordStrength(pw: string): { score: number; label: string; color: string } {
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;

  if (score <= 1) return { score, label: "Weak", color: "bg-red-500" };
  if (score <= 2) return { score, label: "Fair", color: "bg-orange-500" };
  if (score <= 3) return { score, label: "Good", color: "bg-yellow-500" };
  if (score <= 4) return { score, label: "Strong", color: "bg-emerald-500" };
  return { score, label: "Excellent", color: "bg-emerald-400" };
}

const ROLES = [
  { value: "planner", label: "Site Planner", desc: "Evaluate and select deployment locations", icon: "🗺️" },
  { value: "gis_analyst", label: "GIS Analyst", desc: "Perform spatial analysis and mapping", icon: "📊" },
  { value: "project_manager", label: "Project Manager", desc: "Oversee project portfolios and reports", icon: "📋" },
];

export default function SignupPage() {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [mounted, setMounted] = useState(false);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [role, setRole] = useState("planner");
  const [organization, setOrganization] = useState("");

  const router = useRouter();
  const { signup, isAuthenticated, isLoading: authLoading } = useAuth();

  const passwordStrength = useMemo(() => getPasswordStrength(password), [password]);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [authLoading, isAuthenticated, router]);

  const isStep1Valid = fullName.trim() !== "" && email.trim() !== "" && password.length >= 8;

  const handleNextStep = (e: React.FormEvent) => {
    e.preventDefault();
    if (isStep1Valid) {
      setError("");
      setStep(2);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      await signup({
        email,
        password,
        full_name: fullName,
        role,
        organization: organization || "Independent",
      });
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.status === 422) {
        setError("Validation error. Please check your inputs.");
        console.error("Pydantic Validation Logs:", err.response.data);
      } else {
        setError("Registration failed. Please try again.");
      }
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
      <div className="relative hidden bg-muted lg:block overflow-hidden">
        {}
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-950 via-blue-950 to-slate-900" />

        {}
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: "60px 60px",
          }}
        />

        {}
        <div className="absolute top-1/3 left-1/3 h-72 w-72 rounded-full bg-indigo-500/20 blur-[120px] animate-pulse" />
        <div
          className="absolute bottom-1/4 right-1/4 h-48 w-48 rounded-full bg-blue-500/20 blur-[80px] animate-pulse"
          style={{ animationDelay: "1.5s" }}
        />

        {}
        <div className="absolute inset-0 flex flex-col justify-between p-10 text-white">
          <div className="flex-1 flex flex-col justify-center space-y-6">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/10 text-xs font-medium text-blue-300 backdrop-blur-sm">
                <Sparkles className="h-3 w-3" />
                Free to get started
              </div>
              <h2 className="text-3xl font-bold tracking-tight">
                Start Deploying
                <br />
                Smarter, Today.
              </h2>
              <p className="text-sm text-slate-400 max-w-md">
                Join teams using AI-powered spatial intelligence to identify optimal renewable energy deployment sites.
              </p>
            </div>

            {}
            <div className="space-y-3 max-w-xs">
              {[
                "ML-powered solar & wind yield forecasting",
                "Real-time NASA climate data integration",
                "Infrastructure proximity analysis",
              ].map((item) => (
                <div key={item} className="flex items-center gap-3">
                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
                    <Check className="h-3 w-3" />
                  </div>
                  <p className="text-sm text-slate-400">{item}</p>
                </div>
              ))}
            </div>
          </div>

          <blockquote className="space-y-2 border-t border-white/10 pt-6">
            <p className="text-sm text-slate-400 leading-relaxed">
              &ldquo;Empowering field analysts and planners with unified, production-grade spatial intelligence.&rdquo;
            </p>
            <footer className="text-xs text-slate-600">Infosys AI Domain Platform</footer>
          </blockquote>
        </div>
      </div>

      {}
      <div className="flex flex-col gap-4 p-6 md:p-10 justify-center items-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/5 pointer-events-none" />

        <div className="w-full max-w-sm space-y-6 relative z-10">
          {}
          <div className="flex items-center gap-2.5 font-semibold text-lg">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-600/25">
              <GalleryVerticalEnd className="size-4" />
            </div>
            <span className="tracking-tight">SiteScout</span>
          </div>

          {}
          <div className="flex items-center gap-3">
            {[1, 2].map((s) => (
              <div key={s} className="flex items-center gap-2">
                <div
                  className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-semibold transition-all duration-300 ${
                    step >= s
                      ? "bg-primary text-primary-foreground shadow-md shadow-primary/25"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {step > s ? <Check className="h-4 w-4" /> : s}
                </div>
                <span className={`text-xs font-medium ${step >= s ? "text-foreground" : "text-muted-foreground"}`}>
                  {s === 1 ? "Identity" : "Profile"}
                </span>
                {s === 1 && (
                  <div className="flex-1 h-px bg-border mx-2 min-w-[2rem]">
                    <div
                      className={`h-full transition-all duration-500 ${step >= 2 ? "bg-primary w-full" : "bg-transparent w-0"}`}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>

          {}
          {step === 1 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="space-y-2 mb-6">
                <h1 className="text-2xl font-bold tracking-tight">Create your account</h1>
                <p className="text-sm text-muted-foreground">Enter your details to get started</p>
              </div>

              <form onSubmit={handleNextStep} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="signup-name">Full Name</Label>
                  <Input
                    id="signup-name"
                    placeholder="Jane Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    className="h-10 transition-all duration-200 focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="signup-email">Email</Label>
                  <Input
                    id="signup-email"
                    type="email"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="h-10 transition-all duration-200 focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="signup-password">Password</Label>
                  <div className="relative">
                    <Input
                      id="signup-password"
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      minLength={8}
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

                  {}
                  {password.length > 0 && (
                    <div className="space-y-1.5 animate-in fade-in duration-200">
                      <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map((seg) => (
                          <div
                            key={seg}
                            className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                              seg <= passwordStrength.score ? passwordStrength.color : "bg-muted"
                            }`}
                          />
                        ))}
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Shield className="h-3 w-3 text-muted-foreground" />
                        <p className="text-xs text-muted-foreground">
                          Password strength: <span className="font-medium text-foreground">{passwordStrength.label}</span>
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <Button type="submit" className="w-full h-10 font-medium" disabled={!isStep1Valid}>
                  Continue
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </form>
            </div>
          )}

          {}
          {step === 2 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="space-y-2 mb-6">
                <h1 className="text-2xl font-bold tracking-tight">Set up your profile</h1>
                <p className="text-sm text-muted-foreground">Tell us about your role so we can personalize your experience</p>
              </div>

              <form onSubmit={handleSignup} className="space-y-4">
                {}
                <div className="space-y-2">
                  <Label>Your Role</Label>
                  <div className="space-y-2">
                    {ROLES.map((r) => (
                      <label
                        key={r.value}
                        className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                          role === r.value
                            ? "border-primary bg-primary/5 shadow-sm shadow-primary/10"
                            : "border-border hover:border-muted-foreground/30 hover:bg-muted/50"
                        }`}
                      >
                        <input
                          type="radio"
                          name="role"
                          value={r.value}
                          checked={role === r.value}
                          onChange={(e) => setRole(e.target.value)}
                          className="sr-only"
                        />
                        <span className="text-lg mt-0.5">{r.icon}</span>
                        <div className="flex-1">
                          <p className="text-sm font-medium">{r.label}</p>
                          <p className="text-xs text-muted-foreground">{r.desc}</p>
                        </div>
                        {role === r.value && (
                          <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground mt-0.5">
                            <Check className="h-3 w-3" />
                          </div>
                        )}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="signup-org">Organization</Label>
                  <Input
                    id="signup-org"
                    placeholder="Acme Energy Corp (optional)"
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                    className="h-10 transition-all duration-200 focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                {error && (
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                    <p className="text-sm font-medium text-destructive">{error}</p>
                  </div>
                )}

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep(1)}
                    className="h-10"
                  >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back
                  </Button>
                  <Button type="submit" className="flex-1 h-10 font-medium" disabled={isLoading}>
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Creating account...
                      </>
                    ) : (
                      <>
                        Create Account
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </div>
          )}

          <div className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-foreground underline underline-offset-4 hover:text-primary transition-colors">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}