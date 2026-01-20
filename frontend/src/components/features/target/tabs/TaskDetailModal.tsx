import { Clock, Calendar, Timer, AlertTriangle, CheckCircle, XCircle, Loader2, Ban } from 'lucide-react';
import { formatElapsedTime, formatDistanceToNow } from '@/utils/date';
import { TaskStatus } from '@/types/task';
import type { Task, TaskStatus as TaskStatusType } from '@/types/task';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CodeBlock } from '@/components/ui/code-block';

/** Status badge color mapping */
const STATUS_VARIANT_MAP: Record<TaskStatusType, string> = {
  [TaskStatus.PENDING]: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  [TaskStatus.RUNNING]: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  [TaskStatus.COMPLETED]: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  [TaskStatus.FAILED]: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  [TaskStatus.CANCELLED]: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
};

/** Status icon mapping */
const STATUS_ICON_MAP: Record<TaskStatusType, React.ReactNode> = {
  [TaskStatus.PENDING]: <Clock className="h-4 w-4" />,
  [TaskStatus.RUNNING]: <Loader2 className="h-4 w-4 animate-spin" />,
  [TaskStatus.COMPLETED]: <CheckCircle className="h-4 w-4" />,
  [TaskStatus.FAILED]: <XCircle className="h-4 w-4" />,
  [TaskStatus.CANCELLED]: <Ban className="h-4 w-4" />,
};

/** Type badge color mapping */
const TYPE_VARIANT_MAP: Record<string, string> = {
  crawl: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  scan: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
};

interface TaskDetailModalProps {
  /** Task to display (null when no task selected) */
  task: Task | null;
  /** Whether the modal is open */
  open: boolean;
  /** Callback when open state changes */
  onOpenChange: (open: boolean) => void;
}

/**
 * Format task duration from started_at to completed_at or now
 */
function formatDuration(task: Task): string {
  if (!task.started_at) {
    return '-';
  }
  return formatElapsedTime(task.started_at, task.completed_at);
}

/**
 * Parse and format JSON result
 */
function formatResult(result: string | null): string | null {
  if (!result) return null;
  try {
    const parsed = JSON.parse(result);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return result;
  }
}

/**
 * Extract error message from task result
 */
function extractError(task: Task): string | null {
  if (task.status !== TaskStatus.FAILED) return null;
  if (!task.result) return 'Task failed with no error message';

  try {
    const parsed = JSON.parse(task.result);
    return parsed.error || parsed.message || task.result;
  } catch {
    return task.result;
  }
}

/**
 * Task detail modal displaying comprehensive task information.
 * Shows overview, result JSON, and error messages.
 *
 * @example
 * ```tsx
 * <TaskDetailModal
 *   task={selectedTask}
 *   open={isModalOpen}
 *   onOpenChange={setIsModalOpen}
 * />
 * ```
 */
export function TaskDetailModal({ task, open, onOpenChange }: TaskDetailModalProps) {
  if (!task) return null;

  const formattedResult = formatResult(task.result);
  const errorMessage = extractError(task);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-2xl max-h-[80vh]"
        data-testid="task-detail-modal"
        aria-describedby="task-detail-description"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>Task #{task.id}</span>
            <Badge className={TYPE_VARIANT_MAP[task.type] ?? ''}>
              {task.type}
            </Badge>
            <Badge className={STATUS_VARIANT_MAP[task.status]}>
              <span className="flex items-center gap-1">
                {STATUS_ICON_MAP[task.status]}
                {task.status}
              </span>
            </Badge>
          </DialogTitle>
          <DialogDescription id="task-detail-description">
            Detailed information about task execution
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[60vh]">
          <div className="space-y-6 pr-4">
            {/* Overview Section */}
            <section data-testid="task-overview-section">
              <h3 className="text-sm font-medium mb-3 text-muted-foreground">Overview</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Created:</span>
                  <span>{formatDistanceToNow(task.created_at, { addSuffix: true })}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Started:</span>
                  <span>
                    {task.started_at
                      ? formatDistanceToNow(task.started_at, { addSuffix: true })
                      : '-'}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Timer className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Duration:</span>
                  <span>{formatDuration(task)}</span>
                </div>
                {task.completed_at && (
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Completed:</span>
                    <span>{formatDistanceToNow(task.completed_at, { addSuffix: true })}</span>
                  </div>
                )}
              </div>
            </section>

            {/* Error Section (only for failed tasks) */}
            {errorMessage && (
              <section data-testid="task-error-section">
                <h3 className="text-sm font-medium mb-3 text-destructive flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Error
                </h3>
                <div className="bg-destructive/10 border border-destructive/20 rounded-md p-4">
                  <p className="text-sm text-destructive">{errorMessage}</p>
                </div>
              </section>
            )}

            {/* Result Section */}
            {formattedResult && task.status !== TaskStatus.FAILED && (
              <section data-testid="task-result-section">
                <h3 className="text-sm font-medium mb-3 text-muted-foreground">Result</h3>
                <CodeBlock
                  code={formattedResult}
                  language="json"
                  data-testid="task-result-code"
                  aria-label="Task result JSON"
                />
              </section>
            )}

            {/* No result message */}
            {!task.result && task.status !== TaskStatus.FAILED && (
              <section data-testid="task-no-result-section">
                <h3 className="text-sm font-medium mb-3 text-muted-foreground">Result</h3>
                <div className="bg-muted rounded-md p-4 text-center text-sm text-muted-foreground">
                  {task.status === TaskStatus.PENDING || task.status === TaskStatus.RUNNING
                    ? 'Task is still in progress...'
                    : 'No result data available'}
                </div>
              </section>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

export default TaskDetailModal;
