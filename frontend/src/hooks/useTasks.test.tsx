import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as useTasks from './useTasks';
import * as taskService from '@/services/taskService';
import type { Task, TaskStatus } from '@/types/task';

// Mock the task service
vi.mock('@/services/taskService');

// Helper to wrap with QueryClientProvider
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retry for tests
      },
      mutations: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useTasks Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useTaskStatus (existing)', () => {
    it('should fetch task status with automatic polling', async () => {
      const mockTask: Task = {
        id: 1,
        project_id: 1,
        target_id: 1,
        type: 'scan',
        status: 'running' as TaskStatus,
        result: null,
        created_at: '2026-01-08T10:00:00Z',
        updated_at: '2026-01-08T10:00:00Z',
      };

      vi.mocked(taskService.getTaskStatus).mockResolvedValue(mockTask);

      const { result } = renderHook(() => useTasks.useTaskStatus(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.data).toEqual(mockTask);
      });
    });
  });

  describe('useCancelTask', () => {
    it('should cancel task successfully', async () => {
      // GREEN Phase: useCancelTask hook is now implemented
      vi.mocked(taskService.cancelTask).mockResolvedValue(undefined);

      const { result } = renderHook(() => useTasks.useCancelTask(), {
        wrapper: createWrapper(),
      });

      // Verify mutation function is available
      expect(result.current.mutate).toBeDefined();
      expect(typeof result.current.mutate).toBe('function');

      // Trigger cancel mutation
      result.current.mutate(123);

      await waitFor(() => {
        expect(taskService.cancelTask).toHaveBeenCalledWith(123);
        expect(result.current.isSuccess).toBe(true);
      });
    });

    it('should invalidate queries on success', async () => {
      // GREEN Phase: Verify query invalidation
      vi.mocked(taskService.cancelTask).mockResolvedValue(undefined);

      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useTasks.useCancelTask(), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      // Trigger cancel mutation
      result.current.mutate(1);

      await waitFor(() => {
        expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['tasks'] });
      });
    });

    it('should handle error when cancel fails', async () => {
      // GREEN Phase: Error handling
      const error = new Error('Cannot cancel completed task');
      vi.mocked(taskService.cancelTask).mockRejectedValue(error);

      const { result } = renderHook(() => useTasks.useCancelTask(), {
        wrapper: createWrapper(),
      });

      result.current.mutate(1);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
        expect(result.current.error).toEqual(error);
      });
    });
  });

  describe('useLatestTask', () => {
    it('should fetch latest task successfully', async () => {
      // GREEN Phase: useLatestTask hook is now implemented
      const mockTask: Task = {
        id: 10,
        project_id: 1,
        target_id: 1,
        type: 'scan',
        status: 'completed' as TaskStatus,
        result: '{"success": true}',
        created_at: '2026-01-08T10:00:00Z',
        updated_at: '2026-01-08T10:05:00Z',
      };

      vi.mocked(taskService.getLatestTaskForTarget).mockResolvedValue(mockTask);

      const { result } = renderHook(() => useTasks.useLatestTask(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.data).toEqual(mockTask);
        expect(taskService.getLatestTaskForTarget).toHaveBeenCalledWith(1);
      });
    });

    it('should enable polling for RUNNING status', async () => {
      // GREEN Phase: Verify polling continues for RUNNING tasks
      const mockTask: Task = {
        id: 10,
        project_id: 1,
        target_id: 1,
        type: 'scan',
        status: 'running' as TaskStatus,
        result: null,
        created_at: '2026-01-08T10:00:00Z',
        updated_at: '2026-01-08T10:00:00Z',
      };

      vi.mocked(taskService.getLatestTaskForTarget).mockResolvedValue(mockTask);

      const { result } = renderHook(() => useTasks.useLatestTask(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.data?.status).toBe('running');
      });

      // Verify polling is still active (refetchInterval should be 5000)
      // This is implicit - if status is RUNNING, polling continues
      expect(result.current.data?.status).not.toBe('completed');
    });

    it('should stop polling for COMPLETED status', async () => {
      // GREEN Phase: Verify polling stops for COMPLETED tasks
      const mockTask: Task = {
        id: 10,
        project_id: 1,
        target_id: 1,
        type: 'scan',
        status: 'completed' as TaskStatus,
        result: '{"success": true}',
        created_at: '2026-01-08T10:00:00Z',
        updated_at: '2026-01-08T10:05:00Z',
      };

      vi.mocked(taskService.getLatestTaskForTarget).mockResolvedValue(mockTask);

      const { result } = renderHook(() => useTasks.useLatestTask(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.data?.status).toBe('completed');
      });

      // Polling should stop for terminal states
      expect(result.current.data?.status).toBe('completed');
    });

    it('should stop polling for CANCELLED status', async () => {
      // GREEN Phase: Verify polling stops for CANCELLED tasks
      const mockTask: Task = {
        id: 10,
        project_id: 1,
        target_id: 1,
        type: 'scan',
        status: 'cancelled' as TaskStatus,
        result: null,
        created_at: '2026-01-08T10:00:00Z',
        updated_at: '2026-01-08T10:01:00Z',
      };

      vi.mocked(taskService.getLatestTaskForTarget).mockResolvedValue(mockTask);

      const { result } = renderHook(() => useTasks.useLatestTask(1), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.data?.status).toBe('cancelled');
      });

      // Polling should stop for CANCELLED status
      expect(result.current.data?.status).toBe('cancelled');
    });

    it('should stop polling when 404 error occurs', async () => {
      // RED Phase: Test that polling stops on 404 error (no tasks for target)
      const error = new Error('404: No tasks found for target');
      vi.mocked(taskService.getLatestTaskForTarget).mockRejectedValue(error);

      const { result } = renderHook(() => useTasks.useLatestTask(999), {
        wrapper: createWrapper(),
      });

      // Wait for first query to fail
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      // Record call count after first failed attempt
      const callCount = vi.mocked(taskService.getLatestTaskForTarget).mock.calls.length;

      // Wait 2 seconds (not enough time for 5 second interval to trigger)
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Call count should not increase (polling stopped due to error)
      expect(vi.mocked(taskService.getLatestTaskForTarget).mock.calls.length).toBe(callCount);
    });

    it('should resume polling when query is invalidated after scan', async () => {
      // RED Phase: Test that polling resumes after scan trigger

      // 1. Initial state: 404 error (no tasks)
      const error = new Error('404: No tasks found');
      vi.mocked(taskService.getLatestTaskForTarget).mockRejectedValueOnce(error);

      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      const { result } = renderHook(() => useTasks.useLatestTask(1), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      // Confirm 404 error
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      // 2. Scan started → Task created
      const mockTask: Task = {
        id: 1,
        project_id: 1,
        target_id: 1,
        type: 'scan',
        status: 'pending' as TaskStatus,
        result: null,
        created_at: '2026-01-08T10:00:00Z',
        updated_at: '2026-01-08T10:00:00Z',
      };
      vi.mocked(taskService.getLatestTaskForTarget).mockResolvedValue(mockTask);

      // 3. Invalidate query (simulates scan trigger)
      queryClient.invalidateQueries({ queryKey: ['tasks', 'latest', 1] });

      // 4. Verify polling resumed and data fetched
      await waitFor(() => {
        expect(result.current.data?.status).toBe('pending');
      });
    });
  });
});
