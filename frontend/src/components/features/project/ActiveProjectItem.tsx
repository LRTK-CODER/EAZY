import { formatDistanceToNow } from '@/utils/date';
import { Link } from 'react-router-dom';
import type { Project } from '@/types/project';

interface ActiveProjectItemProps {
  project: Project;
}

export function ActiveProjectItem({ project }: ActiveProjectItemProps) {
  return (
    <Link to={`/projects/${project.id}`}>
      <div className="border rounded-lg p-4 hover:bg-accent/50 transition-colors">
        <h3 className="font-medium mb-1">{project.name}</h3>
        <p className="text-sm text-muted-foreground mb-2">
          {project.description || 'No description'}
        </p>
        <p className="text-xs text-muted-foreground">
          Updated {formatDistanceToNow(project.updated_at, { addSuffix: true })}
        </p>
      </div>
    </Link>
  );
}
