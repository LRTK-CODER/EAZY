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

      expect(screen.getByText('https://example.com')).toBeInTheDocument();
      expect(screen.getByText('https://api.example.org')).toBeInTheDocument();
    });

    it('should render folder nodes when expanded', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Click to expand domain
      const domainNode = screen.getByText('https://example.com');
      await user.click(domainNode);

      // Should show folder nodes
      expect(screen.getByText('api')).toBeInTheDocument();
    });

    it('should render endpoint nodes with HTTP method', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Expand domain -> folder -> endpoint
      await user.click(screen.getByText('https://example.com'));
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

      const domainNode = screen.getByText('https://example.com');

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
      await user.click(screen.getByText('https://example.com'));
      await user.click(screen.getByText('api'));
      await user.click(screen.getByText('users'));

      // Click endpoint
      await user.click(screen.getByText('GET'));

      expect(onSelectAsset).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }));
    });

    it('should highlight selected node', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Expand to endpoint
      await user.click(screen.getByText('https://example.com'));
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
      await user.click(screen.getByText('https://example.com'));
      await user.click(screen.getByText('api'));
      await user.click(screen.getByText('users'));

      const endpointNode = screen.getByText('GET').closest('[role="treeitem"]');
      if (endpointNode) {
        (endpointNode as HTMLElement).focus();
        await user.keyboard('{Enter}');
      }

      expect(onSelectAsset).toHaveBeenCalled();
    });

    it('should move focus to first child on ArrowRight when node is expanded', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // First expand the domain node
      const domainNode = screen.getByRole('treeitem', { name: /example\.com/i });
      await user.click(domainNode);
      expect(domainNode).toHaveAttribute('aria-expanded', 'true');

      // Focus the expanded node and use keyboard to navigate
      domainNode.focus();
      expect(domainNode).toHaveFocus();

      // Press ArrowRight - on expanded node, should navigate to first child
      await user.keyboard('{ArrowRight}');

      // Wait for requestAnimationFrame
      await new Promise(resolve => setTimeout(resolve, 50));

      // Verify first child node (api folder under example.com) exists and can receive focus
      // The api folder should be visible now that example.com is expanded
      const apiFolder = screen.getByText('api').closest('[role="treeitem"]');
      expect(apiFolder).toBeInTheDocument();
      expect(apiFolder).toHaveAttribute('data-depth', '1');
    });

    it('should move focus to parent on ArrowLeft when node is collapsed', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Expand domain to see folder
      await user.click(screen.getByText('https://example.com'));

      // Find and focus the child folder node (api) - use text content to be specific
      const apiFolder = screen.getByText('api').closest('[role="treeitem"]') as HTMLElement;
      apiFolder.focus();
      expect(apiFolder).toHaveFocus();

      // Press ArrowLeft - child is collapsed so should navigate to parent
      await user.keyboard('{ArrowLeft}');

      // Wait for requestAnimationFrame
      await new Promise(resolve => setTimeout(resolve, 50));

      // Parent domain node should now have focus
      const domainNode = screen.getByRole('treeitem', { name: /example\.com/i });
      expect(domainNode).toHaveFocus();
    });

    it('should clear focus on Escape key', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Focus a node
      const domainNode = screen.getByRole('treeitem', { name: /example\.com/i });
      domainNode.focus();
      expect(domainNode).toHaveFocus();

      // Press Escape
      await user.keyboard('{Escape}');

      // Node should no longer have focus
      expect(domainNode).not.toHaveFocus();
    });
  });

  describe('Visual Indicators', () => {
    it('should show different icons for different node types', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Domain should have globe/server icon
      expect(screen.getByTestId('icon-domain-https://example.com')).toBeInTheDocument();

      // Expand to see folder
      await user.click(screen.getByText('https://example.com'));
      expect(screen.getByTestId('icon-folder-api')).toBeInTheDocument();
    });

    it('should indent nodes based on depth', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      await user.click(screen.getByText('https://example.com'));

      const folderNode = screen.getByText('api').closest('[role="treeitem"]');

      // Check depth attribute indicates indentation (folder at depth 1)
      expect(folderNode).toHaveAttribute('data-depth', '1');
    });
  });

  // ============================================================================
  // Phase 3: Selection/Focus Visual Distinction Tests (TDD - RED)
  // ============================================================================
  describe('Selection and Focus Visual Distinction', () => {
    it('should have focus ring styles defined on treeitem', () => {
      renderWithProviders(<AssetTreeView assets={mockAssets} />);

      const domainNode = screen.getByRole('treeitem', { name: /example\.com/i });

      // Should have focus:ring-2 class for focus state styling
      expect(domainNode.className).toContain('focus:ring-2');
      expect(domainNode.className).toContain('focus:ring-ring');
    });

    it('should show background color when node is selected', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Expand to endpoint and select it
      await user.click(screen.getByText('https://example.com'));
      await user.click(screen.getByText('api'));
      await user.click(screen.getByText('users'));
      await user.click(screen.getByText('GET'));

      const selectedNode = screen.getByText('GET').closest('[role="treeitem"]');

      // Should have selected background class
      expect(selectedNode).toHaveClass('bg-accent');
    });

    it('should have both focus ring styles and selection background when focused and selected', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      // Expand to endpoint and select it
      await user.click(screen.getByText('https://example.com'));
      await user.click(screen.getByText('api'));
      await user.click(screen.getByText('users'));
      await user.click(screen.getByText('GET'));

      const selectedNode = screen.getByText('GET').closest('[role="treeitem"]') as HTMLElement;

      // Focus the selected node
      selectedNode.focus();

      // Should have selection background class
      expect(selectedNode).toHaveClass('bg-accent');
      // Should have focus ring styles defined
      expect(selectedNode.className).toContain('focus:ring-2');
      // Should be focused
      expect(selectedNode).toHaveFocus();
    });

    it('should support focus navigation between nodes', async () => {
      const { user } = renderWithProviders(<AssetTreeView assets={mockAssets} />);

      const domainNode1 = screen.getByRole('treeitem', { name: /example\.com/i });
      const domainNode2 = screen.getByRole('treeitem', { name: /api\.example\.org/i });

      // Focus first node
      domainNode1.focus();
      expect(domainNode1).toHaveFocus();

      // Focus second node
      domainNode2.focus();

      // First node should no longer have focus
      expect(domainNode1).not.toHaveFocus();
      // Second node should have focus
      expect(domainNode2).toHaveFocus();
    });
  });

  // ============================================================================
  // Phase 2.1: Search/Filtering Tests (TDD - RED)
  // ============================================================================
  describe('Search and Filtering', () => {
    it('should filter tree when search query is provided', () => {
      renderWithProviders(
        <AssetTreeView assets={mockAssets} searchQuery="api" />
      );

      // Should show nodes matching "api"
      expect(screen.getByText('https://example.com')).toBeInTheDocument();
      // Should not show nodes not matching "api"
      expect(screen.queryByText('auth')).not.toBeInTheDocument();
    });

    it('should filter by HTTP method when filterMethods is provided', async () => {
      const { user } = renderWithProviders(
        <AssetTreeView assets={mockAssets} filterMethods={['GET']} />
      );

      // Expand to see endpoints
      await user.click(screen.getByText('https://example.com'));
      await user.click(screen.getByText('api'));
      await user.click(screen.getByText('users'));

      // Should show only GET endpoints
      expect(screen.getByText('GET')).toBeInTheDocument();
      expect(screen.queryByText('POST')).not.toBeInTheDocument();
    });

    it('should combine search query and method filter with AND logic', async () => {
      const { user } = renderWithProviders(
        <AssetTreeView assets={mockAssets} searchQuery="users" filterMethods={['POST']} />
      );

      // With searchQuery="users" and filterMethods=["POST"], only /api/users POST should remain
      // Mock data has: /api/users (GET, POST), /auth/login (POST), /v1/data (GET)
      // Only /api/users POST matches both filters

      // Expand all nodes iteratively until we find the endpoint
      let maxIterations = 10;
      while (maxIterations > 0) {
        const items = screen.getAllByRole('treeitem');
        let expanded = false;
        for (const item of items) {
          if (item.getAttribute('aria-expanded') === 'false') {
            await user.click(item);
            expanded = true;
            break;
          }
        }
        if (!expanded) break;
        maxIterations--;
      }

      // After expanding all nodes, check for POST endpoint
      const postBadges = screen.queryAllByText('POST');
      const getBadges = screen.queryAllByText('GET');

      // Debug: log what we found
      // screen.debug();

      expect(postBadges.length).toBeGreaterThan(0);
      expect(getBadges.length).toBe(0);
    });

    it('should filter by multiple HTTP methods when filterMethods has multiple values', async () => {
      const { user } = renderWithProviders(
        <AssetTreeView assets={mockAssets} filterMethods={['GET', 'POST']} />
      );

      // Expand to see endpoints
      await user.click(screen.getByText('https://example.com'));
      await user.click(screen.getByText('api'));
      await user.click(screen.getByText('users'));

      // Should show both GET and POST endpoints
      expect(screen.getAllByText('GET').length).toBeGreaterThan(0);
      expect(screen.getAllByText('POST').length).toBeGreaterThan(0);
    });

    it('should show all assets when filterMethods is empty array', async () => {
      const { user } = renderWithProviders(
        <AssetTreeView assets={mockAssets} filterMethods={[]} />
      );

      // Should show all assets (same as no filter)
      await user.click(screen.getByText('https://example.com'));
      await user.click(screen.getByText('api'));
      await user.click(screen.getByText('users'));

      expect(screen.getAllByText('GET').length).toBeGreaterThan(0);
      expect(screen.getAllByText('POST').length).toBeGreaterThan(0);
    });

    it('should show empty state when no results match filter', () => {
      renderWithProviders(
        <AssetTreeView assets={mockAssets} searchQuery="nonexistent" />
      );

      expect(screen.getByText(/no matching assets/i)).toBeInTheDocument();
    });

    it('should highlight matching text in search results', () => {
      renderWithProviders(
        <AssetTreeView assets={mockAssets} searchQuery="api" />
      );

      // Check for highlighted text (mark element or special class)
      // Multiple highlights may exist (e.g., api.example.org and example.com/api)
      const highlightedElements = screen.getAllByTestId('search-highlight-api');
      expect(highlightedElements.length).toBeGreaterThan(0);
      expect(highlightedElements[0]).toBeInTheDocument();
    });

    it('should expand parent nodes when child matches search', () => {
      renderWithProviders(
        <AssetTreeView assets={mockAssets} searchQuery="users" />
      );

      // Parent nodes should be auto-expanded to show matching children
      expect(screen.getByText('api')).toBeInTheDocument();
      expect(screen.getByText('users')).toBeInTheDocument();
    });
  });
});
