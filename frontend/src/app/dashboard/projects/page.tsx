"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";
import ProjectWizardModal, {
  type ProjectWizardData,
} from "@/components/ProjectWizardModal";
import {
  FolderKanban,
  MapPin,
  Calendar,
  ArrowRight,
  Plus,
  Loader2,
  Tag,
} from "lucide-react";

// ---------- Sector badge ----------

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

// ---------- Main Component ----------

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [wizardOpen, setWizardOpen] = useState(false);
  const router = useRouter();

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const res = await api.get("/projects/");
      setProjects(res.data);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleProjectCreated = (projectId: string, config: ProjectWizardData) => {
    setWizardOpen(false);
    // Navigate to dashboard which will auto-select the new project
    router.push("/dashboard");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 min-h-[calc(100vh-3.5rem)]">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mr-3" />
        <span className="text-sm text-muted-foreground">Loading projects...</span>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-[1600px] mx-auto space-y-6">
      <header className="flex items-center justify-between">
        <div className="space-y-1.5">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">My Projects</h2>
          <p className="text-sm text-muted-foreground">
            View and manage your saved site feasibility projects.
          </p>
        </div>
        <Button onClick={() => setWizardOpen(true)} className="gap-2 shadow-lg shadow-primary/20">
          <Plus className="h-4 w-4" />
          New Project
        </Button>
      </header>

      {projects.length === 0 ? (
        <div className="text-center p-16 border-2 border-dashed border-border rounded-xl bg-card/30">
          <FolderKanban className="mx-auto h-14 w-14 text-muted-foreground/40 mb-5" />
          <h3 className="text-lg font-semibold text-foreground mb-2">No projects yet</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
            Create your first project to define a target sector, spatial constraints,
            and begin scanning for optimal deployment sites.
          </p>
          <Button onClick={() => setWizardOpen(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            Create First Project
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project: any) => {
            // Load config from localStorage for sector badge
            let config: ProjectWizardData | null = null;
            try {
              const stored = localStorage.getItem(`project_config_${project.id}`);
              if (stored) config = JSON.parse(stored);
            } catch {}

            return (
              <Card
                key={project.id}
                className="group cursor-pointer border-border hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300"
                onClick={() => router.push("/dashboard")}
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
                    {config?.optimizationObjective && (
                      <div className="flex items-center gap-1.5">
                        <Tag className="h-3 w-3" />
                        <span className="capitalize">{config.optimizationObjective.replace(/_/g, " ")}</span>
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
                    Open in Scanner
                    <ArrowRight className="h-3 w-3" />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Wizard Modal */}
      <ProjectWizardModal
        open={wizardOpen}
        onOpenChange={setWizardOpen}
        onProjectCreated={handleProjectCreated}
      />
    </div>
  );
}