import { toast } from 'sonner';
import { useDeleteTarget } from '@/hooks/useTargets';
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
import type { Target } from '@/types/target';

interface DeleteTargetDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  target: Target | null;
  projectId: number;
}

export function DeleteTargetDialog({
  open,
  onOpenChange,
  target,
  projectId,
}: DeleteTargetDialogProps) {
  const deleteTarget = useDeleteTarget();

  const isDeleting = deleteTarget.isPending;

  const handleDelete = async () => {
    if (!target) return;

    try {
      await deleteTarget.mutateAsync({ projectId, targetId: target.id });
      toast.success('Target deleted successfully');
      onOpenChange(false);
    } catch {
      toast.error('Failed to delete target');
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Target?</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete{' '}
            {target ? (
              <>
                <strong>{target.name}</strong>?
              </>
            ) : (
              'this target?'
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>

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
