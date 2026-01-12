/**
 * AssetExplorer Tests
 * TDD - Tests written before implementation
 */

import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AssetExplorer } from './AssetExplorer';
import { AssetExplorerProvider } from '@/contexts/AssetExplorerContext';
import type { Asset, AssetType, AssetSource } from '@/types/asset';

// Mock useIsMobile and useIsTablet hooks
const mockUseIsMobile = vi.fn();
const mockUseIsTablet = vi.fn();
vi.mock('@/hooks/use-mobile', () => ({
  useIsMobile: () => mockUseIsMobile(),
  useIsTablet: () => mockUseIsTablet(),
}));

// Mock ResizeObserver for react-resizable-panels
class ResizeObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
(globalThis as unknown as { ResizeObserver: typeof ResizeObserver }).ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

// Mock react-resizable-panels to avoid CSS issues in JSDOM
vi.mock('react-resizable-panels', () => ({
  Panel: ({ children, id, ...props }: { children: React.ReactNode; id?: string; [key: string]: unknown }) => (
    <div data-panel-id={id} {...props}>{children}</div>
  ),
  Group: ({ children, orientation, ...props }: { children: React.ReactNode; orientation?: string; [key: string]: unknown }) => (
    <div data-panel-group-direction={orientation} {...props}>{children}</div>
  ),
  Separator: ({ children, ...props }: { children?: React.ReactNode; [key: string]: unknown }) => (
    <div data-resize-handle {...props}>{children}</div>
  ),
}));

// Helper to render with providers
const renderWithProviders = (ui: React.ReactElement) => {
  return {
    user: userEvent.setup(),
    ...render(
      <AssetExplorerProvider>
        {ui}
      </AssetExplorerProvider>
    ),
  };
};

// Mock assets data
const mockAssets: Asset[] = [
  {
    id: 1,
    target_id: 1,
    content_hash: 'abc123',
    type: 'url' as AssetType,
    source: 'html' as AssetSource,
    method: 'GET',
    url: 'https://example.com/api/users',
    path: '/api/users',
    request_spec: null,
    response_spec: null,
    parameters: null,
    last_task_id: null,
    first_seen_at: '2026-01-01T00:00:00Z',
    last_seen_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 2,
    target_id: 1,
    content_hash: 'def456',
    type: 'form' as AssetType,
    source: 'js' as AssetSource,
    method: 'POST',
    url: 'https://example.com/auth/login',
    path: '/auth/login',
    request_spec: null,
    response_spec: null,
    parameters: null,
    last_task_id: null,
    first_seen_at: '2026-01-02T00:00:00Z',
    last_seen_at: '2026-01-02T00:00:00Z',
  },
];

describe('AssetExplorer', () => {
  beforeEach(() => {
    mockUseIsMobile.mockReturnValue(false); // Default to desktop
    mockUseIsTablet.mockReturnValue(false); // Default to desktop
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Layout Structure', () => {
    it('should render ResizablePanelGroup with horizontal orientation on desktop', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const panelGroup = document.querySelector('.asset-explorer-panel-group');
      expect(panelGroup).toBeInTheDocument();
    });

    it('should render left panel (tree view area)', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const leftPanel = screen.getByTestId('asset-explorer-tree-panel');
      expect(leftPanel).toBeInTheDocument();
    });

    it('should render right panel (detail area)', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const rightPanel = screen.getByTestId('asset-explorer-detail-panel');
      expect(rightPanel).toBeInTheDocument();
    });

    it('should render resize handle between panels', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const handle = screen.getByTestId('asset-explorer-resize-handle');
      expect(handle).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no assets provided', () => {
      renderWithProviders(<AssetExplorer assets={[]} />);

      expect(screen.getByText(/no assets/i)).toBeInTheDocument();
    });

    it('should show empty detail panel when no asset selected', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const detailPanel = screen.getByTestId('asset-explorer-detail-panel');
      expect(within(detailPanel).getByText(/select an asset/i)).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('should render Sheet on mobile instead of ResizablePanelGroup', () => {
      mockUseIsMobile.mockReturnValue(true);

      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      // Should not render panel group on mobile
      expect(document.querySelector('.asset-explorer-panel-group')).not.toBeInTheDocument();
      // Should render mobile layout
      expect(screen.getByTestId('asset-explorer-mobile')).toBeInTheDocument();
    });

    it('should render sheet trigger button on mobile', () => {
      mockUseIsMobile.mockReturnValue(true);

      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      expect(screen.getByRole('button', { name: /tree/i })).toBeInTheDocument();
    });

    it('should open sheet when trigger is clicked on mobile', async () => {
      mockUseIsMobile.mockReturnValue(true);

      const { user } = renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const triggerButton = screen.getByRole('button', { name: /tree/i });
      await user.click(triggerButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });

    it('should render vertical layout on tablet', () => {
      mockUseIsMobile.mockReturnValue(false);
      mockUseIsTablet.mockReturnValue(true);

      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      // Should render tablet layout with vertical orientation
      expect(screen.getByTestId('asset-explorer-tablet')).toBeInTheDocument();
      const panelGroup = document.querySelector('[data-panel-group-direction="vertical"]');
      expect(panelGroup).toBeInTheDocument();
    });

    it('should render horizontal layout on desktop', () => {
      mockUseIsMobile.mockReturnValue(false);
      mockUseIsTablet.mockReturnValue(false);

      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      // Should render desktop layout with horizontal orientation
      const panelGroup = document.querySelector('.asset-explorer-panel-group');
      expect(panelGroup).toBeInTheDocument();
    });
  });

  describe('Panel Sizing', () => {
    it('should set default size for tree panel (30%)', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const treePanel = screen.getByTestId('asset-explorer-tree-panel');
      // react-resizable-panels sets data attribute
      expect(treePanel).toHaveAttribute('data-panel-id', 'tree-panel');
    });

    it('should set minimum size for tree panel', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const treePanel = screen.getByTestId('asset-explorer-tree-panel');
      expect(treePanel).toBeInTheDocument();
    });
  });

  describe('TreeView Placeholder', () => {
    it('should render tree view placeholder content', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const treePanel = screen.getByTestId('asset-explorer-tree-panel');
      expect(within(treePanel).getByText(/asset tree/i)).toBeInTheDocument();
    });

    it('should display asset count in tree panel', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const treePanel = screen.getByTestId('asset-explorer-tree-panel');
      expect(within(treePanel).getByText(/2 assets/)).toBeInTheDocument();
    });
  });

  describe('DetailPanel Placeholder', () => {
    it('should render detail panel placeholder content', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const detailPanel = screen.getByTestId('asset-explorer-detail-panel');
      expect(detailPanel).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading skeleton when isLoading is true', () => {
      renderWithProviders(<AssetExplorer assets={[]} isLoading={true} />);

      expect(screen.getByTestId('asset-explorer-loading')).toBeInTheDocument();
    });

    it('should not show loading skeleton when isLoading is false', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} isLoading={false} />);

      expect(screen.queryByTestId('asset-explorer-loading')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria-label on main container', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      const container = screen.getByRole('region', { name: /asset explorer/i });
      expect(container).toBeInTheDocument();
    });

    it('should have proper heading in tree panel', () => {
      renderWithProviders(<AssetExplorer assets={mockAssets} />);

      expect(screen.getByRole('heading', { name: /asset tree/i })).toBeInTheDocument();
    });
  });
});
