"use client";

import { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/lib/api";
import ProjectWizardModal, {
  type ProjectWizardData,
} from "@/components/ProjectWizardModal";
import {
  Loader2,
  Sun,
  Wind,
  Zap,
  Flag,
  Plus,
  FolderKanban,
  ArrowRight,
  ArrowLeft,
  MapPin,
  Calendar,
  Tag,
  Layers,
  CheckCircle2,
} from "lucide-react";

interface Project {
  id: string;
  name: string;
  description?: string;
  system_type?: string;
  created_at?: string;
}

const REGION_CENTERS: Record<string, [number, number]> = {
  "Maharashtra, India": [19.7515, 75.7139],
  "Rajasthan, India": [27.0238, 74.2179],
  "Gujarat, India": [22.2587, 71.1924],
  "Tamil Nadu, India": [11.1271, 78.6569],
  "Karnataka, India": [15.3173, 75.7139],
  "Andhra Pradesh, India": [15.9129, 79.74],
  "Madhya Pradesh, India": [22.9734, 78.6569],
  "Telangana, India": [18.1124, 79.0193],
  "Uttar Pradesh, India": [26.8467, 80.9462],
  "Punjab, India": [31.1471, 75.3412],
};

const MapScanner = dynamic(() => import("@/components/MapScanner"), {
  ssr: false,
  loading: () => (
    <div className="h-[560px] w-full flex items-center justify-center bg-muted/30 text-muted-foreground rounded-lg border border-border">
      <Loader2 className="h-6 w-6 animate-spin mr-3 text-muted-foreground" />
      Initializing GIS Canvas...
    </div>
  ),
});

const SECTOR_LABELS: Record<string, { label: string; color: string }> = {
  solar_pv: { label: "Solar PV", color: "bg-amber-500/15 text-amber-500 border-amber-500/20" },
  wind_energy: { label: "Wind", color: "bg-cyan-500/15 text-cyan-500 border-cyan-500/20" },
  bess: { label: "BESS", color: "bg-violet-500/15 text-violet-500 border-violet-500/20" },
  ev_charging: { label: "EV Hub", color: "bg-green-500/15 text-green-500 border-green-500/20" },
  logistics: { label: "Logistics", color: "bg-orange-500/15 text-orange-500 border-orange-500/20" },
  commercial_re: { label: "Commercial", color: "bg-blue-500/15 text-blue-500 border-blue-500/20" },
};

function SectorBadge({ sector }: { sector: string }) {
  const info = SECTOR_LABELS[sector] || { label: sector, color: "bg-muted text-muted-foreground" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border ${info.color}`}>
      {info.label}
    </span>
  );
}

export default function DashboardPage() {
  
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [activeConfig, setActiveConfig] = useState<ProjectWizardData | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);

  const [selectedCoords, setSelectedCoords] = useState<[number, number] | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = useCallback(async () => {
    setProjectsLoading(true);
    try {
      const res = await api.get("/projects/");
      setProjects(res.data);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    } finally {
      setProjectsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects().then(() => {
      // Restore last active project from localStorage
      const lastProjectId = localStorage.getItem("lastActiveProjectId");
      if (lastProjectId) {
        // We'll restore after projects state is set — use a small timeout
        setTimeout(() => {
          setProjects((prev) => {
            const found = prev.find((p) => p.id === lastProjectId);
            if (found) handleSelectProject(found);
            return prev;
          });
        }, 0);
      }
    });
  }, [fetchProjects]);

  const handleSelectProject = (project: Project) => {
    setActiveProject(project);
    setAnalysis(null);
    setSelectedCoords(null);
    setError(null);

    // Persist active project for cross-session restore
    localStorage.setItem("lastActiveProjectId", project.id);

    const stored = localStorage.getItem(`project_config_${project.id}`);
    if (stored) {
      try {
        setActiveConfig(JSON.parse(stored));
      } catch {
        setActiveConfig(null);
      }
    } else {
      setActiveConfig(null);
    }
  };

  const handleProjectCreated = (projectId: string, config: ProjectWizardData) => {
    setWizardOpen(false);
    
    fetchProjects().then(() => {
      const newProject: Project = {
        id: projectId,
        name: config.name,
        description: `${config.sector} — ${config.optimizationObjective}`,
      };
      handleSelectProject(newProject);
      setActiveConfig(config);
    });
  };

  const handleLocationSelect = async (lat: number, lon: number) => {
    if (!activeProject) return;
    setSelectedCoords([lat, lon]);
    setLoading(true);
    setError(null);

    try {
      const res = await api.post("/api/analysis/scan-site", {
        latitude: lat,
        longitude: lon,
        system_capacity_kw: 1000,
      });
      setAnalysis(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Error scanning site.");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSite = async () => {
    if (!activeProject || !selectedCoords || !analysis) return;
    setLoading(true);

    try {
      const siteRes = await api.post(`/projects/${activeProject.id}/sites`, {
        name: `Site @ ${selectedCoords[0].toFixed(4)}, ${selectedCoords[1].toFixed(4)}`,
        latitude: selectedCoords[0],
        longitude: selectedCoords[1],
        region: activeConfig?.targetRegion || "India",
        land_area_sqkm: 5.0,
        elevation_m: 0.0,
        land_ownership: "Unknown",
      });

      const siteData = siteRes.data;
      await api.post(
        `/projects/${activeProject.id}/sites/${siteData.site_id}/analyze`
      );

      setError(null);
      
      alert("Site saved and analyzed successfully.");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Error saving site.");
    } finally {
      setLoading(false);
    }
  };

  const mapCenter: [number, number] | undefined =
    activeConfig?.targetRegion
      ? REGION_CENTERS[activeConfig.targetRegion]
      : undefined;

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-[1600px] mx-auto bg-background min-h-[calc(100vh-3.5rem)]">
      {}
      {!activeProject && (
        <div className="space-y-6 animate-in fade-in duration-300">
          <header className="flex items-center justify-between">
            <div className="space-y-1.5">
              <h2 className="text-2xl font-semibold tracking-tight text-foreground">
                Project Hub
              </h2>
              <p className="text-sm text-muted-foreground">
                Select an existing project or create a new one to begin site analysis.
              </p>
            </div>
            <Button onClick={() => setWizardOpen(true)} className="gap-2 shadow-lg shadow-primary/20">
              <Plus className="h-4 w-4" />
              New Project
            </Button>
          </header>

          {}
          {projectsLoading && (
            <div className="flex items-center justify-center p-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mr-3" />
              <span className="text-sm text-muted-foreground">Loading projects...</span>
            </div>
          )}

          {}
          {!projectsLoading && projects.length === 0 && (
            <div className="text-center p-16 border-2 border-dashed border-border rounded-xl bg-card/30">
              <FolderKanban className="mx-auto h-14 w-14 text-muted-foreground/40 mb-5" />
              <h3 className="text-lg font-semibold text-foreground mb-2">No projects yet</h3>
              <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
                Create your first project to define a target sector, spatial constraints, and begin scanning for optimal deployment sites.
              </p>
              <Button onClick={() => setWizardOpen(true)} className="gap-2">
                <Plus className="h-4 w-4" />
                Create First Project
              </Button>
            </div>
          )}

          {}
          {!projectsLoading && projects.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project: any) => {
                
                let config: ProjectWizardData | null = null;
                try {
                  const stored = localStorage.getItem(`project_config_${project.id}`);
                  if (stored) config = JSON.parse(stored);
                } catch {}

                return (
                  <Card
                    key={project.id}
                    className="group cursor-pointer border-border hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300"
                    onClick={() => handleSelectProject(project)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-base font-semibold text-foreground flex items-center gap-2">
                          <FolderKanban className="h-4 w-4 text-muted-foreground shrink-0" />
                          {project.name}
                        </CardTitle>
                        {config && <SectorBadge sector={config.sector} />}
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {project.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2">{project.description}</p>
                      )}
                      <div className="space-y-1.5 text-xs text-muted-foreground">
                        {config?.targetRegion && (
                          <div className="flex items-center gap-1.5">
                            <MapPin className="h-3 w-3" />
                            <span>{config.targetRegion}</span>
                          </div>
                        )}
                        {project.created_at && (
                          <div className="flex items-center gap-1.5">
                            <Calendar className="h-3 w-3" />
                            <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 text-xs font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity duration-200 pt-1">
                        Open Project
                        <ArrowRight className="h-3 w-3" />
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {}
      {activeProject && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {}
          <header className="flex items-center justify-between border-b border-border pb-4">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setActiveProject(null);
                  setActiveConfig(null);
                  setAnalysis(null);
                  setSelectedCoords(null);
                  fetchProjects();
                }}
                className="gap-1.5 text-muted-foreground hover:text-foreground"
              >
                <ArrowLeft className="h-4 w-4" />
                Projects
              </Button>
              <div className="h-6 w-px bg-border" />
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-semibold tracking-tight text-foreground">
                    {activeProject.name}
                  </h2>
                  {activeConfig && <SectorBadge sector={activeConfig.sector} />}
                </div>
                {activeConfig?.targetRegion && (
                  <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                    <MapPin className="h-3 w-3" />
                    {activeConfig.targetRegion}
                    {activeConfig.optimizationObjective && (
                      <>
                        <span className="mx-1">·</span>
                        <Tag className="h-3 w-3" />
                        {activeConfig.optimizationObjective.replace(/_/g, " ")}
                      </>
                    )}
                  </p>
                )}
              </div>
            </div>
            {analysis && selectedCoords && (
              <Button
                onClick={handleSaveSite}
                disabled={loading}
                size="sm"
                className="gap-2"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-4 w-4" />
                )}
                Save Site to Project
              </Button>
            )}
          </header>

          {}
          <div className="relative z-0 rounded-lg border border-border bg-card p-1 shadow-sm">
            <MapScanner
              onLocationSelect={handleLocationSelect}
              selectedPos={selectedCoords}
              center={mapCenter}
              zoom={mapCenter ? 8 : 7}
            />
          </div>

          {}
          {loading && (
            <div className="flex items-center justify-center p-6 border border-border rounded-lg bg-muted/40 text-muted-foreground text-sm shadow-sm">
              <Loader2 className="mr-3 h-4 w-4 animate-spin" />
              Ingesting NASA climate data and executing ML inference...
            </div>
          )}

          {}
          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm font-medium">
              {error}
            </div>
          )}

          {}
          {analysis && !loading && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 ease-in-out">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {}
                <Card className="shadow-sm">
                  <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Solar Potential
                    </CardTitle>
                    <Sun className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-foreground">
                      {analysis.predictions.solar.annual_energy_output_mwh}{" "}
                      <span className="text-sm font-normal text-muted-foreground">MWh/yr</span>
                    </div>
                    <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                      <div className="flex justify-between">
                        <span>Capacity Factor</span>
                        <span className="font-medium text-foreground">
                          {analysis.predictions.solar.capacity_factor_percent}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Irradiance</span>
                        <span className="font-medium text-foreground">
                          {analysis.climate_intelligence.annual_solar_irradiance_kwh_m2_day} kWh/m²
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {}
                <Card className="shadow-sm">
                  <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Wind Potential
                    </CardTitle>
                    <Wind className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-foreground">
                      {analysis.predictions.wind.annual_energy_output_mwh}{" "}
                      <span className="text-sm font-normal text-muted-foreground">MWh/yr</span>
                    </div>
                    <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                      <div className="flex justify-between">
                        <span>Capacity Factor</span>
                        <span className="font-medium text-foreground">
                          {analysis.predictions.wind.capacity_factor_percent}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Avg Wind Speed</span>
                        <span className="font-medium text-foreground">
                          {analysis.climate_intelligence.annual_wind_speed_50m_m_s} m/s
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {}
                <Card className="shadow-sm">
                  <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Infrastructure
                    </CardTitle>
                    <Zap className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 mt-1 text-sm text-muted-foreground">
                      <div className="flex justify-between items-center border-b border-border pb-1">
                        <span>Power Line</span>
                        <span className="font-medium text-foreground">
                          {analysis.infrastructure_intelligence.nearest_power_line_km ?? "N/A"} km
                        </span>
                      </div>
                      <div className="flex justify-between items-center border-b border-border pb-1">
                        <span>Substation</span>
                        <span className="font-medium text-foreground">
                          {analysis.infrastructure_intelligence.nearest_substation_km ?? "N/A"} km
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Major Road</span>
                        <span className="font-medium text-foreground">
                          {analysis.infrastructure_intelligence.nearest_major_road_km ?? "N/A"} km
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {}
                <Card
                  className={`shadow-sm ${
                    analysis.land_use_conflicts.is_unsuitable
                      ? "border-destructive bg-destructive/5"
                      : ""
                  }`}
                >
                  <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Land Use Screen
                    </CardTitle>
                    <Flag
                      className={`h-4 w-4 ${
                        analysis.land_use_conflicts.is_unsuitable
                          ? "text-destructive"
                          : "text-muted-foreground"
                      }`}
                    />
                  </CardHeader>
                  <CardContent>
                    {analysis.land_use_conflicts.is_unsuitable ? (
                      <div className="space-y-1 mt-1">
                        <p className="text-sm font-semibold text-destructive">
                          High Conflict Detected
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Location intersects with restricted zones. Not viable for deployment.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-1 mt-1">
                        <p className="text-sm font-semibold text-emerald-500 dark:text-emerald-400">
                          Clear for Feasibility
                        </p>
                        <p className="text-xs text-muted-foreground">
                          No critical hard flags detected in immediate radius.
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </div>
      )}

      {}
      <ProjectWizardModal
        open={wizardOpen}
        onOpenChange={setWizardOpen}
        onProjectCreated={handleProjectCreated}
      />
    </div>
  );
}
