/**
 * AssetExplorerContext Tests
 * TDD - Tests written before implementation
 */

import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import type { ReactNode } from 'react';
import {
  AssetExplorerProvider,
  useAssetExplorer,
} from './AssetExplorerContext';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('AssetExplorerContext', () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  describe('Provider Error Handling', () => {
    it('should throw error when useAssetExplorer is used outside Provider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useAssetExplorer());
      }).toThrow('useAssetExplorer must be used within AssetExplorerProvider');

      consoleSpy.mockRestore();
    });
  });

  describe('selectedAsset State', () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <AssetExplorerProvider>{children}</AssetExplorerProvider>
    );

    it('should have null selectedAssetId initially', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      expect(result.current.selectedAssetId).toBeNull();
    });

    it('should update selectedAssetId when setSelectedAssetId is called', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      act(() => {
        result.current.setSelectedAssetId(123);
      });

      expect(result.current.selectedAssetId).toBe(123);
    });

    it('should allow setting selectedAssetId to null', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      act(() => {
        result.current.setSelectedAssetId(123);
      });
      expect(result.current.selectedAssetId).toBe(123);

      act(() => {
        result.current.setSelectedAssetId(null);
      });
      expect(result.current.selectedAssetId).toBeNull();
    });
  });

  describe('expandedNodes State', () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <AssetExplorerProvider>{children}</AssetExplorerProvider>
    );

    it('should have empty expandedNodes initially', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      expect(result.current.expandedNodes.size).toBe(0);
    });

    it('should add node to expandedNodes when toggleNode is called with collapsed node', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      act(() => {
        result.current.toggleNode('node-1');
      });

      expect(result.current.expandedNodes.has('node-1')).toBe(true);
    });

    it('should remove node from expandedNodes when toggleNode is called with expanded node', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      act(() => {
        result.current.toggleNode('node-1');
      });
      expect(result.current.expandedNodes.has('node-1')).toBe(true);

      act(() => {
        result.current.toggleNode('node-1');
      });
      expect(result.current.expandedNodes.has('node-1')).toBe(false);
    });

    it('should expand node when expandNode is called', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      act(() => {
        result.current.expandNode('node-1');
      });

      expect(result.current.expandedNodes.has('node-1')).toBe(true);
    });

    it('should collapse node when collapseNode is called', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      act(() => {
        result.current.expandNode('node-1');
      });
      expect(result.current.expandedNodes.has('node-1')).toBe(true);

      act(() => {
        result.current.collapseNode('node-1');
      });
      expect(result.current.expandedNodes.has('node-1')).toBe(false);
    });

    it('should expand all nodes when expandAll is called', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });
      const nodeIds = ['node-1', 'node-2', 'node-3'];

      act(() => {
        result.current.expandAll(nodeIds);
      });

      expect(result.current.expandedNodes.size).toBe(3);
      nodeIds.forEach((id) => {
        expect(result.current.expandedNodes.has(id)).toBe(true);
      });
    });

    it('should collapse all nodes when collapseAll is called', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      act(() => {
        result.current.toggleNode('node-1');
        result.current.toggleNode('node-2');
      });
      expect(result.current.expandedNodes.size).toBe(2);

      act(() => {
        result.current.collapseAll();
      });

      expect(result.current.expandedNodes.size).toBe(0);
    });
  });

  describe('localStorage Persistence', () => {
    const STORAGE_KEY = 'asset-explorer-expanded-nodes';

    it('should save expandedNodes to localStorage when nodes are toggled', () => {
      const wrapper = ({ children }: { children: ReactNode }) => (
        <AssetExplorerProvider>{children}</AssetExplorerProvider>
      );
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      act(() => {
        result.current.toggleNode('node-1');
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        STORAGE_KEY,
        JSON.stringify(['node-1'])
      );
    });

    it('should restore expandedNodes from localStorage on mount', () => {
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify(['node-1', 'node-2']));

      const wrapper = ({ children }: { children: ReactNode }) => (
        <AssetExplorerProvider>{children}</AssetExplorerProvider>
      );
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      expect(result.current.expandedNodes.has('node-1')).toBe(true);
      expect(result.current.expandedNodes.has('node-2')).toBe(true);
    });

    it('should handle corrupted localStorage data gracefully', () => {
      localStorageMock.getItem.mockReturnValueOnce('invalid-json');

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const wrapper = ({ children }: { children: ReactNode }) => (
        <AssetExplorerProvider>{children}</AssetExplorerProvider>
      );
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      expect(result.current.expandedNodes.size).toBe(0);
      consoleSpy.mockRestore();
    });

    it('should update localStorage when collapseAll is called', () => {
      const wrapper = ({ children }: { children: ReactNode }) => (
        <AssetExplorerProvider>{children}</AssetExplorerProvider>
      );
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      act(() => {
        result.current.toggleNode('node-1');
        result.current.toggleNode('node-2');
      });

      act(() => {
        result.current.collapseAll();
      });

      expect(localStorageMock.setItem).toHaveBeenLastCalledWith(
        STORAGE_KEY,
        JSON.stringify([])
      );
    });
  });

  describe('isNodeExpanded Helper', () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <AssetExplorerProvider>{children}</AssetExplorerProvider>
    );

    it('should return true for expanded node', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      act(() => {
        result.current.expandNode('node-1');
      });

      expect(result.current.isNodeExpanded('node-1')).toBe(true);
    });

    it('should return false for collapsed node', () => {
      const { result } = renderHook(() => useAssetExplorer(), { wrapper });

      expect(result.current.isNodeExpanded('node-1')).toBe(false);
    });
  });
});
