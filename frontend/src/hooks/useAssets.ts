import { useQuery } from '@tanstack/react-query';
import { getTargetAssets } from '@/services/assetService';

/**
 * Query key factory for assets
 * Provides consistent query keys for caching and invalidation
 */
export const assetKeys = {
  all: ['assets'] as const,
  lists: () => [...assetKeys.all, 'list'] as const,
  list: (projectId: number, targetId: number) =>
    [...assetKeys.lists(), projectId, targetId] as const,
};

/**
 * Hook to fetch assets for a specific target
 *
 * @param projectId - Project ID
 * @param targetId - Target ID
 * @param options - Optional configuration
 * @param options.enabled - Whether to automatically fetch data (default: true)
 */
export const useTargetAssets = (
  projectId: number,
  targetId: number,
  options?: { enabled?: boolean }
) => {
  return useQuery({
    queryKey: assetKeys.list(projectId, targetId),
    queryFn: () => getTargetAssets(projectId, targetId),
    enabled: options?.enabled ?? true, // Default to true
  });
};
