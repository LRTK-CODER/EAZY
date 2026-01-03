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
