"use client";

import { useState, useCallback, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Calculator,
  Loader2,
  Sun,
  Wind,
  Zap,
  DollarSign,
  TrendingUp,
} from "lucide-react";
import api from "@/lib/api";
import type { YieldCalculatorResponse } from "@/lib/types";

type EnergyType = "solar" | "wind" | "hybrid";

const SLIDER_CONFIG = [
  { key: "ghi_kwh_m2_day", label: "Solar Irradiance (GHI)", unit: "kWh/m²/day", min: 1, max: 8, step: 0.1, default: 5.2, icon: Sun, color: "accent-amber-500" },
  { key: "wind_speed_m_s", label: "Wind Speed (50m)", unit: "m/s", min: 0, max: 15, step: 0.1, default: 5.5, icon: Wind, color: "accent-cyan-500" },
  { key: "solar_capacity_mw", label: "Solar Capacity", unit: "MW", min: 0, max: 50, step: 0.5, default: 5.0, icon: Sun, color: "accent-amber-500" },
  { key: "wind_capacity_mw", label: "Wind Capacity", unit: "MW", min: 0, max: 50, step: 0.5, default: 3.0, icon: Wind, color: "accent-cyan-500" },
  { key: "fit_usd_per_mwh", label: "Tariff Rate", unit: "$/MWh", min: 20, max: 150, step: 1, default: 65, icon: DollarSign, color: "accent-emerald-500" },
  { key: "land_area_sqkm", label: "Land Area", unit: "km²", min: 0.5, max: 50, step: 0.5, default: 5.0, icon: Zap, color: "accent-violet-500" },
];

export default function YieldCalculatorPage() {
  const [params, setParams] = useState<Record<string, number>>({
    ghi_kwh_m2_day: 5.2,
    wind_speed_m_s: 5.5,
    solar_capacity_mw: 5.0,
    wind_capacity_mw: 3.0,
    fit_usd_per_mwh: 65,
    land_area_sqkm: 5.0,
    avg_temp_c: 28.0,
    slope_deg: 2.0,
  });

  const [energyType, setEnergyType] = useState<EnergyType>("hybrid");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<YieldCalculatorResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [debounceTimer, setDebounceTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const calculate = useCallback(async (p: Record<string, number>, et: EnergyType) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/api/analysis/yield-calculator", {
        ...p,
        energy_type: et,
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Calculation failed");
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-calculate on mount
  useEffect(() => {
    calculate(params, energyType);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSliderChange = (key: string, value: number) => {
    const newParams = { ...params, [key]: value };
    setParams(newParams);

    // Debounce API calls
    if (debounceTimer) clearTimeout(debounceTimer);
    const timer = setTimeout(() => calculate(newParams, energyType), 400);
    setDebounceTimer(timer);
  };

  const handleTypeChange = (type: EnergyType) => {
    setEnergyType(type);
    calculate(params, type);
  };

  const fin = result?.financial;
  const ey = result?.energy_yield;
  const ms = result?.micrositing;

  // Build yearly chart data from financial cash flows
  const yearlyChartData = fin?.yearly_cash_flows?.map((y) => ({
    year: `Y${y.year}`,
    revenue: y.revenue_usd / 1000,
    opex: y.opex_usd / 1000,
    netCF: y.net_cash_flow_usd / 1000,
    cumulative: y.cumulative_cash_flow_usd / 1000,
  })) || [];

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1400px] mx-auto min-h-[calc(100vh-3.5rem)]">
      {/* Header */}
      <header className="space-y-1">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
          <Calculator className="h-6 w-6 text-primary" />
          Yield Calculator
        </h2>
        <p className="text-sm text-muted-foreground">
          Adjust parameters in real-time to explore energy yield and financial outcomes.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Sliders */}
        <div className="lg:col-span-4 space-y-4">
          {/* Energy type selector */}
          <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Technology</p>
            <div className="flex gap-2">
              {(["solar", "wind", "hybrid"] as EnergyType[]).map((t) => (
                <button
                  key={t}
                  onClick={() => handleTypeChange(t)}
                  className={`flex-1 h-9 rounded-lg text-xs font-semibold transition-all capitalize ${
                    energyType === t
                      ? "bg-primary text-primary-foreground shadow-md"
                      : "bg-muted text-muted-foreground hover:bg-accent"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Sliders */}
          <div className="rounded-xl border border-border bg-card p-4 shadow-sm space-y-5">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Parameters</p>
            {SLIDER_CONFIG.map((s) => {
              // Skip irrelevant sliders
              if (energyType === "solar" && (s.key === "wind_speed_m_s" || s.key === "wind_capacity_mw")) return null;
              if (energyType === "wind" && (s.key === "ghi_kwh_m2_day" || s.key === "solar_capacity_mw")) return null;

              return (
                <div key={s.key} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs text-muted-foreground flex items-center gap-1.5">
                      <s.icon className="h-3 w-3" />
                      {s.label}
                    </label>
                    <span className="text-xs font-mono font-semibold text-foreground">
                      {params[s.key]?.toFixed(s.step < 1 ? 1 : 0)} {s.unit}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={s.min}
                    max={s.max}
                    step={s.step}
                    value={params[s.key]}
                    onChange={(e) => handleSliderChange(s.key, parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-muted rounded-full appearance-none cursor-pointer accent-primary"
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>{s.min}</span>
                    <span>{s.max}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Results */}
        <div className="lg:col-span-8 space-y-4">
          {loading && (
            <div className="flex items-center justify-center p-8 rounded-xl border border-border bg-card/50">
              <Loader2 className="h-5 w-5 animate-spin text-primary mr-2" />
              <span className="text-sm text-muted-foreground">Recalculating...</span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
              {error}
            </div>
          )}

          {result && !loading && (
            <>
              {/* KPI Row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: "Annual Yield", value: `${(ey?.annual_energy_yield_mwh || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })} MWh`, icon: Zap, color: "text-amber-500" },
                  { label: "Capacity Factor", value: `${(ey?.capacity_factor_pct || 0).toFixed(1)}%`, icon: TrendingUp, color: "text-primary" },
                  { label: "LCOE", value: `$${(fin?.lcoe_usd_per_mwh || 0).toFixed(2)}/MWh`, icon: DollarSign, color: "text-emerald-500" },
                  { label: "NPV (25yr)", value: `$${((fin?.npv_usd || 0) / 1e6).toFixed(2)}M`, icon: TrendingUp, color: (fin?.npv_usd || 0) >= 0 ? "text-emerald-500" : "text-destructive" },
                ].map((kpi) => (
                  <div key={kpi.label} className="rounded-xl border border-border bg-card p-3.5 shadow-sm">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{kpi.label}</span>
                      <kpi.icon className={`h-3.5 w-3.5 ${kpi.color}`} />
                    </div>
                    <p className="text-lg font-bold text-foreground">{kpi.value}</p>
                  </div>
                ))}
              </div>

              {/* Second KPI Row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: "CAPEX", value: `$${((fin?.estimated_project_cost_usd || 0) / 1e6).toFixed(2)}M` },
                  { label: "Annual Revenue", value: `$${((fin?.annual_revenue_usd || 0) / 1e3).toFixed(0)}K` },
                  { label: "Payback", value: fin?.payback_period_years ? `${fin.payback_period_years.toFixed(1)} yrs` : "N/A" },
                  { label: "IRR", value: `${(fin?.irr_pct || 0).toFixed(1)}%` },
                ].map((kpi) => (
                  <div key={kpi.label} className="rounded-lg border border-border bg-background/50 p-3">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-0.5">{kpi.label}</p>
                    <p className="text-sm font-semibold text-foreground">{kpi.value}</p>
                  </div>
                ))}
              </div>

              {/* Micrositing summary */}
              {ms && (
                <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground mb-3">Capacity Planning</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div><span className="text-xs text-muted-foreground block">Total Capacity</span><span className="font-semibold">{ms.total_capacity_mw?.toFixed(1)} MW</span></div>
                    {ms.solar && <div><span className="text-xs text-muted-foreground block">Solar Panels</span><span className="font-semibold">{ms.solar.panel_count?.toLocaleString()}</span></div>}
                    {ms.wind && <div><span className="text-xs text-muted-foreground block">Turbines</span><span className="font-semibold">{ms.wind.turbine_count}</span></div>}
                    <div><span className="text-xs text-muted-foreground block">Expansion</span><span className={`font-semibold text-xs ${ms.expansion_status === "Expandable" ? "text-emerald-500" : ms.expansion_status === "Limited Expansion" ? "text-amber-500" : "text-destructive"}`}>{ms.expansion_status}</span></div>
                  </div>
                </div>
              )}

              {/* Cash Flow Chart */}
              {yearlyChartData.length > 0 && (
                <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground mb-1">25-Year Cumulative Cash Flow</h3>
                  <p className="text-xs text-muted-foreground mb-4">Revenue, OPEX, and net cumulative position (in $K)</p>
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={yearlyChartData} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
                      <defs>
                        <linearGradient id="cumGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0.05} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
                      <XAxis dataKey="year" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} interval={4} />
                      <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                      <Tooltip
                        content={({ active, payload, label }) => {
                          if (!active || !payload?.length) return null;
                          return (
                            <div className="rounded-lg border border-border bg-popover p-3 text-xs shadow-xl">
                              <p className="font-semibold text-foreground mb-1">{label}</p>
                              {payload.map((p: any) => (
                                <p key={p.dataKey} style={{ color: p.stroke || p.fill }}>
                                  {p.name}: ${Number(p.value).toFixed(0)}K
                                </p>
                              ))}
                            </div>
                          );
                        }}
                      />
                      <Area type="monotone" dataKey="cumulative" name="Cumulative" stroke="hsl(var(--primary))" fill="url(#cumGradient)" strokeWidth={2} />
                      <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#f59e0b" fill="none" strokeWidth={1} strokeDasharray="4 4" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
