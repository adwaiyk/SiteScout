"use client";

import { useState } from "react";
import Link from "next/link";
import axios from "axios";
import { Loader2, GalleryVerticalEnd } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SignupPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");

  const API_URL = "http://127.0.0.1:8000";

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    setSuccess("");

    try {
      await axios.post(`${API_URL}/auth/register`, {
        email: email,
        password: password,
        full_name: fullName,
        role: "planner",
        organization: "Independent", // Add this field to satisfy your backend schema requirements!
      });
      setSuccess("Account created successfully! Redirecting to login...");
      setTimeout(() => {
        window.location.href = "/";
      }, 2000);
    } catch (err: any) {
      // Enhanced error handling to show what the backend is actually complaining about
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.status === 422) {
        setError(
          "Validation Error: Frontend payload fields do not match backend model expectations.",
        );
        console.error("Pydantic Validation Logs:", err.response.data);
      } else {
        setError("Registration failed. Please try again.");
      }
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden bg-muted lg:block">
        <div className="absolute inset-0 bg-slate-800 flex flex-col justify-end p-10 text-white">
          <blockquote className="space-y-2">
            <p className="text-lg">
              &ldquo;Empowering field analysts and planners with unified,
              production-grade spatial intelligence.&rdquo;
            </p>
          </blockquote>
        </div>
      </div>
      <div className="flex flex-col gap-4 p-6 md:p-10 justify-center items-center">
        <div className="w-full max-w-sm space-y-6">
          <div className="flex items-center gap-2 font-medium">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <GalleryVerticalEnd className="size-4" />
            </div>
            SiteScout
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl font-bold tracking-tight">
              Create an account
            </h1>
            <p className="text-sm text-muted-foreground">
              Enter your details below to set up your profile
            </p>
          </div>

          <form onSubmit={handleSignup} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                placeholder="John Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && (
              <p className="text-sm font-medium text-destructive">{error}</p>
            )}
            {success && (
              <p className="text-sm font-medium text-emerald-500">{success}</p>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                "Sign Up"
              )}
            </Button>
          </form>

          <div className="text-center text-sm">
            Already have an account?{" "}
            <Link
              href="/"
              className="underline underline-offset-4 hover:text-primary"
            >
              Log in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}