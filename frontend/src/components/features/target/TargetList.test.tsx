import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { TargetList } from './TargetList';
import * as targetService from '@/services/targetService';
import * as useTasks from '@/hooks/useTasks';
import type { Target, TargetScope } from '@/types/target';
import type { Task, TaskStatus } from '@/types/task';

// Mock the target service
vi.mock('@/services/targetService');

// Mock the useTasks hooks
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

  return {
    user: userEvent.setup(),
    ...render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <div id="root">{ui}</div>
        </MemoryRouter>
      </QueryClientProvider>
    ),
  };
};

// Mock targets data (with asset_count for Phase 4)
const mockTargets: Target[] = [
  {
    id: 1,
    project_id: 1,
    name: 'Target DOMAIN',
    url: 'https://example.com',
    description: 'Test target with DOMAIN scope',
    scope: 'DOMAIN' as TargetScope,
    created_at: '2026-01-01T10:00:00Z',
    updated_at: '2026-01-01T10:00:00Z',
    asset_count: 42,
  },
  {
    id: 2,
    project_id: 1,
    name: 'Target SUBDOMAIN',
    url: 'https://test.example.com',
    description: 'Test target with SUBDOMAIN scope',
    scope: 'SUBDOMAIN' as TargetScope,
    created_at: '2026-01-01T11:00:00Z',
    updated_at: '2026-01-01T11:00:00Z',
    asset_count: 0,
  },
  {
    id: 3,
    project_id: 1,
    name: 'Target URL_ONLY',
    url: 'https://example.com/specific-page',
    description: null,
    scope: 'URL_ONLY' as TargetScope,
    created_at: '2026-01-01T12:00:00Z',
    updated_at: '2026-01-01T12:00:00Z',
    asset_count: 156,
  },
];

// Mock task data
const mockPendingTask: Task = {
  id: 100,
  project_id: 1,
  target_id: 1,
  type: 'scan',
  status: 'pending' as TaskStatus,
  result: null,
  created_at: '2026-01-01T10:00:00Z',
  updated_at: '2026-01-01T10:00:00Z',
};

const mockRunningTask: Task = {
  id: 101,
  project_id: 1,
  target_id: 2,
  type: 'scan',
  status: 'running' as TaskStatus,
  result: null,
  created_at: '2026-01-01T11:00:00Z',
  updated_at: '2026-01-01T11:05:00Z',
};

const mockCompletedTask: Task = {
  id: 102,
  project_id: 1,
  target_id: 3,
  type: 'scan',
  status: 'completed' as TaskStatus,
  result: '{"vulnerabilities": 0}',
  created_at: '2026-01-01T12:00:00Z',
  updated_at: '2026-01-01T12:30:00Z',
};

const mockFailedTask: Task = {
  id: 103,
  project_id: 1,
  target_id: 1,
  type: 'scan',
  status: 'failed' as TaskStatus,
  result: null,
  created_at: '2026-01-01T13:00:00Z',
  updated_at: '2026-01-01T13:05:00Z',
};

describe('TargetList Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock useLatestTask to return null (no task) by default
    vi.mocked(useTasks.useLatestTask).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    } as any);

    // Mock useLatestTasks (plural) for batch task fetching
    vi.mocked(useTasks.useLatestTasks).mockReturnValue({
      tasksMap: new Map(),
      isLoading: false,
      hasActiveTasks: false,
      queries: [],
    } as any);

    // Mock useCancelTask by default
    vi.mocked(useTasks.useCancelTask).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any);
  });

  describe('Table Rendering', () => {
    it('renders table correctly', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });
    });

    it('renders all column headers', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/name/i)).toBeInTheDocument();
        expect(screen.getByText(/url/i)).toBeInTheDocument();
        expect(screen.getByText(/scope/i)).toBeInTheDocument();
        expect(screen.getByText(/assets/i)).toBeInTheDocument();
        expect(screen.getByText(/last scan/i)).toBeInTheDocument();
        expect(screen.getByText(/created at/i)).toBeInTheDocument();
        expect(screen.getByText(/actions/i)).toBeInTheDocument();
      });
    });

    it('renders target data as table rows', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Target DOMAIN')).toBeInTheDocument();
        expect(screen.getByText('https://example.com')).toBeInTheDocument();
        expect(screen.getByText('DOMAIN')).toBeInTheDocument();
      });
    });

    it('renders multiple targets correctly', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Target DOMAIN')).toBeInTheDocument();
        expect(screen.getByText('Target SUBDOMAIN')).toBeInTheDocument();
        expect(screen.getByText('Target URL_ONLY')).toBeInTheDocument();
      });
    });

    it('displays DOMAIN scope correctly', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('DOMAIN')).toBeInTheDocument();
      });
    });

    it('displays SUBDOMAIN scope correctly', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[1]]);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('SUBDOMAIN')).toBeInTheDocument();
      });
    });

    it('displays URL_ONLY scope correctly', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[2]]);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('URL_ONLY')).toBeInTheDocument();
      });
    });
  });

  describe('Loading/Error/Empty States', () => {
    it('shows loader during loading', () => {
      vi.mocked(targetService.getTargets).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderWithProviders(<TargetList projectId={1} />);

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('shows error message on error', async () => {
      vi.mocked(targetService.getTargets).mockRejectedValue(
        new Error('Failed to fetch targets')
      );

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/error.*loading.*targets/i)).toBeInTheDocument();
      });
    });

    it('shows empty state message when no targets', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([]);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/no targets/i)).toBeInTheDocument();
      });
    });

    it('shows table when data loads successfully', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Action Buttons', () => {
    it('renders edit button in each row', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const editButtons = screen.getAllByRole('button', { name: /edit/i });
        expect(editButtons).toHaveLength(mockTargets.length);
      });
    });

    it('opens EditTargetForm dialog when edit button is clicked', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);

      const { user } = renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Target DOMAIN')).toBeInTheDocument();
      });

      const editButton = screen.getByRole('button', { name: /edit/i });
      await user.click(editButton);

      await waitFor(() => {
        // EditTargetForm dialog should be visible
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });

    it('renders delete button in each row', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        expect(deleteButtons).toHaveLength(mockTargets.length);
      });
    });

    it('opens DeleteTargetDialog when delete button is clicked', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);

      const { user } = renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Target DOMAIN')).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      await waitFor(() => {
        // DeleteTargetDialog should be visible
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });
    });

    // Note: Scan button tests removed in Phase 4 - scan functionality moved to Target detail page
  });

  describe('Last Scan Status (TargetScanSummary)', () => {
    it('displays PENDING status correctly', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);
      const tasksMap = new Map<number, Task>();
      tasksMap.set(1, mockPendingTask);
      vi.mocked(useTasks.useLatestTasks).mockReturnValue({
        tasksMap,
        isLoading: false,
        hasActiveTasks: true,
        queries: [],
      } as any);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/pending/i)).toBeInTheDocument();
      });
    });

    it('displays RUNNING status with elapsed time', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[1]]);
      const tasksMap = new Map<number, Task>();
      tasksMap.set(2, { ...mockRunningTask, started_at: new Date().toISOString() });
      vi.mocked(useTasks.useLatestTasks).mockReturnValue({
        tasksMap,
        isLoading: false,
        hasActiveTasks: true,
        queries: [],
      } as any);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        // TargetScanSummary shows elapsed time or Running status
        expect(screen.getByRole('status')).toBeInTheDocument();
      });
    });

    it('displays COMPLETED status correctly', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[2]]);
      const tasksMap = new Map<number, Task>();
      tasksMap.set(3, mockCompletedTask);
      vi.mocked(useTasks.useLatestTasks).mockReturnValue({
        tasksMap,
        isLoading: false,
        hasActiveTasks: false,
        queries: [],
      } as any);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        // TargetScanSummary shows relative time for completed tasks
        expect(screen.getByRole('status')).toBeInTheDocument();
      });
    });

    it('displays FAILED status correctly', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);
      const tasksMap = new Map<number, Task>();
      tasksMap.set(1, mockFailedTask);
      vi.mocked(useTasks.useLatestTasks).mockReturnValue({
        tasksMap,
        isLoading: false,
        hasActiveTasks: false,
        queries: [],
      } as any);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/failed/i)).toBeInTheDocument();
      });
    });

    it('shows "-" when no scan exists', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);
      vi.mocked(useTasks.useLatestTasks).mockReturnValue({
        tasksMap: new Map(),
        isLoading: false,
        hasActiveTasks: false,
        queries: [],
      } as any);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Target DOMAIN')).toBeInTheDocument();
      });

      // TargetScanSummary shows "-" when no task exists
      expect(screen.getByText('-')).toBeInTheDocument();
    });
  });

  describe('Query Hook Usage', () => {
    it('calls useTargets with correct projectId', async () => {
      const mockGetTargets = vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={42} />);

      await waitFor(() => {
        expect(mockGetTargets).toHaveBeenCalledWith(42, undefined);
      });
    });

    it('refetches targets after successful delete', async () => {
      const mockGetTargets = vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);
      vi.mocked(targetService.deleteTarget).mockResolvedValue(undefined);

      const { user } = renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Target DOMAIN')).toBeInTheDocument();
      });

      // Clear the mock to track new calls
      mockGetTargets.mockClear();

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      // Confirm deletion in dialog
      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('button', { name: /confirm|delete/i });
      await user.click(confirmButton);

      // Should refetch targets
      await waitFor(() => {
        expect(mockGetTargets).toHaveBeenCalled();
      });
    });
  });

  // ============================================================================
  // Phase 4: Column Structure Changes (TDD RED Phase)
  // ============================================================================

  describe('Phase 4: Column Headers', () => {
    it('renders "Last Scan" header instead of "Status"', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/last scan/i)).toBeInTheDocument();
        // Status header should NOT be present
        expect(screen.queryByRole('columnheader', { name: /^status$/i })).not.toBeInTheDocument();
      });
    });

    it('renders "Assets" column header', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/assets/i)).toBeInTheDocument();
      });
    });

    it('renders all 7 column headers in correct order', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const headers = screen.getAllByRole('columnheader');
        expect(headers).toHaveLength(7);
        // Verify order: Name, URL, Scope, Assets, Last Scan, Created At, Actions
        expect(headers[0]).toHaveTextContent(/name/i);
        expect(headers[1]).toHaveTextContent(/url/i);
        expect(headers[2]).toHaveTextContent(/scope/i);
        expect(headers[3]).toHaveTextContent(/assets/i);
        expect(headers[4]).toHaveTextContent(/last scan/i);
        expect(headers[5]).toHaveTextContent(/created at/i);
        expect(headers[6]).toHaveTextContent(/actions/i);
      });
    });
  });

  describe('Phase 4: Assets Column', () => {
    it('displays asset_count for each target', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('42')).toBeInTheDocument();
        expect(screen.getByText('0')).toBeInTheDocument();
        expect(screen.getByText('156')).toBeInTheDocument();
      });
    });

    it('displays 0 when asset_count is undefined', async () => {
      const targetWithoutAssetCount: Target = {
        ...mockTargets[0],
        asset_count: undefined,
      };
      vi.mocked(targetService.getTargets).mockResolvedValue([targetWithoutAssetCount]);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        // Should display 0 as fallback
        expect(screen.getByText('0')).toBeInTheDocument();
      });
    });
  });

  describe('Phase 4: Last Scan Column with TargetScanSummary', () => {
    it('uses TargetScanSummary component (has role="status")', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);
      const tasksMap = new Map<number, Task>();
      tasksMap.set(1, mockRunningTask);
      vi.mocked(useTasks.useLatestTasks).mockReturnValue({
        tasksMap,
        isLoading: false,
        hasActiveTasks: true,
        queries: [],
      } as any);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        // TargetScanSummary renders with role="status"
        expect(screen.getByRole('status')).toBeInTheDocument();
      });
    });

    it('shows "-" when no task exists', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);
      vi.mocked(useTasks.useLatestTasks).mockReturnValue({
        tasksMap: new Map(),
        isLoading: false,
        hasActiveTasks: false,
        queries: [],
      } as any);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('-')).toBeInTheDocument();
      });
    });
  });

  describe('Phase 4: Scan Button Removed from Actions', () => {
    it('does NOT render scan button in actions', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        // Scan buttons should NOT exist
        expect(screen.queryAllByRole('button', { name: /^scan$/i })).toHaveLength(0);
      });
    });

    it('renders only View Results, Edit, Delete buttons in actions', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /view scan results/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
        // Scan button should NOT exist
        expect(screen.queryByRole('button', { name: /^scan$/i })).not.toBeInTheDocument();
      });
    });
  });

  describe('View Results Button', () => {
    it('renders View Results button for each target', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const viewResultsLinks = screen.getAllByRole('link', { name: /view scan results/i });
        expect(viewResultsLinks).toHaveLength(mockTargets.length);
      });
    });

    it('navigates to correct URL when clicked', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const viewResultsLink = screen.getByRole('link', { name: /view scan results for target domain/i });
        expect(viewResultsLink).toHaveAttribute('href', '/projects/1/targets/1/results');
      });
    });

    it('displays BarChart icon', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const viewResultsLink = screen.getByRole('link', { name: /view scan results for target domain/i });
        // BarChart icon should be present inside the link
        expect(viewResultsLink).toBeInTheDocument();
        // Check for svg element (lucide-react renders icons as svg)
        const svg = viewResultsLink.querySelector('svg');
        expect(svg).toBeInTheDocument();
      });
    });

    it('has accessibility attributes (aria-label, title)', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const viewResultsLink = screen.getByRole('link', { name: /view scan results for target domain/i });
        expect(viewResultsLink).toHaveAttribute('aria-label', 'View scan results for Target DOMAIN');
        expect(viewResultsLink).toHaveAttribute('title', 'View scan results');
      });
    });

    it('shows "View Results" text on larger screens', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const viewResultsText = screen.getByText('View Results');
        expect(viewResultsText).toBeInTheDocument();
        // Check for responsive class (hidden sm:inline)
        expect(viewResultsText).toHaveClass('hidden', 'sm:inline');
      });
    });

    it('each target has unique results link', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const link1 = screen.getByRole('link', { name: /view scan results for target domain/i });
        const link2 = screen.getByRole('link', { name: /view scan results for target subdomain/i });
        const link3 = screen.getByRole('link', { name: /view scan results for target url_only/i });

        expect(link1).toHaveAttribute('href', '/projects/1/targets/1/results');
        expect(link2).toHaveAttribute('href', '/projects/1/targets/2/results');
        expect(link3).toHaveAttribute('href', '/projects/1/targets/3/results');
      });
    });

    it('does not show button during loading', async () => {
      vi.mocked(targetService.getTargets).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/loading/i)).toBeInTheDocument();
      });

      // View Results buttons should not be present during loading
      expect(screen.queryByRole('link', { name: /view scan results/i })).not.toBeInTheDocument();
    });

    it('does not show button during error', async () => {
      vi.mocked(targetService.getTargets).mockRejectedValue(
        new Error('Failed to fetch targets')
      );

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/error.*loading.*targets/i)).toBeInTheDocument();
      });

      // View Results buttons should not be present during error
      expect(screen.queryByRole('link', { name: /view scan results/i })).not.toBeInTheDocument();
    });
  });
});
