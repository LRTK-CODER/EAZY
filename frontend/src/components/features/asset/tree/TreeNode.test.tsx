/**
 * TreeNode Component Tests
 * Tests for individual tree node rendering, badges, and interactions
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TreeNode, getNodeIcon, getTypeBadgeVariant, getSourceBadgeVariant } from './TreeNode';
import { getHttpMethodVariant } from '@/lib/http-method';
import type { FlatNode } from '@/utils/assetTree';
import type { Asset } from '@/types/asset';

// Mock asset factory
function createMockAsset(overrides: Partial<Asset> = {}): Asset {
  return {
    id: 1,
    target_id: 1,
    content_hash: 'abc123',
    type: 'url',
    source: 'html',
    method: 'GET',
    url: 'https://example.com/api/users',
    path: '/api/users',
    request_spec: null,
    response_spec: null,
    parameters: null,
    last_task_id: null,
    first_seen_at: '2024-01-01T00:00:00Z',
    last_seen_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

// Mock FlatNode factory
function createMockFlatNode(overrides: Partial<FlatNode> = {}): FlatNode {
  return {
    id: 'domain-example.com',
    name: 'example.com',
    path: 'example.com',
    type: 'domain',
    depth: 0,
    hasChildren: true,
    isExpanded: false,
    ...overrides,
  };
}

describe('TreeNode Component', () => {
  const defaultProps = {
    node: createMockFlatNode(),
    isSelected: false,
    onToggle: vi.fn(),
    onSelect: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // =====================
  // 5.1.1 Domain Node Rendering Tests
  // =====================
  describe('Domain Node Rendering', () => {
    it('renders domain node with Globe icon', () => {
      const domainNode = createMockFlatNode({
        type: 'domain',
        name: 'api.example.com',
      });

      render(<TreeNode {...defaultProps} node={domainNode} />);

      expect(screen.getByText('api.example.com')).toBeInTheDocument();
      expect(screen.getByTestId('icon-domain-api.example.com')).toBeInTheDocument();
    });

    it('renders domain node with expand chevron when has children', () => {
      const domainNode = createMockFlatNode({
        type: 'domain',
        hasChildren: true,
        isExpanded: false,
      });

      render(<TreeNode {...defaultProps} node={domainNode} />);

      expect(screen.getByTestId('chevron-collapsed')).toBeInTheDocument();
    });

    it('renders expanded chevron when domain is expanded', () => {
      const domainNode = createMockFlatNode({
        type: 'domain',
        hasChildren: true,
        isExpanded: true,
      });

      render(<TreeNode {...defaultProps} node={domainNode} />);

      expect(screen.getByTestId('chevron-expanded')).toBeInTheDocument();
    });

    it('renders at depth 0 with minimal indent', () => {
      const domainNode = createMockFlatNode({
        type: 'domain',
        depth: 0,
      });

      const { container } = render(<TreeNode {...defaultProps} node={domainNode} />);
      const treeItem = container.querySelector('[role="treeitem"]');

      expect(treeItem).toHaveStyle({ paddingLeft: '8px' });
    });
  });

  // =====================
  // 5.1.2 Folder Node Rendering Tests
  // =====================
  describe('Folder Node Rendering', () => {
    it('renders folder node with Folder icon when collapsed', () => {
      const folderNode = createMockFlatNode({
        id: 'folder-api',
        type: 'folder',
        name: 'api',
        depth: 1,
        hasChildren: true,
        isExpanded: false,
      });

      render(<TreeNode {...defaultProps} node={folderNode} />);

      expect(screen.getByText('api')).toBeInTheDocument();
      expect(screen.getByTestId('icon-folder-api')).toBeInTheDocument();
    });

    it('renders folder node with FolderOpen icon when expanded', () => {
      const folderNode = createMockFlatNode({
        id: 'folder-users',
        type: 'folder',
        name: 'users',
        depth: 2,
        hasChildren: true,
        isExpanded: true,
      });

      render(<TreeNode {...defaultProps} node={folderNode} />);

      expect(screen.getByTestId('icon-folder-users')).toBeInTheDocument();
    });

    it('renders folder with correct depth indentation', () => {
      const folderNode = createMockFlatNode({
        type: 'folder',
        name: 'nested',
        depth: 3,
      });

      const { container } = render(<TreeNode {...defaultProps} node={folderNode} />);
      const treeItem = container.querySelector('[role="treeitem"]');

      // depth * 16 + 8 = 3 * 16 + 8 = 56px
      expect(treeItem).toHaveStyle({ paddingLeft: '56px' });
    });

    it('renders leaf folder without chevron', () => {
      const leafFolder = createMockFlatNode({
        type: 'folder',
        name: 'empty',
        hasChildren: false,
      });

      render(<TreeNode {...defaultProps} node={leafFolder} />);

      expect(screen.queryByTestId('chevron-collapsed')).not.toBeInTheDocument();
      expect(screen.queryByTestId('chevron-expanded')).not.toBeInTheDocument();
    });
  });

  // =====================
  // 5.1.3 Endpoint Node Rendering Tests
  // =====================
  describe('Endpoint Node Rendering', () => {
    it('renders endpoint node with FileCode icon', () => {
      const endpointNode = createMockFlatNode({
        id: 'endpoint-1-GET',
        type: 'endpoint',
        name: 'GET',
        method: 'GET',
        depth: 3,
        hasChildren: false,
        asset: createMockAsset(),
      });

      render(<TreeNode {...defaultProps} node={endpointNode} />);

      expect(screen.getByTestId('icon-endpoint-GET')).toBeInTheDocument();
    });

    it('renders method badge instead of name for endpoints', () => {
      const endpointNode = createMockFlatNode({
        type: 'endpoint',
        name: 'POST',
        method: 'POST',
        hasChildren: false,
        asset: createMockAsset({ method: 'POST' }),
      });

      render(<TreeNode {...defaultProps} node={endpointNode} />);

      // Should show badge with method, not plain text
      const badge = screen.getByText('POST');
      expect(badge).toBeInTheDocument();
      expect(badge.closest('[data-testid="method-badge"]')).toBeInTheDocument();
    });

    it('renders endpoint without chevron (leaf node)', () => {
      const endpointNode = createMockFlatNode({
        type: 'endpoint',
        method: 'GET',
        hasChildren: false,
      });

      render(<TreeNode {...defaultProps} node={endpointNode} />);

      expect(screen.queryByTestId('chevron-collapsed')).not.toBeInTheDocument();
    });

    it('renders endpoint at correct depth', () => {
      const endpointNode = createMockFlatNode({
        type: 'endpoint',
        depth: 5,
        hasChildren: false,
      });

      const { container } = render(<TreeNode {...defaultProps} node={endpointNode} />);
      const treeItem = container.querySelector('[role="treeitem"]');

      // 5 * 16 + 8 = 88px
      expect(treeItem).toHaveStyle({ paddingLeft: '88px' });
    });
  });

  // =====================
  // 5.1.4 Badge (Type/Source/Method) Tests
  // =====================
  describe('Badge Rendering', () => {
    describe('Method Badge', () => {
      it.each([
        ['GET', 'method-get'],
        ['POST', 'method-post'],
        ['PUT', 'method-put'],
        ['DELETE', 'method-delete'],
        ['PATCH', 'method-patch'],
        ['OPTIONS', 'method-options'],
      ])('renders %s method with %s variant', (method, expectedVariant) => {
        const variant = getHttpMethodVariant(method);
        expect(variant).toBe(expectedVariant);
      });

      it('renders method badge on endpoint nodes', () => {
        const endpointNode = createMockFlatNode({
          type: 'endpoint',
          method: 'DELETE',
          name: 'DELETE',
          hasChildren: false,
          asset: createMockAsset({ method: 'DELETE' }),
        });

        render(<TreeNode {...defaultProps} node={endpointNode} />);

        const methodBadge = screen.getByTestId('method-badge');
        expect(methodBadge).toHaveTextContent('DELETE');
      });
    });

    describe('Type Badge', () => {
      it.each([
        ['url', 'secondary'],
        ['form', 'default'],
        ['xhr', 'outline'],
      ])('returns %s type with %s variant', (type, expectedVariant) => {
        const variant = getTypeBadgeVariant(type as 'url' | 'form' | 'xhr');
        expect(variant).toBe(expectedVariant);
      });

      it('renders type badge on endpoint nodes when showTypeBadge is true', () => {
        const endpointNode = createMockFlatNode({
          type: 'endpoint',
          method: 'GET',
          hasChildren: false,
          asset: createMockAsset({ type: 'form' }),
        });

        render(<TreeNode {...defaultProps} node={endpointNode} showTypeBadge />);

        const typeBadge = screen.getByTestId('type-badge');
        expect(typeBadge).toHaveTextContent('form');
      });

      it('does not render type badge when showTypeBadge is false', () => {
        const endpointNode = createMockFlatNode({
          type: 'endpoint',
          method: 'GET',
          hasChildren: false,
          asset: createMockAsset({ type: 'xhr' }),
        });

        render(<TreeNode {...defaultProps} node={endpointNode} showTypeBadge={false} />);

        expect(screen.queryByTestId('type-badge')).not.toBeInTheDocument();
      });
    });

    describe('Source Badge', () => {
      it.each([
        ['html', 'secondary'],
        ['js', 'default'],
        ['network', 'outline'],
        ['dom', 'secondary'],
      ])('returns %s source with %s variant', (source, expectedVariant) => {
        const variant = getSourceBadgeVariant(source as 'html' | 'js' | 'network' | 'dom');
        expect(variant).toBe(expectedVariant);
      });

      it('renders source badge on endpoint nodes when showSourceBadge is true', () => {
        const endpointNode = createMockFlatNode({
          type: 'endpoint',
          method: 'GET',
          hasChildren: false,
          asset: createMockAsset({ source: 'js' }),
        });

        render(<TreeNode {...defaultProps} node={endpointNode} showSourceBadge />);

        const sourceBadge = screen.getByTestId('source-badge');
        expect(sourceBadge).toHaveTextContent('js');
      });
    });

    describe('Multiple Badges', () => {
      it('renders all badges when all options enabled', () => {
        const endpointNode = createMockFlatNode({
          type: 'endpoint',
          method: 'POST',
          hasChildren: false,
          asset: createMockAsset({
            method: 'POST',
            type: 'xhr',
            source: 'network',
          }),
        });

        render(
          <TreeNode
            {...defaultProps}
            node={endpointNode}
            showTypeBadge
            showSourceBadge
          />
        );

        expect(screen.getByTestId('method-badge')).toHaveTextContent('POST');
        expect(screen.getByTestId('type-badge')).toHaveTextContent('xhr');
        expect(screen.getByTestId('source-badge')).toHaveTextContent('network');
      });
    });
  });

  // =====================
  // 5.1.5 Collapsible Behavior Tests
  // =====================
  describe('Collapsible Behavior', () => {
    it('calls onToggle when clicking node with children', async () => {
      const onToggle = vi.fn();
      const folderNode = createMockFlatNode({
        id: 'folder-test',
        type: 'folder',
        hasChildren: true,
      });

      render(<TreeNode {...defaultProps} node={folderNode} onToggle={onToggle} />);

      await userEvent.click(screen.getByRole('treeitem'));

      expect(onToggle).toHaveBeenCalledWith('folder-test');
    });

    it('calls onSelect when clicking any node', async () => {
      const onSelect = vi.fn();
      const node = createMockFlatNode();

      render(<TreeNode {...defaultProps} node={node} onSelect={onSelect} />);

      await userEvent.click(screen.getByRole('treeitem'));

      expect(onSelect).toHaveBeenCalledWith(node);
    });

    it('does not call onToggle for leaf nodes', async () => {
      const onToggle = vi.fn();
      const leafNode = createMockFlatNode({
        hasChildren: false,
      });

      render(<TreeNode {...defaultProps} node={leafNode} onToggle={onToggle} />);

      await userEvent.click(screen.getByRole('treeitem'));

      expect(onToggle).not.toHaveBeenCalled();
    });

    describe('Keyboard Navigation', () => {
      it('expands node on ArrowRight when collapsed', async () => {
        const onToggle = vi.fn();
        const node = createMockFlatNode({
          id: 'node-1',
          hasChildren: true,
          isExpanded: false,
        });

        render(<TreeNode {...defaultProps} node={node} onToggle={onToggle} />);

        const treeItem = screen.getByRole('treeitem');
        fireEvent.keyDown(treeItem, { key: 'ArrowRight' });

        expect(onToggle).toHaveBeenCalledWith('node-1');
      });

      it('collapses node on ArrowLeft when expanded', async () => {
        const onToggle = vi.fn();
        const node = createMockFlatNode({
          id: 'node-2',
          hasChildren: true,
          isExpanded: true,
        });

        render(<TreeNode {...defaultProps} node={node} onToggle={onToggle} />);

        const treeItem = screen.getByRole('treeitem');
        fireEvent.keyDown(treeItem, { key: 'ArrowLeft' });

        expect(onToggle).toHaveBeenCalledWith('node-2');
      });

      it('does not toggle on ArrowRight when already expanded', async () => {
        const onToggle = vi.fn();
        const node = createMockFlatNode({
          hasChildren: true,
          isExpanded: true,
        });

        render(<TreeNode {...defaultProps} node={node} onToggle={onToggle} />);

        const treeItem = screen.getByRole('treeitem');
        fireEvent.keyDown(treeItem, { key: 'ArrowRight' });

        expect(onToggle).not.toHaveBeenCalled();
      });

      it('does not toggle on ArrowLeft when already collapsed', async () => {
        const onToggle = vi.fn();
        const node = createMockFlatNode({
          hasChildren: true,
          isExpanded: false,
        });

        render(<TreeNode {...defaultProps} node={node} onToggle={onToggle} />);

        const treeItem = screen.getByRole('treeitem');
        fireEvent.keyDown(treeItem, { key: 'ArrowLeft' });

        expect(onToggle).not.toHaveBeenCalled();
      });

      it('selects node on Enter key', async () => {
        const onSelect = vi.fn();
        const node = createMockFlatNode();

        render(<TreeNode {...defaultProps} node={node} onSelect={onSelect} />);

        const treeItem = screen.getByRole('treeitem');
        fireEvent.keyDown(treeItem, { key: 'Enter' });

        expect(onSelect).toHaveBeenCalledWith(node);
      });

      it('selects node on Space key', async () => {
        const onSelect = vi.fn();
        const node = createMockFlatNode();

        render(<TreeNode {...defaultProps} node={node} onSelect={onSelect} />);

        const treeItem = screen.getByRole('treeitem');
        fireEvent.keyDown(treeItem, { key: ' ' });

        expect(onSelect).toHaveBeenCalledWith(node);
      });
    });
  });

  // =====================
  // Selection State Tests
  // =====================
  describe('Selection State Styling', () => {
    it('applies selected style when isSelected is true', () => {
      const node = createMockFlatNode();

      const { container } = render(<TreeNode {...defaultProps} node={node} isSelected />);

      const treeItem = container.querySelector('[role="treeitem"]');
      expect(treeItem).toHaveClass('bg-accent');
    });

    it('does not apply selected style when isSelected is false', () => {
      const node = createMockFlatNode();

      const { container } = render(<TreeNode {...defaultProps} node={node} isSelected={false} />);

      const treeItem = container.querySelector('[role="treeitem"]');
      // bg-accent should only appear with hover: or focus: prefix when not selected
      const classes = treeItem?.className.split(' ') || [];
      const bgAccentClasses = classes.filter(c => c.includes('bg-accent'));
      // All bg-accent classes should be prefixed with hover: or focus:
      expect(bgAccentClasses.every(c => c.startsWith('hover:') || c.startsWith('focus:'))).toBe(true);
    });

    it('sets aria-selected attribute correctly', () => {
      const node = createMockFlatNode();

      const { rerender } = render(<TreeNode {...defaultProps} node={node} isSelected />);
      expect(screen.getByRole('treeitem')).toHaveAttribute('aria-selected', 'true');

      rerender(<TreeNode {...defaultProps} node={node} isSelected={false} />);
      expect(screen.getByRole('treeitem')).toHaveAttribute('aria-selected', 'false');
    });
  });

  // =====================
  // ARIA Attributes Tests
  // =====================
  describe('ARIA Attributes', () => {
    it('has correct role="treeitem"', () => {
      render(<TreeNode {...defaultProps} />);
      expect(screen.getByRole('treeitem')).toBeInTheDocument();
    });

    it('sets aria-expanded for nodes with children', () => {
      const nodeWithChildren = createMockFlatNode({
        hasChildren: true,
        isExpanded: true,
      });

      render(<TreeNode {...defaultProps} node={nodeWithChildren} />);

      expect(screen.getByRole('treeitem')).toHaveAttribute('aria-expanded', 'true');
    });

    it('does not set aria-expanded for leaf nodes', () => {
      const leafNode = createMockFlatNode({
        hasChildren: false,
      });

      render(<TreeNode {...defaultProps} node={leafNode} />);

      expect(screen.getByRole('treeitem')).not.toHaveAttribute('aria-expanded');
    });

    it('sets aria-level based on depth', () => {
      const node = createMockFlatNode({ depth: 3 });

      render(<TreeNode {...defaultProps} node={node} />);

      // aria-level is 1-indexed, depth is 0-indexed
      expect(screen.getByRole('treeitem')).toHaveAttribute('aria-level', '4');
    });

    it('has data-depth attribute', () => {
      const node = createMockFlatNode({ depth: 2 });

      const { container } = render(<TreeNode {...defaultProps} node={node} />);

      expect(container.querySelector('[data-depth="2"]')).toBeInTheDocument();
    });
  });
});

// =====================
// Helper Function Tests
// =====================
describe('Helper Functions', () => {
  describe('getNodeIcon', () => {
    it('returns Globe for domain type', () => {
      const Icon = getNodeIcon('domain', false);
      expect(Icon.displayName || Icon.name).toMatch(/Globe/i);
    });

    it('returns Folder for collapsed folder type', () => {
      const Icon = getNodeIcon('folder', false);
      expect(Icon.displayName || Icon.name).toMatch(/Folder/i);
    });

    it('returns FolderOpen for expanded folder type', () => {
      const Icon = getNodeIcon('folder', true);
      expect(Icon.displayName || Icon.name).toMatch(/FolderOpen/i);
    });

    it('returns FileCode for endpoint type', () => {
      const Icon = getNodeIcon('endpoint', false);
      expect(Icon.displayName || Icon.name).toMatch(/FileCode/i);
    });
  });

  describe('getHttpMethodVariant', () => {
    it('handles undefined method', () => {
      expect(getHttpMethodVariant(undefined)).toBe('outline');
    });

    it('handles lowercase methods', () => {
      expect(getHttpMethodVariant('get')).toBe('method-get');
      expect(getHttpMethodVariant('post')).toBe('method-post');
    });
  });
});
