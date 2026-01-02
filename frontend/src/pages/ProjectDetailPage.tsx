import { useParams, Link } from 'react-router-dom';
import { Loader2, AlertCircle, ArrowLeft } from 'lucide-react';
import { formatDistanceToNow } from '@/utils/date';
import { useProject } from '@/hooks/useProjects';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: project, isLoading, isError } = useProject(Number(id));

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError || !project) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
          <h2 className="text-xl font-semibold mb-2">Project not found</h2>
          <p className="text-muted-foreground">
            The project you're looking for doesn't exist.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Project Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">{project.name}</h1>
          <p className="text-muted-foreground">
            {project.description || 'No description provided'}
          </p>
        </div>
        <Link to="/projects">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Projects
          </Button>
        </Link>
      </div>

      {/* Metadata */}
      <div className="flex items-center gap-4 text-sm text-muted-foreground mb-6">
        <span>
          Created {formatDistanceToNow(project.created_at, { addSuffix: true })}
        </span>
        <span>•</span>
        <span>
          Updated {formatDistanceToNow(project.updated_at, { addSuffix: true })}
        </span>
      </div>

      <Separator className="mb-6" />

      {/* Future expansion area - Tabs, Scan Results, etc. */}
      <div className="text-muted-foreground">
        Additional project features will be added here.
      </div>
    </div>
  );
}
