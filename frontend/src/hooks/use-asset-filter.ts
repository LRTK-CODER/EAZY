/**
 * useAssetFilter Hook
 * Custom hook for filtering assets by search query and HTTP methods (multiple selection)
 */

import { useMemo, useState, useCallback } from 'react';
import type { Asset } from '@/types/asset';

/**
 * HTTP methods for filtering
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';

/**
 * Filter state type
 */
export interface AssetFilterState {
  /** Search query string */
  searchQuery: string;
  /** HTTP method filters (multiple selection) */
  filterMethods: HttpMethod[];
}

/**
 * Filter actions type
 */
export interface AssetFilterActions {
  /** Set search query */
  setSearchQuery: (query: string) => void;
  /** Toggle HTTP method filter (add/remove from selection) */
  toggleFilterMethod: (method: HttpMethod) => void;
  /** Set HTTP method filters directly */
  setFilterMethods: (methods: HttpMethod[]) => void;
  /** Clear all filters */
  clearFilters: () => void;
  /** Check if any filter is active */
  hasActiveFilters: boolean;
}

/**
 * Filter assets based on search query and method filters
 * @param assets - Array of assets to filter
 * @param searchQuery - Search query string
 * @param filterMethods - Array of HTTP methods to filter by (empty = show all)
 */
export function filterAssets(
  assets: Asset[],
  searchQuery?: string,
  filterMethods?: HttpMethod[]
): Asset[] {
  const hasMethodFilter = filterMethods && filterMethods.length > 0;

  if (!searchQuery && !hasMethodFilter) {
    return assets;
  }

  return assets.filter((asset) => {
    // Apply method filter - asset must match one of the selected methods
    if (hasMethodFilter) {
      const assetMethod = asset.method?.toUpperCase() as HttpMethod;
      if (!filterMethods.includes(assetMethod)) {
        return false;
      }
    }

    // Apply search query filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchesPath = asset.path?.toLowerCase().includes(query);
      const matchesUrl = asset.url?.toLowerCase().includes(query);
      const matchesMethod = asset.method?.toLowerCase().includes(query);

      if (!matchesPath && !matchesUrl && !matchesMethod) {
        return false;
      }
    }

    return true;
  });
}

/**
 * useAssetFilter
 * Hook for managing asset filter state and computed filtered assets
 *
 * @param assets - Array of assets to filter
 * @returns Filter state, actions, and filtered assets
 */
export function useAssetFilter(assets: Asset[]) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterMethods, setFilterMethods] = useState<HttpMethod[]>([]);

  // Toggle method in filter array
  const toggleFilterMethod = useCallback((method: HttpMethod) => {
    setFilterMethods((prev) => {
      if (prev.includes(method)) {
        // Remove if already selected
        return prev.filter((m) => m !== method);
      } else {
        // Add if not selected
        return [...prev, method];
      }
    });
  }, []);

  // Compute filtered assets
  const filteredAssets = useMemo(
    () => filterAssets(assets, searchQuery, filterMethods),
    [assets, searchQuery, filterMethods]
  );

  // Clear all filters
  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setFilterMethods([]);
  }, []);

  // Check if any filter is active
  const hasActiveFilters = searchQuery !== '' || filterMethods.length > 0;

  return {
    // State
    searchQuery,
    filterMethods,
    // Actions
    setSearchQuery,
    toggleFilterMethod,
    setFilterMethods,
    clearFilters,
    hasActiveFilters,
    // Computed
    filteredAssets,
    // Stats
    totalCount: assets.length,
    filteredCount: filteredAssets.length,
  };
}

export default useAssetFilter;
