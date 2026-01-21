import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TargetSearchBar } from './TargetSearchBar';
import * as targetService from '@/services/targetService';
import type { Target, TargetSearchResponse } from '@/types/target';

// Mock the targetService
vi.mock('@/services/targetService');

// Helper to render with providers
const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return {
    user: userEvent.setup(),
    ...render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    ),
  };
};

// Helper to create mock target
const createMockTarget = (overrides: Partial<Target> = {}): Target => ({
  id: 1,
  project_id: 1,
  name: 'Main API Server',
  url: 'https://api.example.com',
  description: null,
  scope: 'DOMAIN',
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-15T10:00:00Z',
  asset_count: 5,
  ...overrides,
});

// Helper to create mock search response
const createMockSearchResponse = (
  targets: Target[],
  total?: number
): TargetSearchResponse => ({
  items: targets,
  total: total ?? targets.length,
});

describe('TargetSearchBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1. Rendering
  describe('Rendering', () => {
    it('should render search input with placeholder', async () => {
      vi.mocked(targetService.searchTargets).mockResolvedValue(
        createMockSearchResponse([])
      );

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Click the trigger button to open the popover
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      await waitFor(() => {
        const input = screen.getByPlaceholderText(/search by name or url/i);
        expect(input).toBeInTheDocument();
      });
    });

    it('should render trigger button', () => {
      renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      const triggerButton = screen.getByRole('button', { name: /search/i });
      expect(triggerButton).toBeInTheDocument();
    });
  });

  // 2. Debounce Behavior
  describe('Debounce Behavior', () => {
    it('should debounce search input by 300ms', async () => {
      const mockSearchTargets = vi
        .mocked(targetService.searchTargets)
        .mockResolvedValue(createMockSearchResponse([]));

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Open popover
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      // Type search query
      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'api');

      // Should not be called immediately (debounce is 300ms)
      expect(mockSearchTargets).not.toHaveBeenCalled();

      // After debounce delay, should be called
      await waitFor(
        () => {
          expect(mockSearchTargets).toHaveBeenCalledTimes(1);
          expect(mockSearchTargets).toHaveBeenCalledWith(1, { q: 'api' });
        },
        { timeout: 500 }
      );
    });

    it('should not call API immediately on typing', async () => {
      const mockSearchTargets = vi
        .mocked(targetService.searchTargets)
        .mockResolvedValue(createMockSearchResponse([]));

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Open popover
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      // Type search query
      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'api');

      // Should not be called immediately
      expect(mockSearchTargets).not.toHaveBeenCalled();
    });
  });

  // 3. Search Results
  describe('Search Results', () => {
    it('should display search results in dropdown', async () => {
      const mockTargets = [
        createMockTarget({ id: 1, name: 'Main API', url: 'https://api.example.com' }),
        createMockTarget({ id: 2, name: 'REST API', url: 'https://rest.example.com' }),
      ];
      vi.mocked(targetService.searchTargets).mockResolvedValue(
        createMockSearchResponse(mockTargets)
      );

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Open popover and search
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'api');

      // Wait for results to appear (text may be split by highlight marks)
      await waitFor(() => {
        // Check for options in the list
        const options = screen.getAllByRole('option');
        expect(options).toHaveLength(2);
      });
    });

    it('should show target name, URL, and asset_count', async () => {
      const mockTarget = createMockTarget({
        id: 1,
        name: 'Test Server',
        url: 'https://test.example.com',
        asset_count: 42,
      });
      vi.mocked(targetService.searchTargets).mockResolvedValue(
        createMockSearchResponse([mockTarget])
      );

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Open popover and search
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'test');

      // Wait for results (text is split by highlight marks, so use textContent matching)
      await waitFor(() => {
        const option = screen.getByRole('option');
        expect(option.textContent).toContain('Test');
        expect(option.textContent).toContain('Server');
        expect(option.textContent).toContain('test.example.com');
        expect(option.textContent).toContain('42');
        expect(option.textContent).toContain('assets');
      });
    });

    it('should highlight matching text in results', async () => {
      const mockTarget = createMockTarget({
        id: 1,
        name: 'API Server',
        url: 'https://api.example.com',
      });
      vi.mocked(targetService.searchTargets).mockResolvedValue(
        createMockSearchResponse([mockTarget])
      );

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Open popover and search
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'API');

      // Wait for results with highlighted text
      await waitFor(() => {
        // Check for mark element with highlighted text
        const marks = screen.getAllByText('API');
        expect(marks.some((el) => el.tagName === 'MARK')).toBe(true);
      });
    });
  });

  // 4. Selection
  describe('Selection', () => {
    it('should call onSelect when result clicked', async () => {
      const mockTarget = createMockTarget({ id: 1, name: 'Main API' });
      vi.mocked(targetService.searchTargets).mockResolvedValue(
        createMockSearchResponse([mockTarget])
      );

      const onSelect = vi.fn();
      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={onSelect} />
      );

      // Open popover and search
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'api');

      // Wait for results
      await waitFor(() => {
        expect(screen.getByRole('option')).toBeInTheDocument();
      });

      // Click the CommandItem (role="option")
      const option = screen.getByRole('option');
      await user.click(option);

      expect(onSelect).toHaveBeenCalledTimes(1);
      expect(onSelect).toHaveBeenCalledWith(mockTarget);
    });

    it('should close dropdown after selection', async () => {
      const mockTarget = createMockTarget({ id: 1, name: 'Main API' });
      vi.mocked(targetService.searchTargets).mockResolvedValue(
        createMockSearchResponse([mockTarget])
      );

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Open popover and search
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'api');

      // Wait for results
      await waitFor(() => {
        expect(screen.getByRole('option')).toBeInTheDocument();
      });

      // Click the CommandItem (role="option")
      const option = screen.getByRole('option');
      await user.click(option);

      // Dropdown should be closed - search input should not be visible
      await waitFor(() => {
        expect(
          screen.queryByPlaceholderText(/search by name or url/i)
        ).not.toBeInTheDocument();
      });
    });

    it('should call onSelect on Enter key', async () => {
      const mockTarget = createMockTarget({ id: 1, name: 'Main API' });
      vi.mocked(targetService.searchTargets).mockResolvedValue(
        createMockSearchResponse([mockTarget])
      );

      const onSelect = vi.fn();
      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={onSelect} />
      );

      // Open popover and search
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'api');

      // Wait for results
      await waitFor(() => {
        expect(screen.getByRole('option')).toBeInTheDocument();
      });

      // Press Enter to select (cmdk automatically selects first item)
      await user.keyboard('{Enter}');

      expect(onSelect).toHaveBeenCalledTimes(1);
      expect(onSelect).toHaveBeenCalledWith(mockTarget);
    });
  });

  // 5. Loading and Error States
  describe('Loading and Error States', () => {
    it('should show loading state while searching', async () => {
      // Never resolves to keep loading
      vi.mocked(targetService.searchTargets).mockImplementation(
        () => new Promise(() => {})
      );

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Open popover and search
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'api');

      // Wait for loading state
      await waitFor(() => {
        expect(screen.getByText(/searching/i)).toBeInTheDocument();
      });
    });

    it('should show empty state when no results', async () => {
      vi.mocked(targetService.searchTargets).mockResolvedValue(
        createMockSearchResponse([])
      );

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Open popover and search
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'nonexistent');

      // Wait for empty state
      await waitFor(() => {
        expect(screen.getByText(/no targets found/i)).toBeInTheDocument();
      });
    });

    it('should show error state when API fails', async () => {
      vi.mocked(targetService.searchTargets).mockRejectedValue(
        new Error('Network Error')
      );

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Open popover and search
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'api');

      // Wait for error state (use longer timeout since debounce + error handling)
      await waitFor(
        () => {
          expect(screen.getByText(/search failed/i)).toBeInTheDocument();
        },
        { timeout: 2000 }
      );
    });
  });

  // 6. Edge Cases
  describe('Edge Cases', () => {
    it('should not search when query is less than 2 chars', async () => {
      const mockSearchTargets = vi
        .mocked(targetService.searchTargets)
        .mockResolvedValue(createMockSearchResponse([]));

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Open popover and type only 1 character
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      const input = screen.getByPlaceholderText(/search by name or url/i);
      await user.type(input, 'a');

      // Wait for potential debounced call and check it wasn't made
      await waitFor(
        () => {
          // Should show hint message instead of results
          expect(screen.getByText(/type at least 2 characters/i)).toBeInTheDocument();
        },
        { timeout: 500 }
      );

      // API should not be called for query length < 2
      expect(mockSearchTargets).not.toHaveBeenCalled();
    });

    it('should close dropdown on Escape key', async () => {
      vi.mocked(targetService.searchTargets).mockResolvedValue(
        createMockSearchResponse([])
      );

      const { user } = renderWithProviders(
        <TargetSearchBar projectId={1} onSelect={vi.fn()} />
      );

      // Open popover
      const triggerButton = screen.getByRole('button', { name: /search/i });
      await user.click(triggerButton);

      // Verify popover is open
      expect(
        screen.getByPlaceholderText(/search by name or url/i)
      ).toBeInTheDocument();

      // Press Escape
      await user.keyboard('{Escape}');

      // Dropdown should be closed
      await waitFor(() => {
        expect(
          screen.queryByPlaceholderText(/search by name or url/i)
        ).not.toBeInTheDocument();
      });
    });
  });
});
