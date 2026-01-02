import { toast } from 'sonner';
import { useDeletePermanent, useDeletePermanentBulk } from '@/hooks/useProjects';
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

interface PermanentDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectIds: number[];
  projectNames: string[];
}

export function PermanentDeleteDialog({
  open,
  onOpenChange,
  projectIds,
  projectNames,
}: PermanentDeleteDialogProps) {
  const deletePermanent = useDeletePermanent();
  const deletePermanentBulk = useDeletePermanentBulk();

  const isDeleting = deletePermanent.isPending || deletePermanentBulk.isPending;
  const isBulk = projectIds.length > 1;
  const count = projectIds.length;

  const handleDelete = async () => {
    try {
      if (isBulk) {
        await deletePermanentBulk.mutateAsync(projectIds);
        toast.success(`${count} projects permanently deleted`);
      } else {
        await deletePermanent.mutateAsync(projectIds[0]);
        toast.success('Project permanently deleted');
      }
      onOpenChange(false);
    } catch {
      toast.error(isBulk ? 'Failed to delete projects' : 'Failed to delete project');
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-destructive">
            ⚠️ Permanently Delete {isBulk ? `${count} Projects` : 'Project'}?
          </AlertDialogTitle>
          <AlertDialogDescription>
            This action <strong>CANNOT</strong> be undone.{' '}
            {isBulk ? (
              `These ${count} projects`
            ) : (
              <><strong>{projectNames[0]}</strong></>
            )}{' '}
            will be permanently deleted from the database.
          </AlertDialogDescription>
        </AlertDialogHeader>

        {isBulk && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Projects to be permanently deleted:</p>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
              {projectNames.map((name, index) => (
                <li key={index}>{name}</li>
              ))}
            </ul>
          </div>
        )}

        <AlertDialogDescription className="text-destructive font-semibold">
          ⚠️ This is irreversible. All project data will be lost forever.
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
            Permanently Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
