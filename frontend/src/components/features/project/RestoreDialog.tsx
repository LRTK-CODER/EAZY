import { toast } from 'sonner';
import { useRestoreProject, useRestoreProjects } from '@/hooks/useProjects';
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

interface RestoreDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectIds: number[];
  projectNames: string[];
}

export function RestoreDialog({
  open,
  onOpenChange,
  projectIds,
  projectNames,
}: RestoreDialogProps) {
  const restoreProject = useRestoreProject();
  const restoreProjects = useRestoreProjects();

  const isRestoring = restoreProject.isPending || restoreProjects.isPending;
  const isBulk = projectIds.length > 1;
  const count = projectIds.length;

  const handleRestore = async () => {
    try {
      if (isBulk) {
        await restoreProjects.mutateAsync(projectIds);
        toast.success(`${count} projects restored`);
      } else {
        await restoreProject.mutateAsync(projectIds[0]);
        toast.success('Project restored');
      }
      onOpenChange(false);
    } catch {
      toast.error(isBulk ? 'Failed to restore projects' : 'Failed to restore project');
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {isBulk ? `Restore ${count} Projects?` : 'Restore Project?'}
          </AlertDialogTitle>
          <AlertDialogDescription>
            {isBulk ? (
              `These ${count} projects will be restored to your active projects list.`
            ) : (
              <>
                Restore <strong>{projectNames[0]}</strong> to your active projects?
              </>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>

        {isBulk && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Projects to restore:</p>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
              {projectNames.map((name, index) => (
                <li key={index}>{name}</li>
              ))}
            </ul>
          </div>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isRestoring}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              handleRestore();
            }}
            disabled={isRestoring}
          >
            Restore
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
