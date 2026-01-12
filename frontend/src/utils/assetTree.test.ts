/**
 * Asset Tree Utility Tests
 * TDD - Tests written before implementation
 */

import { describe, it, expect } from 'vitest';
import type { Asset, AssetType, AssetSource } from '@/types/asset';
import {
  buildAssetTree,
  flattenTreeForVirtualization,
  type TreeNode,
} from './assetTree';

// Mock Asset factory for testing
function createMockAsset(overrides: Partial<Asset> = {}): Asset {
  return {
    id: 1,
    target_id: 1,
    content_hash: 'abc123',
    type: 'url' as AssetType,
    source: 'html' as AssetSource,
    method: 'GET',
    url: 'https://example.com/api/users',
    path: '/api/users',
    request_spec: null,
    response_spec: null,
    parameters: null,
    last_task_id: null,
    first_seen_at: '2026-01-01T00:00:00Z',
    last_seen_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('buildAssetTree', () => {
  describe('Basic Conversion', () => {
    it('should return empty array for empty input', () => {
      const result = buildAssetTree([]);
      expect(result).toEqual([]);
    });

    it('should create single domain node for single asset', () => {
      const assets = [createMockAsset({ url: 'https://example.com/api' })];
      const result = buildAssetTree(assets);

      expect(result).toHaveLength(1);
      expect(result[0].type).toBe('domain');
      expect(result[0].name).toBe('example.com');
    });

    it('should group assets by domain', () => {
      const assets = [
        createMockAsset({ id: 1, url: 'https://example.com/api/users' }),
        createMockAsset({ id: 2, url: 'https://example.com/api/posts' }),
        createMockAsset({ id: 3, url: 'https://other.com/api' }),
      ];
      const result = buildAssetTree(assets);

      expect(result).toHaveLength(2);
      expect(result.map((n) => n.name).sort()).toEqual(['example.com', 'other.com']);
    });

    it('should create nested folder structure from path', () => {
      const assets = [
        createMockAsset({ url: 'https://example.com/api/v1/users', path: '/api/v1/users' }),
      ];
      const result = buildAssetTree(assets);

      // example.com > api > v1 > users
      expect(result[0].name).toBe('example.com');
      expect(result[0].children[0].name).toBe('api');
      expect(result[0].children[0].children[0].name).toBe('v1');
      expect(result[0].children[0].children[0].children[0].name).toBe('users');
    });

    it('should group same path with different methods', () => {
      const assets = [
        createMockAsset({ id: 1, url: 'https://example.com/api/users', method: 'GET' }),
        createMockAsset({ id: 2, url: 'https://example.com/api/users', method: 'POST' }),
        createMockAsset({ id: 3, url: 'https://example.com/api/users', method: 'DELETE' }),
      ];
      const result = buildAssetTree(assets);

      // Find the 'users' node
      const usersNode = result[0].children[0].children[0];
      expect(usersNode.name).toBe('users');
      expect(usersNode.children).toHaveLength(3);
      expect(usersNode.children.map((c) => c.method).sort()).toEqual(['DELETE', 'GET', 'POST']);
    });
  });

  describe('Deep Nesting', () => {
    it('should handle deeply nested paths (7+ levels)', () => {
      const assets = [
        createMockAsset({
          url: 'https://example.com/api/v1/users/123/profile/settings/privacy',
          path: '/api/v1/users/123/profile/settings/privacy',
        }),
      ];
      const result = buildAssetTree(assets);

      // Traverse the tree
      let node = result[0]; // example.com
      const expectedPath = ['api', 'v1', 'users', '123', 'profile', 'settings', 'privacy'];

      for (const segment of expectedPath) {
        expect(node.children.length).toBeGreaterThanOrEqual(1);
        node = node.children.find((c) => c.name === segment)!;
        expect(node).toBeDefined();
        expect(node.name).toBe(segment);
      }
    });

    it('should set correct depth for each node', () => {
      const assets = [
        createMockAsset({
          url: 'https://example.com/api/users',
          path: '/api/users',
        }),
      ];
      const result = buildAssetTree(assets);

      expect(result[0].depth).toBe(0); // domain
      expect(result[0].children[0].depth).toBe(1); // api
      expect(result[0].children[0].children[0].depth).toBe(2); // users
    });
  });

  describe('Special Characters', () => {
    it('should handle query parameters in URL', () => {
      const assets = [
        createMockAsset({
          url: 'https://example.com/search?query=test&page=1',
          path: '/search',
        }),
      ];
      const result = buildAssetTree(assets);

      // Path should be /search (without query string)
      expect(result[0].children[0].name).toBe('search');
    });

    it('should handle hash fragments in URL', () => {
      const assets = [
        createMockAsset({
          url: 'https://example.com/docs#section-1',
          path: '/docs',
        }),
      ];
      const result = buildAssetTree(assets);

      expect(result[0].children[0].name).toBe('docs');
    });

    it('should handle URL-encoded characters', () => {
      const assets = [
        createMockAsset({
          url: 'https://example.com/api/users%2F123',
          path: '/api/users%2F123',
        }),
      ];
      const result = buildAssetTree(assets);

      // Should decode or preserve the encoded character
      expect(result[0].children[0].name).toBe('api');
    });

    it('should handle root path "/"', () => {
      const assets = [
        createMockAsset({
          url: 'https://example.com/',
          path: '/',
        }),
      ];
      const result = buildAssetTree(assets);

      expect(result[0].name).toBe('example.com');
      // Root should have endpoint directly or as special node
      expect(result[0].children.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Node Properties', () => {
    it('should set correct node type for domains', () => {
      const assets = [createMockAsset()];
      const result = buildAssetTree(assets);

      expect(result[0].type).toBe('domain');
    });

    it('should set correct node type for folders', () => {
      const assets = [
        createMockAsset({
          url: 'https://example.com/api/users',
          path: '/api/users',
        }),
      ];
      const result = buildAssetTree(assets);

      expect(result[0].children[0].type).toBe('folder'); // api
    });

    it('should set correct node type for endpoints', () => {
      const assets = [
        createMockAsset({
          url: 'https://example.com/api/users',
          path: '/api/users',
          method: 'GET',
        }),
      ];
      const result = buildAssetTree(assets);

      // Find the endpoint node (leaf with method)
      const usersNode = result[0].children[0].children[0];
      const endpointNode = usersNode.children[0];
      expect(endpointNode.type).toBe('endpoint');
      expect(endpointNode.method).toBe('GET');
      expect(endpointNode.asset).toBeDefined();
    });

    it('should include asset reference in endpoint nodes', () => {
      const asset = createMockAsset({ id: 42 });
      const result = buildAssetTree([asset]);

      // Find the endpoint node
      const findEndpoint = (node: TreeNode): TreeNode | undefined => {
        if (node.type === 'endpoint') return node;
        for (const child of node.children) {
          const found = findEndpoint(child);
          if (found) return found;
        }
        return undefined;
      };

      const endpoint = findEndpoint(result[0]);
      expect(endpoint?.asset?.id).toBe(42);
    });

    it('should generate unique IDs for each node', () => {
      const assets = [
        createMockAsset({ id: 1, url: 'https://example.com/api/users', method: 'GET' }),
        createMockAsset({ id: 2, url: 'https://example.com/api/users', method: 'POST' }),
      ];
      const result = buildAssetTree(assets);

      const collectIds = (node: TreeNode): string[] => {
        const ids = [node.id];
        for (const child of node.children) {
          ids.push(...collectIds(child));
        }
        return ids;
      };

      const allIds = result.flatMap(collectIds);
      const uniqueIds = new Set(allIds);
      expect(uniqueIds.size).toBe(allIds.length);
    });
  });

  describe('Edge Cases', () => {
    it('should handle assets with same URL but different parameters', () => {
      const assets = [
        createMockAsset({
          id: 1,
          url: 'https://example.com/api/users?role=admin',
          path: '/api/users',
          parameters: { role: 'admin' },
        }),
        createMockAsset({
          id: 2,
          url: 'https://example.com/api/users?role=user',
          path: '/api/users',
          parameters: { role: 'user' },
        }),
      ];
      const result = buildAssetTree(assets);

      // Should have 2 endpoint nodes under users
      const usersNode = result[0].children[0].children[0];
      expect(usersNode.children.length).toBe(2);
    });

    it('should handle malformed URLs gracefully', () => {
      const assets = [
        createMockAsset({
          url: 'not-a-valid-url',
          path: '/unknown',
        }),
      ];

      // Should not throw
      expect(() => buildAssetTree(assets)).not.toThrow();
    });

    it('should handle empty path', () => {
      const assets = [
        createMockAsset({
          url: 'https://example.com',
          path: '',
        }),
      ];
      const result = buildAssetTree(assets);

      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('example.com');
    });

    it('should handle very long paths', () => {
      const longPath = '/' + Array(50).fill('segment').join('/');
      const assets = [
        createMockAsset({
          url: `https://example.com${longPath}`,
          path: longPath,
        }),
      ];

      expect(() => buildAssetTree(assets)).not.toThrow();
    });
  });
});

describe('flattenTreeForVirtualization', () => {
  it('should return empty array for empty tree', () => {
    const result = flattenTreeForVirtualization([]);
    expect(result).toEqual([]);
  });

  it('should include only root nodes when none expanded', () => {
    const tree: TreeNode[] = [
      {
        id: 'domain-1',
        name: 'example.com',
        path: 'example.com',
        type: 'domain',
        depth: 0,
        isExpanded: false,
        children: [
          {
            id: 'folder-1',
            name: 'api',
            path: '/api',
            type: 'folder',
            depth: 1,
            isExpanded: false,
            children: [],
          },
        ],
      },
    ];

    const result = flattenTreeForVirtualization(tree);
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('domain-1');
  });

  it('should include children when parent is expanded', () => {
    const tree: TreeNode[] = [
      {
        id: 'domain-1',
        name: 'example.com',
        path: 'example.com',
        type: 'domain',
        depth: 0,
        isExpanded: true,
        children: [
          {
            id: 'folder-1',
            name: 'api',
            path: '/api',
            type: 'folder',
            depth: 1,
            isExpanded: false,
            children: [],
          },
        ],
      },
    ];

    const result = flattenTreeForVirtualization(tree);
    expect(result).toHaveLength(2);
    expect(result[0].id).toBe('domain-1');
    expect(result[1].id).toBe('folder-1');
  });

  it('should recursively include nested expanded nodes', () => {
    const tree: TreeNode[] = [
      {
        id: 'domain-1',
        name: 'example.com',
        path: 'example.com',
        type: 'domain',
        depth: 0,
        isExpanded: true,
        children: [
          {
            id: 'folder-1',
            name: 'api',
            path: '/api',
            type: 'folder',
            depth: 1,
            isExpanded: true,
            children: [
              {
                id: 'folder-2',
                name: 'users',
                path: '/api/users',
                type: 'folder',
                depth: 2,
                isExpanded: false,
                children: [],
              },
            ],
          },
        ],
      },
    ];

    const result = flattenTreeForVirtualization(tree);
    expect(result).toHaveLength(3);
    expect(result.map((n) => n.id)).toEqual(['domain-1', 'folder-1', 'folder-2']);
  });

  it('should preserve depth information in flattened nodes', () => {
    const tree: TreeNode[] = [
      {
        id: 'domain-1',
        name: 'example.com',
        path: 'example.com',
        type: 'domain',
        depth: 0,
        isExpanded: true,
        children: [
          {
            id: 'folder-1',
            name: 'api',
            path: '/api',
            type: 'folder',
            depth: 1,
            isExpanded: true,
            children: [
              {
                id: 'folder-2',
                name: 'users',
                path: '/api/users',
                type: 'folder',
                depth: 2,
                isExpanded: false,
                children: [],
              },
            ],
          },
        ],
      },
    ];

    const result = flattenTreeForVirtualization(tree);
    expect(result[0].depth).toBe(0);
    expect(result[1].depth).toBe(1);
    expect(result[2].depth).toBe(2);
  });

  it('should include hasChildren flag for virtualization', () => {
    const tree: TreeNode[] = [
      {
        id: 'domain-1',
        name: 'example.com',
        path: 'example.com',
        type: 'domain',
        depth: 0,
        isExpanded: false,
        children: [
          {
            id: 'folder-1',
            name: 'api',
            path: '/api',
            type: 'folder',
            depth: 1,
            isExpanded: false,
            children: [],
          },
        ],
      },
    ];

    const result = flattenTreeForVirtualization(tree);
    expect(result[0].hasChildren).toBe(true);
  });

  it('should handle multiple root nodes', () => {
    const tree: TreeNode[] = [
      {
        id: 'domain-1',
        name: 'example.com',
        path: 'example.com',
        type: 'domain',
        depth: 0,
        isExpanded: false,
        children: [],
      },
      {
        id: 'domain-2',
        name: 'other.com',
        path: 'other.com',
        type: 'domain',
        depth: 0,
        isExpanded: false,
        children: [],
      },
    ];

    const result = flattenTreeForVirtualization(tree);
    expect(result).toHaveLength(2);
    expect(result.map((n) => n.name)).toEqual(['example.com', 'other.com']);
  });
});

describe('Performance', () => {
  // Helper to generate large asset sets
  function generateAssets(count: number): Asset[] {
    const domains = ['api.example.com', 'cdn.example.com', 'auth.example.com', 'data.example.com'];
    const paths = ['users', 'posts', 'comments', 'auth', 'settings', 'profile', 'admin', 'dashboard'];
    const methods = ['GET', 'POST', 'PUT', 'DELETE'] as const;
    const types = ['url', 'form', 'xhr'] as const;
    const sources = ['html', 'js', 'network', 'dom'] as const;

    return Array.from({ length: count }, (_, i) => ({
      id: i + 1,
      target_id: 1,
      content_hash: `hash-${i}`,
      type: types[i % types.length] as AssetType,
      source: sources[i % sources.length] as AssetSource,
      method: methods[i % methods.length],
      url: `https://${domains[i % domains.length]}/${paths[i % paths.length]}/v${Math.floor(i / 100)}/item/${i}`,
      path: `/${paths[i % paths.length]}/v${Math.floor(i / 100)}/item/${i}`,
      request_spec: null,
      response_spec: null,
      parameters: null,
      last_task_id: null,
      first_seen_at: '2026-01-01T00:00:00Z',
      last_seen_at: '2026-01-01T00:00:00Z',
    }));
  }

  it('should build tree from 1000 assets in under 50ms', () => {
    const assets = generateAssets(1000);

    const start = performance.now();
    const result = buildAssetTree(assets);
    const duration = performance.now() - start;

    expect(result.length).toBeGreaterThan(0);
    expect(duration).toBeLessThan(50);
  });

  it('should flatten 1000-node tree in under 20ms', () => {
    const assets = generateAssets(1000);
    const tree = buildAssetTree(assets);

    // Expand all nodes for worst-case flattening
    const expandAll = (nodes: TreeNode[]): TreeNode[] =>
      nodes.map((node) => ({
        ...node,
        isExpanded: true,
        children: expandAll(node.children),
      }));

    const expandedTree = expandAll(tree);

    const start = performance.now();
    const result = flattenTreeForVirtualization(expandedTree);
    const duration = performance.now() - start;

    expect(result.length).toBeGreaterThan(0);
    expect(duration).toBeLessThan(20);
  });

  it('should handle 5000 assets without performance degradation', () => {
    const assets = generateAssets(5000);

    const start = performance.now();
    const result = buildAssetTree(assets);
    const duration = performance.now() - start;

    expect(result.length).toBeGreaterThan(0);
    // 5x assets should take roughly 5x time, with some overhead allowance
    expect(duration).toBeLessThan(250);
  });
});
