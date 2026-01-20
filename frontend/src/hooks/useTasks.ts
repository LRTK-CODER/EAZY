import { useQuery, useQueries, useMutation, useQueryClient } from '@tanstack/react-query';
import * as taskService from '@/services/taskService';
import { TaskStatus, type Task } from '@/types/task';

// Constants
const POLLING_INTERVAL_MS = 5000;

/**
 * Query key factory for tasks
 * Provides consistent query keys for caching and invalidation
 */
export const taskKeys = {
  all: () => ['tasks'] as const,
  details: () => ['tasks', 'detail'] as const,
  detail: (taskId: number) => [...taskKeys.details(), taskId] as const,
  latestForTarget: (targetId: number) => [...taskKeys.all(), 'latest', targetId] as const,
  forTarget: (targetId: number) => [...taskKeys.all(), 'target', targetId] as const,
  forTargetWithParams: (targetId: number, params: taskService.GetTasksParams) =>
    [...taskKeys.forTarget(targetId), params] as const,
};

/**
 * Hook to fetch task status with automatic polling
 *
 * Polls every 5 seconds until the task reaches a terminal state.
 * Polling automatically stops when status is COMPLETED or FAILED.
 *
 * @param taskId - The task ID to monitor
 * @returns Query result with task status and polling state
 *
 * @example
 * ```tsx
 * const { data: task, isLoading } = useTaskStatus(taskId);
 *
 * if (task?.status === TaskStatus.COMPLETED) {
 *   console.log('Task completed!', task.result);
 * }
 * ```
 */
export const useTaskStatus = (taskId: number) => {
  return useQuery({
    queryKey: taskKeys.detail(taskId),
    queryFn: () => taskService.getTaskStatus(taskId),
    refetchInterval: (query) => {
      // If no data yet, continue polling
      if (!query.state.data) return POLLING_INTERVAL_MS;

      // Stop polling when task reaches terminal state (completed or failed)
      if (query.state.data.status === TaskStatus.COMPLETED || query.state.data.status === TaskStatus.FAILED) {
        return false;
      }

      // Continue polling for pending/running tasks
      return POLLING_INTERVAL_MS;
    },
    enabled: !!taskId, // Only run query if taskId is truthy
  });
};

/**
 * Hook to fetch the latest task for a specific target with automatic polling
 *
 * Polls every 5 seconds until the task reaches a terminal state.
 * Polling automatically stops when status is COMPLETED, FAILED, or CANCELLED.
 *
 * @param targetId - The target ID to fetch the latest task for
 * @returns Query result with latest task and polling state
 *
 * @example
 * ```tsx
 * const { data: task, isLoading } = useLatestTask(targetId);
 *
 * if (task?.status === TaskStatus.COMPLETED) {
 *   console.log('Task completed!', task.result);
 * }
 * ```
 */
export const useLatestTask = (targetId: number) => {
  return useQuery({
    queryKey: taskKeys.latestForTarget(targetId),
    queryFn: () => taskService.getLatestTaskForTarget(targetId),
    refetchInterval: (query) => {
      // Stop polling if there's an error (e.g., 404 when no tasks exist)
      if (query.state.error) {
        return false;
      }

      // If no data yet, continue polling
      if (!query.state.data) return POLLING_INTERVAL_MS;

      // Stop polling when task reaches terminal state (completed, failed, or cancelled)
      if (
        query.state.data.status === TaskStatus.COMPLETED ||
        query.state.data.status === TaskStatus.FAILED ||
        query.state.data.status === TaskStatus.CANCELLED
      ) {
        return false;
      }

      // Continue polling for pending/running tasks
      return POLLING_INTERVAL_MS;
    },
  });
};

/**
 * Helper to check if a task is in a terminal state
 */
const isTerminalStatus = (status: TaskStatus): boolean => {
  return (
    status === TaskStatus.COMPLETED ||
    status === TaskStatus.FAILED ||
    status === TaskStatus.CANCELLED
  );
};

/**
 * Hook to fetch latest tasks for multiple targets with optimized polling
 *
 * Uses useQueries to batch all requests together, reducing N+1 problem.
 * Polling continues only for targets with active (non-terminal) tasks.
 *
 * @param targetIds - Array of target IDs to fetch tasks for
 * @returns Map of targetId to task data and loading state
 *
 * @example
 * ```tsx
 * const { tasksMap, isLoading } = useLatestTasks([1, 2, 3]);
 * const task = tasksMap.get(1); // Get task for target ID 1
 * ```
 */
export const useLatestTasks = (targetIds: number[]) => {
  const queries = useQueries({
    queries: targetIds.map((targetId) => ({
      queryKey: taskKeys.latestForTarget(targetId),
      queryFn: () => taskService.getLatestTaskForTarget(targetId),
      refetchInterval: (query: { state: { error: unknown; data?: Task } }) => {
        // Stop polling if there's an error (e.g., 404 when no tasks exist)
        if (query.state.error) {
          return false;
        }

        // If no data yet, continue polling
        if (!query.state.data) return POLLING_INTERVAL_MS;

        // Stop polling when task reaches terminal state
        if (isTerminalStatus(query.state.data.status)) {
          return false;
        }

        // Continue polling for pending/running tasks
        return POLLING_INTERVAL_MS;
      },
    })),
  });

  // Build a map of targetId -> task for easy lookup
  const tasksMap = new Map<number, Task | undefined>();
  targetIds.forEach((targetId, index) => {
    tasksMap.set(targetId, queries[index]?.data);
  });

  // Check if any query is still loading
  const isLoading = queries.some((q) => q.isLoading);

  // Check if there are any active (polling) tasks
  const hasActiveTasks = queries.some(
    (q) => q.data && !isTerminalStatus(q.data.status)
  );

  return {
    tasksMap,
    isLoading,
    hasActiveTasks,
    queries, // Expose raw queries for advanced use cases
  };
};

/**
 * Hook to cancel a task
 *
 * Invalidates all task queries on successful cancellation to trigger refetch.
 *
 * @returns Mutation function for cancelling tasks
 *
 * @example
 * ```tsx
 * const cancelTask = useCancelTask();
 *
 * const handleCancel = (taskId: number) => {
 *   cancelTask.mutate(taskId, {
 *     onSuccess: () => {
 *       console.log('Task cancelled successfully');
 *     },
 *     onError: (error) => {
 *       console.error('Failed to cancel task:', error);
 *     }
 *   });
 * };
 * ```
 */
export const useCancelTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: number) => taskService.cancelTask(taskId),
    onSuccess: () => {
      // Invalidate all task queries to trigger refetch
      // This includes latest-task queries and task-status queries
      queryClient.invalidateQueries({ queryKey: taskKeys.all() });
    },
  });
};

/**
 * Parameters for useTaskHistory hook
 */
export interface UseTaskHistoryParams {
  /** Number of tasks to skip (for pagination) */
  skip?: number;
  /** Maximum number of tasks to return */
  limit?: number;
  /** Filter by task status */
  status?: TaskStatus;
}

/**
 * Hook to fetch task history for a target with pagination and filtering
 *
 * @param targetId - The target ID to fetch tasks for
 * @param params - Pagination and filtering parameters
 * @returns Query result with tasks array
 *
 * @example
 * ```tsx
 * const { data: tasks, isLoading } = useTaskHistory(targetId, {
 *   skip: 0,
 *   limit: 10,
 *   status: TaskStatus.COMPLETED,
 * });
 * ```
 */
export const useTaskHistory = (
  targetId: number,
  params: UseTaskHistoryParams = {}
) => {
  return useQuery({
    queryKey: taskKeys.forTargetWithParams(targetId, params),
    queryFn: () => taskService.getTasksForTarget(targetId, params),
    enabled: !!targetId,
  });
};
