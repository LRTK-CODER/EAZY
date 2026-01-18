/**
 * TreeNode Component
 * Individual tree node for asset tree view with support for different node types,
 * badges, and collapsible behavior
 */

import React, { useCallback } from 'react';
import { ChevronRight, ChevronDown, Globe, Folder, FolderOpen, FileCode } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import type { FlatNode, TreeNodeType } from '@/utils/assetTree';

/**
 * Get icon component for node type
 */
export function getNodeIcon(type: TreeNodeType, isExpanded: boolean) {
  switch (type) {
    case 'domain':
      return Globe;
    case 'folder':
      return isExpanded ? FolderOpen : Folder;
    case 'endpoint':
      return FileCode;
    default:
      return Folder;
  }
}

/**
 * Get badge variant for HTTP method
 */
export function getMethodVariant(method?: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (method?.toUpperCase()) {
    case 'GET':
      return 'secondary';
    case 'POST':
      return 'default';
    case 'PUT':
      return 'outline';
    case 'DELETE':
      return 'destructive';
    default:
      return 'outline';
  }
}

/**
 * Get badge variant for asset type
 */
export function getTypeBadgeVariant(type?: string): 'default' | 'secondary' | 'outline' {
  switch (type) {
    case 'url':
      return 'secondary';
    case 'form':
      return 'default';
    case 'xhr':
      return 'outline';
    default:
      return 'secondary';
  }
}

/**
 * Get badge variant for asset source
 */
export function getSourceBadgeVariant(source?: string): 'default' | 'secondary' | 'outline' {
  switch (source) {
    case 'html':
      return 'secondary';
    case 'js':
      return 'default';
    case 'network':
      return 'outline';
    case 'dom':
      return 'secondary';
    default:
      return 'secondary';
  }
}

/**
 * Highlight matching text in a string
 */
export function highlightMatch(text: string, query?: string): React.ReactNode {
  if (!query || !text) {
    return text;
  }

  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();
  const index = lowerText.indexOf(lowerQuery);

  if (index === -1) {
    return text;
  }

  const before = text.slice(0, index);
  const match = text.slice(index, index + query.length);
  const after = text.slice(index + query.length);

  return (
    <>
      {before}
      <mark
        className="bg-yellow-200 dark:bg-yellow-800 text-inherit rounded-sm px-0.5"
        data-testid={`search-highlight-${lowerQuery}`}
      >
        {match}
      </mark>
      {after}
    </>
  );
}

/**
 * Props for TreeNode component
 */
export interface TreeNodeProps {
  /** The flattened node data */
  node: FlatNode;
  /** Whether this node is currently selected */
  isSelected: boolean;
  /** Callback when node is toggled (expand/collapse) */
  onToggle: (nodeId: string) => void;
  /** Callback when node is selected */
  onSelect: (node: FlatNode) => void;
  /** Whether to show the asset type badge (default: false) */
  showTypeBadge?: boolean;
  /** Whether to show the asset source badge (default: false) */
  showSourceBadge?: boolean;
  /** Search query for highlighting matching text */
  searchQuery?: string;
  /** Additional className */
  className?: string;
}

/**
 * TreeNode Component
 * Renders a single tree node with appropriate icon, badges, and interaction handlers
 */
export const TreeNode = React.memo(function TreeNode({
  node,
  isSelected,
  onToggle,
  onSelect,
  showTypeBadge = false,
  showSourceBadge = false,
  searchQuery,
  className,
}: TreeNodeProps) {
  const Icon = getNodeIcon(node.type, node.isExpanded);
  const indentPx = node.depth * 16;

  const handleClick = useCallback(() => {
    if (node.hasChildren) {
      onToggle(node.id);
    }
    onSelect(node);
  }, [node, onToggle, onSelect]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'Enter':
        case ' ':
          e.preventDefault();
          onSelect(node);
          break;
        case 'ArrowRight':
          // Only expand if collapsed and has children
          if (node.hasChildren && !node.isExpanded) {
            e.preventDefault();
            e.stopPropagation();
            onToggle(node.id);
          }
          // If already expanded, let parent handle navigation to first child
          break;
        case 'ArrowLeft':
          // Only collapse if expanded and has children
          if (node.hasChildren && node.isExpanded) {
            e.preventDefault();
            e.stopPropagation();
            onToggle(node.id);
          }
          // If already collapsed, let parent handle navigation to parent node
          break;
      }
    },
    [node, onToggle, onSelect]
  );

  return (
    <div
      role="treeitem"
      aria-expanded={node.hasChildren ? node.isExpanded : undefined}
      aria-selected={isSelected}
      aria-level={node.depth + 1}
      data-depth={node.depth}
      tabIndex={0}
      className={cn(
        'flex items-center gap-1 px-2 py-1 cursor-pointer rounded-sm text-sm',
        'hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1',
        isSelected && 'bg-accent',
        className
      )}
      style={{ paddingLeft: `${indentPx + 8}px` }}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      {/* Expand/Collapse Chevron */}
      {node.hasChildren ? (
        <span className="w-4 h-4 flex items-center justify-center">
          {node.isExpanded ? (
            <ChevronDown className="h-3 w-3" data-testid="chevron-expanded" />
          ) : (
            <ChevronRight className="h-3 w-3" data-testid="chevron-collapsed" />
          )}
        </span>
      ) : (
        <span className="w-4" />
      )}

      {/* Node Type Icon */}
      <Icon
        className="h-4 w-4 text-muted-foreground"
        data-testid={`icon-${node.type}-${node.name}`}
      />

      {/* Node Name or Method Badge */}
      {node.type === 'endpoint' && node.method ? (
        <div className="flex items-center gap-1.5 min-w-0">
          <Badge
            variant={getMethodVariant(node.method)}
            className="text-xs shrink-0"
            data-testid="method-badge"
          >
            {node.method}
          </Badge>
          {node.endpointSuffix && (
            <span
              className="text-muted-foreground text-xs font-mono truncate"
              data-testid="endpoint-suffix"
              title={node.endpointSuffix}
            >
              {node.endpointSuffix}
            </span>
          )}
        </div>
      ) : (
        <span className="truncate">{highlightMatch(node.name, searchQuery)}</span>
      )}

      {/* Optional Type Badge (for endpoints) */}
      {showTypeBadge && node.type === 'endpoint' && node.asset?.type && (
        <Badge
          variant={getTypeBadgeVariant(node.asset.type)}
          className="text-xs ml-1"
          data-testid="type-badge"
        >
          {node.asset.type}
        </Badge>
      )}

      {/* Optional Source Badge (for endpoints) */}
      {showSourceBadge && node.type === 'endpoint' && node.asset?.source && (
        <Badge
          variant={getSourceBadgeVariant(node.asset.source)}
          className="text-xs ml-1"
          data-testid="source-badge"
        >
          {node.asset.source}
        </Badge>
      )}
    </div>
  );
});

export default TreeNode;
