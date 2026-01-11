import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Check, X, Loader2, StopCircle } from 'lucide-react';
import { useMemo } from 'react';
import { useCancelTask } from '@/hooks/useTasks';
import { TaskStatus, type Task } from '@/types/task';
import { formatElapsedTime } from '@/utils/date';

interface ScanStatusBadgeProps {
  /** Task data to display (passed from parent for optimized batching) */
  task?: Task;
  /** Whether the task data is loading */
  isLoading?: boolean;
}

/**
 * Component to display scan status badge for a target with stop functionality
 *
 * Features:
 * - Displays current task status with appropriate badge variant
 * - Shows elapsed time for PENDING and RUNNING tasks
 * - Provides stop button to cancel PENDING or RUNNING tasks
 *
 * Note: Task data should be passed from parent component using useLatestTasks
 * hook for optimized batch fetching instead of individual polling.
 *
 * @param task - The task object to display status for
 * @param isLoading - Whether the task data is still loading
 *
 * @example
 * ```tsx
 * const { tasksMap, isLoading } = useLatestTasks(targetIds);
 * <ScanStatusBadge task={tasksMap.get(targetId)} isLoading={isLoading} />
 * ```
 */
export function ScanStatusBadge({ task, isLoading = false }: ScanStatusBadgeProps) {
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
