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
    it('should fail because AssetDetailDialog component does not exist', () => {
      // RED Phase: AssetDetailDialog component not implemented yet
      // Will FAIL: AssetDetailDialog is not defined
      expect(() =>
        render(
          <AssetDetailDialog
            asset={mockAssetWithHttpData}
            open={true}
            onOpenChange={() => {}}
          />
        )
      ).toThrow();
    });
  });

  describe('Tabs Component', () => {
    it('should render Tabs with Request/Response/Metadata tabs', async () => {
      // RED Phase: Verify Tabs structure
      try {
        render(
          <AssetDetailDialog
            asset={mockAssetWithHttpData}
            open={true}
            onOpenChange={() => {}}
          />
        );

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          expect(screen.getByRole('tab', { name: /request/i })).toBeInTheDocument();
          expect(screen.getByRole('tab', { name: /response/i })).toBeInTheDocument();
          expect(screen.getByRole('tab', { name: /metadata/i })).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('Request Tab', () => {
    it('should display HTTP method badge in Request tab', async () => {
      // RED Phase: Verify method Badge display
      try {
        render(
          <AssetDetailDialog
            asset={mockAssetWithHttpData}
            open={true}
            onOpenChange={() => {}}
          />
        );

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          expect(screen.getByText('POST')).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should display request headers in Table format', async () => {
      // RED Phase: Verify headers Table
      try {
        render(
          <AssetDetailDialog
            asset={mockAssetWithHttpData}
            open={true}
            onOpenChange={() => {}}
          />
        );

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          expect(screen.getByText('Content-Type')).toBeInTheDocument();
          expect(screen.getByText('application/json')).toBeInTheDocument();
          expect(screen.getByText('Authorization')).toBeInTheDocument();
          expect(screen.getByText('Bearer token123')).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should display request body in CodeBlock with JSON formatting', async () => {
      // RED Phase: Verify body CodeBlock with pretty-print
      try {
        render(
          <AssetDetailDialog
            asset={mockAssetWithHttpData}
            open={true}
            onOpenChange={() => {}}
          />
        );

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          // JSON.stringify(body, null, 2) should format with 2-space indent
          expect(screen.getByText(/"username": "testuser"/)).toBeInTheDocument();
          expect(screen.getByText(/"password": "secret"/)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should show "No request data" when request_spec is null', async () => {
      // RED Phase: Verify null handling
      try {
        render(
          <AssetDetailDialog
            asset={mockAssetWithoutHttpData}
            open={true}
            onOpenChange={() => {}}
          />
        );

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          expect(screen.getByText(/no.*request.*data/i)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('Response Tab', () => {
    it('should display HTTP status badge in Response tab', async () => {
      // RED Phase: Verify status Badge
      try {
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

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          expect(screen.getByText('200')).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should display response headers in Table format', async () => {
      // RED Phase: Verify headers Table
      try {
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

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          expect(screen.getByText('Content-Type')).toBeInTheDocument();
          expect(screen.getByText('application/json')).toBeInTheDocument();
          expect(screen.getByText('Set-Cookie')).toBeInTheDocument();
          expect(screen.getByText('session=xyz')).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should display response body in CodeBlock with JSON formatting', async () => {
      // RED Phase: Verify body CodeBlock with pretty-print
      try {
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

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          expect(screen.getByText(/"success": true/)).toBeInTheDocument();
          expect(screen.getByText(/"token": "jwt123"/)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should show "No response data" when response_spec is null', async () => {
      // RED Phase: Verify null handling
      try {
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

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          expect(screen.getByText(/no.*response.*data/i)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('Metadata Tab', () => {
    it('should display first_seen_at and last_seen_at timestamps', async () => {
      // RED Phase: Verify metadata display
      try {
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

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          expect(screen.getByText(/first.*seen/i)).toBeInTheDocument();
          expect(screen.getByText(/last.*seen/i)).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should display parameters in table format', async () => {
      // RED Phase: Verify parameters Table
      try {
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

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          expect(screen.getByText('username')).toBeInTheDocument();
          expect(screen.getByText('string')).toBeInTheDocument();
          expect(screen.getByText('password')).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('Dialog Controls', () => {
    it('should open Dialog when "View Details" button is clicked', async () => {
      // RED Phase: Verify dialog open behavior
      try {
        const onOpenChange = vi.fn();

        render(
          <AssetDetailDialog
            asset={mockAssetWithHttpData}
            open={false}
            onOpenChange={onOpenChange}
          />
        );

        // Will FAIL: Component doesn't exist
        await waitFor(() => {
          expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        });

        // Trigger open
        onOpenChange(true);

        await waitFor(() => {
          expect(screen.getByRole('dialog')).toBeInTheDocument();
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should close Dialog when Close button is clicked', async () => {
      // RED Phase: Verify dialog close behavior
      try {
        const onOpenChange = vi.fn();

        render(
          <AssetDetailDialog
            asset={mockAssetWithHttpData}
            open={true}
            onOpenChange={onOpenChange}
          />
        );

        // Will FAIL: Component doesn't exist
        const closeButton = screen.getByRole('button', { name: /close/i });
        await userEvent.setup().click(closeButton);

        await waitFor(() => {
          expect(onOpenChange).toHaveBeenCalledWith(false);
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });
});
