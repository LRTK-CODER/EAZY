import { useState, useEffect, useRef, useCallback } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { History, AlertCircle, Loader2 } from 'lucide-react';
import { useTaskHistoryInfinite } from '@/hooks/useTasks';
import { formatElapsedTime, formatDistanceToNow } from '@/utils/date';
import { TaskStatus } from '@/types/task';
import type { Task, TaskStatus as TaskStatusType } from '@/types/task';
import { TaskDetailModal } from './TaskDetailModal';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';

/** Row height for virtualization */
const ROW_HEIGHT = 48;

/**
 * Layout overhead for viewport-based height calculation
 * - Breadcrumb + Target Header + TabsList + TabsContent margin = ~184px
 * - Back Button area = ~84px
 * - History Filter section = ~56px
 * - Table Header = ~48px
 * - Page padding (p-6 * 2) = ~48px
 * Total = ~420px
 */
const LAYOUT_OVERHEAD = 510;

/** Overscan count for virtualization */
const OVERSCAN_COUNT = 5;

/** Status badge color mapping */
const STATUS_VARIANT_MAP: Record<TaskStatusType, string> = {
  [TaskStatus.PENDING]: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  [TaskStatus.RUNNING]: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  [TaskStatus.COMPLETED]: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  [TaskStatus.FAILED]: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  [TaskStatus.CANCELLED]: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
};

/** Type badge color mapping */
const TYPE_VARIANT_MAP: Record<string, string> = {
  crawl: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  scan: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
};

interface HistoryTabContentProps {
  /** Target ID to fetch history for */
  targetId: number;
}

/**
 * Loading skeleton for history table
 */
function HistoryLoadingSkeleton() {
  return (
    <div data-testid="history-loading-skeleton" className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-10 w-[180px]" />
      </div>
      <div className="border rounded-md">
        {/* Header */}
        <div className="flex items-center h-12 px-4 border-b bg-muted/50">
          <div className="flex-1 text-sm font-medium text-muted-foreground">Type</div>
          <div className="flex-1 text-sm font-medium text-muted-foreground">Status</div>
          <div className="flex-1 text-sm font-medium text-muted-foreground">Started</div>
          <div className="flex-1 text-sm font-medium text-muted-foreground">Duration</div>
          <div className="flex-1 text-sm font-medium text-muted-foreground">Created</div>
        </div>
        {/* Skeleton rows */}
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center h-12 px-4 border-b">
            <div className="flex-1"><Skeleton className="h-5 w-16" /></div>
            <div className="flex-1"><Skeleton className="h-5 w-20" /></div>
            <div className="flex-1"><Skeleton className="h-5 w-24" /></div>
            <div className="flex-1"><Skeleton className="h-5 w-16" /></div>
            <div className="flex-1"><Skeleton className="h-5 w-24" /></div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Empty state when no tasks exist
 */
function HistoryEmptyState() {
  return (
    <div className="flex items-center justify-center h-[200px] border rounded-md bg-muted/50">
      <div className="text-center text-muted-foreground">
        <History className="h-12 w-12 mx-auto mb-4 opacity-50" aria-hidden="true" />
        <p className="text-lg font-medium">No Scan History</p>
        <p className="text-sm">Run a scan to see history here.</p>
      </div>
    </div>
  );
}

/**
 * Error state when API fails
 */
function HistoryErrorState() {
  return (
    <div className="flex items-center justify-center h-[200px] border rounded-md bg-destructive/10">
      <div className="text-center text-destructive">
        <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-70" aria-hidden="true" />
        <p className="text-lg font-medium">Failed to Load</p>
        <p className="text-sm">Unable to load scan history. Please try again.</p>
      </div>
    </div>
  );
}

/**
 * Loading indicator for fetching more
 */
function LoadingMore() {
  return (
    <div
      className="flex items-center justify-center py-4 text-muted-foreground"
      data-testid="loading-more-indicator"
    >
      <Loader2 className="h-5 w-5 animate-spin mr-2" />
      <span className="text-sm">Loading more...</span>
    </div>
  );
}

/**
 * Format task duration
 */
function formatDuration(task: Task): string {
  if (!task.started_at) {
    return '-';
  }
  return formatElapsedTime(task.started_at, task.completed_at);
}

/**
 * Virtualized table header
 */
function TableHeader() {
  return (
    <div
      className="flex items-center h-12 px-4 border-b bg-muted/50 sticky top-0 z-10"
      role="row"
    >
      <div className="flex-1 text-sm font-medium text-muted-foreground" role="columnheader">
        Type
      </div>
      <div className="flex-1 text-sm font-medium text-muted-foreground" role="columnheader">
        Status
      </div>
      <div className="flex-1 text-sm font-medium text-muted-foreground" role="columnheader">
        Started
      </div>
      <div className="flex-1 text-sm font-medium text-muted-foreground" role="columnheader">
        Duration
      </div>
      <div className="flex-1 text-sm font-medium text-muted-foreground" role="columnheader">
        Created
      </div>
    </div>
  );
}

/**
 * Virtualized table row
 */
interface TableRowProps {
  task: Task;
  onClick: () => void;
  style?: React.CSSProperties;
}

function TaskTableRow({ task, onClick, style }: TableRowProps) {
  return (
    <div
      role="row"
      className={cn(
        'flex items-center h-12 px-4 border-b cursor-pointer',
        'hover:bg-muted/50 transition-colors'
      )}
      style={style}
      onClick={onClick}
      data-testid={`task-row-${task.id}`}
    >
      <div className="flex-1" role="cell">
        <Badge className={TYPE_VARIANT_MAP[task.type] ?? ''}>
          {task.type}
        </Badge>
      </div>
      <div className="flex-1" role="cell">
        <Badge className={STATUS_VARIANT_MAP[task.status]}>
          {task.status}
        </Badge>
      </div>
      <div className="flex-1 text-sm" role="cell">
        {task.started_at
          ? formatDistanceToNow(task.started_at, { addSuffix: true })
          : '-'}
      </div>
      <div className="flex-1 text-sm" role="cell">
        {formatDuration(task)}
      </div>
      <div className="flex-1 text-sm" role="cell">
        {formatDistanceToNow(task.created_at, { addSuffix: true })}
      </div>
    </div>
  );
}

/**
 * Scan History tab content displaying task history with virtualization,
 * infinite scroll, and filtering.
 *
 * @example
 * ```tsx
 * <HistoryTabContent targetId={1} />
 * ```
 */
export function HistoryTabContent({ targetId }: HistoryTabContentProps) {
  // Status filter state
  const [statusFilter, setStatusFilter] = useState<TaskStatusType | 'all'>('all');
  // Selected task for detail modal
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  // Ref for virtualized scroll container
  const parentRef = useRef<HTMLDivElement>(null);
  // Ref for infinite scroll sentinel
  const sentinelRef = useRef<HTMLDivElement>(null);

  // Fetch task history with infinite scroll
  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useTaskHistoryInfinite(targetId, {
    status: statusFilter === 'all' ? undefined : statusFilter,
  });

  // Flatten all pages into a single array and get total count
  const tasks = data?.pages.flatMap((p) => p.items) ?? [];
  const totalCount = data?.pages[0]?.total ?? 0;

  // Setup virtualizer
  const virtualizer = useVirtualizer({
    count: tasks.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: OVERSCAN_COUNT,
  });

  const virtualItems = virtualizer.getVirtualItems();

  // Setup Intersection Observer for infinite scroll (trigger near bottom)
  const handleScroll = useCallback(() => {
    if (!parentRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = parentRef.current;
    const scrollThreshold = scrollHeight - clientHeight - 100;

    if (scrollTop >= scrollThreshold && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  useEffect(() => {
    const container = parentRef.current;
    if (!container) return;

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  // IntersectionObserver for infinite scroll when sentinel becomes visible
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  // Handle filter change
  const handleFilterChange = (value: string) => {
    setStatusFilter(value as TaskStatusType | 'all');
  };

  // Loading state (initial load only)
  if (isLoading) {
    return (
      <div data-testid="history-tab-content">
        <HistoryLoadingSkeleton />
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div data-testid="history-tab-content">
        <HistoryErrorState />
      </div>
    );
  }

  // Empty state
  if (tasks.length === 0) {
    return (
      <div data-testid="history-tab-content">
        <div className="flex items-center gap-4 mb-4">
          <Select value={statusFilter} onValueChange={handleFilterChange}>
            <SelectTrigger className="w-[180px]" aria-label="Status filter">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value={TaskStatus.PENDING}>Pending</SelectItem>
              <SelectItem value={TaskStatus.RUNNING}>Running</SelectItem>
              <SelectItem value={TaskStatus.COMPLETED}>Completed</SelectItem>
              <SelectItem value={TaskStatus.FAILED}>Failed</SelectItem>
              <SelectItem value={TaskStatus.CANCELLED}>Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <HistoryEmptyState />
      </div>
    );
  }

  return (
    <div data-testid="history-tab-content" className="space-y-4">
      {/* Status Filter */}
      <div className="flex items-center gap-4">
        <Select value={statusFilter} onValueChange={handleFilterChange}>
          <SelectTrigger className="w-[180px]" aria-label="Status filter">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value={TaskStatus.PENDING}>Pending</SelectItem>
            <SelectItem value={TaskStatus.RUNNING}>Running</SelectItem>
            <SelectItem value={TaskStatus.COMPLETED}>Completed</SelectItem>
            <SelectItem value={TaskStatus.FAILED}>Failed</SelectItem>
            <SelectItem value={TaskStatus.CANCELLED}>Cancelled</SelectItem>
          </SelectContent>
        </Select>
        <span className="text-sm text-muted-foreground">
          {totalCount} task{totalCount !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Virtualized History Table */}
      <div className="border rounded-md" role="table" aria-label="Task history">
        <TableHeader />
        <div
          ref={parentRef}
          className="overflow-auto"
          style={{ height: `calc(100vh - ${LAYOUT_OVERHEAD}px)`, minHeight: '400px' }}
          data-testid="virtualized-list-container"
        >
          <div
            style={{
              height: virtualizer.getTotalSize() + (hasNextPage ? ROW_HEIGHT : 0),
              width: '100%',
              position: 'relative',
            }}
          >
            {virtualItems.map((virtualRow) => {
              const task = tasks[virtualRow.index];
              return (
                <div
                  key={virtualRow.key}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                >
                  <TaskTableRow
                    task={task}
                    onClick={() => setSelectedTask(task)}
                  />
                </div>
              );
            })}
            {/* Infinite scroll sentinel inside table */}
            {hasNextPage && (
              <div
                ref={sentinelRef}
                data-testid="infinite-scroll-sentinel"
                style={{
                  position: 'absolute',
                  top: virtualizer.getTotalSize(),
                  left: 0,
                  width: '100%',
                  height: ROW_HEIGHT,
                }}
              >
                {isFetchingNextPage && <LoadingMore />}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Task Detail Modal */}
      <TaskDetailModal
        task={selectedTask}
        open={selectedTask !== null}
        onOpenChange={(open) => !open && setSelectedTask(null)}
      />
    </div>
  );
}
