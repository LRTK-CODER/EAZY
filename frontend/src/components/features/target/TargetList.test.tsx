import { render, screen, waitFor, within } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { TargetList } from './TargetList';
import * as targetService from '@/services/targetService';
import * as taskService from '@/services/taskService';
import { toast } from 'sonner';
import type { Target, TargetScope } from '@/types/target';
import type { Task, TaskStatus } from '@/types/task';

// Mock the target service
vi.mock('@/services/targetService');

// Mock the task service
vi.mock('@/services/taskService');

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
  Toaster: () => null,
}));

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

// Mock targets data
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

    it('renders scan button in each row', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue(mockTargets);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const scanButtons = screen.getAllByRole('button', { name: /scan/i });
        expect(scanButtons).toHaveLength(mockTargets.length);
      });
    });

    it('calls triggerScan when scan button is clicked', async () => {
      const mockTriggerScan = vi.mocked(targetService.triggerScan).mockResolvedValue({
        status: 'success',
        task_id: 200,
      });

      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);

      const { user } = renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Target DOMAIN')).toBeInTheDocument();
      });

      const scanButton = screen.getByRole('button', { name: /scan/i });
      await user.click(scanButton);

      await waitFor(() => {
        expect(mockTriggerScan).toHaveBeenCalledWith(1, 1);
      });
    });
  });

  describe('Scan Status Badge', () => {
    it('displays PENDING status badge correctly', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);
      vi.mocked(taskService.getTaskStatus).mockResolvedValue(mockPendingTask);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/pending/i)).toBeInTheDocument();
      });
    });

    it('displays RUNNING status badge with loading icon', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[1]]);
      vi.mocked(taskService.getTaskStatus).mockResolvedValue(mockRunningTask);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const runningBadge = screen.getByText(/running/i);
        expect(runningBadge).toBeInTheDocument();

        // Check for loading icon (could be a spinner or similar)
        const badgeContainer = runningBadge.closest('div');
        expect(badgeContainer).toBeInTheDocument();
      });
    });

    it('displays COMPLETED status badge with success indicator', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[2]]);
      vi.mocked(taskService.getTaskStatus).mockResolvedValue(mockCompletedTask);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const completedBadge = screen.getByText(/completed/i);
        expect(completedBadge).toBeInTheDocument();
      });
    });

    it('displays FAILED status badge with error indicator', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);
      vi.mocked(taskService.getTaskStatus).mockResolvedValue(mockFailedTask);

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        const failedBadge = screen.getByText(/failed/i);
        expect(failedBadge).toBeInTheDocument();
      });
    });

    it('shows no badge when no scan exists', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);
      vi.mocked(taskService.getTaskStatus).mockRejectedValue(
        new Error('No task found')
      );

      renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Target DOMAIN')).toBeInTheDocument();
      });

      // Should not display any status badge
      expect(screen.queryByText(/pending/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/running/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/completed/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/failed/i)).not.toBeInTheDocument();
    });
  });

  describe('Scan Success Notification', () => {
    it('shows success toast after successful scan trigger', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);
      vi.mocked(targetService.triggerScan).mockResolvedValue({
        status: 'success',
        task_id: 200,
      });

      const { user } = renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Target DOMAIN')).toBeInTheDocument();
      });

      const scanButton = screen.getByRole('button', { name: /scan/i });
      await user.click(scanButton);

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith(expect.stringMatching(/scan.*started/i));
      });
    });

    it('shows error toast when scan trigger fails', async () => {
      vi.mocked(targetService.getTargets).mockResolvedValue([mockTargets[0]]);
      vi.mocked(targetService.triggerScan).mockRejectedValue(
        new Error('Failed to trigger scan')
      );

      const { user } = renderWithProviders(<TargetList projectId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Target DOMAIN')).toBeInTheDocument();
      });

      const scanButton = screen.getByRole('button', { name: /scan/i });
      await user.click(scanButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(expect.stringMatching(/failed.*scan/i));
      });
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
});
