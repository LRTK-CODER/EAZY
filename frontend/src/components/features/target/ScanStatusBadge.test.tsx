import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ScanStatusBadge } from './ScanStatusBadge';
import * as useTasks from '@/hooks/useTasks';
import * as dateUtils from '@/utils/date';
import type { Task, TaskStatus } from '@/types/task';

// Mock the useTasks hook
vi.mock('@/hooks/useTasks');

// Mock the date utils
vi.mock('@/utils/date', async () => {
  const actual = await vi.importActual('@/utils/date');
  return {
    ...actual,
    formatElapsedTime: vi.fn((_startedAt: string, _completedAt?: string) => {
      // Simple mock implementation for testing
      if (_startedAt.includes('3m')) return '3m 25s';
      if (_startedAt.includes('10s')) return '10s';
      return '1m 30s';
    }),
  };
});

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
    it('should call useLatestTask hook with targetId', async () => {
      const mockUseLatestTask = vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={42} />);

      // Should call useLatestTask with targetId
      expect(mockUseLatestTask).toHaveBeenCalledWith(42);
    });

    it('should call useCancelTask hook', async () => {
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      } as any);

      const mockUseCancelTask = vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      // Should call useCancelTask
      expect(mockUseCancelTask).toHaveBeenCalled();
    });

    it('should display loading state', async () => {
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('should display no scan badge when task is null', async () => {
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      expect(screen.getByText(/no scan/i)).toBeInTheDocument();
    });
  });

  describe('Elapsed Time Display', () => {
    it('should display elapsed time for RUNNING task', async () => {
      const now = new Date();
      const startedAt = new Date(now.getTime() - 3 * 60 * 1000 - 25 * 1000).toISOString(); // 3m 25s ago

      const mockRunningTask: Partial<Task> = {
        id: 1,
        status: 'running' as TaskStatus,
        started_at: startedAt,
        completed_at: undefined,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockRunningTask as Task,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      // Mock formatElapsedTime to return a specific value
      vi.mocked(dateUtils.formatElapsedTime).mockReturnValue('3m 25s');

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      // Should display elapsed time like "Running (3m 25s)"
      await waitFor(() => {
        expect(screen.getByText(/running.*\(.*3m 25s\)/i)).toBeInTheDocument();
      });
    });

    it('should display elapsed time for PENDING task', async () => {
      const now = new Date();
      const startedAt = new Date(now.getTime() - 10 * 1000).toISOString(); // 10s ago

      const mockPendingTask: Partial<Task> = {
        id: 2,
        status: 'pending' as TaskStatus,
        started_at: startedAt,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockPendingTask as Task,
        isLoading: false,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      // Mock formatElapsedTime to return a specific value
      vi.mocked(dateUtils.formatElapsedTime).mockReturnValue('10s');

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/pending.*\(.*10s\)/i)).toBeInTheDocument();
      });
    });

    it('should call formatElapsedTime with correct arguments', async () => {
      const startedAt = new Date().toISOString();
      const completedAt = new Date(Date.now() + 5000).toISOString();

      const mockTask: Partial<Task> = {
        id: 1,
        status: 'completed' as TaskStatus,
        started_at: startedAt,
        completed_at: completedAt,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      // Should call formatElapsedTime with started_at and completed_at
      await waitFor(() => {
        expect(dateUtils.formatElapsedTime).toHaveBeenCalledWith(startedAt, completedAt);
      });
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

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/pending/i)).toBeInTheDocument();
      });
    });

    it('should display RUNNING status badge with Loader2 icon', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'running' as TaskStatus,
        started_at: new Date().toISOString(),
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      const { container } = renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/running/i)).toBeInTheDocument();
        // Check for animate-spin class (Loader2 icon)
        const loader = container.querySelector('.animate-spin');
        expect(loader).toBeInTheDocument();
      });
    });

    it('should display COMPLETED status badge with Check icon', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'completed' as TaskStatus,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/completed/i)).toBeInTheDocument();
      });
    });

    it('should display FAILED status badge with X icon', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'failed' as TaskStatus,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/failed/i)).toBeInTheDocument();
      });
    });

    it('should display CANCELLED status badge with StopCircle icon', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'cancelled' as TaskStatus,
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/cancelled/i)).toBeInTheDocument();
      });
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

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /stop scan/i })).toBeInTheDocument();
      });
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

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /stop scan/i })).toBeInTheDocument();
      });
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

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /stop scan/i })).not.toBeInTheDocument();
      });
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

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /stop scan/i })).not.toBeInTheDocument();
      });
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

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /stop scan/i })).not.toBeInTheDocument();
      });
    });

    it('should call cancelTask.mutate when Stop button is clicked', async () => {
      const user = userEvent.setup();
      const mockMutate = vi.fn();

      const mockTask: Partial<Task> = {
        id: 123,
        status: 'running' as TaskStatus,
        started_at: new Date().toISOString(),
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      const stopButton = screen.getByRole('button', { name: /stop scan/i });
      await user.click(stopButton);

      // Should call mutate with task ID
      expect(mockMutate).toHaveBeenCalledWith(123);
    });

    it('should show Loader2 icon when cancelTask is pending', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'running' as TaskStatus,
        started_at: new Date().toISOString(),
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: true, // Cancel is in progress
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        const stopButton = screen.getByRole('button', { name: /stop scan/i });
        expect(stopButton).toBeDisabled();

        // Check for animate-spin class in the button (Loader2 icon)
        const buttonLoader = stopButton.querySelector('.animate-spin');
        expect(buttonLoader).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle task without started_at (no elapsed time)', async () => {
      const mockTask: Partial<Task> = {
        id: 1,
        status: 'pending' as TaskStatus,
        started_at: undefined, // No started_at
      };

      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: mockTask as Task,
        isLoading: false,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      await waitFor(() => {
        // Should show "Pending" without elapsed time
        const badge = screen.getByText('Pending');
        expect(badge).toBeInTheDocument();
        // Should NOT contain parentheses (no elapsed time)
        expect(badge.textContent).not.toContain('(');
        expect(badge.textContent).not.toContain(')');
      });
    });

    it('should handle loading state correctly', async () => {
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('should handle no task scenario', async () => {
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      renderWithProviders(<ScanStatusBadge targetId={1} />);

      expect(screen.getByText(/no scan/i)).toBeInTheDocument();
    });
  });
});
