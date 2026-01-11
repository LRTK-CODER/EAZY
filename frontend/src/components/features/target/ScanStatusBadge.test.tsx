import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ScanStatusBadge } from './ScanStatusBadge';
import * as useTasks from '@/hooks/useTasks';
import * as dateUtils from '@/utils/date';
import type { Task, TaskStatus } from '@/types/task';

// Mock the useTasks hook (only useCancelTask is used now)
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

// Helper to create mock task
const createMockTask = (overrides: Partial<Task> = {}): Task => ({
  id: 1,
  project_id: 1,
  target_id: 1,
  type: 'scan' as const,
  status: 'pending' as TaskStatus,
  result: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

describe('ScanStatusBadge Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default mock for useCancelTask
    vi.mocked(useTasks.useCancelTask).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useTasks.useCancelTask>);
  });

  describe('Loading and Empty States', () => {
    it('should display loading state when isLoading is true', async () => {
      renderWithProviders(<ScanStatusBadge isLoading={true} />);
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('should display no scan badge when task is undefined', async () => {
      renderWithProviders(<ScanStatusBadge task={undefined} />);
      expect(screen.getByText(/no scan/i)).toBeInTheDocument();
    });
  });

  describe('Elapsed Time Display', () => {
    it('should display elapsed time for RUNNING task', async () => {
      const now = new Date();
      const startedAt = new Date(now.getTime() - 3 * 60 * 1000 - 25 * 1000).toISOString();

      const mockTask = createMockTask({
        status: 'running' as TaskStatus,
        started_at: startedAt,
      });

      vi.mocked(dateUtils.formatElapsedTime).mockReturnValue('3m 25s');

      renderWithProviders(<ScanStatusBadge task={mockTask} />);

      await waitFor(() => {
        expect(screen.getByText(/running.*\(.*3m 25s\)/i)).toBeInTheDocument();
      });
    });

    it('should display elapsed time for PENDING task', async () => {
      const now = new Date();
      const startedAt = new Date(now.getTime() - 10 * 1000).toISOString();

      const mockTask = createMockTask({
        status: 'pending' as TaskStatus,
        started_at: startedAt,
      });

      vi.mocked(dateUtils.formatElapsedTime).mockReturnValue('10s');

      renderWithProviders(<ScanStatusBadge task={mockTask} />);

      await waitFor(() => {
        expect(screen.getByText(/pending.*\(.*10s\)/i)).toBeInTheDocument();
      });
    });

    it('should call formatElapsedTime with correct arguments', async () => {
      const startedAt = new Date().toISOString();
      const completedAt = new Date(Date.now() + 5000).toISOString();

      const mockTask = createMockTask({
        status: 'completed' as TaskStatus,
        started_at: startedAt,
        completed_at: completedAt,
      });

      renderWithProviders(<ScanStatusBadge task={mockTask} />);

      await waitFor(() => {
        expect(dateUtils.formatElapsedTime).toHaveBeenCalledWith(startedAt, completedAt);
      });
    });
  });

  describe('Status Badge Variants', () => {
    it('should display PENDING status badge', async () => {
      const mockTask = createMockTask({ status: 'pending' as TaskStatus });
      renderWithProviders(<ScanStatusBadge task={mockTask} />);
      await waitFor(() => {
        expect(screen.getByText(/pending/i)).toBeInTheDocument();
      });
    });

    it('should display RUNNING status badge with Loader2 icon', async () => {
      const mockTask = createMockTask({
        status: 'running' as TaskStatus,
        started_at: new Date().toISOString(),
      });

      const { container } = renderWithProviders(<ScanStatusBadge task={mockTask} />);

      await waitFor(() => {
        expect(screen.getByText(/running/i)).toBeInTheDocument();
        const loader = container.querySelector('.animate-spin');
        expect(loader).toBeInTheDocument();
      });
    });

    it('should display COMPLETED status badge with Check icon', async () => {
      const mockTask = createMockTask({ status: 'completed' as TaskStatus });
      renderWithProviders(<ScanStatusBadge task={mockTask} />);
      await waitFor(() => {
        expect(screen.getByText(/completed/i)).toBeInTheDocument();
      });
    });

    it('should display FAILED status badge with X icon', async () => {
      const mockTask = createMockTask({ status: 'failed' as TaskStatus });
      renderWithProviders(<ScanStatusBadge task={mockTask} />);
      await waitFor(() => {
        expect(screen.getByText(/failed/i)).toBeInTheDocument();
      });
    });

    it('should display CANCELLED status badge with StopCircle icon', async () => {
      const mockTask = createMockTask({ status: 'cancelled' as TaskStatus });
      renderWithProviders(<ScanStatusBadge task={mockTask} />);
      await waitFor(() => {
        expect(screen.getByText(/cancelled/i)).toBeInTheDocument();
      });
    });
  });

  describe('Stop Button', () => {
    it('should show Stop button when status is RUNNING', async () => {
      const mockTask = createMockTask({
        status: 'running' as TaskStatus,
        started_at: new Date().toISOString(),
      });

      renderWithProviders(<ScanStatusBadge task={mockTask} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /stop scan/i })).toBeInTheDocument();
      });
    });

    it('should show Stop button when status is PENDING', async () => {
      const mockTask = createMockTask({ status: 'pending' as TaskStatus });
      renderWithProviders(<ScanStatusBadge task={mockTask} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /stop scan/i })).toBeInTheDocument();
      });
    });

    it('should NOT show Stop button when status is COMPLETED', async () => {
      const mockTask = createMockTask({ status: 'completed' as TaskStatus });
      renderWithProviders(<ScanStatusBadge task={mockTask} />);

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /stop scan/i })).not.toBeInTheDocument();
      });
    });

    it('should NOT show Stop button when status is FAILED', async () => {
      const mockTask = createMockTask({ status: 'failed' as TaskStatus });
      renderWithProviders(<ScanStatusBadge task={mockTask} />);

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /stop scan/i })).not.toBeInTheDocument();
      });
    });

    it('should NOT show Stop button when status is CANCELLED', async () => {
      const mockTask = createMockTask({ status: 'cancelled' as TaskStatus });
      renderWithProviders(<ScanStatusBadge task={mockTask} />);

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /stop scan/i })).not.toBeInTheDocument();
      });
    });

    it('should call cancelTask.mutate when Stop button is clicked', async () => {
      const user = userEvent.setup();
      const mockMutate = vi.fn();

      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      } as unknown as ReturnType<typeof useTasks.useCancelTask>);

      const mockTask = createMockTask({
        id: 123,
        status: 'running' as TaskStatus,
        started_at: new Date().toISOString(),
      });

      renderWithProviders(<ScanStatusBadge task={mockTask} />);

      const stopButton = screen.getByRole('button', { name: /stop scan/i });
      await user.click(stopButton);

      expect(mockMutate).toHaveBeenCalledWith(123);
    });

    it('should show Loader2 icon when cancelTask is pending', async () => {
      vi.mocked(useTasks.useCancelTask).mockReturnValue({
        mutate: vi.fn(),
        isPending: true,
      } as unknown as ReturnType<typeof useTasks.useCancelTask>);

      const mockTask = createMockTask({
        status: 'running' as TaskStatus,
        started_at: new Date().toISOString(),
      });

      renderWithProviders(<ScanStatusBadge task={mockTask} />);

      await waitFor(() => {
        const stopButton = screen.getByRole('button', { name: /stop scan/i });
        expect(stopButton).toBeDisabled();

        const buttonLoader = stopButton.querySelector('.animate-spin');
        expect(buttonLoader).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle task without started_at (no elapsed time)', async () => {
      const mockTask = createMockTask({
        status: 'pending' as TaskStatus,
        started_at: undefined,
      });

      renderWithProviders(<ScanStatusBadge task={mockTask} />);

      await waitFor(() => {
        const badge = screen.getByText('Pending');
        expect(badge).toBeInTheDocument();
        expect(badge.textContent).not.toContain('(');
        expect(badge.textContent).not.toContain(')');
      });
    });
  });
});
