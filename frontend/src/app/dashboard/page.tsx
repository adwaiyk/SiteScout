"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Save,
  Loader2,
  CheckCircle2,
  Sun,
  Wind,
  Zap,
  Flag,
} from "lucide-react";

// Dynamically import map with SSR disabled
const MapScanner = dynamic(() => import("@/components/MapScanner"), {
  ssr: false,
  loading: () => (
    <div className="h-[500px] w-full flex items-center justify-center bg-muted/30 text-muted-foreground rounded-md border border-border">
      <Loader2 className="h-6 w-6 animate-spin mr-3 text-muted-foreground" />
      Initializing GIS Canvas...
    </div>
  ),
});

export default function DashboardPage() {
  const [selectedCoords, setSelectedCoords] = useState<[number, number] | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Save Modal States
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [siteName, setSiteName] = useState("");

  const handleLocationSelect = async (lat: number, lon: number) => {
    setSelectedCoords([lat, lon]);
    setLoading(true);
    setError(null);
    setSaveSuccess(false);

    try {
      const res = await api.post("/api/analysis/scan-site", {
        latitude: lat,
        longitude: lon,
        system_capacity_kw: 1000,
      });
      setAnalysis(res.data);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || err.message || "Error scanning site.",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProject = async () => {
    if (!selectedCoords) return;
    setIsSaving(true);

    try {
      const projRes = await api.post("/projects/", {
        name: projectName,
        description: "Saved via Map Scanner",
      });
      const projData = projRes.data;

      const siteRes = await api.post(`/projects/${projData.project_id}/sites`, {
        name: siteName,
        latitude: selectedCoords[0],
        longitude: selectedCoords[1],
        region: "India",
        land_area_sqkm: 5.0,
        elevation_m: 0.0,
        land_ownership: "Unknown",
      });
      const siteData = siteRes.data;

      await api.post(
        `/projects/${projData.project_id}/sites/${siteData.site_id}/analyze`,
      );

      setSaveSuccess(true);
      setTimeout(() => {
        setIsSaveModalOpen(false);
        setSaveSuccess(false);
        setProjectName("");
        setSiteName("");
      }, 2000);
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || "Error saving project.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-[1600px] mx-auto bg-background min-h-[calc(100vh-3.5rem)]">
      {/* Enterprise Typography Header */}
      <header className="space-y-1.5">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          Feasibility Scanner
        </h2>
        <p className="text-sm text-muted-foreground">
          Select target coordinates to initiate real-time infrastructure and
          climate yield analysis.
        </p>
      </header>

      {/* Sharpened Map Canvas Container */}
      <div className="relative z-0 rounded-md border border-border bg-card p-1 shadow-sm">
        <MapScanner
          onLocationSelect={handleLocationSelect}
          selectedPos={selectedCoords}
        />
      </div>

      {/* Muted Loading State */}
      {loading && (
        <div className="flex items-center justify-center p-6 border border-border rounded-md bg-muted/40 text-muted-foreground text-sm shadow-sm">
          <Loader2 className="mr-3 h-4 w-4 animate-spin" />
          Ingesting NASA climate data and executing ML inference...
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md text-destructive text-sm font-medium">
          {error}
        </div>
      )}

      {/* Results Grid using shadcn Cards */}
      {analysis && !loading && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 ease-in-out">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Solar Analytics */}
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
                  <span className="text-sm font-normal text-muted-foreground">
                    MWh/yr
                  </span>
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
                      {
                        analysis.climate_intelligence
                          .annual_solar_irradiance_kwh_m2_day
                      }{" "}
                      kWh/m²
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Wind Analytics */}
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
                  <span className="text-sm font-normal text-muted-foreground">
                    MWh/yr
                  </span>
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
                      {analysis.climate_intelligence.annual_wind_speed_50m_m_s}{" "}
                      m/s
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Infrastructure Proximity */}
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
                      {analysis.infrastructure_intelligence
                        .nearest_power_line_km ?? "N/A"}{" "}
                      km
                    </span>
                  </div>
                  <div className="flex justify-between items-center border-b border-border pb-1">
                    <span>Substation</span>
                    <span className="font-medium text-foreground">
                      {analysis.infrastructure_intelligence
                        .nearest_substation_km ?? "N/A"}{" "}
                      km
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Major Road</span>
                    <span className="font-medium text-foreground">
                      {analysis.infrastructure_intelligence
                        .nearest_major_road_km ?? "N/A"}{" "}
                      km
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Conflict Detector */}
            <Card
              className={`shadow-sm ${analysis.land_use_conflicts.is_unsuitable ? "border-destructive bg-destructive/5" : ""}`}
            >
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Land Use Screen
                </CardTitle>
                <Flag
                  className={`h-4 w-4 ${analysis.land_use_conflicts.is_unsuitable ? "text-destructive" : "text-muted-foreground"}`}
                />
              </CardHeader>
              <CardContent>
                {analysis.land_use_conflicts.is_unsuitable ? (
                  <div className="space-y-1 mt-1">
                    <p className="text-sm font-semibold text-destructive">
                      High Conflict Detected
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Location intersects with restricted zones. Not viable for
                      deployment.
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

          {/* SAVE BUTTON ACTION BAR */}
          <div className="flex justify-end pt-2 border-t border-border">
            <Dialog open={isSaveModalOpen} onOpenChange={setIsSaveModalOpen}>
              <DialogTrigger
                className={buttonVariants({
                  variant: "default",
                  size: "sm",
                  className: "gap-2",
                })}
              >
                <Save className="h-4 w-4" /> Save Configuration
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>Save Feasibility Scan</DialogTitle>
                  <DialogDescription>
                    Store this coordinate profile and ML yield analysis to your
                    workspace.
                  </DialogDescription>
                </DialogHeader>

                {!saveSuccess ? (
                  <div className="grid gap-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="project">Project Designation</Label>
                      <Input
                        id="project"
                        placeholder="e.g., Alpha Phase 1"
                        value={projectName}
                        onChange={(e) => setProjectName(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="site">Site/Plot Identity</Label>
                      <Input
                        id="site"
                        placeholder="e.g., Sector 4A"
                        value={siteName}
                        onChange={(e) => setSiteName(e.target.value)}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="py-6 flex flex-col items-center justify-center space-y-3">
                    <CheckCircle2 className="h-10 w-10 text-emerald-500" />
                    <p className="text-sm font-medium text-foreground">
                      Scan committed to database.
                    </p>
                  </div>
                )}

                <DialogFooter>
                  {!saveSuccess && (
                    <Button
                      onClick={handleSaveProject}
                      disabled={isSaving || !projectName || !siteName}
                      className="w-full sm:w-auto"
                    >
                      {isSaving ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />{" "}
                          Committing...
                        </>
                      ) : (
                        "Save Profile"
                      )}
                    </Button>
                  )}
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      )}
    </div>
  );
}
