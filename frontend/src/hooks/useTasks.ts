import { useQuery } from '@tanstack/react-query';
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
