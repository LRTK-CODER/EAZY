import { Link } from 'react-router-dom';
import { ArrowLeft, FolderOpen, Loader2 } from 'lucide-react';
import { useProjects } from '@/hooks/useProjects';
import { Button } from '@/components/ui/button';
import { ActiveProjectItem } from '@/components/features/project/ActiveProjectItem';

export function ActiveProjectsListPage() {
  const { data: projects = [], isLoading, isError } = useProjects();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-destructive">Failed to load active projects</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Active Projects</h1>
          <p className="text-muted-foreground">
            {projects.length} active project{projects.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Link to="/projects">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Projects
          </Button>
        </Link>
      </div>

      {/* Project List */}
      {projects.length === 0 ? (
        <div className="text-center py-12">
          <FolderOpen className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium mb-2">No active projects</h3>
          <p className="text-muted-foreground">
            Get started by creating your first project.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map((project) => (
            <ActiveProjectItem key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  );
}
