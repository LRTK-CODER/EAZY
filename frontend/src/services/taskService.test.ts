import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getTaskStatus, cancelTask, getLatestTaskForTarget } from './taskService';
import type { Task } from '@/types/task';
import * as api from '@/lib/api';

vi.mock('@/lib/api');

describe('Task Service', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('getTaskStatus', () => {
        it('should fetch task status', async () => {
            const mockTask: Task = {
                id: 123,
                project_id: 1,
                target_id: 1,
                type: 'scan',
                status: 'pending',
                result: null,
                created_at: '2026-01-03T00:00:00Z',
                updated_at: '2026-01-03T00:00:00Z',
            };

            vi.mocked(api.get).mockResolvedValue(mockTask);
            const result = await getTaskStatus(123);

            expect(api.get).toHaveBeenCalledWith('/tasks/123');
            expect(result).toEqual(mockTask);
            expect(result.status).toBe('pending');
        });

        it('should throw error when task not found', async () => {
            const error = new Error('Task not found');
            vi.mocked(api.get).mockRejectedValue(error);

            await expect(getTaskStatus(999)).rejects.toThrow('Task not found');
            expect(api.get).toHaveBeenCalledWith('/tasks/999');
        });

        it('should fetch task with RUNNING status', async () => {
            const mockTask: Task = {
                id: 456,
                project_id: 1,
                target_id: 2,
                type: 'crawl',
                status: 'running',
                result: null,
                created_at: '2026-01-03T00:00:00Z',
                updated_at: '2026-01-03T01:00:00Z',
            };

            vi.mocked(api.get).mockResolvedValue(mockTask);
            const result = await getTaskStatus(456);

            expect(api.get).toHaveBeenCalledWith('/tasks/456');
            expect(result.status).toBe('running');
        });

        it('should fetch completed task with result data', async () => {
            const mockTask: Task = {
                id: 789,
                project_id: 1,
                target_id: 3,
                type: 'scan',
                status: 'completed',
                result: '{"assets_found": 42, "duration": 120}',
                created_at: '2026-01-03T00:00:00Z',
                updated_at: '2026-01-03T02:00:00Z',
            };

            vi.mocked(api.get).mockResolvedValue(mockTask);
            const result = await getTaskStatus(789);

            expect(api.get).toHaveBeenCalledWith('/tasks/789');
            expect(result.status).toBe('completed');
            expect(result.result).toBeTruthy();
            expect(result.result).toContain('assets_found');
        });
    });

    describe('cancelTask', () => {
        it('should cancel task successfully', async () => {
            vi.mocked(api.post).mockResolvedValue(undefined);

            await cancelTask(123);

            expect(api.post).toHaveBeenCalledWith('/tasks/123/cancel');
        });

        it('should throw error when cancelling completed task', async () => {
            const error = new Error('Cannot cancel completed task');
            vi.mocked(api.post).mockRejectedValue(error);

            await expect(cancelTask(456)).rejects.toThrow('Cannot cancel completed task');
            expect(api.post).toHaveBeenCalledWith('/tasks/456/cancel');
        });
    });

    describe('getLatestTaskForTarget', () => {
        it('should fetch latest task for target', async () => {
            const mockTask: Task = {
                id: 789,
                project_id: 1,
                target_id: 5,
                type: 'crawl',
                status: 'completed',
                result: '{"found_links": 25}',
                created_at: '2026-01-03T00:00:00Z',
                updated_at: '2026-01-03T01:00:00Z',
                started_at: '2026-01-03T00:05:00Z',
                completed_at: '2026-01-03T01:00:00Z',
            };

            vi.mocked(api.get).mockResolvedValue(mockTask);
            const result = await getLatestTaskForTarget(5);

            expect(api.get).toHaveBeenCalledWith('/targets/5/latest-task');
            expect(result).toEqual(mockTask);
            expect(result.target_id).toBe(5);
        });

        it('should throw error when target has no tasks', async () => {
            const error = new Error('No tasks found for target');
            vi.mocked(api.get).mockRejectedValue(error);

            await expect(getLatestTaskForTarget(999)).rejects.toThrow('No tasks found for target');
            expect(api.get).toHaveBeenCalledWith('/targets/999/latest-task');
        });
    });
});
