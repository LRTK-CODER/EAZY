import { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, History, AlertCircle } from 'lucide-react';
import { useTaskHistory } from '@/hooks/useTasks';
import { formatElapsedTime, formatDistanceToNow } from '@/utils/date';
import { TaskStatus } from '@/types/task';
import type { Task, TaskStatus as TaskStatusType } from '@/types/task';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

/** Page size for pagination */
const PAGE_SIZE = 10;

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
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Started</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 4 }).map((_, i) => (
              <TableRow key={i}>
                <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                <TableCell><Skeleton className="h-5 w-20" /></TableCell>
                <TableCell><Skeleton className="h-5 w-24" /></TableCell>
                <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                <TableCell><Skeleton className="h-5 w-24" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
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
 * Format task duration
 */
function formatDuration(task: Task): string {
  if (!task.started_at) {
    return '-';
  }
  return formatElapsedTime(task.started_at, task.completed_at);
}

/**
 * Scan History tab content displaying task history with pagination and filtering.
 *
 * @example
 * ```tsx
 * <HistoryTabContent targetId={1} />
 * ```
 */
export function HistoryTabContent({ targetId }: HistoryTabContentProps) {
  // Pagination state
  const [page, setPage] = useState(0);
  // Status filter state
  const [statusFilter, setStatusFilter] = useState<TaskStatusType | 'all'>('all');

  // Build query params
  const queryParams = useMemo(() => ({
    skip: page * PAGE_SIZE,
    limit: PAGE_SIZE,
    status: statusFilter === 'all' ? undefined : statusFilter,
  }), [page, statusFilter]);

  // Fetch task history
  const { data: tasks, isLoading, isError } = useTaskHistory(targetId, queryParams);

  // Pagination helpers
  const hasPrevious = page > 0;
  const hasNext = (tasks?.length ?? 0) === PAGE_SIZE;

  // Handle filter change - reset to first page
  const handleFilterChange = (value: string) => {
    setStatusFilter(value as TaskStatusType | 'all');
    setPage(0);
  };

  // Loading state
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
  if (!tasks || tasks.length === 0) {
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
      </div>

      {/* History Table */}
      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Started</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tasks.map((task) => (
              <TableRow key={task.id}>
                <TableCell>
                  <Badge className={TYPE_VARIANT_MAP[task.type] ?? ''}>
                    {task.type}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge className={STATUS_VARIANT_MAP[task.status]}>
                    {task.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  {task.started_at
                    ? formatDistanceToNow(task.started_at, { addSuffix: true })
                    : '-'}
                </TableCell>
                <TableCell>{formatDuration(task)}</TableCell>
                <TableCell>
                  {formatDistanceToNow(task.created_at, { addSuffix: true })}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-2">
        <div className="text-sm text-muted-foreground">
          Page {page + 1}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p - 1)}
            disabled={!hasPrevious}
            aria-label="Previous page"
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={!hasNext}
            aria-label="Next page"
          >
            Next
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>
    </div>
  );
}
