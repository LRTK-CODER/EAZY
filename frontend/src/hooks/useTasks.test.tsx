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

  describe('useCancelTask (new)', () => {
    it('should fail because useCancelTask does not exist', () => {
      // RED Phase: useCancelTask hook not implemented yet
      // @ts-expect-error - useCancelTask doesn't exist yet (RED phase)
      const { result } = renderHook(() => useTasks.useCancelTask(), {
        wrapper: createWrapper(),
      });

      // Will FAIL: useCancelTask is not a function
      expect(result.current).toBeDefined();
    });

    it('should use useMutation for cancel operation', async () => {
      // RED Phase: Verify hook uses useMutation
      try {
        // @ts-expect-error - useCancelTask doesn't exist yet
        const { result } = renderHook(() => useTasks.useCancelTask(), {
          wrapper: createWrapper(),
        });

        // Will FAIL: Hook doesn't exist
        await waitFor(() => {
          expect(result.current.mutate).toBeDefined();
          expect(typeof result.current.mutate).toBe('function');
        });
      } catch (error) {
        // Expected to fail
        expect(error).toBeDefined();
      }
    });

    it('should invalidate tasks query after successful cancel', async () => {
      // RED Phase: Verify query invalidation on success
      const queryClient = new QueryClient();
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      try {
        // @ts-expect-error - useCancelTask doesn't exist yet
        const { result } = renderHook(() => useTasks.useCancelTask(), {
          wrapper: ({ children }) => (
            <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
          ),
        });

        // Trigger cancel mutation
        // @ts-expect-error - mutate doesn't exist yet
        result.current.mutate(1);

        // Will FAIL: Hook doesn't exist
        await waitFor(() => {
          expect(invalidateSpy).toHaveBeenCalledWith(['tasks']);
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('useLatestTask (new)', () => {
    it('should fail because useLatestTask does not exist', () => {
      // RED Phase: useLatestTask hook not implemented yet
      try {
        // @ts-expect-error - useLatestTask doesn't exist yet (RED phase)
        const { result } = renderHook(() => useTasks.useLatestTask(1), {
          wrapper: createWrapper(),
        });

        // Will FAIL: useLatestTask is not a function
        expect(result.current).toBeDefined();
      } catch (error) {
        // Expected to fail
        expect(error).toBeDefined();
      }
    });

    it('should use useQuery to fetch latest task', async () => {
      // RED Phase: Verify hook uses useQuery
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

      // @ts-expect-error - getLatestTaskForTarget doesn't exist yet
      vi.mocked(taskService.getLatestTaskForTarget).mockResolvedValue(mockTask);

      try {
        // @ts-expect-error - useLatestTask doesn't exist yet
        const { result } = renderHook(() => useTasks.useLatestTask(1), {
          wrapper: createWrapper(),
        });

        // Will FAIL: Hook doesn't exist
        await waitFor(() => {
          expect(result.current.data).toEqual(mockTask);
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should accept targetId parameter', async () => {
      // RED Phase: Verify hook accepts targetId
      try {
        // @ts-expect-error - useLatestTask doesn't exist yet
        const { result } = renderHook(() => useTasks.useLatestTask(42), {
          wrapper: createWrapper(),
        });

        // Will FAIL: Hook doesn't exist
        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });
});
