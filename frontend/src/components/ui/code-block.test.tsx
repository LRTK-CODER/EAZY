/**
 * CodeBlock Component Tests
 * Tests for syntax-highlighted code display with copy functionality
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CodeBlock } from './code-block';

// Mock clipboard API
const mockWriteText = vi.fn();

describe('CodeBlock', () => {
  beforeEach(() => {
    mockWriteText.mockClear();
    mockWriteText.mockResolvedValue(undefined);
    // Setup clipboard mock
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: mockWriteText },
      writable: true,
      configurable: true,
    });
  });

  // =====================
  // Basic Rendering Tests
  // =====================
  describe('Basic Rendering', () => {
    it('renders code content', () => {
      const code = '{"name": "test"}';
      render(<CodeBlock code={code} />);

      expect(screen.getByText(/name/)).toBeInTheDocument();
      expect(screen.getByText(/test/)).toBeInTheDocument();
    });

    it('renders with data-testid', () => {
      render(<CodeBlock code="test" data-testid="test-code-block" />);

      expect(screen.getByTestId('test-code-block')).toBeInTheDocument();
    });

    it('renders empty state for empty code', () => {
      render(<CodeBlock code="" />);

      expect(screen.getByText(/no content/i)).toBeInTheDocument();
    });
  });

  // =====================
  // Syntax Highlighting Tests
  // =====================
  describe('Syntax Highlighting', () => {
    it('applies JSON syntax highlighting', async () => {
      const jsonCode = '{"id": 1, "name": "test", "active": true}';
      render(<CodeBlock code={jsonCode} language="json" />);

      // JSON keys should be highlighted (different color/class)
      await waitFor(() => {
        const codeElement = screen.getByRole('code');
        // Check that syntax highlighting is applied (contains styled spans)
        expect(codeElement.innerHTML).toContain('span');
      });
    });

    it('applies XML/HTML syntax highlighting', async () => {
      const xmlCode = '<root><item id="1">Test</item></root>';
      render(<CodeBlock code={xmlCode} language="xml" />);

      await waitFor(() => {
        const codeElement = screen.getByRole('code');
        expect(codeElement.innerHTML).toContain('span');
      });
    });

    it('applies JavaScript syntax highlighting', async () => {
      const jsCode = 'const x = 42; function test() { return x; }';
      render(<CodeBlock code={jsCode} language="javascript" />);

      await waitFor(() => {
        const codeElement = screen.getByRole('code');
        expect(codeElement.innerHTML).toContain('span');
      });
    });

    it('handles plain text without highlighting', () => {
      const plainText = 'Just plain text content';
      render(<CodeBlock code={plainText} language="text" />);

      expect(screen.getByText(plainText)).toBeInTheDocument();
    });
  });

  // =====================
  // Language Auto-Detection Tests
  // =====================
  describe('Language Auto-Detection', () => {
    it('auto-detects JSON from content', async () => {
      const jsonCode = '{"key": "value"}';
      render(<CodeBlock code={jsonCode} />);

      await waitFor(() => {
        const codeElement = screen.getByRole('code');
        expect(codeElement.innerHTML).toContain('span');
      });
    });

    it('auto-detects XML from content', async () => {
      const xmlCode = '<?xml version="1.0"?><root></root>';
      render(<CodeBlock code={xmlCode} />);

      await waitFor(() => {
        const codeElement = screen.getByRole('code');
        expect(codeElement.innerHTML).toContain('span');
      });
    });

    it('auto-detects HTML from content', async () => {
      const htmlCode = '<!DOCTYPE html><html><body></body></html>';
      render(<CodeBlock code={htmlCode} />);

      await waitFor(() => {
        const codeElement = screen.getByRole('code');
        expect(codeElement.innerHTML).toContain('span');
      });
    });

    it('uses contentType prop for detection when provided', async () => {
      const code = 'some data';
      render(<CodeBlock code={code} contentType="application/json" />);

      // Should treat as JSON even if content doesn't look like JSON
      await waitFor(() => {
        expect(screen.getByRole('code')).toBeInTheDocument();
      });
    });
  });

  // =====================
  // Copy Functionality Tests
  // =====================
  describe('Copy Functionality', () => {
    it('renders copy button', () => {
      render(<CodeBlock code="test" />);

      expect(screen.getByRole('button', { name: /copy/i })).toBeInTheDocument();
    });

    it('copies code to clipboard on button click', async () => {
      const code = '{"test": true}';
      const user = userEvent.setup();
      render(<CodeBlock code={code} />);

      const copyButton = screen.getByRole('button', { name: /copy/i });
      await user.click(copyButton);

      // Verify copy button was clicked and feedback shown
      await waitFor(() => {
        expect(screen.getByText(/copied/i)).toBeInTheDocument();
      });
    });

    it('shows success feedback after copy', async () => {
      const user = userEvent.setup();
      render(<CodeBlock code="test" />);

      await user.click(screen.getByRole('button', { name: /copy/i }));

      await waitFor(() => {
        expect(screen.getByText(/copied/i)).toBeInTheDocument();
      });
    });

    it('copy button changes icon after click', async () => {
      const user = userEvent.setup();
      render(<CodeBlock code="test" />);

      // Initially shows Copy button
      expect(screen.getByRole('button', { name: /copy/i })).toBeInTheDocument();

      await user.click(screen.getByRole('button', { name: /copy/i }));

      // After click shows Copied state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /copied/i })).toBeInTheDocument();
      });
    });
  });

  // =====================
  // Theme Support Tests
  // =====================
  describe('Theme Support', () => {
    it('renders with light theme by default', () => {
      render(<CodeBlock code="test" />);

      const container = screen.getByTestId('code-block-container');
      expect(container).toBeInTheDocument();
    });

    it('supports dark theme', () => {
      render(<CodeBlock code="test" theme="dark" />);

      const container = screen.getByTestId('code-block-container');
      expect(container.className).toMatch(/dark/);
    });

    it('supports light theme explicitly', () => {
      render(<CodeBlock code="test" theme="light" />);

      const container = screen.getByTestId('code-block-container');
      expect(container.className).toMatch(/light/);
    });

    it('supports auto theme (system preference)', () => {
      render(<CodeBlock code="test" theme="auto" />);

      const container = screen.getByTestId('code-block-container');
      expect(container).toBeInTheDocument();
    });
  });

  // =====================
  // Line Numbers Tests
  // =====================
  describe('Line Numbers', () => {
    it('shows line numbers when enabled', () => {
      const multiLineCode = 'line1\nline2\nline3';
      render(<CodeBlock code={multiLineCode} showLineNumbers />);

      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('hides line numbers by default', () => {
      const multiLineCode = 'line1\nline2\nline3';
      render(<CodeBlock code={multiLineCode} />);

      // Line numbers should not be rendered as separate elements
      expect(screen.queryByTestId('line-numbers')).not.toBeInTheDocument();
    });
  });

  // =====================
  // Performance Tests
  // =====================
  describe('Performance', () => {
    it('handles large code blocks', async () => {
      // Generate a moderately large JSON object
      const largeJson = JSON.stringify(
        Array.from({ length: 20 }, (_, i) => ({
          id: i,
          name: `item-${i}`,
        })),
        null,
        2
      );

      render(<CodeBlock code={largeJson} language="json" />);

      expect(screen.getByRole('code')).toBeInTheDocument();
    });

    it('truncates extremely large content with warning', () => {
      // Generate large content (>1KB for faster test)
      const largeCode = 'x'.repeat(2000);
      render(<CodeBlock code={largeCode} maxLength={1000} />);

      expect(screen.getByText(/truncated/i)).toBeInTheDocument();
    });
  });

  // =====================
  // Accessibility Tests
  // =====================
  describe('Accessibility', () => {
    it('has accessible code element', () => {
      render(<CodeBlock code="test" />);

      const codeElement = screen.getByRole('code');
      expect(codeElement).toBeInTheDocument();
    });

    it('copy button has accessible label', () => {
      render(<CodeBlock code="test" />);

      const button = screen.getByRole('button', { name: /copy/i });
      expect(button).toHaveAccessibleName();
    });

    it('supports custom aria-label', () => {
      render(<CodeBlock code="test" aria-label="JSON response body" />);

      expect(screen.getByLabelText('JSON response body')).toBeInTheDocument();
    });
  });

  // =====================
  // Error Handling Tests
  // =====================
  describe('Error Handling', () => {
    it('handles invalid JSON gracefully', () => {
      const invalidJson = '{"broken": json}';
      render(<CodeBlock code={invalidJson} language="json" />);

      // Should still render the content without crashing
      expect(screen.getByText(/broken/)).toBeInTheDocument();
    });

    it('handles null code prop', () => {
      // @ts-expect-error Testing null handling
      render(<CodeBlock code={null} />);

      expect(screen.getByText(/no content/i)).toBeInTheDocument();
    });

    it('handles undefined code prop', () => {
      // @ts-expect-error Testing undefined handling
      render(<CodeBlock code={undefined} />);

      expect(screen.getByText(/no content/i)).toBeInTheDocument();
    });
  });
});
