import * as api from '@/lib/api';
import type { Asset } from '@/types/asset';

/**
 * Fetch list of assets discovered for a specific target
 *
 * Assets are attack surface items (URLs, Forms, XHR endpoints) discovered during scans.
 * Results are sorted by last_seen_at in descending order (newest first) by the backend.
 *
 * @param projectId - Project ID that owns the target
 * @param targetId - Target ID to fetch assets for
 * @returns Promise resolving to array of Asset objects
 * @throws Error if the API request fails
 *
 * @example
 * ```typescript
 * const assets = await getTargetAssets(1, 10);
 * console.log(`Found ${assets.length} assets`);
 * ```
 */
export const getTargetAssets = async (projectId: number, targetId: number): Promise<Asset[]> => {
  return api.get<Asset[]>(`/projects/${projectId}/targets/${targetId}/assets`);
};
