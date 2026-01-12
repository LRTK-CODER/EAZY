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
import { TreeNode } from './TreeNode';
import type { Asset } from '@/types/asset';

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
  /** Additional className */
  className?: string;
}

/**
 * AssetTreeView
 * Displays assets in a virtualized tree structure
 */
export function AssetTreeView({
  assets,
  onSelectAsset,
  showTypeBadge = false,
  showSourceBadge = false,
  className,
}: AssetTreeViewProps) {
  const parentRef = useRef<HTMLDivElement>(null);
  const { expandedNodes, toggleNode, selectedAssetId, setSelectedAssetId } = useAssetExplorer();
  const [focusedIndex, setFocusedIndex] = useState(-1);

  // Build tree from assets
  const tree = useMemo(() => buildAssetTree(assets), [assets]);

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

  // Empty state
  if (assets.length === 0) {
    return (
      <div className={cn('flex items-center justify-center h-full text-muted-foreground', className)}>
        <p>No assets found</p>
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
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
