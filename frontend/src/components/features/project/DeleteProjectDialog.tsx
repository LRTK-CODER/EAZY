import { useState } from 'react';
import { toast } from 'sonner';
import * as projectService from '@/services/projectService';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

interface DeleteProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectIds: number[];
  projectNames: string[];
}

export function DeleteProjectDialog({
  open,
  onOpenChange,
  projectIds,
  projectNames,
}: DeleteProjectDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const isBulk = projectIds.length > 1;
  const count = projectIds.length;

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      if (isBulk) {
        await projectService.deleteProjects(projectIds);
        toast.success(`${count} projects deleted successfully`);
      } else {
        await projectService.deleteProject(projectIds[0]);
        toast.success('Project deleted successfully');
      }
      onOpenChange(false);
    } catch {
      toast.error(isBulk ? 'Failed to delete projects' : 'Failed to delete project');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {isBulk ? `Delete ${count} Projects?` : 'Delete Project?'}
          </AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete{' '}
            {isBulk ? (
              'the following projects?'
            ) : (
              <>
                <strong>{projectNames[0]}</strong>?
              </>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>

        {isBulk && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Projects to be deleted:</p>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
              {projectNames.map((name, index) => (
                <li key={index}>{name}</li>
              ))}
            </ul>
          </div>
        )}

        <AlertDialogDescription className="text-destructive">
          This action cannot be undone.
        </AlertDialogDescription>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              handleDelete();
            }}
            disabled={isDeleting}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
