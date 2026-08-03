"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  ArrowRight,
  ArrowLeft,
  Loader2,
  Check,
  Zap,
  Sun,
  Wind,
  Battery,
  Car,
  Warehouse,
  Building2,
  Target,
  TrendingDown,
  Timer,
  BarChart3,
} from "lucide-react";
import api from "@/lib/api";

// ---------- Types ----------

export interface ProjectWizardData {
  // Step 1: Identity & Sector
  name: string;
  sector: string;
  optimizationObjective: string;
  // Step 2: Spatial Constraints
  targetRegion: string;
  plotScaleMin: number;
  plotScaleMax: number;
  maxSubstationDistance: number;
  minVoltage: number;
  maxSlope: number;
  exclusionBuffers: string[];
  // Step 3: Financial Defaults
  maxLeaseBudget: number;
  targetWacc: number;
  projectLifespan: number;
}

interface ProjectWizardModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onProjectCreated: (projectId: string, config: ProjectWizardData) => void;
}

// ---------- Constants ----------

const SECTORS = [
  { value: "solar_pv", label: "Solar PV Farm", icon: Sun },
  { value: "wind_energy", label: "Wind Energy", icon: Wind },
  { value: "bess", label: "BESS / Battery Storage", icon: Battery },
  { value: "ev_charging", label: "EV Charging Hub", icon: Car },
  { value: "logistics", label: "Logistics / Warehousing", icon: Warehouse },
  { value: "commercial_re", label: "Commercial Real Estate", icon: Building2 },
];

const OPTIMIZATION_OBJECTIVES = [
  { value: "lowest_capex", label: "Lowest CapEx", icon: TrendingDown, desc: "Minimize upfront capital investment" },
  { value: "max_yield", label: "Maximum Energy Yield", icon: BarChart3, desc: "Maximize annual energy production" },
  { value: "lowest_lcoe", label: "Lowest LCOE", icon: Target, desc: "Optimize levelized cost of energy" },
  { value: "fastest_permitting", label: "Fastest Permitting", icon: Timer, desc: "Prioritize sites with fewest regulatory barriers" },
];

const REGIONS = [
  "Maharashtra, India",
  "Rajasthan, India",
  "Gujarat, India",
  "Tamil Nadu, India",
  "Karnataka, India",
  "Andhra Pradesh, India",
  "Madhya Pradesh, India",
  "Telangana, India",
  "Uttar Pradesh, India",
  "Punjab, India",
  "Custom Bounding Box",
];

const EXCLUSION_BUFFERS = [
  { id: "wetlands", label: "Protected Wetlands" },
  { id: "floodplains", label: "100-Year Floodplains" },
  { id: "national_parks", label: "National Parks / Wildlife Sanctuaries" },
  { id: "residential", label: "Residential Setbacks [300m]" },
];

// ---------- Default values ----------

const DEFAULT_WIZARD_DATA: ProjectWizardData = {
  name: "",
  sector: "solar_pv",
  optimizationObjective: "max_yield",
  targetRegion: "Maharashtra, India",
  plotScaleMin: 10,
  plotScaleMax: 500,
  maxSubstationDistance: 50,
  minVoltage: 33,
  maxSlope: 5,
  exclusionBuffers: ["wetlands", "national_parks"],
  maxLeaseBudget: 0,
  targetWacc: 6.5,
  projectLifespan: 25,
};

// ---------- Component ----------

export default function ProjectWizardModal({
  open,
  onOpenChange,
  onProjectCreated,
}: ProjectWizardModalProps) {
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState<ProjectWizardData>({ ...DEFAULT_WIZARD_DATA });

  const updateField = <K extends keyof ProjectWizardData>(
    key: K,
    value: ProjectWizardData[K]
  ) => {
    setData((prev) => ({ ...prev, [key]: value }));
  };

  const toggleExclusion = (id: string) => {
    setData((prev) => ({
      ...prev,
      exclusionBuffers: prev.exclusionBuffers.includes(id)
        ? prev.exclusionBuffers.filter((b) => b !== id)
        : [...prev.exclusionBuffers, id],
    }));
  };

  const isStep1Valid = data.name.trim().length > 0;
  const isStep2Valid = data.targetRegion.length > 0 && data.plotScaleMax > data.plotScaleMin;

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError("");

    try {
      // Create project via backend API
      const res = await api.post("/projects/", {
        name: data.name,
        description: `${SECTORS.find((s) => s.value === data.sector)?.label || data.sector} — ${OPTIMIZATION_OBJECTIVES.find((o) => o.value === data.optimizationObjective)?.label || data.optimizationObjective}`,
      });

      const projectId = res.data.project_id;

      // Store wizard configuration in localStorage (frontend-only for now)
      localStorage.setItem(
        `project_config_${projectId}`,
        JSON.stringify(data)
      );

      // Reset state
      setStep(1);
      setData({ ...DEFAULT_WIZARD_DATA });
      onProjectCreated(projectId, data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create project. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = (isOpen: boolean) => {
    if (!isOpen) {
      setStep(1);
      setError("");
    }
    onOpenChange(isOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[640px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">
            {step === 1 && "Create New Project"}
            {step === 2 && "Spatial & Technical Constraints"}
            {step === 3 && "Financial Defaults"}
          </DialogTitle>
          <DialogDescription>
            {step === 1 && "Define the project identity, target sector, and optimization objective."}
            {step === 2 && "Configure site selection filters and spatial boundaries."}
            {step === 3 && "Set optional commercial parameters for yield-weighted scoring."}
          </DialogDescription>
        </DialogHeader>

        {/* Step indicator */}
        <div className="flex items-center gap-2 py-2">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center gap-2 flex-1">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 transition-all duration-300 ${
                  step > s
                    ? "bg-emerald-500/20 text-emerald-500 border border-emerald-500/30"
                    : step === s
                      ? "bg-primary text-primary-foreground shadow-md shadow-primary/25"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                {step > s ? <Check className="h-4 w-4" /> : s}
              </div>
              {s < 3 && (
                <div className="flex-1 h-px bg-border">
                  <div
                    className={`h-full transition-all duration-500 ${
                      step > s ? "bg-emerald-500 w-full" : "bg-transparent w-0"
                    }`}
                  />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* ===== STEP 1: Identity & Sector ===== */}
        {step === 1 && (
          <div className="space-y-5 animate-in fade-in slide-in-from-right-4 duration-300">
            {/* Project Name */}
            <div className="space-y-2">
              <Label htmlFor="wizard-project-name" className="text-sm font-medium">
                Project Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="wizard-project-name"
                placeholder="e.g., Nevada Solar Expansion Phase 1"
                value={data.name}
                onChange={(e) => updateField("name", e.target.value)}
                className="h-10"
              />
            </div>

            {/* Industry Sector */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">
                Industry Sector <span className="text-destructive">*</span>
              </Label>
              <div className="grid grid-cols-2 gap-2">
                {SECTORS.map((s) => (
                  <label
                    key={s.value}
                    className={`flex items-center gap-2.5 p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                      data.sector === s.value
                        ? "border-primary bg-primary/5 shadow-sm shadow-primary/10"
                        : "border-border hover:border-muted-foreground/30 hover:bg-muted/50"
                    }`}
                  >
                    <input
                      type="radio"
                      name="sector"
                      value={s.value}
                      checked={data.sector === s.value}
                      onChange={() => updateField("sector", s.value)}
                      className="sr-only"
                    />
                    <s.icon className={`h-4 w-4 shrink-0 ${data.sector === s.value ? "text-primary" : "text-muted-foreground"}`} />
                    <span className="text-sm font-medium">{s.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Optimization Objective */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">
                Optimization Objective <span className="text-destructive">*</span>
              </Label>
              <div className="space-y-2">
                {OPTIMIZATION_OBJECTIVES.map((obj) => (
                  <label
                    key={obj.value}
                    className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                      data.optimizationObjective === obj.value
                        ? "border-primary bg-primary/5 shadow-sm shadow-primary/10"
                        : "border-border hover:border-muted-foreground/30 hover:bg-muted/50"
                    }`}
                  >
                    <input
                      type="radio"
                      name="objective"
                      value={obj.value}
                      checked={data.optimizationObjective === obj.value}
                      onChange={() => updateField("optimizationObjective", obj.value)}
                      className="sr-only"
                    />
                    <obj.icon className={`h-4 w-4 mt-0.5 shrink-0 ${data.optimizationObjective === obj.value ? "text-primary" : "text-muted-foreground"}`} />
                    <div>
                      <p className="text-sm font-medium">{obj.label}</p>
                      <p className="text-xs text-muted-foreground">{obj.desc}</p>
                    </div>
                    {data.optimizationObjective === obj.value && (
                      <div className="ml-auto flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                        <Check className="h-3 w-3" />
                      </div>
                    )}
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ===== STEP 2: Spatial & Technical Constraints ===== */}
        {step === 2 && (
          <div className="space-y-5 animate-in fade-in slide-in-from-right-4 duration-300">
            {/* Target Region */}
            <div className="space-y-2">
              <Label htmlFor="wizard-region" className="text-sm font-medium">
                Target Region <span className="text-destructive">*</span>
              </Label>
              <select
                id="wizard-region"
                value={data.targetRegion}
                onChange={(e) => updateField("targetRegion", e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {REGIONS.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>

            {/* Plot Scale */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Plot Scale (Acres)</Label>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground">Minimum</span>
                  <Input
                    type="number"
                    value={data.plotScaleMin}
                    onChange={(e) => updateField("plotScaleMin", Number(e.target.value))}
                    min={1}
                    className="h-9"
                  />
                </div>
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground">Maximum</span>
                  <Input
                    type="number"
                    value={data.plotScaleMax}
                    onChange={(e) => updateField("plotScaleMax", Number(e.target.value))}
                    min={1}
                    className="h-9"
                  />
                </div>
              </div>
            </div>

            {/* Grid Interconnection */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Grid Interconnection</Label>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground">Max Substation Distance (km)</span>
                  <Input
                    type="number"
                    value={data.maxSubstationDistance}
                    onChange={(e) => updateField("maxSubstationDistance", Number(e.target.value))}
                    min={1}
                    className="h-9"
                  />
                </div>
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground">Min Required Voltage (kV)</span>
                  <Input
                    type="number"
                    value={data.minVoltage}
                    onChange={(e) => updateField("minVoltage", Number(e.target.value))}
                    min={1}
                    className="h-9"
                  />
                </div>
              </div>
            </div>

            {/* Topography */}
            <div className="space-y-2">
              <Label htmlFor="wizard-slope" className="text-sm font-medium">
                Maximum Allowable Land Slope (%)
              </Label>
              <div className="flex items-center gap-3">
                <Input
                  id="wizard-slope"
                  type="number"
                  value={data.maxSlope}
                  onChange={(e) => updateField("maxSlope", Number(e.target.value))}
                  min={0}
                  max={45}
                  step={0.5}
                  className="h-9 w-24"
                />
                <span className="text-sm text-muted-foreground">
                  {data.maxSlope <= 5 ? "Flat terrain (Solar arrays)" : data.maxSlope <= 15 ? "Moderate slope" : "Steep terrain"}
                </span>
              </div>
            </div>

            {/* Exclusion Buffers */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Exclusion Buffers</Label>
              <div className="space-y-2">
                {EXCLUSION_BUFFERS.map((buf) => (
                  <label
                    key={buf.id}
                    className="flex items-center gap-3 p-2.5 rounded-lg border border-border hover:bg-muted/50 cursor-pointer transition-colors"
                  >
                    <Checkbox
                      checked={data.exclusionBuffers.includes(buf.id)}
                      onCheckedChange={() => toggleExclusion(buf.id)}
                    />
                    <span className="text-sm">{buf.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ===== STEP 3: Financial Defaults ===== */}
        {step === 3 && (
          <div className="space-y-5 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/10 text-sm text-blue-400">
              <Zap className="inline h-4 w-4 mr-1.5 -mt-0.5" />
              These fields are optional. Default values will be used if left unchanged.
            </div>

            {/* Max Lease Budget */}
            <div className="space-y-2">
              <Label htmlFor="wizard-lease" className="text-sm font-medium">
                Max Lease Budget ($/acre/year)
              </Label>
              <Input
                id="wizard-lease"
                type="number"
                value={data.maxLeaseBudget || ""}
                onChange={(e) => updateField("maxLeaseBudget", Number(e.target.value))}
                placeholder="e.g., 800"
                min={0}
                className="h-10"
              />
            </div>

            {/* Target WACC */}
            <div className="space-y-2">
              <Label htmlFor="wizard-wacc" className="text-sm font-medium">
                Target WACC / Discount Rate (%)
              </Label>
              <Input
                id="wizard-wacc"
                type="number"
                value={data.targetWacc}
                onChange={(e) => updateField("targetWacc", Number(e.target.value))}
                step={0.1}
                min={0}
                max={30}
                className="h-10"
              />
            </div>

            {/* Project Lifespan */}
            <div className="space-y-2">
              <Label htmlFor="wizard-lifespan" className="text-sm font-medium">
                Project Operational Lifespan (Years)
              </Label>
              <Input
                id="wizard-lifespan"
                type="number"
                value={data.projectLifespan}
                onChange={(e) => updateField("projectLifespan", Number(e.target.value))}
                min={1}
                max={50}
                className="h-10"
              />
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
            <p className="text-sm font-medium text-destructive">{error}</p>
          </div>
        )}

        {/* Footer Navigation */}
        <DialogFooter className="flex-row gap-3 sm:justify-between">
          <div>
            {step > 1 && (
              <Button variant="ghost" onClick={() => setStep(step - 1)} className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            {step < 3 ? (
              <Button
                onClick={() => setStep(step + 1)}
                disabled={step === 1 ? !isStep1Valid : step === 2 ? !isStep2Valid : false}
                className="gap-2"
              >
                {step === 2 ? "Review Financials" : "Configure Constraints"}
                <ArrowRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="gap-2 min-w-[140px]"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4" />
                    Launch Project
                  </>
                )}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
