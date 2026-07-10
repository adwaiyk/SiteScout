"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { FolderPlus, MapPin, Loader2, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 1. Check for token on load
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/"); // Boot them back to login if unauthorized
      return;
    }

    // 2. Fetch their projects
    const fetchProjects = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/projects/", {
          headers: { Authorization: `Bearer ${token}` }
        });
        setProjects(response.data);
      } catch (error) {
        console.error("Failed to fetch projects", error);
        // If token is expired/invalid, clear it and kick them out
        localStorage.removeItem("token");
        router.push("/");
      } finally {
        setIsLoading(false);
      }
    };

    fetchProjects();
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="h-8 w-8 animate-spin text-slate-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header Section */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Deployment Workspace</h1>
            <p className="text-slate-500 mt-1">Manage your renewable energy projects and sites.</p>
          </div>
          <div className="flex gap-4">
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
            <Button>
              <FolderPlus className="mr-2 h-4 w-4" />
              New Project
            </Button>
          </div>
        </div>

        {/* Projects Grid */}
        {projects.length === 0 ? (
          <div className="text-center p-12 border-2 border-dashed rounded-lg border-slate-200">
            <h3 className="text-lg font-medium text-slate-900">No projects yet</h3>
            <p className="text-slate-500 mt-1 mb-4">Create your first deployment project to get started.</p>
            <Button>
              <FolderPlus className="mr-2 h-4 w-4" />
              Create Project
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project, idx) => (
              <Card key={idx} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle>{project.name}</CardTitle>
                  <CardDescription>{project.description || "No description provided."}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="secondary" className="w-full">
                    <MapPin className="mr-2 h-4 w-4" />
                    View Sites
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}