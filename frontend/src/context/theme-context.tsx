"use client";

/**
 * SiteScout — Theme Context
 *
 * Provides dark / light mode toggle with:
 *  - localStorage persistence across sessions
 *  - SSR-safe initialization (suppresses hydration mismatch)
 *  - Default: dark mode for first-time visitors
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";

type Theme = "dark" | "light";

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = "sitescout-theme";
const DEFAULT_THEME: Theme = "dark";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Start with default to avoid SSR mismatch — real value applied in useEffect
  const [theme, setThemeState] = useState<Theme>(DEFAULT_THEME);
  const [mounted, setMounted] = useState(false);

  // On mount: read stored preference or system preference
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
    let resolved: Theme;

    if (stored === "dark" || stored === "light") {
      resolved = stored;
    } else if (
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-color-scheme: light)").matches
    ) {
      resolved = "light";
    } else {
      resolved = DEFAULT_THEME;
    }

    setThemeState(resolved);
    setMounted(true);
  }, []);

  // Sync theme class to <html> whenever theme changes
  useEffect(() => {
    if (!mounted) return;
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
      root.classList.remove("light");
    } else {
      root.classList.remove("dark");
      root.classList.add("light");
    }
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme, mounted]);

  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme);
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeState((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
