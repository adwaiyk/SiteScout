"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import api from '@/lib/api'; // Using our custom Axios interceptor
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Save, Loader2, CheckCircle2 } from "lucide-react";

// Dynamically import map with SSR disabled to prevent Leaflet 'window' crashes
const MapScanner = dynamic(() => import("@/components/MapScanner"), {
  ssr: false,
  loading: () => (
    <div className="h-[500px] w-full flex items-center justify-center bg-slate-800 text-slate-400 rounded-xl border border-slate-700">
      Loading Interactive Map...
    </div>
  ),
});

export default function DashboardPage() {
  const [selectedCoords, setSelectedCoords] = useState<[number, number] | null>(null);
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
      // 🚀 Replaced fetch with api.post
      const res = await api.post("/api/analysis/scan-site", {
        latitude: lat,
        longitude: lon,
        system_capacity_kw: 1000,
      });

      // Axios automatically parses JSON to res.data
      setAnalysis(res.data);
    } catch (err: any) {
      // Axios wraps backend errors in err.response.data
      setError(err.response?.data?.detail || err.message || "Error scanning site.");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProject = async () => {
    if (!selectedCoords) return;
    setIsSaving(true);

    try {
      // 🚀 No need to manually grab the token or set headers! 
      // api.ts handles all of that automatically.

      // 1. Create the Project
      const projRes = await api.post("/projects/", {
        name: projectName,
        description: "Saved via Map Scanner",
      });
      const projData = projRes.data;

      // 2. Register the Site to the Project
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

      // 3. Save the actual Analysis Log to the database!
      await api.post(`/projects/${projData.project_id}/sites/${siteData.site_id}/analyze`);

      setSaveSuccess(true);
      setTimeout(() => {
        setIsSaveModalOpen(false);
        setSaveSuccess(false);
        setProjectName("");
        setSiteName("");
      }, 2000);
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || "Error saving project. Make sure you are logged in!");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6 text-slate-100 max-w-7xl mx-auto">
      <header>
        <h2 className="text-3xl font-bold text-sky-400">
          Site Feasibility Scanner
        </h2>
        <p className="text-slate-400 mt-1">
          Click anywhere on the map to run real-time solar, wind, and
          infrastructure analysis.
        </p>
      </header>

      {/* Map Section */}
      <MapScanner
        onLocationSelect={handleLocationSelect}
        selectedPos={selectedCoords}
      />

      {/* Loading Spinner */}
      {loading && (
        <div className="p-6 bg-slate-800/80 rounded-xl text-center text-sky-400 animate-pulse font-semibold border border-sky-500/30">
          ⚡ Ingesting NASA climate data, mapping grid infrastructure, and
          predicting energy yield...
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="p-4 bg-red-900/50 border border-red-500 rounded-xl text-red-200">
          {error}
        </div>
      )}

      {/* Results Grid */}
      {analysis && !loading && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Solar Analytics */}
            <div className="bg-slate-800 p-6 rounded-xl border border-amber-500/30 space-y-2 hover:border-amber-500/60 transition-colors">
              <h3 className="text-lg font-bold text-amber-400">
                ☀️ Solar Potential
              </h3>
              <p className="text-2xl font-semibold">
                {analysis.predictions.solar.annual_energy_output_mwh} MWh/yr
              </p>
              <div className="text-sm text-slate-300">
                <p>
                  Capacity Factor:{" "}
                  <strong>
                    {analysis.predictions.solar.capacity_factor_percent}%
                  </strong>
                </p>
                <p>
                  Irradiance:{" "}
                  <strong>
                    {
                      analysis.climate_intelligence
                        .annual_solar_irradiance_kwh_m2_day
                    }{" "}
                    kWh/m²/day
                  </strong>
                </p>
              </div>
            </div>

            {/* Wind Analytics */}
            <div className="bg-slate-800 p-6 rounded-xl border border-blue-500/30 space-y-2 hover:border-blue-500/60 transition-colors">
              <h3 className="text-lg font-bold text-blue-400">
                💨 Wind Potential
              </h3>
              <p className="text-2xl font-semibold">
                {analysis.predictions.wind.annual_energy_output_mwh} MWh/yr
              </p>
              <div className="text-sm text-slate-300">
                <p>
                  Capacity Factor:{" "}
                  <strong>
                    {analysis.predictions.wind.capacity_factor_percent}%
                  </strong>
                </p>
                <p>
                  Avg Wind Speed:{" "}
                  <strong>
                    {analysis.climate_intelligence.annual_wind_speed_50m_m_s}{" "}
                    m/s
                  </strong>
                </p>
              </div>
            </div>

            {/* Infrastructure Proximity */}
            <div className="bg-slate-800 p-6 rounded-xl border border-emerald-500/30 space-y-2 hover:border-emerald-500/60 transition-colors">
              <h3 className="text-lg font-bold text-emerald-400">
                🔌 Infrastructure
              </h3>
              <div className="text-sm text-slate-300 space-y-1">
                <p>
                  Power Line:{" "}
                  <strong>
                    {analysis.infrastructure_intelligence
                      .nearest_power_line_km ?? "N/A"}{" "}
                    km
                  </strong>
                </p>
                <p>
                  Substation:{" "}
                  <strong>
                    {analysis.infrastructure_intelligence
                      .nearest_substation_km ?? "N/A"}{" "}
                    km
                  </strong>
                </p>
                <p>
                  Major Road:{" "}
                  <strong>
                    {analysis.infrastructure_intelligence
                      .nearest_major_road_km ?? "N/A"}{" "}
                    km
                  </strong>
                </p>
              </div>
            </div>

            {/* Conflict Detector */}
            <div
              className={`p-6 rounded-xl border space-y-2 ${analysis.land_use_conflicts.is_unsuitable ? "bg-red-950/40 border-red-500" : "bg-slate-800 border-slate-700"}`}
            >
              <h3 className="text-lg font-bold text-slate-200">
                🚩 Land Use Flags
              </h3>
              {analysis.land_use_conflicts.is_unsuitable ? (
                <p className="text-red-400 font-bold text-sm">
                  ⚠️ High Conflict Area Detected!
                </p>
              ) : (
                <p className="text-emerald-400 font-semibold text-sm">
                  ✅ Clear for Feasibility Screening
                </p>
              )}
            </div>
          </div>

          {/* SAVE BUTTON ACTION BAR */}
          <div className="flex justify-end pt-4">
            <Dialog open={isSaveModalOpen} onOpenChange={setIsSaveModalOpen}>
              <DialogTrigger
                className={buttonVariants({
                  className:
                    "bg-sky-600 hover:bg-sky-500 text-white gap-2 font-semibold cursor-pointer",
                })}
              >
                <Save className="h-4 w-4" /> Save Site to Profile
              </DialogTrigger>
              <DialogContent className="bg-slate-900 border-slate-700 text-slate-100 max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-sky-400">
                    Save Feasibility Scan
                  </DialogTitle>
                  <DialogDescription className="text-slate-400">
                    Store this location and its intelligence data in your
                    workspace.
                  </DialogDescription>
                </DialogHeader>

                {!saveSuccess ? (
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="project">Project Name</Label>
                      <Input
                        id="project"
                        placeholder="e.g., Pune Solar Farm Beta"
                        className="bg-slate-800 border-slate-700 text-slate-100"
                        value={projectName}
                        onChange={(e) => setProjectName(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="site">Site Name / Plot</Label>
                      <Input
                        id="site"
                        placeholder="e.g., Sector 4A"
                        className="bg-slate-800 border-slate-700 text-slate-100"
                        value={siteName}
                        onChange={(e) => setSiteName(e.target.value)}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="py-8 flex flex-col items-center justify-center space-y-3">
                    <CheckCircle2 className="h-12 w-12 text-emerald-500" />
                    <p className="text-lg font-medium text-emerald-400">
                      Successfully Saved!
                    </p>
                  </div>
                )}

                <DialogFooter>
                  {!saveSuccess && (
                    <Button
                      onClick={handleSaveProject}
                      disabled={isSaving || !projectName || !siteName}
                      className="bg-sky-600 hover:bg-sky-500 w-full"
                    >
                      {isSaving ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />{" "}
                          Saving to Database...
                        </>
                      ) : (
                        "Confirm & Save"
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