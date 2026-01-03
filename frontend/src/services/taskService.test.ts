import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getTaskStatus } from './taskService';
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
});
