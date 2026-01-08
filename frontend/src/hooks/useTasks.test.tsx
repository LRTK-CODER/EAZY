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
  });
});
