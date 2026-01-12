/**
 * AssetDetailPanel Component Tests
 * Tests for the detail panel shown when an asset is selected in the tree view
 */

import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AssetDetailPanel } from './AssetDetailPanel';
import type { Asset } from '@/types/asset';

// Mock asset factory
function createMockAsset(overrides: Partial<Asset> = {}): Asset {
  return {
    id: 1,
    target_id: 1,
    content_hash: 'abc123',
    type: 'url',
    source: 'html',
    method: 'GET',
    url: 'https://example.com/api/users',
    path: '/api/users',
    request_spec: {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer token123',
      },
      body: '{"name": "test"}',
    },
    response_spec: {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
      body: '{"id": 1, "name": "test"}',
    },
    parameters: {
      id: '123',
      name: 'test',
    },
    last_task_id: null,
    first_seen_at: '2024-01-01T00:00:00Z',
    last_seen_at: '2024-01-02T00:00:00Z',
    ...overrides,
  };
}

describe('AssetDetailPanel', () => {
  // =====================
  // 6.1.1 Empty State UI Tests
  // =====================
  describe('Empty State UI', () => {
    it('renders empty state when no asset is selected', () => {
      render(<AssetDetailPanel asset={null} />);

      expect(screen.getByText('No asset selected')).toBeInTheDocument();
      expect(screen.getByText(/select an asset/i)).toBeInTheDocument();
    });

    it('renders empty state with icon', () => {
      render(<AssetDetailPanel asset={null} />);

      expect(screen.getByTestId('empty-state-icon')).toBeInTheDocument();
    });

    it('does not render tabs when no asset selected', () => {
      render(<AssetDetailPanel asset={null} />);

      expect(screen.queryByRole('tablist')).not.toBeInTheDocument();
    });
  });

  // =====================
  // 6.1.2 Asset Information Display Tests
  // =====================
  describe('Asset Information Display', () => {
    it('renders asset URL in header', () => {
      const asset = createMockAsset();
      render(<AssetDetailPanel asset={asset} />);

      expect(screen.getByText(asset.url)).toBeInTheDocument();
    });

    it('renders HTTP method badge in header', () => {
      const asset = createMockAsset({ method: 'POST' });
      render(<AssetDetailPanel asset={asset} />);

      expect(screen.getByTestId('method-badge-header')).toHaveTextContent('POST');
    });

    it('renders request headers table', async () => {
      const asset = createMockAsset();
      render(<AssetDetailPanel asset={asset} />);

      // Should be on Request tab by default
      expect(screen.getByText('Content-Type')).toBeInTheDocument();
      expect(screen.getByText('application/json')).toBeInTheDocument();
    });

    it('renders request body in code block', () => {
      const asset = createMockAsset();
      render(<AssetDetailPanel asset={asset} />);

      const codeBlock = screen.getByTestId('request-body');
      expect(codeBlock).toBeInTheDocument();
    });

    it('renders response status badge', async () => {
      const asset = createMockAsset();
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      // Click Response tab
      await user.click(screen.getByRole('tab', { name: /response/i }));

      expect(screen.getByTestId('status-badge')).toHaveTextContent('200');
    });

    it('renders response headers table', async () => {
      const asset = createMockAsset();
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      await user.click(screen.getByRole('tab', { name: /response/i }));

      expect(screen.getByText('Content-Type')).toBeInTheDocument();
    });

    it('renders metadata timestamps', async () => {
      const asset = createMockAsset();
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      await user.click(screen.getByRole('tab', { name: /metadata/i }));

      expect(screen.getByText(/first seen/i)).toBeInTheDocument();
      expect(screen.getByText(/last seen/i)).toBeInTheDocument();
    });

    it('renders parameters table in metadata tab', async () => {
      const asset = createMockAsset();
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      await user.click(screen.getByRole('tab', { name: /metadata/i }));

      expect(screen.getByText('id')).toBeInTheDocument();
      expect(screen.getByText('123')).toBeInTheDocument();
    });

    it('renders type and source badges in metadata', async () => {
      const asset = createMockAsset({ type: 'xhr', source: 'js' });
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      await user.click(screen.getByRole('tab', { name: /metadata/i }));

      expect(screen.getByTestId('type-badge')).toHaveTextContent('XHR');
      expect(screen.getByTestId('source-badge')).toHaveTextContent('JS');
    });
  });

  // =====================
  // 6.1.3 Tabs Navigation Tests
  // =====================
  describe('Tabs Navigation', () => {
    it('renders three tabs: Request, Response, Metadata', () => {
      const asset = createMockAsset();
      render(<AssetDetailPanel asset={asset} />);

      expect(screen.getByRole('tab', { name: /request/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /response/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /metadata/i })).toBeInTheDocument();
    });

    it('defaults to Request tab', () => {
      const asset = createMockAsset();
      render(<AssetDetailPanel asset={asset} />);

      const requestTab = screen.getByRole('tab', { name: /request/i });
      expect(requestTab).toHaveAttribute('data-state', 'active');
    });

    it('switches to Response tab on click', async () => {
      const asset = createMockAsset();
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      await user.click(screen.getByRole('tab', { name: /response/i }));

      const responseTab = screen.getByRole('tab', { name: /response/i });
      expect(responseTab).toHaveAttribute('data-state', 'active');
    });

    it('switches to Metadata tab on click', async () => {
      const asset = createMockAsset();
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      await user.click(screen.getByRole('tab', { name: /metadata/i }));

      const metadataTab = screen.getByRole('tab', { name: /metadata/i });
      expect(metadataTab).toHaveAttribute('data-state', 'active');
    });

    it('shows correct content for each tab', async () => {
      const asset = createMockAsset();
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      // Request tab (default) - check for request-specific content
      expect(screen.getByTestId('request-tab-content')).toBeInTheDocument();

      // Switch to Response
      await user.click(screen.getByRole('tab', { name: /response/i }));
      expect(screen.getByTestId('response-tab-content')).toBeInTheDocument();

      // Switch to Metadata
      await user.click(screen.getByRole('tab', { name: /metadata/i }));
      expect(screen.getByTestId('metadata-tab-content')).toBeInTheDocument();
    });
  });

  // =====================
  // 6.1.4 Edge Cases
  // =====================
  describe('Edge Cases', () => {
    it('handles asset with no request_spec', () => {
      const asset = createMockAsset({ request_spec: null });
      render(<AssetDetailPanel asset={asset} />);

      expect(screen.getByText(/no request data/i)).toBeInTheDocument();
    });

    it('handles asset with no response_spec', async () => {
      const asset = createMockAsset({ response_spec: null });
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      await user.click(screen.getByRole('tab', { name: /response/i }));

      expect(screen.getByText(/no response data/i)).toBeInTheDocument();
    });

    it('handles asset with no parameters', async () => {
      const asset = createMockAsset({ parameters: null });
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      await user.click(screen.getByRole('tab', { name: /metadata/i }));

      expect(screen.getByText(/no parameters/i)).toBeInTheDocument();
    });

    it('handles asset with empty parameters object', async () => {
      const asset = createMockAsset({ parameters: {} });
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      await user.click(screen.getByRole('tab', { name: /metadata/i }));

      expect(screen.getByText(/no parameters/i)).toBeInTheDocument();
    });

    it('handles asset with no headers in request_spec', () => {
      const asset = createMockAsset({
        request_spec: { body: 'test' },
      });
      render(<AssetDetailPanel asset={asset} />);

      // Should not crash, just not show headers section
      expect(screen.queryByText('Headers')).not.toBeInTheDocument();
    });

    it('handles different HTTP methods correctly', () => {
      const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];

      methods.forEach((method) => {
        const asset = createMockAsset({ method });
        const { unmount } = render(<AssetDetailPanel asset={asset} />);

        expect(screen.getByTestId('method-badge-header')).toHaveTextContent(method);
        unmount();
      });
    });

    it('handles different response status codes', async () => {
      const statusCodes = [200, 201, 400, 404, 500];
      const user = userEvent.setup();

      for (const status of statusCodes) {
        const asset = createMockAsset({
          response_spec: { status, headers: {}, body: '' },
        });
        const { unmount } = render(<AssetDetailPanel asset={asset} />);

        await user.click(screen.getByRole('tab', { name: /response/i }));
        expect(screen.getByTestId('status-badge')).toHaveTextContent(String(status));
        unmount();
      }
    });
  });

  // =====================
  // Styling Tests
  // =====================
  describe('Styling', () => {
    it('applies correct badge variant for DELETE method', () => {
      const asset = createMockAsset({ method: 'DELETE' });
      render(<AssetDetailPanel asset={asset} />);

      const badge = screen.getByTestId('method-badge-header');
      expect(badge.className).toMatch(/destructive/);
    });

    it('applies correct badge variant for success status', async () => {
      const asset = createMockAsset({
        response_spec: { status: 200, headers: {}, body: '' },
      });
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      await user.click(screen.getByRole('tab', { name: /response/i }));

      const badge = screen.getByTestId('status-badge');
      expect(badge.className).toMatch(/green/);
    });

    it('applies correct badge variant for error status', async () => {
      const asset = createMockAsset({
        response_spec: { status: 500, headers: {}, body: '' },
      });
      const user = userEvent.setup();
      render(<AssetDetailPanel asset={asset} />);

      await user.click(screen.getByRole('tab', { name: /response/i }));

      const badge = screen.getByTestId('status-badge');
      expect(badge.className).toMatch(/destructive/);
    });
  });

  // =====================
  // Accessibility Tests
  // =====================
  describe('Accessibility', () => {
    it('has accessible tab navigation', () => {
      const asset = createMockAsset();
      render(<AssetDetailPanel asset={asset} />);

      const tablist = screen.getByRole('tablist');
      expect(tablist).toBeInTheDocument();

      const tabs = screen.getAllByRole('tab');
      expect(tabs).toHaveLength(3);
    });

    it('has accessible tabpanel', () => {
      const asset = createMockAsset();
      render(<AssetDetailPanel asset={asset} />);

      const tabpanel = screen.getByRole('tabpanel');
      expect(tabpanel).toBeInTheDocument();
    });
  });
});
