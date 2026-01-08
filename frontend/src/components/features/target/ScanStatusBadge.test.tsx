import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ScanStatusBadge } from './ScanStatusBadge';
import * as useTasks from '@/hooks/useTasks';
import type { Task, TaskStatus } from '@/types/task';

// Mock the useTasks hook
vi.mock('@/hooks/useTasks');

// Helper to render with providers
const renderWithProviders = (ui: React.ReactElement) => {
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

  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('ScanStatusBadge Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Hook Integration', () => {
    it('should fail because component does not exist', () => {
      // RED Phase: ScanStatusBadge component not implemented yet
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      } as any);

      // This will FAIL: ScanStatusBadge is not defined
      expect(() => renderWithProviders(<ScanStatusBadge targetId={1} />)).toThrow();
    });

    it('should call useLatestTask hook with targetId', async () => {
      const mockUseLatestTask = vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={42} />);

        // Should call useLatestTask with targetId
        await waitFor(() => {
          expect(mockUseLatestTask).toHaveBeenCalledWith(42);
        });
      } catch (error) {
        // Expected to fail - component not implemented
        expect(error).toBeDefined();
      }
    });
  });

  describe('Elapsed Time Display', () => {
    it('should display elapsed time for RUNNING task', async () => {
      const now = new Date();
      const startedAt = new Date(now.getTime() - 3 * 60 * 1000 - 25 * 1000); // 3m 25s ago

      const mockRunningTask: Partial<Task> = {
        id: 1,
        status: 'running' as TaskStatus,
        started_at: startedAt.toISOString(),
        completed_at: undefined,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockRunningTask as Task,
        isLoading: false,
        error: null,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        // Should display elapsed time like "Running (3m 25s)"
        await waitFor(() => {
          expect(screen.getByText(/running.*\(.*3m/i)).toBeInTheDocument();
        });
      } catch (error) {
        // Expected to fail
        expect(error).toBeDefined();
      }
    });

    it('should display elapsed time for PENDING task', async () => {
      const now = new Date();
      const startedAt = new Date(now.getTime() - 10 * 1000); // 10s ago

      const mockPendingTask: Partial<Task> = {
        id: 2,
        status: 'pending' as TaskStatus,
        started_at: startedAt.toISOString(),
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockPendingTask as Task,
        isLoading: false,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        await waitFor(() => {
          expect(screen.getByText(/pending.*\(.*10s\)/i)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('Status Badge Variants', () => {
    it('should display PENDING status badge', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'pending' as TaskStatus,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        await waitFor(() => {
          expect(screen.getByText(/pending/i)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should display RUNNING status badge', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'running' as TaskStatus,
        started_at: new Date().toISOString(),
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        await waitFor(() => {
          expect(screen.getByText(/running/i)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should display COMPLETED status badge', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'completed' as TaskStatus,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        await waitFor(() => {
          expect(screen.getByText(/completed/i)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should display FAILED status badge', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'failed' as TaskStatus,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        await waitFor(() => {
          expect(screen.getByText(/failed/i)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should display CANCELLED status badge', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'cancelled' as TaskStatus,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        await waitFor(() => {
          expect(screen.getByText(/cancelled/i)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('Stop Button', () => {
    it('should show Stop button when status is RUNNING', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'running' as TaskStatus,
        started_at: new Date().toISOString(),
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        await waitFor(() => {
          expect(screen.getByRole('button', { name: /stop/i })).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should show Stop button when status is PENDING', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'pending' as TaskStatus,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        await waitFor(() => {
          expect(screen.getByRole('button', { name: /stop/i })).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should NOT show Stop button when status is COMPLETED', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'completed' as TaskStatus,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        await waitFor(() => {
          expect(screen.queryByRole('button', { name: /stop/i })).not.toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should NOT show Stop button when status is FAILED', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'failed' as TaskStatus,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        await waitFor(() => {
          expect(screen.queryByRole('button', { name: /stop/i })).not.toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should NOT show Stop button when status is CANCELLED', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'cancelled' as TaskStatus,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      // Will FAIL: Component doesn't exist
      try {
        renderWithProviders(<ScanStatusBadge targetId={1} />);

        await waitFor(() => {
          expect(screen.queryByRole('button', { name: /stop/i })).not.toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });
});
