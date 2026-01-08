import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Check, X, Loader2, StopCircle } from 'lucide-react';
import { useMemo } from 'react';
import { useLatestTask, useCancelTask } from '@/hooks/useTasks';
import { TaskStatus } from '@/types/task';
import { formatElapsedTime } from '@/utils/date';

interface ScanStatusBadgeProps {
  targetId: number;
}

/**
 * Component to display scan status badge for a target with stop functionality
 *
 * Features:
 * - Displays current task status with appropriate badge variant
 * - Shows elapsed time for PENDING and RUNNING tasks
 * - Provides stop button to cancel PENDING or RUNNING tasks
 * - Automatically polls for task status updates (5s interval)
 * - Stops polling when task reaches terminal state (COMPLETED/FAILED/CANCELLED)
 *
 * @param targetId - The target ID to fetch and display the latest task status for
 *
 * @example
 * ```tsx
 * <ScanStatusBadge targetId={123} />
 * ```
 */
export function ScanStatusBadge({ targetId }: ScanStatusBadgeProps) {
  // Fetch latest task for this target with automatic polling
  const { data: task, isLoading } = useLatestTask(targetId);

  // Hook to cancel a task
  const cancelTask = useCancelTask();

  // Calculate elapsed time for PENDING and RUNNING tasks
  const elapsedTime = useMemo(() => {
    if (!task?.started_at) return null;
    return formatElapsedTime(task.started_at, task.completed_at);
  }, [task?.started_at, task?.completed_at]);

  // Determine if stop button should be shown (only for PENDING and RUNNING)
  const showStopButton =
    task?.status === TaskStatus.RUNNING ||
    task?.status === TaskStatus.PENDING;

  // Loading state
  if (isLoading) {
    return <Badge variant="secondary">Loading...</Badge>;
  }

  // No task found
  if (!task) {
    return <Badge variant="secondary">No scan</Badge>;
  }

  return (
    <div className="flex items-center gap-2">
      {/* Status Badge */}
      {task.status === TaskStatus.PENDING && (
        <Badge variant="secondary">
          Pending {elapsedTime && `(${elapsedTime})`}
        </Badge>
      )}
      {task.status === TaskStatus.RUNNING && (
        <Badge variant="default" className="bg-blue-500">
          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          Running {elapsedTime && `(${elapsedTime})`}
        </Badge>
      )}
      {task.status === TaskStatus.COMPLETED && (
        <Badge variant="default" className="bg-green-500">
          <Check className="mr-1 h-3 w-3" />
          Completed
        </Badge>
      )}
      {task.status === TaskStatus.FAILED && (
        <Badge variant="destructive">
          <X className="mr-1 h-3 w-3" />
          Failed
        </Badge>
      )}
      {task.status === TaskStatus.CANCELLED && (
        <Badge variant="secondary">
          <StopCircle className="mr-1 h-3 w-3" />
          Cancelled
        </Badge>
      )}

      {/* Stop Button (only visible for PENDING and RUNNING tasks) */}
      {showStopButton && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => cancelTask.mutate(task.id)}
          disabled={cancelTask.isPending}
          aria-label="Stop scan"
        >
          {cancelTask.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <StopCircle className="h-4 w-4" />
          )}
        </Button>
      )}
    </div>
  );
}
