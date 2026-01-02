import { toast } from 'sonner';
import { useDeleteProject, useDeleteProjects } from '@/hooks/useProjects';
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

interface ArchivedDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectIds: number[];
  projectNames: string[];
}

export function ArchivedDialog({
  open,
  onOpenChange,
  projectIds,
  projectNames,
}: ArchivedDialogProps) {
  const archiveProject = useDeleteProject();
  const archiveProjects = useDeleteProjects();

  const isArchiving = archiveProject.isPending || archiveProjects.isPending;
  const isBulk = projectIds.length > 1;
  const count = projectIds.length;

  const handleArchive = async () => {
    try {
      if (isBulk) {
        await archiveProjects.mutateAsync(projectIds);
        toast.success(`${count} projects moved to archive`);
      } else {
        await archiveProject.mutateAsync(projectIds[0]);
        toast.success('Project moved to archive');
      }
      onOpenChange(false);
    } catch {
      toast.error(isBulk ? 'Failed to archive projects' : 'Failed to archive project');
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {isBulk ? `Archive ${count} Projects?` : 'Archive Project?'}
          </AlertDialogTitle>
          <AlertDialogDescription>
            {isBulk ? (
              `These ${count} projects will be moved to the archive.`
            ) : (
              <>
                Move <strong>{projectNames[0]}</strong> to the archive?
              </>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>

        {isBulk && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Projects to archive:</p>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
              {projectNames.map((name, index) => (
                <li key={index}>{name}</li>
              ))}
            </ul>
          </div>
        )}

        <AlertDialogDescription className="text-muted-foreground">
          You can restore these projects from the Archived page later.
        </AlertDialogDescription>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isArchiving}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              handleArchive();
            }}
            disabled={isArchiving}
          >
            Move to Archive
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
