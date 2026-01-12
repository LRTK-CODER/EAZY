import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AssetDetailDialog } from './AssetDetailDialog';
import type { Asset, AssetType, AssetSource } from '@/types/asset';

// Mock asset data with HTTP specs
const mockAssetWithHttpData: Asset = {
  id: 1,
  target_id: 1,
  content_hash: 'abc123def456',
  type: 'url' as AssetType,
  source: 'html' as AssetSource,
  method: 'POST',
  url: 'https://example.com/api/login',
  path: '/api/login',
  request_spec: {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer token123',
    },
    body: { username: 'testuser', password: 'secret' },
  },
  response_spec: {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Set-Cookie': 'session=xyz',
    },
    body: { success: true, token: 'jwt123', user: { id: 1, name: 'Test User' } },
  },
  parameters: { username: 'string', password: 'string' },
  last_task_id: 10,
  first_seen_at: '2026-01-01T00:00:00Z',
  last_seen_at: '2026-01-06T12:00:00Z',
};

const mockAssetWithoutHttpData: Asset = {
  id: 2,
  target_id: 1,
  content_hash: 'def456ghi789',
  type: 'url' as AssetType,
  source: 'html' as AssetSource,
  method: 'GET',
  url: 'https://example.com/page',
  path: '/page',
  request_spec: null,
  response_spec: null,
  parameters: null,
  last_task_id: 11,
  first_seen_at: '2026-01-02T00:00:00Z',
  last_seen_at: '2026-01-06T11:00:00Z',
};

describe('AssetDetailDialog Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Existence', () => {
    it('should render AssetDetailDialog component successfully', () => {
      // GREEN Phase: AssetDetailDialog component is now implemented
      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      // Verify dialog renders
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Asset Details')).toBeInTheDocument();
    });
  });

  describe('Tabs Component', () => {
    it('should render Tabs with Request/Response/Metadata tabs', async () => {
      // GREEN Phase: Verify Tabs structure
      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /request/i })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: /response/i })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: /metadata/i })).toBeInTheDocument();
      });
    });
  });

  describe('Request Tab', () => {
    it('should display HTTP method badge in Request tab', async () => {
      // GREEN Phase: Verify method Badge display
      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('POST')).toBeInTheDocument();
      });
    });

    it('should display request headers in Table format', async () => {
      // GREEN Phase: Verify headers Table
      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Content-Type')).toBeInTheDocument();
        expect(screen.getByText('application/json')).toBeInTheDocument();
        expect(screen.getByText('Authorization')).toBeInTheDocument();
        expect(screen.getByText('Bearer token123')).toBeInTheDocument();
      });
    });

    it('should display request body in CodeBlock with JSON formatting', async () => {
      // GREEN Phase: Verify body CodeBlock with pretty-print
      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      await waitFor(() => {
        // JSON.stringify(body, null, 2) should format with 2-space indent
        expect(screen.getByText(/"username": "testuser"/)).toBeInTheDocument();
        expect(screen.getByText(/"password": "secret"/)).toBeInTheDocument();
      });
    });

    it('should show "No request data" when request_spec is null', async () => {
      // GREEN Phase: Verify null handling
      render(
        <AssetDetailDialog
          asset={mockAssetWithoutHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/no.*request.*data/i)).toBeInTheDocument();
      });
    });
  });

  describe('Response Tab', () => {
    it('should display HTTP status badge in Response tab', async () => {
      // GREEN Phase: Verify status Badge
      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      // Click Response tab
      const responseTab = screen.getByRole('tab', { name: /response/i });
      await userEvent.setup().click(responseTab);

      await waitFor(() => {
        expect(screen.getByText('200')).toBeInTheDocument();
      });
    });

    it('should display response headers in Table format', async () => {
      // GREEN Phase: Verify headers Table
      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      // Click Response tab
      const responseTab = screen.getByRole('tab', { name: /response/i });
      await userEvent.setup().click(responseTab);

      await waitFor(() => {
        expect(screen.getByText('Content-Type')).toBeInTheDocument();
        expect(screen.getByText('application/json')).toBeInTheDocument();
        expect(screen.getByText('Set-Cookie')).toBeInTheDocument();
        expect(screen.getByText('session=xyz')).toBeInTheDocument();
      });
    });

    it('should display response body in CodeBlock with JSON formatting', async () => {
      // GREEN Phase: Verify body CodeBlock with pretty-print
      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      // Click Response tab
      const responseTab = screen.getByRole('tab', { name: /response/i });
      await userEvent.setup().click(responseTab);

      await waitFor(() => {
        expect(screen.getByText(/"success": true/)).toBeInTheDocument();
        expect(screen.getByText(/"token": "jwt123"/)).toBeInTheDocument();
      });
    });

    it('should show "No response data" when response_spec is null', async () => {
      // GREEN Phase: Verify null handling
      render(
        <AssetDetailDialog
          asset={mockAssetWithoutHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      // Click Response tab
      const responseTab = screen.getByRole('tab', { name: /response/i });
      await userEvent.setup().click(responseTab);

      await waitFor(() => {
        expect(screen.getByText(/no.*response.*data/i)).toBeInTheDocument();
      });
    });
  });

  describe('Metadata Tab', () => {
    it('should display first_seen_at and last_seen_at timestamps', async () => {
      // GREEN Phase: Verify metadata display
      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      // Click Metadata tab
      const metadataTab = screen.getByRole('tab', { name: /metadata/i });
      await userEvent.setup().click(metadataTab);

      await waitFor(() => {
        expect(screen.getByText(/first.*seen/i)).toBeInTheDocument();
        expect(screen.getByText(/last.*seen/i)).toBeInTheDocument();
      });
    });

    it('should display parameters in table format with Name, Value, Type columns', async () => {
      // GREEN Phase: Verify parameters Table with Type column
      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={true}
          onOpenChange={() => {}}
        />
      );

      // Click Metadata tab
      const metadataTab = screen.getByRole('tab', { name: /metadata/i });
      await userEvent.setup().click(metadataTab);

      // Wait for parameters heading
      await waitFor(() => {
        expect(screen.getByText('Parameters')).toBeInTheDocument();
      });

      // Verify table headers include Type column
      expect(screen.getByRole('columnheader', { name: /name/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /value/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /type/i })).toBeInTheDocument();

      // Verify parameter entries with types
      expect(screen.getByText('username')).toBeInTheDocument();
      expect(screen.getByText('password')).toBeInTheDocument();
      // inferType('string') returns 'string' - there should be type badges
      const typeBadges = screen.getAllByText('string');
      expect(typeBadges.length).toBeGreaterThanOrEqual(2); // At least 2 type badges
    });
  });

  describe('Dialog Controls', () => {
    it('should not render Dialog when open is false', async () => {
      // GREEN Phase: Verify dialog open behavior
      const onOpenChange = vi.fn();

      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={false}
          onOpenChange={onOpenChange}
        />
      );

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('should close Dialog when Close button is clicked', async () => {
      // GREEN Phase: Verify dialog close behavior
      const onOpenChange = vi.fn();

      render(
        <AssetDetailDialog
          asset={mockAssetWithHttpData}
          open={true}
          onOpenChange={onOpenChange}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      await userEvent.setup().click(closeButton);

      await waitFor(() => {
        expect(onOpenChange).toHaveBeenCalledWith(false);
      });
    });
  });
});
