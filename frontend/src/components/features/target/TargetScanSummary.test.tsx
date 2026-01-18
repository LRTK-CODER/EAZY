import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TargetScanSummary } from './TargetScanSummary';
import * as dateUtils from '@/utils/date';
import type { Task, TaskStatus } from '@/types/task';

// Mock the date utils
vi.mock('@/utils/date', async () => {
  const actual = await vi.importActual('@/utils/date');
  return {
    ...actual,
    formatElapsedTime: vi.fn(() => '3m 25s'),
    formatDistanceToNow: vi.fn(() => '2 hours ago'),
  };
});

// Helper to create mock task
const createMockTask = (overrides: Partial<Task> = {}): Task => ({
  id: 1,
  project_id: 1,
  target_id: 1,
  type: 'scan' as const,
  status: 'pending' as TaskStatus,
  result: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

describe('TargetScanSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('상태별 렌더링', () => {
    it('task가 undefined일 때 "-" 표시', () => {
      render(<TargetScanSummary />);
      expect(screen.getByText('-')).toBeInTheDocument();
    });

    it('PENDING 상태 표시', () => {
      const mockTask = createMockTask({
        status: 'pending' as TaskStatus,
        started_at: new Date().toISOString(),
      });

      vi.mocked(dateUtils.formatElapsedTime).mockReturnValue('1m 30s');

      render(<TargetScanSummary task={mockTask} />);

      expect(screen.getByText(/1m 30s/)).toBeInTheDocument();
    });

    it('RUNNING 상태에서 animate-spin 아이콘 표시', () => {
      const mockTask = createMockTask({
        status: 'running' as TaskStatus,
        started_at: new Date().toISOString(),
      });

      vi.mocked(dateUtils.formatElapsedTime).mockReturnValue('3m 25s');

      const { container } = render(<TargetScanSummary task={mockTask} />);

      expect(screen.getByText(/3m 25s/)).toBeInTheDocument();
      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('COMPLETED 상태에서 상대 시간 표시', () => {
      const mockTask = createMockTask({
        status: 'completed' as TaskStatus,
        completed_at: new Date().toISOString(),
      });

      vi.mocked(dateUtils.formatDistanceToNow).mockReturnValue('2 hours ago');

      render(<TargetScanSummary task={mockTask} />);

      expect(screen.getByText(/2 hours ago/)).toBeInTheDocument();
    });

    it('FAILED 상태에서 "Failed" 표시', () => {
      const mockTask = createMockTask({
        status: 'failed' as TaskStatus,
      });

      render(<TargetScanSummary task={mockTask} />);

      expect(screen.getByText(/Failed/)).toBeInTheDocument();
    });

    it('CANCELLED 상태에서 "Cancelled" 표시', () => {
      const mockTask = createMockTask({
        status: 'cancelled' as TaskStatus,
      });

      render(<TargetScanSummary task={mockTask} />);

      expect(screen.getByText(/Cancelled/)).toBeInTheDocument();
    });
  });

  describe('시간 표시', () => {
    it('PENDING 상태에서 formatElapsedTime 호출', () => {
      const startedAt = new Date().toISOString();
      const mockTask = createMockTask({
        status: 'pending' as TaskStatus,
        started_at: startedAt,
      });

      render(<TargetScanSummary task={mockTask} />);

      expect(dateUtils.formatElapsedTime).toHaveBeenCalledWith(startedAt);
    });

    it('RUNNING 상태에서 formatElapsedTime 호출', () => {
      const startedAt = new Date().toISOString();
      const mockTask = createMockTask({
        status: 'running' as TaskStatus,
        started_at: startedAt,
      });

      render(<TargetScanSummary task={mockTask} />);

      expect(dateUtils.formatElapsedTime).toHaveBeenCalledWith(startedAt);
    });

    it('COMPLETED 상태에서 formatDistanceToNow 호출', () => {
      const completedAt = new Date().toISOString();
      const mockTask = createMockTask({
        status: 'completed' as TaskStatus,
        completed_at: completedAt,
      });

      render(<TargetScanSummary task={mockTask} />);

      expect(dateUtils.formatDistanceToNow).toHaveBeenCalledWith(completedAt, { addSuffix: true });
    });

    it('started_at 없을 때 formatElapsedTime 호출하지 않음', () => {
      const mockTask = createMockTask({
        status: 'pending' as TaskStatus,
        started_at: undefined,
      });

      render(<TargetScanSummary task={mockTask} />);

      expect(dateUtils.formatElapsedTime).not.toHaveBeenCalled();
      expect(screen.getByText(/Pending/)).toBeInTheDocument();
    });
  });

  describe('클릭 이벤트', () => {
    it('onClick 콜백을 호출한다', async () => {
      const user = userEvent.setup();
      const handleClick = vi.fn();
      const mockTask = createMockTask({ status: 'completed' as TaskStatus });

      render(<TargetScanSummary task={mockTask} onClick={handleClick} />);

      const element = screen.getByRole('button');
      await user.click(element);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('onClick이 undefined일 때 button role이 없다', () => {
      const mockTask = createMockTask();

      render(<TargetScanSummary task={mockTask} />);

      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('키보드(Enter)로 접근 가능하다', async () => {
      const user = userEvent.setup();
      const handleClick = vi.fn();
      const mockTask = createMockTask();

      render(<TargetScanSummary task={mockTask} onClick={handleClick} />);

      const button = screen.getByRole('button');
      button.focus();
      await user.keyboard('{Enter}');

      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('접근성', () => {
    it('role="status" 속성이 있다', () => {
      const mockTask = createMockTask({ status: 'running' as TaskStatus });

      render(<TargetScanSummary task={mockTask} />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('aria-label이 제공된다', () => {
      const mockTask = createMockTask({ status: 'running' as TaskStatus });

      render(<TargetScanSummary task={mockTask} />);

      const status = screen.getByRole('status');
      expect(status).toHaveAttribute('aria-label');
    });

    it('아이콘에 aria-hidden="true" 속성이 있다', () => {
      const mockTask = createMockTask({
        status: 'running' as TaskStatus,
        started_at: new Date().toISOString(),
      });

      const { container } = render(<TargetScanSummary task={mockTask} />);

      const icon = container.querySelector('svg');
      expect(icon).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('엣지 케이스', () => {
    it('started_at 없는 RUNNING 상태를 처리한다', () => {
      const mockTask = createMockTask({
        status: 'running' as TaskStatus,
        started_at: undefined,
      });

      render(<TargetScanSummary task={mockTask} />);

      // 에러 없이 렌더링되고 Running 텍스트 표시
      expect(screen.getByText(/Running/)).toBeInTheDocument();
      expect(dateUtils.formatElapsedTime).not.toHaveBeenCalled();
    });

    it('completed_at 없는 COMPLETED 상태를 처리한다', () => {
      const mockTask = createMockTask({
        status: 'completed' as TaskStatus,
        completed_at: undefined,
      });

      render(<TargetScanSummary task={mockTask} />);

      // 에러 없이 렌더링되고 Completed 텍스트 표시
      expect(screen.getByText(/Completed/)).toBeInTheDocument();
      expect(dateUtils.formatDistanceToNow).not.toHaveBeenCalled();
    });

    it('isLoading=true일 때 로딩 표시', () => {
      render(<TargetScanSummary isLoading={true} />);

      expect(screen.getByText('...')).toBeInTheDocument();
    });

    it('className prop이 적용된다', () => {
      const mockTask = createMockTask();

      const { container } = render(
        <TargetScanSummary task={mockTask} className="custom-class" />
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });
  });
});
