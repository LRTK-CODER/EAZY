/**
 * Resizable Component Tests
 * TDD - Tests for resize handle improvements
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from './resizable';

// Mock ResizeObserver for react-resizable-panels
class ResizeObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
(globalThis as unknown as { ResizeObserver: typeof ResizeObserver }).ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

// Mock react-resizable-panels to avoid CSS issues in JSDOM
vi.mock('react-resizable-panels', () => ({
  Panel: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => (
    <div {...props}>{children}</div>
  ),
  Group: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => (
    <div {...props}>{children}</div>
  ),
  Separator: ({ children, className, ...props }: { children?: React.ReactNode; className?: string; [key: string]: unknown }) => (
    <div className={className} {...props}>{children}</div>
  ),
}));

describe('ResizableHandle', () => {
  describe('Touch Target Size (1.3)', () => {
    it('should have minimum click area of 12px via after pseudo-element', () => {
      render(
        <ResizablePanelGroup orientation="horizontal">
          <ResizablePanel defaultSize={50}>Left</ResizablePanel>
          <ResizableHandle data-testid="resize-handle" withHandle />
          <ResizablePanel defaultSize={50}>Right</ResizablePanel>
        </ResizablePanelGroup>
      );

      const handle = screen.getByTestId('resize-handle');
      // Check that the handle has the w-3 class for 12px hit area
      expect(handle.className).toMatch(/after:w-3/);
    });

    it('should have visible width of at least 4px', () => {
      render(
        <ResizablePanelGroup orientation="horizontal">
          <ResizablePanel defaultSize={50}>Left</ResizablePanel>
          <ResizableHandle data-testid="resize-handle" withHandle />
          <ResizablePanel defaultSize={50}>Right</ResizablePanel>
        </ResizablePanelGroup>
      );

      const handle = screen.getByTestId('resize-handle');
      // Check that the handle has w-1 class (4px) instead of w-px (1px)
      expect(handle.className).toMatch(/\bw-1\b/);
      expect(handle.className).not.toMatch(/\bw-px\b/);
    });

    it('should have hover visual feedback', () => {
      render(
        <ResizablePanelGroup orientation="horizontal">
          <ResizablePanel defaultSize={50}>Left</ResizablePanel>
          <ResizableHandle data-testid="resize-handle" withHandle />
          <ResizablePanel defaultSize={50}>Right</ResizablePanel>
        </ResizablePanelGroup>
      );

      const handle = screen.getByTestId('resize-handle');
      // Check for hover background color class
      expect(handle.className).toMatch(/hover:bg-/);
    });

    it('should have transition for smooth hover effect', () => {
      render(
        <ResizablePanelGroup orientation="horizontal">
          <ResizablePanel defaultSize={50}>Left</ResizablePanel>
          <ResizableHandle data-testid="resize-handle" withHandle />
          <ResizablePanel defaultSize={50}>Right</ResizablePanel>
        </ResizablePanelGroup>
      );

      const handle = screen.getByTestId('resize-handle');
      // Check for transition class
      expect(handle.className).toMatch(/transition-colors/);
    });

    it('should render handle icon with increased size', () => {
      render(
        <ResizablePanelGroup orientation="horizontal">
          <ResizablePanel defaultSize={50}>Left</ResizablePanel>
          <ResizableHandle data-testid="resize-handle" withHandle />
          <ResizablePanel defaultSize={50}>Right</ResizablePanel>
        </ResizablePanelGroup>
      );

      const handle = screen.getByTestId('resize-handle');
      const handleIcon = handle.querySelector('div');

      // Check handle icon container has increased size
      expect(handleIcon?.className).toMatch(/h-6/);
      expect(handleIcon?.className).toMatch(/w-4/);
    });
  });

  describe('Basic Functionality', () => {
    it('should render without handle icon when withHandle is false', () => {
      render(
        <ResizablePanelGroup orientation="horizontal">
          <ResizablePanel defaultSize={50}>Left</ResizablePanel>
          <ResizableHandle data-testid="resize-handle" />
          <ResizablePanel defaultSize={50}>Right</ResizablePanel>
        </ResizablePanelGroup>
      );

      const handle = screen.getByTestId('resize-handle');
      const handleIcon = handle.querySelector('div');

      expect(handleIcon).toBeNull();
    });

    it('should render handle icon when withHandle is true', () => {
      render(
        <ResizablePanelGroup orientation="horizontal">
          <ResizablePanel defaultSize={50}>Left</ResizablePanel>
          <ResizableHandle data-testid="resize-handle" withHandle />
          <ResizablePanel defaultSize={50}>Right</ResizablePanel>
        </ResizablePanelGroup>
      );

      const handle = screen.getByTestId('resize-handle');
      const handleIcon = handle.querySelector('div');

      expect(handleIcon).toBeInTheDocument();
    });
  });
});
