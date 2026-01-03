import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
    getTargets,
    getTarget,
    createTarget,
    updateTarget,
    deleteTarget,
    triggerScan,
} from './targetService';
import type { Target, TargetCreate, TargetUpdate, TargetListParams } from '@/types/target';
import { TargetScope } from '@/types/target';
import * as api from '@/lib/api';

// Mock the API module
vi.mock('@/lib/api');

describe('Target Service', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('getTargets', () => {
        it('should fetch targets list without parameters', async () => {
            const mockTargets: Target[] = [
                {
                    id: 1,
                    project_id: 1,
                    name: 'example.com',
                    url: 'https://example.com',
                    description: 'Test target',
                    scope: TargetScope.DOMAIN,
                    created_at: '2025-01-01T00:00:00Z',
                    updated_at: '2025-01-01T00:00:00Z',
                },
                {
                    id: 2,
                    project_id: 1,
                    name: 'test.com',
                    url: 'https://test.com',
                    description: null,
                    scope: TargetScope.SUBDOMAIN,
                    created_at: '2025-01-01T00:00:00Z',
                    updated_at: '2025-01-01T00:00:00Z',
                },
            ];

            vi.mocked(api.get).mockResolvedValue(mockTargets);

            const result = await getTargets(1);

            expect(api.get).toHaveBeenCalledWith('/projects/1/targets/');
            expect(result).toEqual(mockTargets);
        });

        it('should fetch targets list with skip parameter', async () => {
            const mockTargets: Target[] = [
                {
                    id: 3,
                    project_id: 1,
                    name: 'skipped.com',
                    url: 'https://skipped.com',
                    description: null,
                    scope: TargetScope.URL_ONLY,
                    created_at: '2025-01-01T00:00:00Z',
                    updated_at: '2025-01-01T00:00:00Z',
                },
            ];

            vi.mocked(api.get).mockResolvedValue(mockTargets);

            const params: TargetListParams = { skip: 10 };
            const result = await getTargets(1, params);

            expect(api.get).toHaveBeenCalledWith('/projects/1/targets/', { skip: 10 });
            expect(result).toEqual(mockTargets);
        });

        it('should fetch targets list with limit parameter', async () => {
            const mockTargets: Target[] = [];

            vi.mocked(api.get).mockResolvedValue(mockTargets);

            const params: TargetListParams = { limit: 5 };
            const result = await getTargets(1, params);

            expect(api.get).toHaveBeenCalledWith('/projects/1/targets/', { limit: 5 });
            expect(result).toEqual(mockTargets);
        });

        it('should fetch targets list with both skip and limit parameters', async () => {
            const mockTargets: Target[] = [
                {
                    id: 1,
                    project_id: 1,
                    name: 'example.com',
                    url: 'https://example.com',
                    description: 'Test target',
                    scope: TargetScope.DOMAIN,
                    created_at: '2025-01-01T00:00:00Z',
                    updated_at: '2025-01-01T00:00:00Z',
                },
            ];

            vi.mocked(api.get).mockResolvedValue(mockTargets);

            const params: TargetListParams = { skip: 10, limit: 5 };
            const result = await getTargets(1, params);

            expect(api.get).toHaveBeenCalledWith('/projects/1/targets/', { skip: 10, limit: 5 });
            expect(result).toEqual(mockTargets);
        });
    });

    describe('getTarget', () => {
        it('should fetch a single target', async () => {
            const mockTarget: Target = {
                id: 1,
                project_id: 1,
                name: 'example.com',
                url: 'https://example.com',
                description: 'Test target',
                scope: 'DOMAIN',
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
            };

            vi.mocked(api.get).mockResolvedValue(mockTarget);

            const result = await getTarget(1, 1);

            expect(api.get).toHaveBeenCalledWith('/projects/1/targets/1');
            expect(result).toEqual(mockTarget);
        });

        it('should throw error when target not found', async () => {
            const error = new Error('Target not found');
            vi.mocked(api.get).mockRejectedValue(error);

            await expect(getTarget(1, 999)).rejects.toThrow('Target not found');
        });
    });

    describe('createTarget', () => {
        it('should create target with all fields', async () => {
            const newTarget: TargetCreate = {
                name: 'example.com',
                url: 'https://example.com',
                description: 'Test target',
                scope: 'DOMAIN',
            };

            const createdTarget: Target = {
                id: 1,
                project_id: 1,
                name: 'example.com',
                url: 'https://example.com',
                description: 'Test target',
                scope: 'DOMAIN',
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
            };

            vi.mocked(api.post).mockResolvedValue(createdTarget);

            const result = await createTarget(1, newTarget);

            expect(api.post).toHaveBeenCalledWith('/projects/1/targets/', newTarget);
            expect(result).toEqual(createdTarget);
        });

        it('should create target with required fields only', async () => {
            const newTarget: TargetCreate = {
                name: 'example.com',
                url: 'https://example.com',
            };

            const createdTarget: Target = {
                id: 1,
                project_id: 1,
                name: 'example.com',
                url: 'https://example.com',
                description: null,
                scope: 'DOMAIN',
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
            };

            vi.mocked(api.post).mockResolvedValue(createdTarget);

            const result = await createTarget(1, newTarget);

            expect(api.post).toHaveBeenCalledWith('/projects/1/targets/', newTarget);
            expect(result).toEqual(createdTarget);
        });

        it('should handle validation error', async () => {
            const newTarget: TargetCreate = {
                name: '',
                url: 'invalid-url',
            };

            const error = new Error('Validation error');
            vi.mocked(api.post).mockRejectedValue(error);

            await expect(createTarget(1, newTarget)).rejects.toThrow('Validation error');
        });
    });

    describe('updateTarget', () => {
        it('should update target', async () => {
            const updateData: TargetUpdate = {
                name: 'updated.com',
                description: 'Updated description',
            };

            const updatedTarget: Target = {
                id: 1,
                project_id: 1,
                name: 'updated.com',
                url: 'https://example.com',
                description: 'Updated description',
                scope: 'DOMAIN',
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
            };

            vi.mocked(api.patch).mockResolvedValue(updatedTarget);

            const result = await updateTarget(1, 1, updateData);

            expect(api.patch).toHaveBeenCalledWith('/projects/1/targets/1', updateData);
            expect(result).toEqual(updatedTarget);
        });

        it('should throw error when target not found', async () => {
            const updateData: TargetUpdate = {
                name: 'test',
            };

            const error = new Error('Target not found');
            vi.mocked(api.patch).mockRejectedValue(error);

            await expect(updateTarget(1, 999, updateData)).rejects.toThrow('Target not found');
        });
    });

    describe('deleteTarget', () => {
        it('should delete target', async () => {
            vi.mocked(api.del).mockResolvedValue(undefined);

            await deleteTarget(1, 1);

            expect(api.del).toHaveBeenCalledWith('/projects/1/targets/1');
            expect(api.del).toHaveBeenCalledTimes(1);
        });

        it('should throw error when target not found', async () => {
            const error = new Error('Target not found');
            vi.mocked(api.del).mockRejectedValue(error);

            await expect(deleteTarget(1, 999)).rejects.toThrow('Target not found');
        });
    });

    describe('triggerScan', () => {
        it('should trigger scan for target', async () => {
            const mockResponse = {
                status: 'pending',
                task_id: 123,
            };

            vi.mocked(api.post).mockResolvedValue(mockResponse);

            const result = await triggerScan(1, 1);

            expect(api.post).toHaveBeenCalledWith('/projects/1/targets/1/scan');
            expect(result).toEqual(mockResponse);
        });

        it('should throw error when target not found', async () => {
            const error = new Error('Target not found');
            vi.mocked(api.post).mockRejectedValue(error);

            await expect(triggerScan(1, 999)).rejects.toThrow('Target not found');
        });
    });
});
