import { Button } from '@/components/ui/button';
import { Play, Loader2 } from 'lucide-react';
import { useLatestTask } from '@/hooks/useTasks';
import { useTriggerScan } from '@/hooks/useTargets';
import { TaskStatus, type TaskStatus as TaskStatusType } from '@/types/task';
import { ScanStatusBadge } from './ScanStatusBadge';

/** Terminal states where a new scan can be started */
const TERMINAL_STATUSES: TaskStatusType[] = [
  TaskStatus.COMPLETED,
  TaskStatus.FAILED,
  TaskStatus.CANCELLED,
];

interface ScanControlProps {
  /** Project ID for triggering scan */
  projectId: number;
  /** Target ID for fetching latest task and triggering scan */
  targetId: number;
  /** Target name for accessibility labels */
  targetName: string;
  /** Compact mode for inline display (e.g., in tables) */
  compact?: boolean;
}

/**
 * Controls scan operations for a target with status display and action buttons.
 *
 * @example
 * ```tsx
 * <ScanControl projectId={1} targetId={1} targetName="Example Target" />
 * ```
 */
export function ScanControl({
  projectId,
  targetId,
  targetName,
  compact = false,
}: ScanControlProps) {
  const { data: task, isLoading } = useLatestTask(targetId);
  const triggerScan = useTriggerScan();

  const canStartScan = !task || TERMINAL_STATUSES.includes(task.status);

  const handleStartScan = () => {
    triggerScan.mutate({ projectId, targetId });
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2" role="status" aria-label="Loading scan status">
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        <span>Loading...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2" role="group" aria-label={`Scan controls for ${targetName}`}>
      {task && <ScanStatusBadge task={task} />}

      {canStartScan && (
        <Button
          variant="outline"
          size="sm"
          onClick={handleStartScan}
          disabled={triggerScan.isPending}
          aria-label={`Start scan for ${targetName}`}
        >
          {triggerScan.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Play className="h-4 w-4" aria-hidden="true" />
          )}
          <span className={compact ? 'sr-only' : 'ml-2'}>Start Scan</span>
        </Button>
      )}
    </div>
  );
}
