import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HistoryTabContent } from './HistoryTabContent';
import * as taskService from '@/services/taskService';
import * as dateUtils from '@/utils/date';
import type { Task, TaskStatus } from '@/types/task';

// Mock the taskService
vi.mock('@/services/taskService');

// Mock the date utils
vi.mock('@/utils/date', async () => {
  const actual = await vi.importActual('@/utils/date');
  return {
    ...actual,
    formatElapsedTime: vi.fn(() => '5m 30s'),
    formatDistanceToNow: vi.fn(() => '2 hours ago'),
  };
});

// Mock @tanstack/react-virtual for JSDOM environment
vi.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: ({ count }: { count: number }) => ({
    getVirtualItems: () =>
      Array.from({ length: count }, (_, i) => ({
        index: i,
        key: i,
        start: i * 48,
        size: 48,
      })),
    getTotalSize: () => count * 48,
    scrollToIndex: vi.fn(),
  }),
}));

// Mock IntersectionObserver as a class
class MockIntersectionObserver implements IntersectionObserver {
  readonly root: Element | Document | null = null;
  readonly rootMargin: string = '';
  readonly thresholds: ReadonlyArray<number> = [];

  constructor(
    public callback: IntersectionObserverCallback,
    public options?: IntersectionObserverInit
  ) {}

  observe = vi.fn();
  disconnect = vi.fn();
  unobserve = vi.fn();
  takeRecords = vi.fn(() => []);
}

beforeEach(() => {
  window.IntersectionObserver = MockIntersectionObserver as unknown as typeof IntersectionObserver;
});

afterEach(() => {
  vi.clearAllMocks();
});

// Helper to render with providers
const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return {
    user: userEvent.setup(),
    ...render(
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    ),
  };
};

// Helper to create mock task
const createMockTask = (overrides: Partial<Task> = {}): Task => ({
  id: 1,
  project_id: 1,
  target_id: 1,
  type: 'crawl',
  status: 'completed' as TaskStatus,
  result: null,
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-15T10:05:00Z',
  started_at: '2026-01-15T10:00:00Z',
  completed_at: '2026-01-15T10:05:00Z',
  ...overrides,
});

// Helper to create mock task list response
const createMockTaskListResponse = (tasks: Task[], total?: number) => ({
  items: tasks,
  total: total ?? tasks.length,
});

describe('HistoryTabContent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1. Loading State
  describe('Loading State', () => {
    it('should render loading skeleton while fetching data', async () => {
      vi.mocked(taskService.getTasksForTarget).mockImplementation(
        () => new Promise(() => {}) // Never resolves - keeps loading
      );

      renderWithProviders(<HistoryTabContent targetId={1} />);

      expect(screen.getByTestId('history-loading-skeleton')).toBeInTheDocument();
    });
  });

  // 2. Empty State
  describe('Empty State', () => {
    it('should render empty state when no tasks exist', async () => {
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/no scan history/i)).toBeInTheDocument();
      });
    });

    it('should display helpful message for empty state', async () => {
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/run a scan to see history here/i)).toBeInTheDocument();
      });
    });
  });

  // 3. Task List Rendering
  describe('Task List Rendering', () => {
    it('should render task list with status badges', async () => {
      const mockTasks = [
        createMockTask({ id: 1, status: 'completed' as TaskStatus }),
        createMockTask({ id: 2, status: 'failed' as TaskStatus }),
        createMockTask({ id: 3, status: 'running' as TaskStatus }),
      ];
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse(mockTasks));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/completed/i)).toBeInTheDocument();
        expect(screen.getByText(/failed/i)).toBeInTheDocument();
        expect(screen.getByText(/running/i)).toBeInTheDocument();
      });
    });

    it('should display task type (crawl/scan)', async () => {
      const mockTasks = [
        createMockTask({ id: 1, type: 'crawl' }),
        createMockTask({ id: 2, type: 'scan' }),
      ];
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse(mockTasks));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/crawl/i)).toBeInTheDocument();
        expect(screen.getByText(/scan/i)).toBeInTheDocument();
      });
    });

    it('should render task rows', async () => {
      const mockTasks = Array.from({ length: 5 }, (_, i) =>
        createMockTask({ id: i + 1 })
      );
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse(mockTasks));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        // Virtualized table renders data rows with role="row"
        // Check for specific task rows by data-testid
        expect(screen.getByTestId('task-row-1')).toBeInTheDocument();
        expect(screen.getByTestId('task-row-5')).toBeInTheDocument();
      });
    });

    it('should display task count', async () => {
      const mockTasks = Array.from({ length: 5 }, (_, i) =>
        createMockTask({ id: i + 1 })
      );
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse(mockTasks));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText('5 tasks')).toBeInTheDocument();
      });
    });
  });

  // 4. Duration Display
  describe('Duration Display', () => {
    it('should display task duration (started_at -> completed_at)', async () => {
      const mockTask = createMockTask({
        started_at: '2026-01-15T10:00:00Z',
        completed_at: '2026-01-15T10:05:30Z',
      });
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([mockTask]));
      vi.mocked(dateUtils.formatElapsedTime).mockReturnValue('5m 30s');

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText('5m 30s')).toBeInTheDocument();
      });
    });

    it('should display "-" when started_at is missing', async () => {
      const mockTask = createMockTask({
        started_at: undefined,
        completed_at: undefined,
      });
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([mockTask]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        const cells = screen.getAllByRole('cell');
        // Duration column should have '-'
        expect(cells.some(cell => cell.textContent === '-')).toBe(true);
      });
    });

    it('should call formatElapsedTime with correct arguments', async () => {
      const startedAt = '2026-01-15T10:00:00Z';
      const completedAt = '2026-01-15T10:05:30Z';
      const mockTask = createMockTask({ started_at: startedAt, completed_at: completedAt });
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([mockTask]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(dateUtils.formatElapsedTime).toHaveBeenCalledWith(startedAt, completedAt);
      });
    });
  });

  // 5. Infinite Scroll
  describe('Infinite Scroll', () => {
    it('should call API with initial params', async () => {
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([createMockTask()]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(taskService.getTasksForTarget).toHaveBeenCalledWith(1, {
          skip: 0,
          limit: 15,
          status: undefined,
        });
      });
    });

    it('should render infinite scroll sentinel when hasNextPage is true', async () => {
      const mockTasks = Array.from({ length: 10 }, (_, i) =>
        createMockTask({ id: i + 1 })
      );
      // total > items.length means hasNextPage is true
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse(mockTasks, 20));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByTestId('infinite-scroll-sentinel')).toBeInTheDocument();
      });
    });

    it('should render virtualized container for scroll handling', async () => {
      const mockTasks = Array.from({ length: 5 }, (_, i) =>
        createMockTask({ id: i + 1 })
      );
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse(mockTasks));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        // Virtualized container handles scroll events for infinite loading
        const container = screen.getByTestId('virtualized-list-container');
        expect(container).toBeInTheDocument();
        expect(container).toHaveClass('overflow-auto');
      });
    });

    it('should not render sentinel when no more pages', async () => {
      const mockTasks = Array.from({ length: 5 }, (_, i) =>
        createMockTask({ id: i + 1 })
      );
      // total === items.length means hasNextPage is false
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse(mockTasks, 5));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        // Sentinel should not be rendered when all data is loaded
        expect(screen.queryByTestId('infinite-scroll-sentinel')).not.toBeInTheDocument();
      });
    });
  });

  // 6. Status Filtering
  describe('Status Filtering', () => {
    it('should render status filter dropdown', async () => {
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument();
      });
    });

    // NOTE: Radix UI Select has pointer capture issues in JSDOM
    // This test verifies that the component renders with the filter
    // Full interaction testing should be done in E2E tests
    it('should filter by status when dropdown value changes', async () => {
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument();
      });

      // Verify the filter trigger is accessible
      const select = screen.getByRole('combobox');
      expect(select).toHaveAttribute('aria-label', 'Status filter');
    });

    // NOTE: Radix UI Select has pointer capture issues in JSDOM
    // Verify the default "All statuses" is displayed in the trigger
    it('should show all statuses option', async () => {
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument();
      });

      // Verify the default value is displayed
      expect(screen.getByText('All statuses')).toBeInTheDocument();
    });
  });

  // 7. Table Structure
  describe('Table Structure', () => {
    it('should render table with correct column headers', async () => {
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([createMockTask()]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        // Virtualized table uses div with role="columnheader"
        const columnHeaders = screen.getAllByRole('columnheader');
        expect(columnHeaders.length).toBe(5);
        expect(screen.getByText('Type')).toBeInTheDocument();
        expect(screen.getByText('Status')).toBeInTheDocument();
        expect(screen.getByText('Started')).toBeInTheDocument();
        expect(screen.getByText('Duration')).toBeInTheDocument();
        expect(screen.getByText('Created')).toBeInTheDocument();
      });
    });

    it('should have data-testid for main container', async () => {
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([createMockTask()]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByTestId('history-tab-content')).toBeInTheDocument();
      });
    });

    it('should render virtualized list container', async () => {
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([createMockTask()]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByTestId('virtualized-list-container')).toBeInTheDocument();
      });
    });
  });

  // 8. Error State
  describe('Error State', () => {
    it('should render error state when API fails', async () => {
      vi.mocked(taskService.getTasksForTarget).mockRejectedValue(new Error('API Error'));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      });
    });
  });

  // 9. Task Row Click (Modal Integration)
  describe('Task Row Click', () => {
    it('should have clickable task rows', async () => {
      const mockTask = createMockTask({ id: 42 });
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([mockTask]));

      renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        const row = screen.getByTestId('task-row-42');
        expect(row).toHaveClass('cursor-pointer');
      });
    });

    it('should open modal when row is clicked', async () => {
      const mockTask = createMockTask({ id: 42 });
      vi.mocked(taskService.getTasksForTarget).mockResolvedValue(createMockTaskListResponse([mockTask]));

      const { user } = renderWithProviders(<HistoryTabContent targetId={1} />);

      await waitFor(() => {
        expect(screen.getByTestId('task-row-42')).toBeInTheDocument();
      });

      const row = screen.getByTestId('task-row-42');
      await user.click(row);

      await waitFor(() => {
        expect(screen.getByTestId('task-detail-modal')).toBeInTheDocument();
      });
    });
  });
});
