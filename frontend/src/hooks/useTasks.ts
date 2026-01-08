import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as taskService from '@/services/taskService';
import { TaskStatus } from '@/types/task';

/**
 * Query key factory for tasks
 * Provides consistent query keys for caching and invalidation
 */
export const taskKeys = {
  all: () => ['tasks'] as const,
  details: () => ['tasks', 'detail'] as const,
  detail: (taskId: number) => [...taskKeys.details(), taskId] as const,
  latestForTarget: (targetId: number) => [...taskKeys.all(), 'latest', targetId] as const,
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
      // If no data yet, continue polling every 5 seconds
      if (!query.state.data) return 5000;

      // Stop polling when task reaches terminal state (completed or failed)
      if (query.state.data.status === TaskStatus.COMPLETED || query.state.data.status === TaskStatus.FAILED) {
        return false;
      }

      // Continue polling every 5 seconds for pending/running tasks
      return 5000;
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
      // If no data yet, continue polling every 5 seconds
      if (!query.state.data) return 5000;

      // Stop polling when task reaches terminal state (completed, failed, or cancelled)
      if (
        query.state.data.status === TaskStatus.COMPLETED ||
        query.state.data.status === TaskStatus.FAILED ||
        query.state.data.status === TaskStatus.CANCELLED
      ) {
        return false;
      }

      // Continue polling every 5 seconds for pending/running tasks
      return 5000;
    },
  });
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
