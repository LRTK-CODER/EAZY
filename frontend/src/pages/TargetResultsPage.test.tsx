import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import { TargetResultsPage } from './TargetResultsPage';
import { useProject } from '@/hooks/useProjects';
import { useTarget } from '@/hooks/useTargets';
import { useTargetAssets } from '@/hooks/useAssets';
import type { Project } from '@/types/project';
import type { Target } from '@/types/target';
import type { Asset, AssetType, AssetSource } from '@/types/asset';

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(),
  };
});

// Mock the hooks
vi.mock('@/hooks/useProjects', () => ({
  useProject: vi.fn(),
}));

vi.mock('@/hooks/useTargets', () => ({
  useTarget: vi.fn(),
}));

vi.mock('@/hooks/useAssets', () => ({
  useTargetAssets: vi.fn(),
  assetKeys: {
    all: ['assets'] as const,
    lists: () => ['assets', 'list'] as const,
    list: (projectId: number, targetId: number) => ['assets', 'list', projectId, targetId] as const,
  },
}));

// Mock AssetExplorer component
vi.mock('@/components/features/asset/AssetExplorer', () => ({
  AssetExplorer: ({ assets, isLoading }: { assets: Asset[]; isLoading?: boolean }) => {
    if (isLoading) {
      return <div data-testid="asset-explorer-loading">Loading...</div>;
    }

    if (!assets || assets.length === 0) {
      return <div data-testid="asset-explorer">No assets discovered yet</div>;
    }

    return (
      <div data-testid="asset-explorer">
        <div data-testid="asset-count">{assets.length}</div>
        {assets.map((asset: Asset) => (
          <div key={asset.id} data-testid={`asset-${asset.id}`}>
            {asset.url}
          </div>
        ))}
      </div>
    );
  },
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
const renderWithProviders = (ui: React.ReactElement, initialUrl: string = '/projects/1/targets/2/results') => {
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
        <MemoryRouter initialEntries={[initialUrl]}>
          <Routes>
            <Route path="/projects/:projectId/targets/:targetId/results" element={ui} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    ),
  };
};

// Mock data
const mockProject: Project = {
  id: 1,
  name: 'Test Project',
  description: 'Test project description',
  is_archived: false,
  archived_at: null,
  created_at: '2026-01-01T10:00:00Z',
  updated_at: '2026-01-02T15:30:00Z',
};

const mockTarget: Target = {
  id: 2,
  project_id: 1,
  name: 'Main Website',
  url: 'https://example.com',
  description: 'Test target',
  scope: 'DOMAIN',
  created_at: '2026-01-01T10:00:00Z',
  updated_at: '2026-01-02T15:30:00Z',
};

const mockAssets: Asset[] = [
  {
    id: 1,
    target_id: 2,
    content_hash: 'abc123',
    type: 'url' as AssetType,
    source: 'html' as AssetSource,
    method: 'GET',
    url: 'https://example.com/page1',
    path: '/page1',
    request_spec: null,
    response_spec: null,
    parameters: null,
    last_task_id: 1,
    first_seen_at: '2026-01-01T10:00:00Z',
    last_seen_at: '2026-01-06T10:00:00Z',
  },
  {
    id: 2,
    target_id: 2,
    content_hash: 'def456',
    type: 'form' as AssetType,
    source: 'html' as AssetSource,
    method: 'POST',
    url: 'https://example.com/login',
    path: '/login',
    request_spec: { headers: { 'Content-Type': 'application/json' } },
    response_spec: { status: 200 },
    parameters: { username: 'string', password: 'string' },
    last_task_id: 1,
    first_seen_at: '2026-01-01T10:00:00Z',
    last_seen_at: '2026-01-06T10:00:00Z',
  },
  {
    id: 3,
    target_id: 2,
    content_hash: 'ghi789',
    type: 'xhr' as AssetType,
    source: 'network' as AssetSource,
    method: 'POST',
    url: 'https://example.com/api/data',
    path: '/api/data',
    request_spec: { headers: { 'Content-Type': 'application/json' } },
    response_spec: { status: 200 },
    parameters: { query: 'string' },
    last_task_id: 1,
    first_seen_at: '2026-01-01T10:00:00Z',
    last_seen_at: '2026-01-06T10:00:00Z',
  },
];

describe('TargetResultsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Route & Params (5 tests)', () => {
    it('extracts projectId and targetId from URL params', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: mockTarget,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      expect(useParams).toHaveBeenCalled();
      expect(useProject).toHaveBeenCalledWith(1);
      expect(useTarget).toHaveBeenCalledWith(1, 2);
    });

    it('handles invalid projectId (non-numeric string) - redirects to 404', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: 'invalid', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      // Invalid params trigger redirect, so hooks are not called
      expect(useProject).not.toHaveBeenCalled();
      expect(useTarget).not.toHaveBeenCalled();
    });

    it('handles invalid targetId (non-numeric string) - redirects to 404', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: 'invalid' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      // Invalid params trigger redirect, so hooks are not called
      expect(useProject).not.toHaveBeenCalled();
      expect(useTarget).not.toHaveBeenCalled();
    });

    it('calls useTargetAssets with correct parameters', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '5', targetId: '10' });
      vi.mocked(useProject).mockReturnValue({
        data: { ...mockProject, id: 5 },
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: { ...mockTarget, id: 10, project_id: 5 },
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />, '/projects/5/targets/10/results');

      expect(useTargetAssets).toHaveBeenCalledWith(5, 10);
    });

    it('handles missing params (undefined) - redirects to 404', () => {
      vi.mocked(useParams).mockReturnValue({});
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      // Invalid params trigger redirect, so hooks are not called
      expect(useProject).not.toHaveBeenCalled();
      expect(useTarget).not.toHaveBeenCalled();
    });
  });

  describe('Data Fetching (5 tests)', () => {
    it('calls useProject with projectId', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '7', targetId: '14' });
      vi.mocked(useProject).mockReturnValue({
        data: { ...mockProject, id: 7 },
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: { ...mockTarget, id: 14, project_id: 7 },
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />, '/projects/7/targets/14/results');

      expect(useProject).toHaveBeenCalledWith(7);
      expect(useProject).toHaveBeenCalledTimes(1);
    });

    it('calls useTarget with projectId and targetId', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '3', targetId: '8' });
      vi.mocked(useProject).mockReturnValue({
        data: { ...mockProject, id: 3 },
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: { ...mockTarget, id: 8, project_id: 3 },
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />, '/projects/3/targets/8/results');

      expect(useTarget).toHaveBeenCalledWith(3, 8);
      expect(useTarget).toHaveBeenCalledTimes(1);
    });

    it('calls useTargetAssets with projectId and targetId', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: mockTarget,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      expect(useTargetAssets).toHaveBeenCalledWith(1, 2);
      expect(useTargetAssets).toHaveBeenCalledTimes(1);
    });

    it('ensures query keys are consistent across hooks', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: mockTarget,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      // Verify all hooks were called with consistent IDs
      expect(useProject).toHaveBeenCalledWith(1);
      expect(useTarget).toHaveBeenCalledWith(1, 2);
      expect(useTargetAssets).toHaveBeenCalledWith(1, 2);
    });

    it('verifies data dependency chain (project → target → assets)', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });

      // First render: project loading
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);

      const { rerender } = renderWithProviders(<TargetResultsPage />);

      // All hooks should be called even during loading
      expect(useProject).toHaveBeenCalledWith(1);
      expect(useTarget).toHaveBeenCalledWith(1, 2);
      expect(useTargetAssets).toHaveBeenCalledWith(1, 2);

      // Second render: all data loaded
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: mockTarget,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      rerender(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={['/projects/1/targets/2/results']}>
            <Routes>
              <Route path="/projects/:projectId/targets/:targetId/results" element={<TargetResultsPage />} />
            </Routes>
          </MemoryRouter>
        </QueryClientProvider>
      );

      // Verify hooks still called with same params
      expect(useProject).toHaveBeenCalledWith(1);
      expect(useTarget).toHaveBeenCalledWith(1, 2);
      expect(useTargetAssets).toHaveBeenCalledWith(1, 2);
    });
  });

  describe('Integration (5 tests)', () => {
    it('renders Breadcrumb navigation (Home → Projects → Detail → Results)', async () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: mockTarget,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      await waitFor(() => {
        // Check for breadcrumb navigation items
        expect(screen.getByText('Home')).toBeInTheDocument();
        expect(screen.getByText('Projects')).toBeInTheDocument();
        expect(screen.getByText(mockProject.name)).toBeInTheDocument();
        expect(screen.getByText('Results')).toBeInTheDocument();
      });
    });

    it('displays Target information header (Name and URL)', async () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: mockTarget,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: mockTarget.name })).toBeInTheDocument();
        expect(screen.getByText(mockTarget.url)).toBeInTheDocument();
      });
    });

    it('displays Scope badge', async () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: mockTarget,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      await waitFor(() => {
        expect(screen.getByText(mockTarget.scope)).toBeInTheDocument();
      });
    });

    it('integrates AssetExplorer component with assets data', async () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: mockTarget,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      await waitFor(() => {
        const assetExplorer = screen.getByTestId('asset-explorer');
        expect(assetExplorer).toBeInTheDocument();

        // Verify asset count
        const assetCount = screen.getByTestId('asset-count');
        expect(assetCount).toHaveTextContent('3');

        // Verify individual assets are rendered
        expect(screen.getByTestId('asset-1')).toBeInTheDocument();
        expect(screen.getByTestId('asset-2')).toBeInTheDocument();
        expect(screen.getByTestId('asset-3')).toBeInTheDocument();
      });
    });

    it('renders "Back to Project" button with correct link', async () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: mockTarget,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: mockAssets,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      await waitFor(() => {
        const backButton = screen.getByRole('link', { name: /back to project/i });
        expect(backButton).toBeInTheDocument();
        expect(backButton).toHaveAttribute('href', '/projects/1');
      });
    });
  });

  describe('Edge Cases (5 tests)', () => {
    it('shows loading spinner when data is loading', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
      } as any);

      const { container } = renderWithProviders(<TargetResultsPage />);

      // Check for loading spinner (Loader2 component with animate-spin class)
      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('shows error message when target not found (isError=true)', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      expect(screen.getByText(/target not found/i)).toBeInTheDocument();
      expect(screen.getByText(/the target you're looking for doesn't exist/i)).toBeInTheDocument();
    });

    it('displays empty state message when no assets found', async () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: mockTarget,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: [],
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      await waitFor(() => {
        expect(screen.getByText(/no assets discovered yet/i)).toBeInTheDocument();
      });
    });

    it('shows error when project not found (useProject isError)', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      expect(screen.getByText(/project not found/i)).toBeInTheDocument();
    });

    it('shows error when target is null', () => {
      vi.mocked(useParams).mockReturnValue({ projectId: '1', targetId: '2' });
      vi.mocked(useProject).mockReturnValue({
        data: mockProject,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTarget).mockReturnValue({
        data: null,
        isLoading: false,
        isError: false,
      } as any);
      vi.mocked(useTargetAssets).mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<TargetResultsPage />);

      expect(screen.getByText(/target not found/i)).toBeInTheDocument();
    });
  });
});
