/**
 * AssetExplorerContext
 * State management for Asset Explorer tree view
 */

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react';

const STORAGE_KEY = 'asset-explorer-expanded-nodes';

/**
 * Context value interface
 */
interface AssetExplorerContextValue {
  /** Currently selected asset ID */
  selectedAssetId: number | null;
  /** Set selected asset ID */
  setSelectedAssetId: (id: number | null) => void;
  /** Set of expanded node IDs */
  expandedNodes: Set<string>;
  /** Toggle node expanded state */
  toggleNode: (nodeId: string) => void;
  /** Expand a specific node */
  expandNode: (nodeId: string) => void;
  /** Collapse a specific node */
  collapseNode: (nodeId: string) => void;
  /** Expand all nodes */
  expandAll: (nodeIds: string[]) => void;
  /** Collapse all nodes */
  collapseAll: () => void;
  /** Check if node is expanded */
  isNodeExpanded: (nodeId: string) => boolean;
}

const AssetExplorerContext = createContext<AssetExplorerContextValue | null>(null);

/**
 * Load expanded nodes from localStorage
 */
function loadExpandedNodes(): Set<string> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        return new Set(parsed);
      }
    }
  } catch {
    console.warn('Failed to load expanded nodes from localStorage');
  }
  return new Set();
}

/**
 * Save expanded nodes to localStorage
 */
function saveExpandedNodes(nodes: Set<string>): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...nodes]));
  } catch {
    console.warn('Failed to save expanded nodes to localStorage');
  }
}

/**
 * Provider props
 */
interface AssetExplorerProviderProps {
  children: ReactNode;
}

/**
 * AssetExplorerProvider
 * Provides state management for the asset explorer tree view
 */
export function AssetExplorerProvider({ children }: AssetExplorerProviderProps) {
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(() => loadExpandedNodes());

  // Save to localStorage whenever expandedNodes changes
  useEffect(() => {
    saveExpandedNodes(expandedNodes);
  }, [expandedNodes]);

  const toggleNode = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  const expandNode = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      if (prev.has(nodeId)) return prev;
      const next = new Set(prev);
      next.add(nodeId);
      return next;
    });
  }, []);

  const collapseNode = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      if (!prev.has(nodeId)) return prev;
      const next = new Set(prev);
      next.delete(nodeId);
      return next;
    });
  }, []);

  const expandAll = useCallback((nodeIds: string[]) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      nodeIds.forEach((id) => next.add(id));
      return next;
    });
  }, []);

  const collapseAll = useCallback(() => {
    setExpandedNodes(new Set());
  }, []);

  const isNodeExpanded = useCallback(
    (nodeId: string) => expandedNodes.has(nodeId),
    [expandedNodes]
  );

  const value: AssetExplorerContextValue = {
    selectedAssetId,
    setSelectedAssetId,
    expandedNodes,
    toggleNode,
    expandNode,
    collapseNode,
    expandAll,
    collapseAll,
    isNodeExpanded,
  };

  return (
    <AssetExplorerContext.Provider value={value}>
      {children}
    </AssetExplorerContext.Provider>
  );
}

/**
 * useAssetExplorer hook
 * Access asset explorer context
 * @throws Error if used outside AssetExplorerProvider
 */
export function useAssetExplorer(): AssetExplorerContextValue {
  const context = useContext(AssetExplorerContext);
  if (!context) {
    throw new Error('useAssetExplorer must be used within AssetExplorerProvider');
  }
  return context;
}
