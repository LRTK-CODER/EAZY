import { toast } from 'sonner';
import { AlertCircle } from 'lucide-react';
import { AxiosError } from 'axios';
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
      toast.success('Target deleted successfully', {
        description: 'Related tasks and assets were also removed.',
      });
      onOpenChange(false);
    } catch (error) {
      // 에러 타입별 상세 메시지 제공
      if (error instanceof AxiosError) {
        const statusCode = error.response?.status;
        const errorDetail = error.response?.data?.detail || 'Unknown error';

        if (statusCode === 404) {
          toast.error('Target not found', {
            description: 'The target may have been already deleted.',
          });
        } else if (statusCode === 500) {
          toast.error('Failed to delete target', {
            description: `Database error: ${errorDetail}`,
          });
        } else {
          toast.error('Failed to delete target', {
            description: errorDetail,
          });
        }
      } else {
        toast.error('Failed to delete target', {
          description: 'An unexpected error occurred. Please try again.',
        });
      }
      console.error('Delete target error:', error);
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

        <AlertDialogDescription className="flex items-center gap-2 text-destructive">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>
            This will permanently delete the target and all related tasks, assets, and
            scan history. This action cannot be undone.
          </span>
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
