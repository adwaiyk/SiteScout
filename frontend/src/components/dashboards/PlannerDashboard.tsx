"use client";

/**
 * SiteScout — Planner Dashboard
 *
 * Targeted at renewable energy planners and investment managers.
 * Three primary intelligence panels:
 *   1. Pareto Frontier Trade-Off Chart (scatter)
 *   2. SHAP Feature Explanation Panel (waterfall bars)
 *   3. Energy Forecasting Chart (area with P10/P50/P90 bands)
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import {
  ScatterChart,
  Scatter,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
  ReferenceLine,
} from "recharts";
import {
  Loader2,
  TrendingUp,
  Brain,
  Zap,
  Target,
  ChevronDown,
  AlertTriangle,
  Info,
} from "lucide-react";
import api from "@/lib/api";

/* ═══════════════════════════════════════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════════════════════════════════ */

interface Project {
  id: string;
  name: string;
}

interface ParetoSolution {
  site_id: string;
  site_name: string;
  energy_output_mwh: number;
  environmental_impact_score: number;
  infrastructure_cost_proxy: number;
  is_dominated: boolean;
}

interface SHAPContribution {
  feature_name: string;
  feature_value: number;
  shap_value: number;
  abs_importance: number;
}

interface SHAPExplanation {
  site_id: string;
  site_name: string;
  model_type: string;
  base_value: number;
  predicted_value: number;
  feature_contributions: SHAPContribution[];
  top_positive_drivers: string[];
  top_negative_drivers: string[];
}

interface MonthlyForecast {
  month_index: number;
  month_name: string;
  p10_mwh: number;
  p50_mwh: number;
  p90_mwh: number;
}

interface ForecastData {
  site_name: string;
  energy_type: string;
  capacity_mw: number;
  first_year_p50_mwh: number;
  capacity_factor_pct: number;
  monthly_forecasts: MonthlyForecast[];
  cumulative: {
    lifespan_years: number;
    p10_total_mwh: number;
    p50_total_mwh: number;
    p90_total_mwh: number;
  };
}

/* ═══════════════════════════════════════════════════════════════════════════
   COMPONENT
   ═══════════════════════════════════════════════════════════════════════ */

export default function PlannerDashboard() {
  // ── State ─────────────────────────────────────────────────────────────
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Panel data
  const [paretoSolutions, setParetoSolutions] = useState<ParetoSolution[]>([]);
  const [dominatedSolutions, setDominatedSolutions] = useState<ParetoSolution[]>([]);
  const [selectedSiteId, setSelectedSiteId] = useState<string | null>(null);
  const [shapExplanation, setShapExplanation] = useState<SHAPExplanation | null>(null);
  const [shapLoading, setShapLoading] = useState(false);
  const [forecastData, setForecastData] = useState<ForecastData | null>(null);
  const [forecastLoading, setForecastLoading] = useState(false);

  // ── Fetch projects ────────────────────────────────────────────────────
  useEffect(() => {
    api.get("/projects/").then((res) => setProjects(res.data)).catch(console.error);
  }, []);

  // ── Internal helper: fetch SHAP + Forecast for a site ────────────────
  // Takes explicit projectId to avoid stale closures when called from
  // runOptimization immediately after state updates.
  const fetchSiteIntelligence = useCallback(
    async (projectId: string, siteId: string) => {
      if (!projectId || !siteId) return;

      // Fetch SHAP explanation
      setShapLoading(true);
      try {
        const shapRes = await api.post(
          `/api/projects/${projectId}/explain-site`,
          { site_id: siteId }
        );
        setShapExplanation(shapRes.data);
      } catch (err: any) {
        console.error("SHAP error:", err);
        setShapExplanation(null);
      } finally {
        setShapLoading(false);
      }

      // Fetch energy forecast
      setForecastLoading(true);
      try {
        const fcRes = await api.post(
          `/api/projects/${projectId}/forecast`,
          { site_id: siteId, capacity_mw: 1.0, system_loss_pct: 14.0 }
        );
        setForecastData(fcRes.data);
      } catch (err: any) {
        console.error("Forecast error:", err);
        setForecastData(null);
      } finally {
        setForecastLoading(false);
      }
    },
    [] // No state dependencies — projectId and siteId are passed explicitly
  );

  // ── Run Pareto Optimization ───────────────────────────────────────────
  const runOptimization = useCallback(async () => {
    if (!selectedProjectId) return;

    // Capture project ID at call time — avoids stale closure if user
    // switches projects while optimization is in flight.
    const projectId = selectedProjectId;

    setLoading(true);
    setError(null);
    setParetoSolutions([]);
    setDominatedSolutions([]);
    setSelectedSiteId(null);
    setShapExplanation(null);
    setForecastData(null);

    try {
      const res = await api.post(
        `/api/projects/${projectId}/optimize`,
        { population_size: 100, n_generations: 200 }
      );
      const pareto: ParetoSolution[] = res.data.pareto_solutions || [];
      const dominated: ParetoSolution[] = res.data.dominated_solutions || [];

      setParetoSolutions(pareto);
      setDominatedSolutions(dominated);

      // Auto-select first Pareto solution.
      // Use the locally captured projectId (not from state) and call the
      // explicit-param helper to avoid stale-closure issues.
      if (pareto.length > 0) {
        const firstSiteId = pareto[0].site_id;
        setSelectedSiteId(firstSiteId);
        fetchSiteIntelligence(projectId, firstSiteId);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Optimization failed");
    } finally {
      setLoading(false);
    }
  }, [selectedProjectId, fetchSiteIntelligence]);

  // ── Select a site → load SHAP + Forecast ──────────────────────────────
  // Called when user clicks a point on the Pareto scatter chart.
  const handleSiteSelect = useCallback(
    async (siteId: string) => {
      // Capture current project ID at call time to prevent stale reads
      const projectId = selectedProjectId;
      if (!projectId) return;

      setSelectedSiteId(siteId);
      setShapExplanation(null);
      setForecastData(null);

      // Delegate to the explicit-param helper
      fetchSiteIntelligence(projectId, siteId);
    },
    [selectedProjectId, fetchSiteIntelligence]
  );

  // ── Chart data transforms ─────────────────────────────────────────────
  const scatterData = useMemo(() => {
    const all = [
      ...paretoSolutions.map((s) => ({ ...s, is_dominated: false })),
      ...dominatedSolutions.map((s) => ({ ...s, is_dominated: true })),
    ];
    return all.map((s) => ({
      x: s.energy_output_mwh,
      y: s.environmental_impact_score,
      z: s.infrastructure_cost_proxy,
      name: s.site_name,
      site_id: s.site_id,
      is_dominated: s.is_dominated,
      selected: s.site_id === selectedSiteId,
    }));
  }, [paretoSolutions, dominatedSolutions, selectedSiteId]);

  const shapBarData = useMemo(() => {
    if (!shapExplanation) return [];
    return shapExplanation.feature_contributions.slice(0, 10).map((c) => ({
      name: c.feature_name.length > 22 ? c.feature_name.slice(0, 20) + "…" : c.feature_name,
      fullName: c.feature_name,
      value: c.shap_value,
      absValue: c.abs_importance,
      featureValue: c.feature_value,
      fill: c.shap_value >= 0 ? "#34d399" : "#fb7185",
    }));
  }, [shapExplanation]);

  const forecastChartData = useMemo(() => {
    if (!forecastData) return [];
    return forecastData.monthly_forecasts.map((m) => ({
      month: m.month_name.slice(0, 3),
      p10: m.p10_mwh,
      p50: m.p50_mwh,
      p90: m.p90_mwh,
    }));
  }, [forecastData]);

  // ── Lookups ───────────────────────────────────────────────────────────
  const selectedSiteName = useMemo(() => {
    const all = [...paretoSolutions, ...dominatedSolutions];
    return all.find((s) => s.site_id === selectedSiteId)?.site_name || "—";
  }, [paretoSolutions, dominatedSolutions, selectedSiteId]);

  // ═════════════════════════════════════════════════════════════════════
  // RENDER
  // ═════════════════════════════════════════════════════════════════════

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1600px] mx-auto min-h-[calc(100vh-3.5rem)]">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
            <Target className="h-6 w-6 text-emerald-500" />
            Planner Dashboard
          </h2>
          <p className="text-sm text-muted-foreground">
            Multi-objective trade-off analysis, explainability, and generation forecasts.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            id="planner-project-select"
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="h-9 rounded-lg border border-border bg-card text-foreground text-sm px-3 pr-8 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 appearance-none cursor-pointer"
          >
            <option value="">Select Project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <button
            id="run-optimization-btn"
            onClick={runOptimization}
            disabled={!selectedProjectId || loading}
            className="h-9 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors flex items-center gap-2 shadow-lg shadow-emerald-600/20"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <TrendingUp className="h-4 w-4" />
            )}
            Run Optimization
          </button>
        </div>
      </header>

      {/* ── Error Banner ───────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* ── Empty State ────────────────────────────────────────────────── */}
      {!loading && paretoSolutions.length === 0 && dominatedSolutions.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="h-16 w-16 rounded-2xl bg-emerald-500/10 flex items-center justify-center mb-4">
            <Target className="h-8 w-8 text-emerald-500/60" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">
            No Optimization Results Yet
          </h3>
          <p className="text-sm text-muted-foreground max-w-md">
            Select a project with analyzed sites and run the NSGA-II optimizer
            to generate the Pareto frontier and unlock SHAP explanations.
          </p>
        </div>
      )}

      {/* ── Dashboard Panels ───────────────────────────────────────────── */}
      {(paretoSolutions.length > 0 || dominatedSolutions.length > 0) && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* ═══════ Panel 1: Pareto Frontier Scatter ═══════ */}
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-emerald-500" />
                  Pareto Frontier — Trade-Off Chart
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Energy Output vs. Environmental Impact • Click a point to inspect
                </p>
              </div>
              <div className="flex items-center gap-3 text-[10px]">
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  Pareto-Optimal
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-zinc-500" />
                  Dominated
                </span>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={320}>
              <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
                <XAxis
                  dataKey="x"
                  type="number"
                  name="Energy Output"
                  unit=" MWh"
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                  label={{
                    value: "Energy Output (MWh/yr)",
                    position: "bottom",
                    offset: 0,
                    style: { fontSize: 11, fill: "hsl(var(--muted-foreground))" },
                  }}
                />
                <YAxis
                  dataKey="y"
                  type="number"
                  name="Env. Impact"
                  tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                  label={{
                    value: "Env. Impact (0–1)",
                    angle: -90,
                    position: "insideLeft",
                    style: { fontSize: 11, fill: "hsl(var(--muted-foreground))" },
                  }}
                />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const d = payload[0].payload;
                    return (
                      <div className="rounded-lg border border-border bg-popover p-3 text-xs shadow-xl">
                        <p className="font-semibold text-foreground mb-1">{d.name}</p>
                        <p className="text-muted-foreground">
                          Energy: <span className="text-foreground font-medium">{d.x} MWh</span>
                        </p>
                        <p className="text-muted-foreground">
                          Env. Impact: <span className="text-foreground font-medium">{d.y.toFixed(4)}</span>
                        </p>
                        <p className="text-muted-foreground">
                          Infra Cost: <span className="text-foreground font-medium">{d.z.toFixed(1)} km</span>
                        </p>
                        <p className={`mt-1 font-medium ${d.is_dominated ? "text-zinc-400" : "text-emerald-400"}`}>
                          {d.is_dominated ? "Dominated" : "Pareto-Optimal ✓"}
                        </p>
                      </div>
                    );
                  }}
                />
                <Scatter
                  data={scatterData}
                  onClick={(data: any) => {
                    if (data?.site_id) handleSiteSelect(data.site_id);
                  }}
                  cursor="pointer"
                >
                  {scatterData.map((entry, i) => (
                    <Cell
                      key={`cell-${i}`}
                      fill={entry.selected ? "#f59e0b" : entry.is_dominated ? "#71717a" : "#34d399"}
                      stroke={entry.selected ? "#f59e0b" : "transparent"}
                      strokeWidth={entry.selected ? 3 : 0}
                      r={entry.selected ? 8 : 6}
                    />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          {/* ═══════ Panel 2: SHAP Explanation ═══════ */}
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Brain className="h-4 w-4 text-violet-500" />
                SHAP Feature Explanation
              </h3>
              <p className="text-xs text-muted-foreground mt-1">
                {selectedSiteId
                  ? `Factor contributions for "${selectedSiteName}"`
                  : "Click a site on the Pareto chart to view explanations"}
              </p>
            </div>

            {shapLoading && (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground text-sm">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Computing SHAP values…
              </div>
            )}

            {!shapLoading && !shapExplanation && (
              <div className="flex flex-col items-center justify-center h-[300px] text-muted-foreground text-sm">
                <Brain className="h-8 w-8 opacity-30 mb-2" />
                Select a site to see feature attributions
              </div>
            )}

            {!shapLoading && shapExplanation && (
              <div>
                {/* Model meta */}
                <div className="flex items-center gap-4 mb-3 text-[10px] text-muted-foreground">
                  <span>
                    Model: <span className="text-foreground font-medium">{shapExplanation.model_type}</span>
                  </span>
                  <span>
                    Base: <span className="text-foreground font-medium">{shapExplanation.base_value.toFixed(4)}</span>
                  </span>
                  <span>
                    Predicted:{" "}
                    <span className="text-foreground font-medium">{shapExplanation.predicted_value.toFixed(4)}</span>
                  </span>
                </div>

                <ResponsiveContainer width="100%" height={280}>
                  <BarChart
                    data={shapBarData}
                    layout="vertical"
                    margin={{ top: 5, right: 20, bottom: 5, left: 5 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="hsl(var(--border))"
                      opacity={0.5}
                      horizontal={false}
                    />
                    <XAxis
                      type="number"
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                      label={{
                        value: "SHAP Value (impact on score)",
                        position: "bottom",
                        offset: -2,
                        style: { fontSize: 10, fill: "hsl(var(--muted-foreground))" },
                      }}
                    />
                    <YAxis
                      dataKey="name"
                      type="category"
                      width={135}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                    />
                    <ReferenceLine x={0} stroke="hsl(var(--muted-foreground))" strokeWidth={1} />
                    <Tooltip
                      cursor={{ fill: "hsl(var(--accent))", opacity: 0.3 }}
                      content={({ active, payload }) => {
                        if (!active || !payload?.length) return null;
                        const d = payload[0].payload;
                        return (
                          <div className="rounded-lg border border-border bg-popover p-3 text-xs shadow-xl">
                            <p className="font-semibold text-foreground mb-1">{d.fullName}</p>
                            <p className="text-muted-foreground">
                              Raw Value: <span className="text-foreground font-medium">{d.featureValue}</span>
                            </p>
                            <p className={d.value >= 0 ? "text-emerald-400" : "text-rose-400"}>
                              SHAP: {d.value >= 0 ? "+" : ""}
                              {d.value.toFixed(6)}
                            </p>
                          </div>
                        );
                      }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {shapBarData.map((entry, i) => (
                        <Cell key={`shap-${i}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* ═══════ Panel 3: Energy Forecast P10/P50/P90 ═══════ */}
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm xl:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-500" />
                  Energy Generation Forecast — Confidence Bands
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                  {forecastData
                    ? `Monthly P10/P50/P90 for "${forecastData.site_name}" • ${forecastData.capacity_mw} MW ${forecastData.energy_type}`
                    : "Select a site to generate forecasts"}
                </p>
              </div>

              {forecastData && (
                <div className="flex items-center gap-4 text-[10px]">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-5 rounded bg-amber-500/20 border border-amber-500/40" />
                    P10–P90 Range
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="h-0.5 w-5 bg-amber-500 rounded" />
                    P50 Expected
                  </span>
                </div>
              )}
            </div>

            {forecastLoading && (
              <div className="flex items-center justify-center h-[280px] text-muted-foreground text-sm">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Computing energy forecast…
              </div>
            )}

            {!forecastLoading && !forecastData && (
              <div className="flex flex-col items-center justify-center h-[280px] text-muted-foreground text-sm">
                <Zap className="h-8 w-8 opacity-30 mb-2" />
                Select a site to see generation confidence bands
              </div>
            )}

            {!forecastLoading && forecastData && (
              <div>
                {/* KPI strip */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
                  {[
                    {
                      label: "Year-1 Expected (P50)",
                      value: `${forecastData.first_year_p50_mwh.toLocaleString()} MWh`,
                    },
                    {
                      label: "Capacity Factor",
                      value: `${forecastData.capacity_factor_pct}%`,
                    },
                    {
                      label: "25-Year P50 Total",
                      value: `${forecastData.cumulative.p50_total_mwh.toLocaleString()} MWh`,
                    },
                    {
                      label: "25-Year P10–P90 Range",
                      value: `${forecastData.cumulative.p10_total_mwh.toLocaleString()} – ${forecastData.cumulative.p90_total_mwh.toLocaleString()} MWh`,
                    },
                  ].map((kpi, i) => (
                    <div
                      key={i}
                      className="rounded-lg border border-border bg-background/50 p-3"
                    >
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
                        {kpi.label}
                      </p>
                      <p className="text-sm font-semibold text-foreground">
                        {kpi.value}
                      </p>
                    </div>
                  ))}
                </div>

                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart
                    data={forecastChartData}
                    margin={{ top: 10, right: 20, bottom: 20, left: 10 }}
                  >
                    <defs>
                      <linearGradient id="forecastBand" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="hsl(var(--border))"
                      opacity={0.5}
                    />
                    <XAxis
                      dataKey="month"
                      tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                      label={{
                        value: "MWh",
                        angle: -90,
                        position: "insideLeft",
                        style: { fontSize: 11, fill: "hsl(var(--muted-foreground))" },
                      }}
                    />
                    <Tooltip
                      content={({ active, payload, label }) => {
                        if (!active || !payload?.length) return null;
                        const p10 = payload.find((p: any) => p.dataKey === "p10")?.value;
                        const p50 = payload.find((p: any) => p.dataKey === "p50")?.value;
                        const p90 = payload.find((p: any) => p.dataKey === "p90")?.value;
                        return (
                          <div className="rounded-lg border border-border bg-popover p-3 text-xs shadow-xl">
                            <p className="font-semibold text-foreground mb-1.5">{label}</p>
                            <p className="text-emerald-400">P90 (Optimistic): {Number(p90).toFixed(1)} MWh</p>
                            <p className="text-amber-400 font-medium">P50 (Expected): {Number(p50).toFixed(1)} MWh</p>
                            <p className="text-rose-400">P10 (Conservative): {Number(p10).toFixed(1)} MWh</p>
                          </div>
                        );
                      }}
                    />
                    {/* P90 upper band */}
                    <Area
                      type="monotone"
                      dataKey="p90"
                      stroke="#f59e0b"
                      strokeWidth={0}
                      fill="url(#forecastBand)"
                      fillOpacity={1}
                    />
                    {/* P50 center line */}
                    <Area
                      type="monotone"
                      dataKey="p50"
                      stroke="#f59e0b"
                      strokeWidth={2}
                      fill="none"
                      dot={{ r: 3, fill: "#f59e0b" }}
                    />
                    {/* P10 lower band */}
                    <Area
                      type="monotone"
                      dataKey="p10"
                      stroke="#f59e0b"
                      strokeWidth={0}
                      fill="hsl(var(--background))"
                      fillOpacity={0.7}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
