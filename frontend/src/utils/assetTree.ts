/**
 * Asset Tree Utility
 * Converts flat Asset[] array to hierarchical tree structure for Burp-style tree view
 */

import type { Asset } from '@/types/asset';

/**
 * Tree node types
 */
export type TreeNodeType = 'domain' | 'folder' | 'endpoint';

/**
 * Tree node structure for hierarchical asset display
 */
export interface TreeNode {
  /** Unique identifier for the node */
  id: string;
  /** Display name (domain, path segment, or method) */
  name: string;
  /** Full path from root */
  path: string;
  /** Node type */
  type: TreeNodeType;
  /** HTTP method (only for endpoint nodes) */
  method?: string;
  /** Associated asset (only for endpoint nodes) */
  asset?: Asset;
  /** Child nodes */
  children: TreeNode[];
  /** Depth level in tree (0 = root) */
  depth: number;
  /** Whether node is expanded (for UI state) */
  isExpanded?: boolean;
}

/**
 * Flattened node for virtualization
 */
export interface FlatNode {
  /** Unique identifier */
  id: string;
  /** Display name */
  name: string;
  /** Full path */
  path: string;
  /** Node type */
  type: TreeNodeType;
  /** HTTP method (for endpoints) */
  method?: string;
  /** Associated asset (for endpoints) */
  asset?: Asset;
  /** Depth level for indentation */
  depth: number;
  /** Whether this node has children */
  hasChildren: boolean;
  /** Whether this node is expanded */
  isExpanded: boolean;
}

/**
 * Extract domain from URL
 */
function extractDomain(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.hostname;
  } catch {
    // Handle malformed URLs
    return 'unknown';
  }
}

/**
 * Parse path into segments
 */
function parsePathSegments(path: string): string[] {
  if (!path || path === '/') {
    return [];
  }
  // Remove leading/trailing slashes and split
  return path
    .replace(/^\/+|\/+$/g, '')
    .split('/')
    .filter((segment) => segment.length > 0);
}

/**
 * Generate unique ID for a node
 */
function generateNodeId(type: TreeNodeType, ...parts: string[]): string {
  const key = parts.join('-');
  return `${type}-${key}`;
}

/**
 * Find or create a child node by name
 */
function findOrCreateChild(
  parent: TreeNode,
  name: string,
  type: TreeNodeType,
  path: string,
  depth: number
): TreeNode {
  let child = parent.children.find((c) => c.name === name && c.type === type);

  if (!child) {
    child = {
      id: generateNodeId(type, parent.id, name),
      name,
      path,
      type,
      children: [],
      depth,
      isExpanded: false,
    };
    parent.children.push(child);
  }

  return child;
}

/**
 * Build hierarchical tree from flat asset array
 *
 * Structure:
 * - Domain (root)
 *   - Folder (path segment)
 *     - Folder (nested path segment)
 *       - Endpoint (HTTP method with asset)
 *
 * @param assets - Flat array of assets
 * @returns Array of root tree nodes (domains)
 */
export function buildAssetTree(assets: Asset[]): TreeNode[] {
  if (assets.length === 0) {
    return [];
  }

  // Group assets by domain
  const domainMap = new Map<string, TreeNode>();

  for (const asset of assets) {
    const domain = extractDomain(asset.url);

    // Get or create domain node
    let domainNode = domainMap.get(domain);
    if (!domainNode) {
      domainNode = {
        id: generateNodeId('domain', domain),
        name: domain,
        path: domain,
        type: 'domain',
        children: [],
        depth: 0,
        isExpanded: false,
      };
      domainMap.set(domain, domainNode);
    }

    // Parse path segments
    const segments = parsePathSegments(asset.path);

    // Navigate/create folder structure
    let currentNode = domainNode;
    let currentPath = '';

    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      currentPath += '/' + segment;
      const depth = i + 1;

      // For all segments except the last, create folder nodes
      // The last segment's folder will contain endpoint nodes
      currentNode = findOrCreateChild(
        currentNode,
        segment,
        'folder',
        currentPath,
        depth
      );
    }

    // Create endpoint node with method
    const endpointId = generateNodeId('endpoint', asset.id.toString(), asset.method);
    const existingEndpoint = currentNode.children.find(
      (c) => c.type === 'endpoint' && c.method === asset.method && c.asset?.id === asset.id
    );

    if (!existingEndpoint) {
      const endpointNode: TreeNode = {
        id: endpointId,
        name: asset.method,
        path: asset.path || '/',
        type: 'endpoint',
        method: asset.method,
        asset,
        children: [],
        depth: currentNode.depth + 1,
        isExpanded: false,
      };
      currentNode.children.push(endpointNode);
    }
  }

  // Sort children alphabetically, with endpoints last
  const sortChildren = (node: TreeNode): void => {
    node.children.sort((a, b) => {
      // Endpoints come after folders
      if (a.type === 'endpoint' && b.type !== 'endpoint') return 1;
      if (a.type !== 'endpoint' && b.type === 'endpoint') return -1;
      // Alphabetical sort
      return a.name.localeCompare(b.name);
    });
    node.children.forEach(sortChildren);
  };

  const result = Array.from(domainMap.values());
  result.forEach(sortChildren);

  // Sort domains alphabetically
  result.sort((a, b) => a.name.localeCompare(b.name));

  return result;
}

/**
 * Flatten tree for virtualization
 * Only includes visible nodes (expanded parents' children)
 *
 * @param tree - Tree nodes
 * @returns Flattened array for virtualized list
 */
export function flattenTreeForVirtualization(tree: TreeNode[]): FlatNode[] {
  const result: FlatNode[] = [];

  const traverse = (nodes: TreeNode[]): void => {
    for (const node of nodes) {
      result.push({
        id: node.id,
        name: node.name,
        path: node.path,
        type: node.type,
        method: node.method,
        asset: node.asset,
        depth: node.depth,
        hasChildren: node.children.length > 0,
        isExpanded: node.isExpanded ?? false,
      });

      // Only include children if node is expanded
      if (node.isExpanded && node.children.length > 0) {
        traverse(node.children);
      }
    }
  };

  traverse(tree);
  return result;
}

/**
 * Update expanded state for a node in the tree
 *
 * @param tree - Tree nodes
 * @param nodeId - ID of node to toggle
 * @param expanded - New expanded state
 * @returns New tree with updated state
 */
export function updateNodeExpanded(
  tree: TreeNode[],
  nodeId: string,
  expanded: boolean
): TreeNode[] {
  return tree.map((node) => {
    if (node.id === nodeId) {
      return { ...node, isExpanded: expanded };
    }
    if (node.children.length > 0) {
      return {
        ...node,
        children: updateNodeExpanded(node.children, nodeId, expanded),
      };
    }
    return node;
  });
}

/**
 * Find a node by ID in the tree
 *
 * @param tree - Tree nodes
 * @param nodeId - ID to find
 * @returns Found node or undefined
 */
export function findNodeById(tree: TreeNode[], nodeId: string): TreeNode | undefined {
  for (const node of tree) {
    if (node.id === nodeId) {
      return node;
    }
    const found = findNodeById(node.children, nodeId);
    if (found) {
      return found;
    }
  }
  return undefined;
}
