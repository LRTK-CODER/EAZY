/**
 * AssetTreeView Tests
 * TDD - Tests written before implementation
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AssetTreeView } from './AssetTreeView';
import { AssetExplorerProvider } from '@/contexts/AssetExplorerContext';
import type { Asset, AssetType, AssetSource } from '@/types/asset';

// Mock ResizeObserver
class ResizeObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
(globalThis as unknown as { ResizeObserver: typeof ResizeObserver }).ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

// Mock @tanstack/react-virtual
vi.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: ({ count, estimateSize }: {
    count: number;
    estimateSize: () => number;
  }) => ({
    getVirtualItems: () =>
      Array.from({ length: Math.min(count, 20) }, (_, i) => ({
        index: i,
        start: i * estimateSize(),
        size: estimateSize(),
        key: i,
      })),
    getTotalSize: () => count * estimateSize(),
    scrollToIndex: vi.fn(),
  }),
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

// Mock asset factory
function createMockAsset(overrides: Partial<Asset> = {}): Asset {
  return {
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
    ...overrides,
  };
}

// Mock assets data
const mockAssets: Asset[] = [
  createMockAsset({ id: 1, url: 'https://example.com/api/users', path: '/api/users', method: 'GET' }),
  createMockAsset({ id: 2, url: 'https://example.com/api/users', path: '/api/users', method: 'POST' }),
  createMockAsset({ id: 3, url: 'https://example.com/auth/login', path: '/auth/login', method: 'POST' }),
  createMockAsset({ id: 4, url: 'https://api.example.org/v1/data', path: '/v1/data', method: 'GET' }),
];

// Generate large dataset for virtualization tests
function generateLargeAssetSet(count: number): Asset[] {
  return Array.from({ length: count }, (_, i) =>
    createMockAsset({
      id: i + 1,
      url: `https://example.com/api/resource${i}`,
      path: `/api/resource${i}`,
      method: i % 2 === 0 ? 'GET' : 'POST',
    })
  );
}

describe('AssetTreeView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Tree Node Rendering', () => {
    it('should render tree container with proper role', () => {
      renderWithProviders(<AssetTreeView assets={mockAssets} />);

      expect(screen.getByRole('tree')).toBeInTheDocument();
    });

    it('should render domain nodes', () => {
      renderWithProviders(<AssetTreeView assets={mockAssets} />);

      expect(screen.getByText('example.com')).toBeInTheDocument();
      expect(screen.getByText('api.example.org')).toBeInTheDocument();
    });

    it('should render folder nodes when expanded', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Click to expand domain
      const domainNode = screen.getByText('example.com');
      await user.click(domainNode);

      // Should show folder nodes
      expect(screen.getByText('api')).toBeInTheDocument();
    });

    it('should render endpoint nodes with HTTP method', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Expand domain -> folder -> endpoint
      await user.click(screen.getByText('example.com'));
      await user.click(screen.getByText('api'));
      await user.click(screen.getByText('users'));

      // Should show method badges
      expect(screen.getByText('GET')).toBeInTheDocument();
      expect(screen.getByText('POST')).toBeInTheDocument();
    });

    it('should show empty state when no assets', () => {
      renderWithProviders(<AssetTreeView assets={[]} />);

      expect(screen.getByText(/no assets/i)).toBeInTheDocument();
    });
  });

  describe('Node Expand/Collapse', () => {
    it('should toggle node expansion on click', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      const domainNode = screen.getByText('example.com');

      // Initially collapsed - no children visible
      expect(screen.queryByText('api')).not.toBeInTheDocument();

      // Click to expand
      await user.click(domainNode);
      expect(screen.getByText('api')).toBeInTheDocument();

      // Click to collapse
      await user.click(domainNode);
      expect(screen.queryByText('api')).not.toBeInTheDocument();
    });

    it('should show expand/collapse icon for nodes with children', () => {
      renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Domain nodes should have expand icon
      const treeItems = screen.getAllByRole('treeitem');
      expect(treeItems.length).toBeGreaterThan(0);
    });

    it('should update aria-expanded attribute', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      const domainNode = screen.getByRole('treeitem', { name: /example\.com/i });
      expect(domainNode).toHaveAttribute('aria-expanded', 'false');

      await user.click(domainNode);
      expect(domainNode).toHaveAttribute('aria-expanded', 'true');
    });
  });

  describe('Node Selection', () => {
    it('should call onSelectAsset when endpoint is clicked', async () => {
      const onSelectAsset = vi.fn();
      const { user } = renderWithProviders(
        <AssetTreeView assets={mockAssets} onSelectAsset={onSelectAsset} />
      );

      // Expand to endpoint
      await user.click(screen.getByText('example.com'));
      await user.click(screen.getByText('api'));
      await user.click(screen.getByText('users'));

      // Click endpoint
      await user.click(screen.getByText('GET'));

      expect(onSelectAsset).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }));
    });

    it('should highlight selected node', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Expand to endpoint
      await user.click(screen.getByText('example.com'));
      await user.click(screen.getByText('api'));
      await user.click(screen.getByText('users'));

      // Click endpoint
      const getNode = screen.getByText('GET');
      await user.click(getNode);

      // Check for selected state (aria-selected or class)
      const treeItem = getNode.closest('[role="treeitem"]');
      expect(treeItem).toHaveAttribute('aria-selected', 'true');
    });
  });

  describe('Virtualization', () => {
    it('should handle large datasets without performance issues', () => {
      const largeAssets = generateLargeAssetSet(1000);

      const startTime = performance.now();
      renderWithProviders(<AssetTreeView assets={largeAssets} />);
      const endTime = performance.now();

      // Should render in less than 200ms
      expect(endTime - startTime).toBeLessThan(200);
    });

    it('should render virtualized container', () => {
      const largeAssets = generateLargeAssetSet(100);
      renderWithProviders(<AssetTreeView assets={largeAssets} />);

      expect(screen.getByTestId('asset-tree-virtualizer')).toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    it('should handle keyboard events on tree container', async () => {
      renderWithProviders(<AssetTreeView assets={mockAssets} />);

      const tree = screen.getByRole('tree');
      expect(tree).toHaveAttribute('tabindex', '-1');

      // Tree items should be focusable
      const firstItem = screen.getAllByRole('treeitem')[0];
      expect(firstItem).toHaveAttribute('tabindex', '0');
    });

    it('should expand node on ArrowRight', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      const domainNode = screen.getByRole('treeitem', { name: /example\.com/i });
      domainNode.focus();

      await user.keyboard('{ArrowRight}');

      expect(domainNode).toHaveAttribute('aria-expanded', 'true');
    });

    it('should collapse node on ArrowLeft', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // First expand the node
      const domainNode = screen.getByRole('treeitem', { name: /example\.com/i });
      await user.click(domainNode);
      expect(domainNode).toHaveAttribute('aria-expanded', 'true');

      // Then collapse with ArrowLeft
      domainNode.focus();
      await user.keyboard('{ArrowLeft}');

      expect(domainNode).toHaveAttribute('aria-expanded', 'false');
    });

    it('should select node on Enter', async () => {
      const onSelectAsset = vi.fn();
      const { user } = renderWithProviders(
        <AssetTreeView assets={mockAssets} onSelectAsset={onSelectAsset} />
      );

      // Expand to endpoint
      await user.click(screen.getByText('example.com'));
      await user.click(screen.getByText('api'));
      await user.click(screen.getByText('users'));

      const endpointNode = screen.getByText('GET').closest('[role="treeitem"]');
      if (endpointNode) {
        (endpointNode as HTMLElement).focus();
        await user.keyboard('{Enter}');
      }

      expect(onSelectAsset).toHaveBeenCalled();
    });
  });

  describe('Visual Indicators', () => {
    it('should show different icons for different node types', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Domain should have globe/server icon
      expect(screen.getByTestId('icon-domain-example.com')).toBeInTheDocument();

      // Expand to see folder
      await user.click(screen.getByText('example.com'));
      expect(screen.getByTestId('icon-folder-api')).toBeInTheDocument();
    });

    it('should indent nodes based on depth', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      await user.click(screen.getByText('example.com'));

      const folderNode = screen.getByText('api').closest('[role="treeitem"]');

      // Check depth attribute indicates indentation (folder at depth 1)
      expect(folderNode).toHaveAttribute('data-depth', '1');
    });
  });
});
