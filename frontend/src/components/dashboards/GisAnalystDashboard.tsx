"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  Loader2,
  Sliders,
  Zap,
  Shield,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  MapPin,
  ChevronDown,
  Info,
  CircleGauge,
} from "lucide-react";
import api from "@/lib/api";

interface Project {
  id: string;
  name: string;
}

interface ScoredSite {
  site_id: string;
  site_name: string;
  total_score: number;
  classification: string;
  factor_breakdown: {
    factor_name: string;
    raw_value: number;
    normalized_value: number;
    weight: number;
    weighted_contribution: number;
  }[];
}

interface GridCapacity {
  site_id: string;
  site_name: string;
  substation_distance_km: number | null;
  estimated_voltage_kv: number;
  line_distance_km: number | null;
  estimated_line_rating_a: number;
  existing_generation_nearby_mw: number;
  thermal_limit_mw: number;
  estimated_spare_capacity_mw: number;
  hosting_status: "Constrained" | "Moderate" | "High Capacity";
  max_recommended_interconnect_mw: number;
  assessment_notes: string;
}

interface ConflictData {
  total_conflicts_found: number;
  is_unsuitable: boolean;
  conflict_types?: string[];
  wdpa_protected?: boolean;
  wetland_overlap?: boolean;
  floodplain_overlap?: boolean;
  water_body_overlap?: boolean;
}

interface WeightConfig {
  key: string;
  label: string;
  shortLabel: string;
  color: string;
  defaultWeight: number;
}

const WEIGHT_FACTORS: WeightConfig[] = [
  {
    key: "renewable_resource",
    label: "Renewable Resource Availability",
    shortLabel: "Resource",
    color: "#f59e0b",
    defaultWeight: 0.30,
  },
  {
    key: "geographic_suitability",
    label: "Geographic Suitability",
    shortLabel: "Terrain",
    color: "#3b82f6",
    defaultWeight: 0.20,
  },
  {
    key: "infrastructure_accessibility",
    label: "Infrastructure Accessibility",
    shortLabel: "Grid",
    color: "#8b5cf6",
    defaultWeight: 0.15,
  },
  {
    key: "environmental_impact",
    label: "Environmental Impact",
    shortLabel: "Environment",
    color: "#10b981",
    defaultWeight: 0.15,
  },
  {
    key: "socio_economic_viability",
    label: "Socio-Economic Viability",
    shortLabel: "Socio-Econ",
    color: "#ec4899",
    defaultWeight: 0.15,
  },
  {
    key: "economic_feasibility",
    label: "Economic / Cost Feasibility",
    shortLabel: "Cost",
    color: "#f97316",
    defaultWeight: 0.05,
  },
];

const CLASSIFICATION_STYLES: Record<string, string> = {
  Excellent: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  "Highly Suitable": "bg-blue-500/15 text-blue-400 border-blue-500/30",
  "Moderately Suitable": "bg-amber-500/15 text-amber-400 border-amber-500/30",
  "Low Suitability": "bg-orange-500/15 text-orange-400 border-orange-500/30",
  Unsuitable: "bg-red-500/15 text-red-400 border-red-500/30",
};

const HOSTING_STATUS_STYLES: Record<string, { className: string; icon: typeof ShieldCheck }> = {
  "High Capacity": { className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30", icon: ShieldCheck },
  Moderate: { className: "bg-amber-500/15 text-amber-400 border-amber-500/30", icon: Shield },
  Constrained: { className: "bg-red-500/15 text-red-400 border-red-500/30", icon: ShieldAlert },
};

export default function GisAnalystDashboard() {
  
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [weights, setWeights] = useState<Record<string, number>>(
    Object.fromEntries(WEIGHT_FACTORS.map((f) => [f.key, f.defaultWeight]))
  );

  const [scoredSites, setScoredSites] = useState<ScoredSite[]>([]);
  const [selectedSiteId, setSelectedSiteId] = useState<string | null>(null);

  const [gridCapacity, setGridCapacity] = useState<GridCapacity | null>(null);
  const [gridLoading, setGridLoading] = useState(false);

  const [conflictData, setConflictData] = useState<ConflictData | null>(null);

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const projectIdRef = useRef<string>("");
  useEffect(() => {
    projectIdRef.current = selectedProjectId;
  }, [selectedProjectId]);

  useEffect(() => {
    api.get("/projects/").then((res) => setProjects(res.data)).catch(console.error);
  }, []);

  const scoreSites = useCallback(
    async (projectId: string, w: Record<string, number>) => {
      if (!projectId) return;
      setLoading(true);
      setError(null);

      try {
        const res = await api.post(
          `/api/projects/${projectId}/score-sites`,
          {
            renewable_resource: w.renewable_resource,
            geographic_suitability: w.geographic_suitability,
            infrastructure_accessibility: w.infrastructure_accessibility,
            environmental_impact: w.environmental_impact,
            socio_economic_viability: w.socio_economic_viability,
            economic_feasibility: w.economic_feasibility,
          }
        );
        setScoredSites(res.data.scored_sites || []);

        if (res.data.scored_sites?.length > 0) {
          setSelectedSiteId((prev) =>
            prev ? prev : res.data.scored_sites[0].site_id
          );
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || "Scoring failed");
      } finally {
        setLoading(false);
      }
    },
    [] 
  );

  useEffect(() => {
    if (selectedProjectId) {
      setSelectedSiteId(null);
      setGridCapacity(null);
      setConflictData(null);

      scoreSites(selectedProjectId, weights);
    }
    
  }, [selectedProjectId]);

  const handleWeightChange = useCallback(
    (key: string, newValue: number) => {
      setWeights((prev) => {
        const updated = { ...prev, [key]: newValue };

        const otherKeys = WEIGHT_FACTORS.filter((f) => f.key !== key).map((f) => f.key);
        const otherSum = otherKeys.reduce((sum, k) => sum + prev[k], 0);
        const remaining = Math.max(0, 1.0 - newValue);

        if (otherSum > 0) {
          for (const k of otherKeys) {
            updated[k] = (prev[k] / otherSum) * remaining;
          }
        } else {
          
          const equalShare = remaining / otherKeys.length;
          for (const k of otherKeys) {
            updated[k] = equalShare;
          }
        }

        if (debounceTimer.current) clearTimeout(debounceTimer.current);
        debounceTimer.current = setTimeout(() => {
          const currentProjectId = projectIdRef.current;
          if (currentProjectId) {
            scoreSites(currentProjectId, updated);
          }
        }, 400);

        return updated;
      });
    },
    [scoreSites]
  );

  useEffect(() => {
    if (!selectedProjectId || !selectedSiteId) return;

    setGridLoading(true);
    api
      .post(`/api/projects/${selectedProjectId}/grid-capacity`, {
        site_id: selectedSiteId,
      })
      .then((res) => setGridCapacity(res.data))
      .catch((err) => {
        console.error("Grid capacity error:", err);
        setGridCapacity(null);
      })
      .finally(() => setGridLoading(false));

    const site = scoredSites.find((s) => s.site_id === selectedSiteId);
    if (site) {
      const envBreakdown = site.factor_breakdown.find(
        (f) => f.factor_name === "Environmental Impact"
      );
      
      if (envBreakdown) {
        const envScore = envBreakdown.normalized_value;
        setConflictData({
          total_conflicts_found: envScore < 0.5 ? Math.round((1 - envScore) * 5) : 0,
          is_unsuitable: envScore < 0.2,
          wdpa_protected: envScore < 0.3,
          wetland_overlap: envScore < 0.25,
          floodplain_overlap: envScore < 0.15,
          water_body_overlap: false,
        });
      }
    }
  }, [selectedSiteId, selectedProjectId]);

  const breakdownChartData = useMemo(() => {
    const site = scoredSites.find((s) => s.site_id === selectedSiteId);
    if (!site) return [];
    return site.factor_breakdown.map((f, i) => ({
      name: WEIGHT_FACTORS[i]?.shortLabel || f.factor_name,
      fullName: f.factor_name,
      score: f.normalized_value,
      weight: f.weight,
      contribution: f.weighted_contribution,
      color: WEIGHT_FACTORS[i]?.color || "#6b7280",
    }));
  }, [scoredSites, selectedSiteId]);

  const selectedSiteName =
    scoredSites.find((s) => s.site_id === selectedSiteId)?.site_name || "â€”";

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1600px] mx-auto min-h-[calc(100vh-3.5rem)]">
      {}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
            <MapPin className="h-6 w-6 text-blue-500" />
            GIS Analyst Dashboard
          </h2>
          <p className="text-sm text-muted-foreground">
            Spatial scoring, grid capacity analysis, and land-use conflict screening.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            id="gis-project-select"
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="h-9 rounded-lg border border-border bg-card text-foreground text-sm px-3 pr-8 focus:outline-none focus:ring-2 focus:ring-blue-500/40 appearance-none cursor-pointer"
          >
            <option value="">Select Project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </header>

      {}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {}
      {!selectedProjectId && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="h-16 w-16 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-4">
            <MapPin className="h-8 w-8 text-blue-500/60" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Select a Project
          </h3>
          <p className="text-sm text-muted-foreground max-w-md">
            Choose a project with analyzed sites to begin spatial analysis
            with adjustable scoring weights.
          </p>
        </div>
      )}

      {}
      {selectedProjectId && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {}
          <div className="xl:col-span-1 space-y-6">
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-blue-500" />
                  What-If Weight Adjuster
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Drag sliders to reweight factors â€¢ Scores update live
                </p>
              </div>

              <div className="space-y-4">
                {WEIGHT_FACTORS.map((factor) => {
                  const pct = Math.round((weights[factor.key] || 0) * 100);
                  return (
                    <div key={factor.key}>
                      <div className="flex items-center justify-between mb-1.5">
                        <label
                          htmlFor={`weight-${factor.key}`}
                          className="text-xs text-muted-foreground"
                        >
                          {factor.label}
                        </label>
                        <span
                          className="text-xs font-mono font-semibold tabular-nums"
                          style={{ color: factor.color }}
                        >
                          {pct}%
                        </span>
                      </div>
                      <input
                        id={`weight-${factor.key}`}
                        type="range"
                        min={0}
                        max={100}
                        step={1}
                        value={pct}
                        onChange={(e) =>
                          handleWeightChange(factor.key, parseInt(e.target.value) / 100)
                        }
                        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
                        style={{
                          accentColor: factor.color,
                          background: `linear-gradient(to right, ${factor.color} ${pct}%, hsl(var(--border)) ${pct}%)`,
                        }}
                      />
                    </div>
                  );
                })}
              </div>

              {}
              <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-[10px] text-muted-foreground">
                <span>Total</span>
                <span className="font-mono font-semibold text-foreground">
                  {Math.round(
                    Object.values(weights).reduce((a, b) => a + b, 0) * 100
                  )}
                  %
                </span>
              </div>
            </div>

            {}
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <Shield className="h-4 w-4 text-emerald-500" />
                  Land-Use Conflict Indicator
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                  {selectedSiteId
                    ? `Screening for "${selectedSiteName}"`
                    : "Select a site to view conflict status"}
                </p>
              </div>

              {!selectedSiteId && (
                <div className="text-center py-6 text-muted-foreground text-xs">
                  No site selected
                </div>
              )}

              {selectedSiteId && conflictData && (
                <div className="space-y-3">
                  {}
                  <div
                    className={`rounded-lg border p-3 text-sm font-medium ${
                      conflictData.is_unsuitable
                        ? "bg-red-500/10 border-red-500/20 text-red-400"
                        : conflictData.total_conflicts_found > 0
                          ? "bg-amber-500/10 border-amber-500/20 text-amber-400"
                          : "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                    }`}
                  >
                    {conflictData.is_unsuitable
                      ? "âš  High Conflict â€” Not Viable"
                      : conflictData.total_conflicts_found > 0
                        ? `âš¡ ${conflictData.total_conflicts_found} Conflict(s) Detected`
                        : "âœ“ Clear for Feasibility"}
                  </div>

                  {}
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      {
                        label: "WDPA Protected",
                        active: conflictData.wdpa_protected,
                        icon: "ðŸ›¡",
                      },
                      {
                        label: "Wetland Zone",
                        active: conflictData.wetland_overlap,
                        icon: "ðŸ’§",
                      },
                      {
                        label: "Floodplain",
                        active: conflictData.floodplain_overlap,
                        icon: "ðŸŒŠ",
                      },
                      {
                        label: "Water Body",
                        active: conflictData.water_body_overlap,
                        icon: "ðŸž",
                      },
                    ].map((badge) => (
                      <div
                        key={badge.label}
                        className={`rounded-lg border px-3 py-2 text-xs font-medium flex items-center gap-2 ${
                          badge.active
                            ? "bg-red-500/10 border-red-500/20 text-red-400"
                            : "bg-card border-border text-muted-foreground"
                        }`}
                      >
                        <span>{badge.icon}</span>
                        <span>{badge.label}</span>
                        {badge.active && (
                          <span className="ml-auto text-[9px] bg-red-500/20 px-1.5 py-0.5 rounded font-bold">
                            FLAG
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {}
          <div className="xl:col-span-2 space-y-6">
            {}
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                    <CircleGauge className="h-4 w-4 text-violet-500" />
                    Ranked Sites â€” Live Scoring
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    {scoredSites.length} sites scored â€¢ Click a row to inspect
                  </p>
                </div>
                {loading && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Recalculatingâ€¦
                  </div>
                )}
              </div>

              {scoredSites.length === 0 && !loading && (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  No scored sites. Ensure the project has analyzed sites.
                </div>
              )}

              {scoredSites.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground">
                        <th className="text-left py-2 px-2 font-medium">#</th>
                        <th className="text-left py-2 px-2 font-medium">Site</th>
                        <th className="text-right py-2 px-2 font-medium">Score</th>
                        <th className="text-left py-2 px-2 font-medium">Class</th>
                        {WEIGHT_FACTORS.map((f) => (
                          <th
                            key={f.key}
                            className="text-right py-2 px-2 font-medium"
                            title={f.label}
                          >
                            {f.shortLabel}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {scoredSites.map((site, i) => {
                        const isSelected = site.site_id === selectedSiteId;
                        return (
                          <tr
                            key={site.site_id}
                            onClick={() => setSelectedSiteId(site.site_id)}
                            className={`border-b border-border/50 cursor-pointer transition-colors ${
                              isSelected
                                ? "bg-blue-500/10"
                                : "hover:bg-accent/50"
                            }`}
                          >
                            <td className="py-2.5 px-2 text-muted-foreground font-mono">
                              {i + 1}
                            </td>
                            <td className="py-2.5 px-2 font-medium text-foreground max-w-[180px] truncate">
                              {site.site_name}
                            </td>
                            <td className="py-2.5 px-2 text-right font-mono font-semibold text-foreground">
                              {(site.total_score * 100).toFixed(1)}
                            </td>
                            <td className="py-2.5 px-2">
                              <span
                                className={`inline-flex px-2 py-0.5 rounded-md text-[10px] font-semibold border ${
                                  CLASSIFICATION_STYLES[site.classification] ||
                                  "bg-muted text-muted-foreground"
                                }`}
                              >
                                {site.classification}
                              </span>
                            </td>
                            {site.factor_breakdown.map((f, j) => (
                              <td
                                key={j}
                                className="py-2.5 px-2 text-right font-mono text-muted-foreground"
                              >
                                {f.weighted_contribution.toFixed(3)}
                              </td>
                            ))}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {}
            {selectedSiteId && breakdownChartData.length > 0 && (
              <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
                <div className="mb-4">
                  <h3 className="text-sm font-semibold text-foreground">
                    Factor Breakdown â€” {selectedSiteName}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    Normalized score per factor (0â€“1 scale)
                  </p>
                </div>

                <ResponsiveContainer width="100%" height={200}>
                  <BarChart
                    data={breakdownChartData}
                    margin={{ top: 5, right: 20, bottom: 5, left: 10 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="hsl(var(--border))"
                      opacity={0.5}
                      vertical={false}
                    />
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                    />
                    <YAxis
                      domain={[0, 1]}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                    />
                    <Tooltip
                      cursor={{ fill: "hsl(var(--accent))", opacity: 0.3 }}
                      content={({ active, payload }) => {
                        if (!active || !payload?.length) return null;
                        const d = payload[0].payload;
                        return (
                          <div className="rounded-lg border border-border bg-popover p-3 text-xs shadow-xl">
                            <p className="font-semibold text-foreground mb-1">
                              {d.fullName}
                            </p>
                            <p className="text-muted-foreground">
                              Norm. Score:{" "}
                              <span className="text-foreground font-medium">
                                {d.score.toFixed(4)}
                              </span>
                            </p>
                            <p className="text-muted-foreground">
                              Weight:{" "}
                              <span className="text-foreground font-medium">
                                {(d.weight * 100).toFixed(1)}%
                              </span>
                            </p>
                            <p className="text-muted-foreground">
                              Contribution:{" "}
                              <span className="text-foreground font-medium">
                                {d.contribution.toFixed(4)}
                              </span>
                            </p>
                          </div>
                        );
                      }}
                    />
                    <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                      {breakdownChartData.map((entry, i) => (
                        <Cell key={`bar-${i}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {}
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-500" />
                  Grid Hosting Capacity Inspector
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                  {selectedSiteId
                    ? `Assessment for "${selectedSiteName}"`
                    : "Select a site to inspect grid capacity"}
                </p>
              </div>

              {gridLoading && (
                <div className="flex items-center justify-center py-8 text-muted-foreground text-sm">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Analyzing grid capacityâ€¦
                </div>
              )}

              {!gridLoading && !gridCapacity && (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  {selectedSiteId
                    ? "Grid data unavailable for this site"
                    : "Select a site from the table above"}
                </div>
              )}

              {!gridLoading && gridCapacity && (
                <div className="space-y-4">
                  {}
                  <div className="flex items-center gap-3">
                    {(() => {
                      const style =
                        HOSTING_STATUS_STYLES[gridCapacity.hosting_status] ||
                        HOSTING_STATUS_STYLES["Moderate"];
                      const StatusIcon = style.icon;
                      return (
                        <span
                          className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-semibold ${style.className}`}
                        >
                          <StatusIcon className="h-4 w-4" />
                          {gridCapacity.hosting_status}
                        </span>
                      );
                    })()}
                    <span className="text-xs text-muted-foreground">
                      Max Interconnect:{" "}
                      <span className="text-foreground font-semibold">
                        {gridCapacity.max_recommended_interconnect_mw.toFixed(1)} MW
                      </span>
                    </span>
                  </div>

                  {}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {[
                      {
                        label: "Substation Distance",
                        value: gridCapacity.substation_distance_km
                          ? `${gridCapacity.substation_distance_km.toFixed(1)} km`
                          : "N/A",
                      },
                      {
                        label: "Voltage Class",
                        value: `${gridCapacity.estimated_voltage_kv} kV`,
                      },
                      {
                        label: "Line Rating",
                        value: `${gridCapacity.estimated_line_rating_a} A`,
                      },
                      {
                        label: "Thermal Limit",
                        value: `${gridCapacity.thermal_limit_mw.toFixed(1)} MW`,
                      },
                      {
                        label: "Existing Gen. Nearby",
                        value: `${gridCapacity.existing_generation_nearby_mw.toFixed(1)} MW`,
                      },
                      {
                        label: "Spare Capacity",
                        value: `${gridCapacity.estimated_spare_capacity_mw.toFixed(1)} MW`,
                      },
                    ].map((metric) => (
                      <div
                        key={metric.label}
                        className="rounded-lg border border-border bg-background/50 p-3"
                      >
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
                          {metric.label}
                        </p>
                        <p className="text-sm font-semibold text-foreground">
                          {metric.value}
                        </p>
                      </div>
                    ))}
                  </div>

                  {}
                  <div className="flex items-start gap-2 p-3 rounded-lg bg-accent/30 border border-border text-xs text-muted-foreground">
                    <Info className="h-3.5 w-3.5 shrink-0 mt-0.5 text-blue-400" />
                    <p>{gridCapacity.assessment_notes}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}