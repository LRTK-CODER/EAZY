import { formatDistanceToNow } from '@/utils/date';
import { RotateCcw, Trash2 } from 'lucide-react';
import type { Project } from '@/types/project';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';

interface ArchivedProjectItemProps {
  project: Project;
  isSelected: boolean;
  onToggle: () => void;
  onRestore: () => void;
  onDelete: () => void;
}

export function ArchivedProjectItem({
  project,
  isSelected,
  onToggle,
  onRestore,
  onDelete,
}: ArchivedProjectItemProps) {
  return (
    <div className="border rounded-lg p-4 hover:bg-accent/50 transition-colors">
      <div className="flex items-center gap-4">
        <Checkbox checked={isSelected} onCheckedChange={onToggle} />

        <div className="flex-1">
          <h3 className="font-medium">{project.name}</h3>
          <p className="text-sm text-muted-foreground">
            {project.description || 'No description'}
          </p>
          {project.archived_at && (
            <p className="text-xs text-muted-foreground mt-1">
              Archived {formatDistanceToNow(project.archived_at, { addSuffix: true })}
            </p>
          )}
        </div>

        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={onRestore}>
            <RotateCcw className="h-4 w-4 mr-1" />
            Restore
          </Button>
          <Button size="sm" variant="destructive" onClick={onDelete}>
            <Trash2 className="h-4 w-4 mr-1" />
            Delete
          </Button>
        </div>
      </div>
    </div>
  );
}
