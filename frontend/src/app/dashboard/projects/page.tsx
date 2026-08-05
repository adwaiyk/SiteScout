'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FolderGit2, MapPin, Calendar, ArrowRight } from 'lucide-react';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch user projects on mount
    const fetchProjects = async () => {
      try {
        const token = localStorage.getItem('token'); // Grab the JWT
        const res = await fetch('http://127.0.0.1:8000/projects/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (res.ok) {
          const data = await res.json();
          setProjects(data);
        }
      } catch (error) {
        console.error("Failed to fetch projects:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, []);

  if (loading) {
    return <div className="text-sky-400 animate-pulse font-semibold flex h-full items-center justify-center">Loading Project History...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-sky-400">My Projects</h1>
        <p className="text-slate-400">View and manage your saved site feasibility scans.</p>
      </header>

      {projects.length === 0 ? (
        <div className="text-center p-12 border-2 border-dashed border-slate-700 rounded-xl bg-slate-800/30">
          <FolderGit2 className="mx-auto h-12 w-12 text-slate-500 mb-4" />
          <h3 className="text-lg font-medium text-slate-200">No projects yet</h3>
          <p className="text-slate-400 mt-2">Go to the Map Scanner to analyze and save your first site.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project: any) => (
            <Card key={project.id} className="bg-slate-800 border-slate-700 hover:border-sky-500/50 transition-colors">
              <CardHeader className="pb-3">
                <CardTitle className="text-xl text-slate-100 flex items-center gap-2">
                  <FolderGit2 className="h-5 w-5 text-sky-400" />
                  {project.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {project.description && (
                  <p className="text-sm text-slate-400 line-clamp-2">{project.description}</p>
                )}
                
                <div className="space-y-2 text-sm text-slate-300">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-emerald-400" />
                    <span>{project.system_type} System</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-amber-400" />
                    <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <Button className="w-full mt-4 bg-sky-600 hover:bg-sky-500 text-white group">
                  View Site Analytics
                  <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}