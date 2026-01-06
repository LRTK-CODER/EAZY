import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getTargetAssets } from './assetService';
import type { Asset } from '@/types/asset';
import { AssetType, AssetSource } from '@/types/asset';
import * as api from '@/lib/api';

// Mock @/lib/api module
vi.mock('@/lib/api');

// Mock Asset data
const mockAsset1: Asset = {
  id: 1,
  target_id: 10,
  content_hash: 'abc123hash',
  type: AssetType.URL,
  source: AssetSource.HTML,
  method: 'GET',
  url: 'https://example.com/page1',
  path: '/page1',
  request_spec: null,
  response_spec: null,
  parameters: null,
  last_task_id: 100,
  first_seen_at: '2026-01-05T10:00:00Z',
  last_seen_at: '2026-01-05T12:00:00Z'
};

const mockAsset2: Asset = {
  id: 2,
  target_id: 10,
  content_hash: 'def456hash',
  type: AssetType.FORM,
  source: AssetSource.DOM,
  method: 'POST',
  url: 'https://example.com/login',
  path: '/login',
  request_spec: {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'username=&password='
  },
  response_spec: {
    status: 200,
    headers: { 'Set-Cookie': 'session=...' }
  },
  parameters: {
    username: { type: 'text', location: 'body', value: '' },
    password: { type: 'password', location: 'body', value: '' }
  },
  last_task_id: 101,
  first_seen_at: '2026-01-05T10:30:00Z',
  last_seen_at: '2026-01-05T12:30:00Z'
};

const mockAsset3: Asset = {
  id: 3,
  target_id: 10,
  content_hash: 'ghi789hash',
  type: AssetType.XHR,
  source: AssetSource.JS,
  method: 'POST',
  url: 'https://example.com/api/data',
  path: '/api/data',
  request_spec: {
    headers: { 'Content-Type': 'application/json' },
    body: '{"key":"value"}'
  },
  response_spec: {
    status: 200,
    body: '{"result":"success"}'
  },
  parameters: {
    key: { type: 'string', location: 'json', value: 'value' }
  },
  last_task_id: 102,
  first_seen_at: '2026-01-05T11:00:00Z',
  last_seen_at: '2026-01-05T13:00:00Z'
};

describe('assetService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getTargetAssets', () => {
    // Test 1: Success with multiple assets
    it('should fetch target assets successfully', async () => {
      const mockResponse = [mockAsset1, mockAsset2, mockAsset3];
      vi.mocked(api.get).mockResolvedValueOnce(mockResponse);

      const result = await getTargetAssets(1, 10);

      expect(api.get).toHaveBeenCalledWith('/projects/1/targets/10/assets');
      expect(result).toEqual(mockResponse);
      expect(result).toHaveLength(3);
    });

    // Test 2: Empty array when no assets found
    it('should return empty array when no assets found', async () => {
      vi.mocked(api.get).mockResolvedValueOnce([]);

      const result = await getTargetAssets(1, 10);

      expect(api.get).toHaveBeenCalledWith('/projects/1/targets/10/assets');
      expect(result).toEqual([]);
      expect(result).toHaveLength(0);
    });

    // Test 3: Assets are sorted by last_seen_at DESC (backend responsibility)
    it('should return assets in descending order by last_seen_at', async () => {
      const mockResponse = [mockAsset3, mockAsset2, mockAsset1]; // Newest first
      vi.mocked(api.get).mockResolvedValueOnce(mockResponse);

      const result = await getTargetAssets(1, 10);

      expect(result[0].last_seen_at).toBe('2026-01-05T13:00:00Z');
      expect(result[1].last_seen_at).toBe('2026-01-05T12:30:00Z');
      expect(result[2].last_seen_at).toBe('2026-01-05T12:00:00Z');
    });

    // Test 4: Handle URL type assets
    it('should handle URL type assets correctly', async () => {
      const mockResponse = [mockAsset1];
      vi.mocked(api.get).mockResolvedValueOnce(mockResponse);

      const result = await getTargetAssets(1, 10);

      expect(result[0].type).toBe(AssetType.URL);
      expect(result[0].source).toBe(AssetSource.HTML);
      expect(result[0].method).toBe('GET');
      expect(result[0].request_spec).toBeNull();
      expect(result[0].response_spec).toBeNull();
    });

    // Test 5: Handle FORM type assets with JSONB fields
    it('should handle FORM type assets with request/response specs', async () => {
      const mockResponse = [mockAsset2];
      vi.mocked(api.get).mockResolvedValueOnce(mockResponse);

      const result = await getTargetAssets(1, 10);

      expect(result[0].type).toBe(AssetType.FORM);
      expect(result[0].source).toBe(AssetSource.DOM);
      expect(result[0].method).toBe('POST');
      expect(result[0].request_spec).toEqual({
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'username=&password='
      });
      expect(result[0].parameters).toHaveProperty('username');
      expect(result[0].parameters).toHaveProperty('password');
    });

    // Test 6: Handle XHR type assets
    it('should handle XHR type assets with JSON payloads', async () => {
      const mockResponse = [mockAsset3];
      vi.mocked(api.get).mockResolvedValueOnce(mockResponse);

      const result = await getTargetAssets(1, 10);

      expect(result[0].type).toBe(AssetType.XHR);
      expect(result[0].source).toBe(AssetSource.JS);
      expect(result[0].request_spec).toHaveProperty('body');
      expect(result[0].response_spec).toHaveProperty('body');
    });

    // Test 7: Handle 404 error (target not found)
    it('should throw error when target not found', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { detail: 'Target not found' }
        }
      };
      vi.mocked(api.get).mockRejectedValueOnce(mockError);

      await expect(getTargetAssets(1, 999)).rejects.toThrow();
    });

    // Test 8: Handle network error
    it('should throw error on network failure', async () => {
      const mockError = new Error('Network Error');
      vi.mocked(api.get).mockRejectedValueOnce(mockError);

      await expect(getTargetAssets(1, 10)).rejects.toThrow('Network Error');
    });

    // Test 9: Handle different projectId/targetId combinations
    it('should use correct projectId and targetId in API call', async () => {
      vi.mocked(api.get).mockResolvedValueOnce([]);

      await getTargetAssets(5, 20);

      expect(api.get).toHaveBeenCalledWith('/projects/5/targets/20/assets');
    });

    // Test 10: Validate content_hash uniqueness
    it('should return assets with unique content_hash values', async () => {
      const mockResponse = [mockAsset1, mockAsset2, mockAsset3];
      vi.mocked(api.get).mockResolvedValueOnce(mockResponse);

      const result = await getTargetAssets(1, 10);

      const hashes = result.map(a => a.content_hash);
      const uniqueHashes = new Set(hashes);
      expect(hashes.length).toBe(uniqueHashes.size); // All unique
    });
  });
});
