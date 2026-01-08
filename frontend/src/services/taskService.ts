import * as api from '@/lib/api';
import type { Task } from '@/types/task';

/**
 * Get task status by task ID
 * @param taskId - The task ID
 * @returns Promise resolving to task object
 */
export const getTaskStatus = async (taskId: number): Promise<Task> => {
  return api.get<Task>(`/tasks/${taskId}`);
};

/**
 * Cancel a task by task ID
 * @param taskId - The task ID to cancel
 * @returns Promise resolving when cancellation is successful
 * @throws Error when task cannot be cancelled (e.g., already completed)
 */
export const cancelTask = async (taskId: number): Promise<void> => {
  await api.post(`/tasks/${taskId}/cancel`);
};

/**
 * Get the latest task for a specific target
 * @param targetId - The target ID
 * @returns Promise resolving to the latest task object
 * @throws Error when target has no tasks (404)
 */
export const getLatestTaskForTarget = async (targetId: number): Promise<Task> => {
  return api.get<Task>(`/targets/${targetId}/latest-task`);
};
