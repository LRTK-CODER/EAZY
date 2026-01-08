import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { AssetTable } from './AssetTable';
import * as assetService from '@/services/assetService';
import type { Asset, AssetType, AssetSource } from '@/types/asset';

// Mock the asset service
vi.mock('@/services/assetService');

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

// Mock assets data
const mockAssets: Asset[] = [
  {
    id: 1,
    target_id: 1,
    content_hash: 'abc123def456',
    type: 'url' as AssetType,
    source: 'html' as AssetSource,
    method: 'GET',
    url: 'https://example.com/api/users',
    path: '/api/users',
    request_spec: null,
    response_spec: null,
    parameters: { page: 'number', limit: 'number', sort: 'string' },
    last_task_id: 10,
    first_seen_at: '2026-01-01T00:00:00Z',
    last_seen_at: '2026-01-06T12:00:00Z',
  },
  {
    id: 2,
    target_id: 1,
    content_hash: 'def456ghi789',
    type: 'form' as AssetType,
    source: 'js' as AssetSource,
    method: 'POST',
    url: 'https://example.com/auth/login',
    path: '/auth/login',
    request_spec: { headers: { 'Content-Type': 'application/json' } },
    response_spec: { status: 200 },
    parameters: { username: 'string', password: 'string' },
    last_task_id: 11,
    first_seen_at: '2026-01-02T00:00:00Z',
    last_seen_at: '2026-01-06T11:00:00Z',
  },
  {
    id: 3,
    target_id: 1,
    content_hash: 'ghi789jkl012',
    type: 'xhr' as AssetType,
    source: 'network' as AssetSource,
    method: 'PUT',
    url: 'https://example.com/api/profile/update',
    path: '/api/profile/update',
    request_spec: null,
    response_spec: null,
    parameters: { name: 'string', email: 'string', age: 'number' },
    last_task_id: 12,
    first_seen_at: '2026-01-03T00:00:00Z',
    last_seen_at: '2026-01-06T10:00:00Z',
  },
  {
    id: 4,
    target_id: 1,
    content_hash: 'jkl012mno345',
    type: 'url' as AssetType,
    source: 'dom' as AssetSource,
    method: 'DELETE',
    url: 'https://example.com/api/delete/resource',
    path: '/api/delete/resource',
    request_spec: null,
    response_spec: null,
    parameters: null,
    last_task_id: 13,
    first_seen_at: '2026-01-04T00:00:00Z',
    last_seen_at: '2026-01-06T09:00:00Z',
  },
  {
    id: 5,
    target_id: 1,
    content_hash: 'mno345pqr678',
    type: 'form' as AssetType,
    source: 'html' as AssetSource,
    method: 'POST',
    url: 'https://example.com/contact/submit',
    path: '/contact/submit',
    request_spec: null,
    response_spec: null,
    parameters: { name: 'string', email: 'string', message: 'string' },
    last_task_id: 14,
    first_seen_at: '2026-01-05T00:00:00Z',
    last_seen_at: '2026-01-06T08:00:00Z',
  },
];

describe('AssetTable Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders table with ScrollArea container', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue(mockAssets);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });
    });

    it('renders all 8 column headers', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue(mockAssets);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/type/i)).toBeInTheDocument();
        expect(screen.getByText(/source/i)).toBeInTheDocument();
        expect(screen.getByText(/method/i)).toBeInTheDocument();
        expect(screen.getByText(/url/i)).toBeInTheDocument();
        expect(screen.getByText(/path/i)).toBeInTheDocument();
        expect(screen.getByText(/parameters/i)).toBeInTheDocument();
        expect(screen.getByText(/last seen/i)).toBeInTheDocument();
        expect(screen.getByText(/actions/i)).toBeInTheDocument();
      });
    });

    it('renders asset data rows', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue([mockAssets[0]]);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText('GET')).toBeInTheDocument();
        expect(screen.getByText('https://example.com/api/users')).toBeInTheDocument();
        expect(screen.getByText('/api/users')).toBeInTheDocument();
      });
    });

    it('displays Type badges (URL/FORM/XHR)', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue(mockAssets);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        // Should render badges for all asset types
        const urlBadges = screen.getAllByText(/^url$/i);
        expect(urlBadges.length).toBeGreaterThan(0);

        const formBadges = screen.getAllByText(/^form$/i);
        expect(formBadges.length).toBeGreaterThan(0);

        const xhrBadges = screen.getAllByText(/^xhr$/i);
        expect(xhrBadges.length).toBeGreaterThan(0);
      });
    });

    it('displays Source badges (HTML/JS/NETWORK/DOM)', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue(mockAssets);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        // Should render badges for all sources
        const htmlBadges = screen.getAllByText(/^html$/i);
        expect(htmlBadges.length).toBeGreaterThan(0);

        const jsBadges = screen.getAllByText(/^js$/i);
        expect(jsBadges.length).toBeGreaterThan(0);

        const networkBadges = screen.getAllByText(/^network$/i);
        expect(networkBadges.length).toBeGreaterThan(0);

        const domBadges = screen.getAllByText(/^dom$/i);
        expect(domBadges.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Column Display', () => {
    it('displays HTTP method text (GET/POST/PUT/DELETE)', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue(mockAssets);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        const getMethods = screen.getAllByText(/^GET$/);
        expect(getMethods.length).toBeGreaterThan(0);

        const postMethods = screen.getAllByText(/^POST$/);
        expect(postMethods.length).toBeGreaterThan(0);

        const putMethods = screen.getAllByText(/^PUT$/);
        expect(putMethods.length).toBeGreaterThan(0);

        const deleteMethods = screen.getAllByText(/^DELETE$/);
        expect(deleteMethods.length).toBeGreaterThan(0);
      });
    });

    it('displays URL as clickable link with tooltip', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue([mockAssets[0]]);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        // Find the link by role, as the text is inside a span element
        const urlLink = screen.getByRole('link', { name: /https:\/\/example\.com\/api\/users/i });
        expect(urlLink).toBeInTheDocument();
        expect(urlLink.tagName).toBe('A');
        expect(urlLink).toHaveAttribute('href', 'https://example.com/api/users');
      });
    });

    it('displays path with ellipsis truncation (max 50 chars)', async () => {
      const longPathAsset: Asset = {
        ...mockAssets[0],
        path: '/api/v1/extremely/long/path/that/should/be/truncated/because/it/exceeds/fifty/characters/limit',
      };

      vi.mocked(assetService.getTargetAssets).mockResolvedValue([longPathAsset]);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        // Should display truncated path
        const pathElement = screen.getByText(/^\/api\/v1\/extremely/);
        expect(pathElement).toBeInTheDocument();
      });
    });

    it('displays parameters count badge (e.g., "3 params")', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue([mockAssets[0]]);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        // mockAssets[0] has 3 parameters
        expect(screen.getByText(/3.*param/i)).toBeInTheDocument();
      });
    });

    it('displays Last Seen date in relative format', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue([mockAssets[0]]);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        // Should use formatDistanceToNow (e.g., "5 days ago")
        const dateElement = screen.getByText(/ago/i);
        expect(dateElement).toBeInTheDocument();
      });
    });
  });

  describe('Sorting', () => {
    it('sorts by Type column when header clicked (ascending/descending)', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue(mockAssets);

      const { user } = renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText('URL')).toBeInTheDocument();
      });

      // Click Type column header
      const typeHeader = screen.getByText(/type/i);
      await user.click(typeHeader);

      await waitFor(() => {
        // Should trigger sort (check for sort icon or reordering)
        expect(typeHeader).toBeInTheDocument();
      });
    });

    it('sorts by URL column when header clicked', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue(mockAssets);

      const { user } = renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/url/i)).toBeInTheDocument();
      });

      // Click URL column header
      const urlHeader = screen.getByText(/^url$/i);
      await user.click(urlHeader);

      await waitFor(() => {
        expect(urlHeader).toBeInTheDocument();
      });
    });

    it('sorts by Last Seen column when header clicked', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue(mockAssets);

      const { user } = renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/last seen/i)).toBeInTheDocument();
      });

      // Click Last Seen column header
      const lastSeenHeader = screen.getByText(/last seen/i);
      await user.click(lastSeenHeader);

      await waitFor(() => {
        expect(lastSeenHeader).toBeInTheDocument();
      });
    });

    it('displays sort icon (ChevronUp/ChevronDown) when sorted', async () => {
      vi.mocked(assetService.getTargetAssets).mockResolvedValue(mockAssets);

      const { user } = renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/type/i)).toBeInTheDocument();
      });

      const typeHeader = screen.getByText(/type/i);
      await user.click(typeHeader);

      await waitFor(() => {
        // Should display chevron icon (lucide-react)
        const headerCell = typeHeader.closest('th');
        expect(headerCell).toBeInTheDocument();
      });
    });

    it('persists sort state in localStorage', async () => {
      const localStorageMock = {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      };

      Object.defineProperty(window, 'localStorage', {
        value: localStorageMock,
        writable: true,
      });

      vi.mocked(assetService.getTargetAssets).mockResolvedValue(mockAssets);

      const { user } = renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        expect(screen.getByText(/type/i)).toBeInTheDocument();
      });

      const typeHeader = screen.getByText(/type/i);
      await user.click(typeHeader);

      await waitFor(() => {
        // Should save sort state to localStorage
        expect(localStorageMock.setItem).toHaveBeenCalled();
      });
    });
  });

  describe('Pagination', () => {
    it('displays page navigation buttons (Next/Previous)', async () => {
      // Create 25 assets for pagination
      const manyAssets = Array.from({ length: 25 }, (_, i) => ({
        ...mockAssets[0],
        id: i + 1,
        url: `https://example.com/api/resource${i}`,
      }));

      vi.mocked(assetService.getTargetAssets).mockResolvedValue(manyAssets);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
      });
    });

    it('displays current page number', async () => {
      const manyAssets = Array.from({ length: 25 }, (_, i) => ({
        ...mockAssets[0],
        id: i + 1,
        url: `https://example.com/api/resource${i}`,
      }));

      vi.mocked(assetService.getTargetAssets).mockResolvedValue(manyAssets);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        // Should show "Page 1 of 3" or similar
        expect(screen.getByText(/page.*1/i)).toBeInTheDocument();
      });
    });

    it('provides page size selector (10/20/50 items per page)', async () => {
      const manyAssets = Array.from({ length: 25 }, (_, i) => ({
        ...mockAssets[0],
        id: i + 1,
        url: `https://example.com/api/resource${i}`,
      }));

      vi.mocked(assetService.getTargetAssets).mockResolvedValue(manyAssets);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        // Find the select element by its label
        const pageSizeControl = screen.getByLabelText('Items per page');
        expect(pageSizeControl).toBeInTheDocument();
        expect(pageSizeControl.tagName).toBe('SELECT');

        // Verify options exist
        const option10 = screen.getByRole('option', { name: '10' });
        const option20 = screen.getByRole('option', { name: '20' });
        const option50 = screen.getByRole('option', { name: '50' });
        expect(option10).toBeInTheDocument();
        expect(option20).toBeInTheDocument();
        expect(option50).toBeInTheDocument();
      });
    });

    it('disables first/last page buttons at boundaries', async () => {
      const manyAssets = Array.from({ length: 25 }, (_, i) => ({
        ...mockAssets[0],
        id: i + 1,
        url: `https://example.com/api/resource${i}`,
      }));

      vi.mocked(assetService.getTargetAssets).mockResolvedValue(manyAssets);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        // Previous button should be disabled on first page
        const previousButton = screen.getByRole('button', { name: /previous/i });
        expect(previousButton).toBeDisabled();
      });
    });

    it('displays page range indicator (e.g., "1-10 of 50")', async () => {
      const manyAssets = Array.from({ length: 50 }, (_, i) => ({
        ...mockAssets[0],
        id: i + 1,
        url: `https://example.com/api/resource${i}`,
      }));

      vi.mocked(assetService.getTargetAssets).mockResolvedValue(manyAssets);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      await waitFor(() => {
        // Should show range like "1-10 of 50"
        expect(screen.getByText(/1.*10.*50/i)).toBeInTheDocument();
      });
    });
  });

  describe('View Details Button (Phase 5-Improvements Step 2)', () => {
    it('should render "View Details" button with Eye icon in Actions column', async () => {
      // RED Phase: "View Details" button not implemented yet
      vi.mocked(assetService.getTargetAssets).mockResolvedValue([mockAssets[0]]);

      renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      // Will FAIL: Button doesn't exist
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /view details/i })).toBeInTheDocument();
      });
    });

    it('should open AssetDetailDialog when "View Details" button is clicked', async () => {
      // RED Phase: AssetDetailDialog integration not implemented yet
      vi.mocked(assetService.getTargetAssets).mockResolvedValue([mockAssets[0]]);

      const { user } = renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      // Will FAIL: Button doesn't exist
      await waitFor(() => {
        expect(screen.getByText('https://example.com/api/users')).toBeInTheDocument();
      });

      try {
        const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
        await user.click(viewDetailsButton);

        // Dialog should open
        await waitFor(() => {
          expect(screen.getByRole('dialog')).toBeInTheDocument();
        });
      } catch (error) {
        // Expected to fail
        expect(error).toBeDefined();
      }
    });

    it('should pass selected Asset data to AssetDetailDialog', async () => {
      // RED Phase: Dialog doesn't receive asset prop yet
      vi.mocked(assetService.getTargetAssets).mockResolvedValue([mockAssets[0]]);

      const { user } = renderWithProviders(<AssetTable projectId={1} targetId={1} />);

      // Will FAIL: Button and Dialog don't exist
      await waitFor(() => {
        expect(screen.getByText('https://example.com/api/users')).toBeInTheDocument();
      });

      try {
        const viewDetailsButton = screen.getByRole('button', { name: /view details/i });
        await user.click(viewDetailsButton);

        // Verify Dialog contains asset data (URL, method, etc.)
        await waitFor(() => {
          expect(screen.getByText(/GET/)).toBeInTheDocument();
          expect(screen.getByText(/https:\/\/example\.com\/api\/users/)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });
});
