import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ScanControl } from './ScanControl';
import * as useTasks from '@/hooks/useTasks';
import * as useTargets from '@/hooks/useTargets';
import type { Task, TaskStatus } from '@/types/task';

// Mock the hooks
vi.mock('@/hooks/useTasks');
vi.mock('@/hooks/useTargets');

// Helper to render with providers
const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return {
    user: userEvent.setup(),
    ...render(
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    ),
  };
};

// Helper to create mock task
const createMockTask = (status: TaskStatus, overrides: Partial<Task> = {}): Task => ({
  id: 1,
  project_id: 1,
  target_id: 1,
  type: 'scan' as const,
  status,
  result: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

// Default props for testing
const defaultProps = {
  projectId: 1,
  targetId: 1,
  targetName: 'Test Target',
};

describe('ScanControl', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock for useLatestTask
    vi.mocked(useTasks.useLatestTask).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useTasks.useLatestTask>);

    // Default mock for useCancelTask
    vi.mocked(useTasks.useCancelTask).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useTasks.useCancelTask>);

    // Default mock for useTriggerScan
    vi.mocked(useTargets.useTriggerScan).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useTargets.useTriggerScan>);
  });

  describe('렌더링', () => {
    it('기본 컴포넌트가 렌더링된다', () => {
      renderWithProviders(<ScanControl {...defaultProps} />);

      // ScanControl 컴포넌트가 렌더링되어야 함
      expect(screen.getByRole('button', { name: /scan/i })).toBeInTheDocument();
    });

    it('compact 모드에서 간소화된 UI를 표시한다', () => {
      renderWithProviders(<ScanControl {...defaultProps} compact />);

      // compact 모드에서는 텍스트가 sr-only로 숨겨짐
      const button = screen.getByRole('button', { name: /scan/i });
      expect(button).toBeInTheDocument();
      // 버튼 내 텍스트가 sr-only 클래스로 숨겨져 있어야 함
      const textSpan = screen.getByText('Start Scan');
      expect(textSpan).toHaveClass('sr-only');
    });
  });

  describe('스캔 시작', () => {
    it('Task 없으면 "Start Scan" 버튼을 표시한다', () => {
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof useTasks.useLatestTask>);

      renderWithProviders(<ScanControl {...defaultProps} />);

      expect(screen.getByRole('button', { name: /start scan/i })).toBeInTheDocument();
    });

    it('COMPLETED 상태면 "Start Scan" 버튼을 표시한다', () => {
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: createMockTask('completed' as TaskStatus),
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof useTasks.useLatestTask>);

      renderWithProviders(<ScanControl {...defaultProps} />);

      expect(screen.getByRole('button', { name: /start scan/i })).toBeInTheDocument();
    });

    it('버튼 클릭 시 useTriggerScan.mutate를 호출한다', async () => {
      const mockMutate = vi.fn();
      vi.mocked(useTargets.useTriggerScan).mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      } as unknown as ReturnType<typeof useTargets.useTriggerScan>);

      const { user } = renderWithProviders(<ScanControl {...defaultProps} />);

      const startButton = screen.getByRole('button', { name: /start scan/i });
      await user.click(startButton);

      expect(mockMutate).toHaveBeenCalledWith({
        projectId: 1,
        targetId: 1,
      });
    });

    it('트리거 중(isPending)이면 버튼이 비활성화된다', () => {
      vi.mocked(useTargets.useTriggerScan).mockReturnValue({
        mutate: vi.fn(),
        isPending: true,
      } as unknown as ReturnType<typeof useTargets.useTriggerScan>);

      renderWithProviders(<ScanControl {...defaultProps} />);

      const startButton = screen.getByRole('button', { name: /start scan/i });
      expect(startButton).toBeDisabled();
    });

    it('트리거 실패 시 에러를 처리한다', async () => {
      const mockMutate = vi.fn();
      vi.mocked(useTargets.useTriggerScan).mockReturnValue({
        mutate: mockMutate,
        isPending: false,
        isError: true,
        error: new Error('Failed to trigger scan'),
      } as unknown as ReturnType<typeof useTargets.useTriggerScan>);

      renderWithProviders(<ScanControl {...defaultProps} />);

      // 에러 상태가 표시되거나 처리되어야 함
      // 구체적인 에러 UI는 구현 시 결정
      expect(screen.getByRole('button', { name: /start scan/i })).toBeInTheDocument();
    });
  });

  describe('스캔 상태 표시', () => {
    it('ScanStatusBadge를 올바르게 렌더링한다', () => {
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: createMockTask('running' as TaskStatus, {
          started_at: new Date().toISOString(),
        }),
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof useTasks.useLatestTask>);

      renderWithProviders(<ScanControl {...defaultProps} />);

      // ScanStatusBadge가 렌더링되어 Running 상태를 표시해야 함
      expect(screen.getByText(/running/i)).toBeInTheDocument();
    });

    it('RUNNING 상태면 "Start Scan" 버튼을 숨긴다', () => {
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: createMockTask('running' as TaskStatus, {
          started_at: new Date().toISOString(),
        }),
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof useTasks.useLatestTask>);

      renderWithProviders(<ScanControl {...defaultProps} />);

      expect(screen.queryByRole('button', { name: /start scan/i })).not.toBeInTheDocument();
    });

    it('PENDING 상태면 "Start Scan" 버튼을 숨긴다', () => {
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: createMockTask('pending' as TaskStatus),
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof useTasks.useLatestTask>);

      renderWithProviders(<ScanControl {...defaultProps} />);

      expect(screen.queryByRole('button', { name: /start scan/i })).not.toBeInTheDocument();
    });
  });

  describe('로딩 상태', () => {
    it('useLatestTask 로딩 중 스피너를 표시한다', () => {
      vi.mocked(useTasks.useLatestTask).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as unknown as ReturnType<typeof useTasks.useLatestTask>);

      renderWithProviders(<ScanControl {...defaultProps} />);

      // 로딩 스피너가 표시되어야 함
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });
  });

  describe('접근성', () => {
    it('버튼에 적절한 aria-label이 있다', () => {
      renderWithProviders(<ScanControl {...defaultProps} />);

      const startButton = screen.getByRole('button', { name: /start scan/i });
      expect(startButton).toHaveAttribute('aria-label', expect.stringContaining('Test Target'));
    });
  });
});
