import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import { ProjectDetailPage } from './ProjectDetailPage';
import { useProject } from '@/hooks/useProjects';
import type { Project } from '@/types/project';

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(),
  };
});

// Mock the useProject hook
vi.mock('@/hooks/useProjects', () => ({
  useProject: vi.fn(),
}));

// Mock TargetList component (isolate page testing)
vi.mock('@/components/features/target/TargetList', () => ({
  TargetList: ({ projectId }: { projectId: number }) => (
    <div data-testid="target-list" data-project-id={projectId}>
      TargetList Component
    </div>
  ),
}));

// Mock CreateTargetForm component
vi.mock('@/components/features/target/CreateTargetForm', () => ({
  CreateTargetForm: ({
    open,
    onOpenChange,
    projectId,
  }: {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    projectId: number;
  }) =>
    open ? (
      <div role="dialog" data-testid="create-target-form" data-project-id={projectId}>
        <button onClick={() => onOpenChange(false)}>Close</button>
      </div>
    ) : null,
}));

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
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return {
    user: userEvent.setup(),
    ...render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/projects/123']}>
          <div id="root">{ui}</div>
        </MemoryRouter>
      </QueryClientProvider>
    ),
  };
};

// Mock data
const mockProject: Project = {
  id: 123,
  name: 'Test Project',
  description: 'Test project description',
  is_archived: false,
  archived_at: null,
  created_at: '2026-01-01T10:00:00Z',
  updated_at: '2026-01-02T15:30:00Z',
};

const mockProjectWithoutDescription: Project = {
  ...mockProject,
  description: null,
};

describe('ProjectDetailPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Route Parameter Extraction', () => {
    it('extracts project ID from URL and calls useProject with Number(id)', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      expect(useProject).toHaveBeenCalledWith(123);
    });

    it('handles invalid project ID (non-numeric string)', () => {
      vi.mocked(useParams).mockReturnValue({ id: 'invalid' });
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // NaN is passed to useProject
      expect(useProject).toHaveBeenCalledWith(NaN);
    });

    it('handles missing project ID', () => {
      vi.mocked(useParams).mockReturnValue({});
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // undefined converts to NaN
      expect(useProject).toHaveBeenCalledWith(NaN);
    });
  });

  describe('Page Rendering - Existing Features', () => {
    it('renders project header with name', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      expect(screen.getByRole('heading', { level: 1, name: mockProject.name })).toBeInTheDocument();
    });

    it('renders project description when provided', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      expect(screen.getByText(mockProject.description!)).toBeInTheDocument();
    });

    it('renders "No description provided" when description is null', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProjectWithoutDescription,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      expect(screen.getByText(/no description provided/i)).toBeInTheDocument();
    });

    it('renders project metadata (created and updated dates)', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // formatDistanceToNow is used, so we check for "Created" and "Updated" text
      expect(screen.getByText(/created/i)).toBeInTheDocument();
      expect(screen.getByText(/updated/i)).toBeInTheDocument();
    });

    it('renders "Back to Projects" button', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      const backButton = screen.getByRole('link', { name: /back to projects/i });
      expect(backButton).toBeInTheDocument();
      expect(backButton).toHaveAttribute('href', '/projects');
    });

    it('does not render placeholder text "Additional project features will be added here"', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      expect(screen.queryByText(/additional project features will be added here/i)).not.toBeInTheDocument();
    });
  });

  describe('Loading and Error States', () => {
    it('shows loading spinner while fetching project', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
      } as any);

      const { container } = renderWithProviders(<ProjectDetailPage />);

      // Check for loading spinner (Loader2 component with animate-spin class)
      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('shows error message when project not found (isError=true)', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      expect(screen.getByText(/project not found/i)).toBeInTheDocument();
      expect(screen.getByText(/the project you're looking for doesn't exist/i)).toBeInTheDocument();
    });

    it('shows error message when project is null', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: null,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      expect(screen.getByText(/project not found/i)).toBeInTheDocument();
    });
  });

  describe('Target Section - TargetList Component', () => {
    it('renders TargetList with correct projectId prop', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '456' });
      vi.mocked(useProject).mockReturnValue({
        data: { ...mockProject, id: 456 },
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      await waitFor(() => {
        const targetList = screen.getByTestId('target-list');
        expect(targetList).toBeInTheDocument();
        expect(targetList).toHaveAttribute('data-project-id', '456');
      });
    });

    it('TargetList appears in Target section with heading', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      await waitFor(() => {
        // Check for section heading
        expect(screen.getByRole('heading', { name: /targets/i })).toBeInTheDocument();
        // Check that TargetList is present
        expect(screen.getByTestId('target-list')).toBeInTheDocument();
      });
    });

    it('TargetList only renders after project loads successfully', () => {
      // First render with loading state
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
      } as any);

      const { rerender } = renderWithProviders(<ProjectDetailPage />);

      // TargetList should not be visible during loading
      expect(screen.queryByTestId('target-list')).not.toBeInTheDocument();

      // Update to loaded state
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      rerender(
        <QueryClient>
          <MemoryRouter initialEntries={['/projects/123']}>
            <div id="root">
              <ProjectDetailPage />
            </div>
          </MemoryRouter>
        </QueryClient>
      );

      // This test should FAIL initially (TDD RED phase)
      expect(screen.queryByTestId('target-list')).toBeInTheDocument();
    });

    it('TargetList not shown when project errors', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // TargetList should not be visible when there's an error
      expect(screen.queryByTestId('target-list')).not.toBeInTheDocument();
    });
  });

  describe('Target Section - Add Target Button', () => {
    it('renders "Add Target" button', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add target/i })).toBeInTheDocument();
      });
    });

    it('button appears in correct location (near TargetList)', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      await waitFor(() => {
        const button = screen.getByRole('button', { name: /add target/i });
        const targetList = screen.getByTestId('target-list');

        // Both should be in the document
        expect(button).toBeInTheDocument();
        expect(targetList).toBeInTheDocument();
      });
    });

    it('button is interactive (not disabled)', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      await waitFor(() => {
        const button = screen.getByRole('button', { name: /add target/i });
        expect(button).not.toBeDisabled();
      });
    });

    it('button only shows after project loads', () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // Button should not be visible during loading
      expect(screen.queryByRole('button', { name: /add target/i })).not.toBeInTheDocument();
    });
  });

  describe('Target Section - CreateTargetForm Dialog', () => {
    it('dialog is closed by default', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('clicking "Add Target" button opens dialog', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      const { user } = renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: /add target/i });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });

    it('dialog receives correct projectId prop', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '789' });
      vi.mocked(useProject).mockReturnValue({
        data: { ...mockProject, id: 789 },
        isLoading: false,
        isError: false,
      } as any);

      const { user } = renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      const addButton = screen.getByRole('button', { name: /add target/i });
      await user.click(addButton);

      await waitFor(() => {
        const dialog = screen.getByTestId('create-target-form');
        expect(dialog).toHaveAttribute('data-project-id', '789');
      });
    });

    it('dialog receives open and onOpenChange props', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      const { user } = renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      // Dialog closed initially
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

      // Open dialog
      const addButton = screen.getByRole('button', { name: /add target/i });
      await user.click(addButton);

      // Dialog should be open
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });

    it('dialog closes when onOpenChange(false) is called', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      const { user } = renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      // Open dialog
      const addButton = screen.getByRole('button', { name: /add target/i });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Close dialog
      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('Integration Tests', () => {
    it('complete flow: project loads → TargetList and Add Target button appear', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      await waitFor(() => {
        expect(screen.getByTestId('target-list')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /add target/i })).toBeInTheDocument();
      });
    });

    it('TargetList and CreateTargetForm share same projectId', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '999' });
      vi.mocked(useProject).mockReturnValue({
        data: { ...mockProject, id: 999 },
        isLoading: false,
        isError: false,
      } as any);

      const { user } = renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      await waitFor(() => {
        const targetList = screen.getByTestId('target-list');
        expect(targetList).toHaveAttribute('data-project-id', '999');
      });

      // Open dialog
      const addButton = screen.getByRole('button', { name: /add target/i });
      await user.click(addButton);

      await waitFor(() => {
        const dialog = screen.getByTestId('create-target-form');
        expect(dialog).toHaveAttribute('data-project-id', '999');
      });
    });

    it('opening dialog does not affect TargetList visibility', async () => {
      vi.mocked(useParams).mockReturnValue({ id: '123' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);

      const { user } = renderWithProviders(<ProjectDetailPage />);

      // This test should FAIL initially (TDD RED phase)
      await waitFor(() => {
        expect(screen.getByTestId('target-list')).toBeInTheDocument();
      });

      // Open dialog
      const addButton = screen.getByRole('button', { name: /add target/i });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // TargetList should still be visible
      expect(screen.getByTestId('target-list')).toBeInTheDocument();
    });
  });
});
