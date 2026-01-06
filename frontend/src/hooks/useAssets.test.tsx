import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { assetKeys, useTargetAssets } from './useAssets';
import type { Asset } from '@/types/asset';
import { AssetType, AssetSource } from '@/types/asset';
import React from 'react';

// Mock assetService
vi.mock('@/services/assetService', () => ({
  getTargetAssets: vi.fn()
}));

import { getTargetAssets } from '@/services/assetService';

// Test wrapper component
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

// Mock Asset data
const mockAsset: Asset = {
  id: 1,
  target_id: 10,
  content_hash: 'abc123',
  type: AssetType.URL,
  source: AssetSource.HTML,
  method: 'GET',
  url: 'https://example.com',
  path: '/',
  request_spec: null,
  response_spec: null,
  parameters: null,
  last_task_id: 100,
  first_seen_at: '2026-01-05T10:00:00Z',
  last_seen_at: '2026-01-05T12:00:00Z'
};

describe('useAssets', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('assetKeys', () => {
    // Test 1: Query key factory structure
    it('should generate correct query keys', () => {
      expect(assetKeys.all).toEqual(['assets']);
      expect(assetKeys.lists()).toEqual(['assets', 'list']);
      expect(assetKeys.list(1, 10)).toEqual(['assets', 'list', 1, 10]);
    });

    // Test 2: Unique keys for different targets
    it('should generate unique keys for different projectId and targetId', () => {
      const key1 = assetKeys.list(1, 10);
      const key2 = assetKeys.list(1, 20);
      const key3 = assetKeys.list(2, 10);

      expect(key1).not.toEqual(key2);
      expect(key1).not.toEqual(key3);
      expect(key2).not.toEqual(key3);
    });
  });

  describe('useTargetAssets', () => {
    // Test 3: Fetch assets successfully
    it('should fetch target assets successfully', async () => {
      const mockAssets = [mockAsset];
      vi.mocked(getTargetAssets).mockResolvedValueOnce(mockAssets);

      const { result } = renderHook(
        () => useTargetAssets(1, 10),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockAssets);
      expect(getTargetAssets).toHaveBeenCalledWith(1, 10);
    });

    // Test 4: Handle loading state
    it('should show loading state initially', () => {
      vi.mocked(getTargetAssets).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(
        () => useTargetAssets(1, 10),
        { wrapper: createWrapper() }
      );

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
    });

    // Test 5: Handle error state
    it('should handle error state', async () => {
      const mockError = new Error('Failed to fetch assets');
      vi.mocked(getTargetAssets).mockRejectedValueOnce(mockError);

      const { result } = renderHook(
        () => useTargetAssets(1, 10),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeTruthy();
    });

    // Test 6: Return empty array when no assets
    it('should return empty array when no assets found', async () => {
      vi.mocked(getTargetAssets).mockResolvedValueOnce([]);

      const { result } = renderHook(
        () => useTargetAssets(1, 10),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual([]);
    });

    // Test 7: Should be enabled by default
    it('should fetch data automatically when enabled', async () => {
      vi.mocked(getTargetAssets).mockResolvedValueOnce([mockAsset]);

      renderHook(
        () => useTargetAssets(1, 10),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(getTargetAssets).toHaveBeenCalled();
      });
    });

    // Test 8: Should respect enabled option
    it('should not fetch when enabled is false', async () => {
      const { result } = renderHook(
        () => useTargetAssets(1, 10, { enabled: false }),
        { wrapper: createWrapper() }
      );

      expect(result.current.isLoading).toBe(false);
      expect(getTargetAssets).not.toHaveBeenCalled();
    });
  });
});
