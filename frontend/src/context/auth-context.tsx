"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

interface User {
  name: string;
  email: string;
  role?: string;
  organization?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => void;
}

interface SignupData {
  email: string;
  password: string;
  full_name: string;
  role: string;
  organization: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      
      const cachedName = localStorage.getItem("userName");
      const cachedEmail = localStorage.getItem("userEmail");
      if (cachedName && cachedEmail) {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setUser({ name: cachedName, email: cachedEmail });
      }

      api
        .get("/auth/me")
        .then((res) => {
          const freshUser: User = {
            name: res.data.full_name || cachedName || "SiteScout User",
            email: res.data.email || cachedEmail || "",
            role: res.data.role,
            organization: res.data.organization,
          };
          setUser(freshUser);
          localStorage.setItem("userName", freshUser.name);
          localStorage.setItem("userEmail", freshUser.email);
        })
        .catch(() => {
          
          localStorage.removeItem("token");
          localStorage.removeItem("userName");
          localStorage.removeItem("userEmail");
          setUser(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const response = await api.post("/auth/login", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      const { access_token, username, email: userEmail, full_name } = response.data;

      localStorage.setItem("token", access_token);
      localStorage.setItem("userName", username || full_name || "SiteScout User");
      localStorage.setItem("userEmail", userEmail || email);

      setUser({
        name: username || full_name || "SiteScout User",
        email: userEmail || email,
      });

      router.replace("/dashboard");
    },
    [router]
  );

  const signup = useCallback(
    async (data: SignupData) => {
      const response = await api.post("/auth/register", {
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        role: data.role,
        organization: data.organization,
      });

      const { access_token, username, email: userEmail, full_name } = response.data;

      localStorage.setItem("token", access_token);
      localStorage.setItem("userName", username || full_name || data.full_name);
      localStorage.setItem("userEmail", userEmail || data.email);

      setUser({
        name: username || full_name || data.full_name,
        email: userEmail || data.email,
      });

      router.replace("/onboarding");
    },
    [router]
  );

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("userName");
    localStorage.removeItem("userEmail");
    localStorage.removeItem("onboarding_complete");
    localStorage.removeItem("lastActiveProjectId");
    setUser(null);
    router.replace("/login");
  }, [router]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
