/**
 * useAssetFilter Hook
 * Custom hook for filtering assets by search query and HTTP method
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
  /** HTTP method filter */
  filterMethod: HttpMethod | null;
}

/**
 * Filter actions type
 */
export interface AssetFilterActions {
  /** Set search query */
  setSearchQuery: (query: string) => void;
  /** Set HTTP method filter */
  setFilterMethod: (method: HttpMethod | null) => void;
  /** Clear all filters */
  clearFilters: () => void;
  /** Check if any filter is active */
  hasActiveFilters: boolean;
}

/**
 * Filter assets based on search query and method filter
 */
export function filterAssets(
  assets: Asset[],
  searchQuery?: string,
  filterMethod?: HttpMethod | null
): Asset[] {
  if (!searchQuery && !filterMethod) {
    return assets;
  }

  return assets.filter((asset) => {
    // Apply method filter
    if (filterMethod && asset.method?.toUpperCase() !== filterMethod) {
      return false;
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
  const [filterMethod, setFilterMethod] = useState<HttpMethod | null>(null);

  // Compute filtered assets
  const filteredAssets = useMemo(
    () => filterAssets(assets, searchQuery, filterMethod),
    [assets, searchQuery, filterMethod]
  );

  // Clear all filters
  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setFilterMethod(null);
  }, []);

  // Check if any filter is active
  const hasActiveFilters = searchQuery !== '' || filterMethod !== null;

  return {
    // State
    searchQuery,
    filterMethod,
    // Actions
    setSearchQuery,
    setFilterMethod,
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
