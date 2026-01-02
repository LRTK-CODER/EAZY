import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, ArrowRight, Loader2 } from 'lucide-react';
import { useProjects, useArchivedProjects } from '@/hooks/useProjects';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CreateProjectForm } from '@/components/features/project/CreateProjectForm';

export function ProjectsPage() {
  const { data: projects = [], isLoading: projectsLoading } = useProjects();
  const { data: archivedProjects = [], isLoading: archivedLoading } = useArchivedProjects();
  const [createOpen, setCreateOpen] = useState(false);
  const navigate = useNavigate();

  const isLoading = projectsLoading || archivedLoading;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Projects</h1>
          <p className="text-muted-foreground">
            Manage your security testing projects
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Project
        </Button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardContent className="pt-6">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Statistics Cards */}
      {!isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Active Projects Card */}
          <Card className="hover:shadow-md transition-shadow">
            <CardHeader>
              <CardTitle className="text-lg">Active</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold mb-4">{projects.length}</div>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => navigate('/projects/active')}
              >
                View All
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </CardContent>
          </Card>

          {/* Archived Projects Card */}
          <Card className="hover:shadow-md transition-shadow">
            <CardHeader>
              <CardTitle className="text-lg">Archived</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold mb-4">{archivedProjects.length}</div>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => navigate('/projects/archived')}
              >
                View Archive
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Create Project Dialog */}
      <CreateProjectForm open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}
