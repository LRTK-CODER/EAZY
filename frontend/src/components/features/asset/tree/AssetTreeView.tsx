/**
 * AssetTreeView Component
 * Virtualized tree view for displaying assets in a hierarchical structure
 */

import React, { useRef, useMemo, useCallback, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { cn } from '@/lib/utils';
import { useAssetExplorer } from '@/contexts/AssetExplorerContext';
import {
  buildAssetTree,
  flattenTreeForVirtualization,
  type TreeNode as TreeNodeType,
  type FlatNode,
} from '@/utils/assetTree';
import { filterAssets, type HttpMethod } from '@/hooks/use-asset-filter';
import { TreeNode } from './TreeNode';
import type { Asset } from '@/types/asset';

// Re-export HttpMethod for convenience
export type { HttpMethod } from '@/hooks/use-asset-filter';

/**
 * Props for AssetTreeView
 */
interface AssetTreeViewProps {
  /** Array of assets to display */
  assets: Asset[];
  /** Callback when an asset is selected */
  onSelectAsset?: (asset: Asset) => void;
  /** Whether to show asset type badges */
  showTypeBadge?: boolean;
  /** Whether to show asset source badges */
  showSourceBadge?: boolean;
  /** Search query to filter assets */
  searchQuery?: string;
  /** HTTP method filter */
  filterMethod?: HttpMethod;
  /** Additional className */
  className?: string;
}

/**
 * Get node IDs that should be expanded to show matching nodes
 */
function getExpandedNodesForSearch(
  tree: TreeNodeType[],
  searchQuery: string
): Set<string> {
  const expandedIds = new Set<string>();

  const traverse = (nodes: TreeNodeType[], ancestors: string[]): boolean => {
    let hasMatchingDescendant = false;

    for (const node of nodes) {
      const nodeMatches =
        node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        node.path.toLowerCase().includes(searchQuery.toLowerCase());

      const childHasMatch = node.children.length > 0
        ? traverse(node.children, [...ancestors, node.id])
        : false;

      if (nodeMatches || childHasMatch) {
        hasMatchingDescendant = true;
        // Expand all ancestors
        ancestors.forEach((id) => expandedIds.add(id));
        // Also expand this node if it has matching children
        if (childHasMatch) {
          expandedIds.add(node.id);
        }
      }
    }

    return hasMatchingDescendant;
  };

  traverse(tree, []);
  return expandedIds;
}

export function AssetTreeView({
  assets,
  onSelectAsset,
  showTypeBadge = false,
  showSourceBadge = false,
  searchQuery,
  filterMethod,
  className,
}: AssetTreeViewProps) {
  const parentRef = useRef<HTMLDivElement>(null);
  const { expandedNodes, toggleNode, selectedAssetId, setSelectedAssetId, expandAll } = useAssetExplorer();
  const [focusedIndex, setFocusedIndex] = useState(-1);

  // Filter assets based on search query and method filter
  const filteredAssets = useMemo(
    () => filterAssets(assets, searchQuery, filterMethod),
    [assets, searchQuery, filterMethod]
  );

  // Build tree from filtered assets
  const tree = useMemo(() => buildAssetTree(filteredAssets), [filteredAssets]);

  // Auto-expand nodes when searching
  const searchExpandedNodes = useMemo(() => {
    if (!searchQuery) return null;
    return getExpandedNodesForSearch(tree, searchQuery);
  }, [tree, searchQuery]);

  // Apply search-triggered expansions
  React.useEffect(() => {
    if (searchExpandedNodes && searchExpandedNodes.size > 0) {
      expandAll([...searchExpandedNodes]);
    }
  }, [searchExpandedNodes, expandAll]);

  // Apply expanded state from context to tree
  const treeWithState = useMemo(() => {
    const applyExpandedState = (nodes: TreeNodeType[]): TreeNodeType[] => {
      return nodes.map((node) => ({
        ...node,
        isExpanded: expandedNodes.has(node.id),
        children: applyExpandedState(node.children),
      }));
    };
    return applyExpandedState(tree);
  }, [tree, expandedNodes]);

  // Flatten tree for virtualization
  const flatNodes = useMemo(
    () => flattenTreeForVirtualization(treeWithState),
    [treeWithState]
  );

  // Virtualizer
  const virtualizer = useVirtualizer({
    count: flatNodes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 28, // Estimated row height
    overscan: 5,
  });

  // Handle node selection
  const handleSelect = useCallback(
    (node: FlatNode) => {
      if (node.type === 'endpoint' && node.asset) {
        setSelectedAssetId(node.asset.id);
        onSelectAsset?.(node.asset);
      }
    },
    [setSelectedAssetId, onSelectAsset]
  );

  // Keyboard navigation for tree
  const handleTreeKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const items = flatNodes;
      let newIndex = focusedIndex;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          newIndex = Math.min(focusedIndex + 1, items.length - 1);
          break;
        case 'ArrowUp':
          e.preventDefault();
          newIndex = Math.max(focusedIndex - 1, 0);
          break;
        case 'Home':
          e.preventDefault();
          newIndex = 0;
          break;
        case 'End':
          e.preventDefault();
          newIndex = items.length - 1;
          break;
        default:
          return;
      }

      if (newIndex !== focusedIndex && newIndex >= 0) {
        setFocusedIndex(newIndex);
        virtualizer.scrollToIndex(newIndex);
        // Focus the element
        const container = parentRef.current;
        if (container) {
          const element = container.querySelector(`[data-index="${newIndex}"]`) as HTMLElement;
          element?.focus();
        }
      }
    },
    [flatNodes, focusedIndex, virtualizer]
  );

  // Empty state - no assets at all
  if (assets.length === 0) {
    return (
      <div className={cn('flex items-center justify-center h-full text-muted-foreground', className)}>
        <p>No assets found</p>
      </div>
    );
  }

  // Empty state - no matching assets after filtering
  if (filteredAssets.length === 0 && (searchQuery || filterMethod)) {
    return (
      <div className={cn('flex items-center justify-center h-full text-muted-foreground', className)}>
        <p>No matching assets</p>
      </div>
    );
  }

  return (
    <div
      role="tree"
      aria-label="Asset tree"
      className={cn('h-full overflow-auto', className)}
      ref={parentRef}
      data-testid="asset-tree-virtualizer"
      onKeyDown={handleTreeKeyDown}
      tabIndex={-1}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualRow) => {
          const node = flatNodes[virtualRow.index];
          const isSelected = node.asset?.id === selectedAssetId;

          return (
            <div
              key={node.id}
              data-index={virtualRow.index}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <TreeNode
                node={node}
                isSelected={isSelected}
                onToggle={toggleNode}
                onSelect={handleSelect}
                showTypeBadge={showTypeBadge}
                showSourceBadge={showSourceBadge}
                searchQuery={searchQuery}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
