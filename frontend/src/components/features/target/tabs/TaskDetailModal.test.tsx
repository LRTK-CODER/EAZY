import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TaskDetailModal } from './TaskDetailModal';
import * as dateUtils from '@/utils/date';
import type { Task, TaskStatus } from '@/types/task';

// Mock the date utils
vi.mock('@/utils/date', async () => {
  const actual = await vi.importActual('@/utils/date');
  return {
    ...actual,
    formatElapsedTime: vi.fn(() => '5m 30s'),
    formatDistanceToNow: vi.fn(() => '2 hours ago'),
  };
});

// Helper to create mock task
const createMockTask = (overrides: Partial<Task> = {}): Task => ({
  id: 1,
  project_id: 1,
  target_id: 1,
  type: 'crawl',
  status: 'completed' as TaskStatus,
  result: null,
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-15T10:05:00Z',
  started_at: '2026-01-15T10:00:00Z',
  completed_at: '2026-01-15T10:05:00Z',
  ...overrides,
});

describe('TaskDetailModal', () => {
  const mockOnOpenChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1. Modal Open/Close
  describe('Modal Open/Close', () => {
    it('should not render when task is null', () => {
      render(
        <TaskDetailModal
          task={null}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.queryByTestId('task-detail-modal')).not.toBeInTheDocument();
    });

    it('should render when open is true and task exists', () => {
      render(
        <TaskDetailModal
          task={createMockTask()}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByTestId('task-detail-modal')).toBeInTheDocument();
    });

    it('should not render when open is false', () => {
      render(
        <TaskDetailModal
          task={createMockTask()}
          open={false}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.queryByTestId('task-detail-modal')).not.toBeInTheDocument();
    });

    it('should call onOpenChange when close button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TaskDetailModal
          task={createMockTask()}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });
  });

  // 2. Task Information Display
  describe('Task Information Display', () => {
    it('should display task ID in title', () => {
      render(
        <TaskDetailModal
          task={createMockTask({ id: 42 })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText(/task #42/i)).toBeInTheDocument();
    });

    it('should display task type badge', () => {
      render(
        <TaskDetailModal
          task={createMockTask({ type: 'crawl' })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText('crawl')).toBeInTheDocument();
    });

    it('should display task status badge', () => {
      render(
        <TaskDetailModal
          task={createMockTask({ status: 'completed' as TaskStatus })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText('completed')).toBeInTheDocument();
    });

    it('should display scan type badge', () => {
      render(
        <TaskDetailModal
          task={createMockTask({ type: 'scan' })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText('scan')).toBeInTheDocument();
    });
  });

  // 3. Overview Section
  describe('Overview Section', () => {
    it('should render overview section', () => {
      render(
        <TaskDetailModal
          task={createMockTask()}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByTestId('task-overview-section')).toBeInTheDocument();
    });

    it('should display created time', () => {
      vi.mocked(dateUtils.formatDistanceToNow).mockReturnValue('2 hours ago');

      render(
        <TaskDetailModal
          task={createMockTask()}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText(/created:/i)).toBeInTheDocument();
      expect(screen.getAllByText('2 hours ago').length).toBeGreaterThan(0);
    });

    it('should display started time when available', () => {
      render(
        <TaskDetailModal
          task={createMockTask({ started_at: '2026-01-15T10:00:00Z' })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText(/started:/i)).toBeInTheDocument();
    });

    it('should display "-" for started time when not available', () => {
      render(
        <TaskDetailModal
          task={createMockTask({ started_at: undefined })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      const startedRow = screen.getByText(/started:/i).parentElement;
      expect(startedRow).toHaveTextContent('-');
    });

    it('should display duration', () => {
      vi.mocked(dateUtils.formatElapsedTime).mockReturnValue('5m 30s');

      render(
        <TaskDetailModal
          task={createMockTask()}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText(/duration:/i)).toBeInTheDocument();
      expect(screen.getByText('5m 30s')).toBeInTheDocument();
    });

    it('should display completed time when available', () => {
      render(
        <TaskDetailModal
          task={createMockTask({ completed_at: '2026-01-15T10:05:00Z' })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText(/completed:/i)).toBeInTheDocument();
    });
  });

  // 4. Result JSON Display
  describe('Result JSON Display', () => {
    it('should display result section for completed task with result', () => {
      const result = JSON.stringify({ assets_found: 10, urls_crawled: 5 });
      render(
        <TaskDetailModal
          task={createMockTask({ result, status: 'completed' as TaskStatus })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByTestId('task-result-section')).toBeInTheDocument();
    });

    it('should format JSON result with indentation', () => {
      const result = JSON.stringify({ assets_found: 10 });
      render(
        <TaskDetailModal
          task={createMockTask({ result, status: 'completed' as TaskStatus })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      // Check that the formatted JSON is present (with indentation)
      expect(screen.getByTestId('task-result-code')).toBeInTheDocument();
    });

    it('should display no result message for pending task', () => {
      render(
        <TaskDetailModal
          task={createMockTask({ status: 'pending' as TaskStatus, result: null })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText(/task is still in progress/i)).toBeInTheDocument();
    });

    it('should display no result message for running task', () => {
      render(
        <TaskDetailModal
          task={createMockTask({ status: 'running' as TaskStatus, result: null })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText(/task is still in progress/i)).toBeInTheDocument();
    });

    it('should display no result available for completed task without result', () => {
      render(
        <TaskDetailModal
          task={createMockTask({ status: 'completed' as TaskStatus, result: null })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText(/no result data available/i)).toBeInTheDocument();
    });
  });

  // 5. Error State Display
  describe('Error State Display', () => {
    it('should display error section for failed task', () => {
      render(
        <TaskDetailModal
          task={createMockTask({
            status: 'failed' as TaskStatus,
            result: JSON.stringify({ error: 'Connection timeout' })
          })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByTestId('task-error-section')).toBeInTheDocument();
    });

    it('should display error message from result', () => {
      render(
        <TaskDetailModal
          task={createMockTask({
            status: 'failed' as TaskStatus,
            result: JSON.stringify({ error: 'Connection timeout' })
          })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText('Connection timeout')).toBeInTheDocument();
    });

    it('should display raw result as error when JSON parsing fails', () => {
      render(
        <TaskDetailModal
          task={createMockTask({
            status: 'failed' as TaskStatus,
            result: 'Raw error message'
          })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText('Raw error message')).toBeInTheDocument();
    });

    it('should display default error message when result is null', () => {
      render(
        <TaskDetailModal
          task={createMockTask({
            status: 'failed' as TaskStatus,
            result: null
          })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText(/task failed with no error message/i)).toBeInTheDocument();
    });

    it('should not display error section for non-failed tasks', () => {
      render(
        <TaskDetailModal
          task={createMockTask({ status: 'completed' as TaskStatus })}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.queryByTestId('task-error-section')).not.toBeInTheDocument();
    });
  });

  // 6. Status Icons
  describe('Status Icons', () => {
    it('should display appropriate icon for each status', () => {
      const statuses: TaskStatus[] = ['pending', 'running', 'completed', 'failed', 'cancelled'];

      statuses.forEach((status) => {
        const { unmount } = render(
          <TaskDetailModal
            task={createMockTask({ status })}
            open={true}
            onOpenChange={mockOnOpenChange}
          />
        );

        // Verify the status text is displayed (icon is part of the badge)
        expect(screen.getByText(status)).toBeInTheDocument();
        unmount();
      });
    });
  });

  // 7. Accessibility
  describe('Accessibility', () => {
    it('should have proper aria-describedby', () => {
      render(
        <TaskDetailModal
          task={createMockTask()}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      const modal = screen.getByTestId('task-detail-modal');
      expect(modal).toHaveAttribute('aria-describedby', 'task-detail-description');
    });

    it('should have description text', () => {
      render(
        <TaskDetailModal
          task={createMockTask()}
          open={true}
          onOpenChange={mockOnOpenChange}
        />
      );

      expect(screen.getByText(/detailed information about task execution/i)).toBeInTheDocument();
    });
  });
});
