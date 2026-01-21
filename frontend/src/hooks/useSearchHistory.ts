import { useState, useCallback, useEffect } from 'react';

const STORAGE_KEY = 'target-search-history';
const MAX_HISTORY = 5;

/**
 * Hook to manage search history in localStorage
 * Stores recent search queries per project
 */
export function useSearchHistory(projectId: number) {
  const storageKey = `${STORAGE_KEY}-${projectId}`;

  const [history, setHistory] = useState<string[]>(() => {
    if (typeof window === 'undefined') return [];
    try {
      const stored = localStorage.getItem(storageKey);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Sync with localStorage when projectId changes
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const stored = localStorage.getItem(storageKey);
      setHistory(stored ? JSON.parse(stored) : []);
    } catch {
      setHistory([]);
    }
  }, [storageKey]);

  const addToHistory = useCallback(
    (query: string) => {
      if (!query || query.length < 2) return;

      setHistory((prev) => {
        // Remove duplicates and add to front
        const updated = [query, ...prev.filter((q) => q !== query)].slice(
          0,
          MAX_HISTORY
        );

        // Persist to localStorage
        try {
          localStorage.setItem(storageKey, JSON.stringify(updated));
        } catch {
          // Ignore localStorage errors
        }

        return updated;
      });
    },
    [storageKey]
  );

  const clearHistory = useCallback(() => {
    setHistory([]);
    try {
      localStorage.removeItem(storageKey);
    } catch {
      // Ignore localStorage errors
    }
  }, [storageKey]);

  return { history, addToHistory, clearHistory };
}
