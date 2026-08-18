"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Loader2,
  FileText,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Sun,
  Wind,
  Zap,
  DollarSign,
  MapPin,
  Shield,
  TrendingUp,
  Brain,
  ChevronDown,
  RefreshCw,
} from "lucide-react";
import api from "@/lib/api";
import type { FullAnalysisResponse } from "@/lib/types";

interface Project {
  id: string;
  name: string;
}

interface SiteInfo {
  id: string;
  name: string;
}

export default function ReportsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [sites, setSites] = useState<SiteInfo[]>([]);
  const [selectedSiteId, setSelectedSiteId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<FullAnalysisResponse | null>(null);
  const [narrativeLoading, setNarrativeLoading] = useState(false);
  const [narrative, setNarrative] = useState<string | null>(null);

  useEffect(() => {
    api.get("/projects/").then((r) => setProjects(r.data)).catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedProjectId) { setSites([]); return; }
    // Fetch sites for the project by loading scan logs
    api.get(`/projects/`).then((r) => {
      // We need to get sites — the API returns projects. 
      // Use the analysis scan approach to get sites from the project
    }).catch(console.error);
    // Alternative: fetch sites from analysis data
    setSites([]);
    setSelectedSiteId("");
    setReport(null);
  }, [selectedProjectId]);

  const runFullAnalysis = useCallback(async () => {
    if (!selectedProjectId || !selectedSiteId) return;
    setLoading(true);
    setError(null);
    setReport(null);
    setNarrative(null);
    try {
      const res = await api.post(
        `/api/analysis/projects/${selectedProjectId}/sites/${selectedSiteId}/full-analysis`,
        null,
        { params: { energy_type: "hybrid", fit_usd_per_mwh: 65 } }
      );
      setReport(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [selectedProjectId, selectedSiteId]);

  const fetchNarrative = useCallback(async () => {
    if (!selectedProjectId || !selectedSiteId) return;
    setNarrativeLoading(true);
    try {
      const res = await api.post(
        `/api/analysis/projects/${selectedProjectId}/sites/${selectedSiteId}/narrative`
      );
      setNarrative(res.data.narrative || res.data.error || "AI summary unavailable.");
    } catch {
      setNarrative("AI narrative generation failed.");
    } finally {
      setNarrativeLoading(false);
    }
  }, [selectedProjectId, selectedSiteId]);

  const f = report?.financial;
  const s = report?.suitability;
  const feas = report?.feasibility;
  const ey = report?.energy_yield;
  const rec = report?.recommendation;
  const ms = report?.micrositing;
  const env = report?.environmental_data;
  const infra = report?.infrastructure_data;

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1400px] mx-auto min-h-[calc(100vh-3.5rem)]">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
            <FileText className="h-6 w-6 text-primary" />
            Feasibility Reports
          </h2>
          <p className="text-sm text-muted-foreground">
            Run the full analysis pipeline and generate comprehensive site reports.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="h-9 rounded-lg border border-border bg-card text-foreground text-sm px-3 pr-8 focus:outline-none focus:ring-2 focus:ring-primary/40 appearance-none cursor-pointer"
          >
            <option value="">Select Project</option>
            {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>

          <input
            type="text"
            placeholder="Site ID (paste UUID)"
            value={selectedSiteId}
            onChange={(e) => setSelectedSiteId(e.target.value)}
            className="h-9 rounded-lg border border-border bg-card text-foreground text-sm px-3 w-64 focus:outline-none focus:ring-2 focus:ring-primary/40"
          />

          <button
            onClick={runFullAnalysis}
            disabled={!selectedProjectId || !selectedSiteId || loading}
            className="h-9 px-4 rounded-lg bg-primary hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed text-primary-foreground text-sm font-medium transition-colors flex items-center gap-2 shadow-lg shadow-primary/20"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <TrendingUp className="h-4 w-4" />}
            Run Analysis
          </button>
        </div>
      </header>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center p-16 border border-border rounded-xl bg-card/50">
          <Loader2 className="h-6 w-6 animate-spin text-primary mr-3" />
          <span className="text-sm text-muted-foreground">Running full analysis pipeline (9 stages)...</span>
        </div>
      )}

      {/* Empty state */}
      {!loading && !report && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
            <FileText className="h-8 w-8 text-primary/60" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">No Report Generated</h3>
          <p className="text-sm text-muted-foreground max-w-md">
            Select a project and site, then run the full analysis pipeline to generate a comprehensive feasibility report.
          </p>
        </div>
      )}

      {/* Report */}
      {report && !loading && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

          {/* Recommendation Banner */}
          {rec && (
            <div className={`p-5 rounded-xl border ${
              rec.verdict === "Strongly Recommended" ? "border-emerald-500/30 bg-emerald-500/5" :
              rec.verdict === "Recommended with Conditions" ? "border-amber-500/30 bg-amber-500/5" :
              "border-destructive/30 bg-destructive/5"
            }`}>
              <div className="flex items-start gap-4">
                {rec.verdict === "Strongly Recommended" ? (
                  <CheckCircle2 className="h-6 w-6 text-emerald-500 shrink-0 mt-0.5" />
                ) : rec.verdict === "Not Recommended" ? (
                  <XCircle className="h-6 w-6 text-destructive shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="h-6 w-6 text-amber-500 shrink-0 mt-0.5" />
                )}
                <div>
                  <h3 className="text-lg font-semibold text-foreground">{rec.verdict}</h3>
                  <p className="text-sm text-muted-foreground mt-1">{rec.summary}</p>
                  <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                    <span>Score: <strong className="text-foreground">{rec.suitability_score?.toFixed(0)}/100</strong></span>
                    <span>Class: <strong className="text-foreground">{rec.suitability_class}</strong></span>
                    <span>Tech: <strong className="text-foreground">{rec.recommended_technology}</strong></span>
                    <span>Capacity: <strong className="text-foreground">{rec.recommended_capacity_mw?.toFixed(1)} MW</strong></span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Annual Yield", value: `${(ey?.annual_energy_yield_mwh || 0).toLocaleString()} MWh`, icon: Zap, color: "text-amber-500" },
              { label: "CAPEX", value: `$${((f?.estimated_project_cost_usd || 0) / 1e6).toFixed(1)}M`, icon: DollarSign, color: "text-emerald-500" },
              { label: "Payback", value: f?.payback_period_years ? `${f.payback_period_years.toFixed(1)} yrs` : "N/A", icon: TrendingUp, color: "text-primary" },
              { label: "LCOE", value: `$${(f?.lcoe_usd_per_mwh || 0).toFixed(2)}/MWh`, icon: BarChart, color: "text-violet-500" },
            ].map((kpi) => (
              <div key={kpi.label} className="rounded-xl border border-border bg-card p-4 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-muted-foreground uppercase tracking-wider">{kpi.label}</span>
                  <kpi.icon className={`h-4 w-4 ${kpi.color}`} />
                </div>
                <p className="text-xl font-bold text-foreground">{kpi.value}</p>
              </div>
            ))}
          </div>

          {/* Two-column layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* Site Analysis */}
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
                <MapPin className="h-4 w-4 text-primary" />
                Site Analysis
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">Coordinates</span><span className="text-foreground font-mono text-xs">{report.coordinates.latitude.toFixed(4)}°N, {report.coordinates.longitude.toFixed(4)}°E</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Solar Irradiance</span><span className="text-foreground">{env?.annual_solar_irradiance_kwh_m2_day?.toFixed(2)} kWh/m²/day</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Wind Speed (50m)</span><span className="text-foreground">{env?.annual_wind_speed_50m_m_s?.toFixed(2)} m/s</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Avg Temperature</span><span className="text-foreground">{env?.annual_avg_temp_c?.toFixed(1)}°C</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Grid Distance</span><span className="text-foreground">{infra?.nearest_substation_km ?? infra?.nearest_power_line_km ?? "N/A"} km</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Road Distance</span><span className="text-foreground">{infra?.nearest_major_road_km ?? "N/A"} km</span></div>
              </div>
            </div>

            {/* Technical Feasibility */}
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
                <Shield className="h-4 w-4 text-primary" />
                Technical Feasibility
              </h3>
              <div className="flex items-center gap-2 mb-3">
                {feas?.is_feasible ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="h-3 w-3" /> Feasible
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-destructive/10 text-destructive">
                    <XCircle className="h-3 w-3" /> Not Feasible
                  </span>
                )}
                <span className="text-xs text-muted-foreground">
                  Score: {feas?.feasibility_score?.toFixed(0)}/100 · {feas?.hard_constraint_summary?.passed}/{feas?.hard_constraint_summary?.total} constraints passed
                </span>
              </div>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {feas?.hard_constraints?.map((c, i) => (
                  <div key={i} className={`flex items-center gap-2 text-xs p-1.5 rounded ${c.passed ? "text-muted-foreground" : "text-destructive bg-destructive/5"}`}>
                    {c.passed ? <CheckCircle2 className="h-3 w-3 text-emerald-500 shrink-0" /> : <XCircle className="h-3 w-3 text-destructive shrink-0" />}
                    <span className="font-medium">{c.constraint}</span>
                    <span className="ml-auto text-[10px]">{c.actual_value ?? "N/A"}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Financial Analysis */}
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
                <DollarSign className="h-4 w-4 text-emerald-500" />
                Financial Analysis
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">Deployment</span><span className="text-foreground font-medium">{f?.deployment}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Total CAPEX</span><span className="text-foreground">${(f?.estimated_project_cost_usd || 0).toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Annual OPEX</span><span className="text-foreground">${(f?.annual_opex_usd || 0).toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Annual Revenue</span><span className="text-foreground">${(f?.annual_revenue_usd || 0).toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">NPV (25yr)</span><span className={`font-medium ${(f?.npv_usd || 0) >= 0 ? "text-emerald-500" : "text-destructive"}`}>${(f?.npv_usd || 0).toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">IRR</span><span className="text-foreground">{f?.irr_pct?.toFixed(1)}%</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">ROI</span><span className="text-foreground">{f?.roi_pct?.toFixed(1)}%</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Payback Status</span><span className="text-foreground text-xs">{f?.payback_status}</span></div>
              </div>
            </div>

            {/* Suitability Scores */}
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
                <BarChart className="h-4 w-4 text-violet-500" />
                Suitability Breakdown
              </h3>
              <div className="mb-3 flex items-center gap-2">
                <span className="text-2xl font-bold text-foreground">{s?.overall_score?.toFixed(0)}</span>
                <span className="text-sm text-muted-foreground">/ 100</span>
                <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-semibold ${
                  (s?.overall_score || 0) >= 70 ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" :
                  (s?.overall_score || 0) >= 50 ? "bg-amber-500/10 text-amber-600 dark:text-amber-400" :
                  "bg-destructive/10 text-destructive"
                }`}>{s?.classification}</span>
              </div>
              <div className="space-y-2">
                {s?.component_scores && Object.entries(s.component_scores).map(([key, val]) => (
                  <div key={key} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground capitalize">{key}</span>
                      <span className="text-foreground font-medium">{val.combined_score.toFixed(0)}</span>
                    </div>
                    <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${Math.min(100, val.combined_score)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* AI Narrative */}
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Brain className="h-4 w-4 text-violet-500" />
                AI Investment Narrative
              </h3>
              <button
                onClick={fetchNarrative}
                disabled={narrativeLoading}
                className="text-xs text-primary hover:underline flex items-center gap-1 disabled:opacity-50"
              >
                {narrativeLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
                {report.ai_narrative?.narrative ? "Regenerate" : "Generate Narrative"}
              </button>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {narrative || report.ai_narrative?.narrative || report.ai_narrative?.error || "Click 'Generate Narrative' to create an AI-powered investment summary."}
            </p>
          </div>

        </div>
      )}
    </div>
  );
}

// Simple bar chart icon component (since we use it in KPI cards)
function BarChart({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" x2="12" y1="20" y2="10" /><line x1="18" x2="18" y1="20" y2="4" /><line x1="6" x2="6" y1="20" y2="16" />
    </svg>
  );
}
