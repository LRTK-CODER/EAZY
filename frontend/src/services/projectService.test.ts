import { describe, it, expect, vi, beforeEach } from 'vitest';
// @ts-expect-error - projectService.ts doesn't exist yet (TDD RED phase)
import {
    getProjects,
    getProject,
    createProject,
    updateProject,
    deleteProject,
    deleteProjects,
} from './projectService';
// @ts-expect-error - project types don't exist yet (TDD RED phase)
import type { Project, ProjectCreate, ProjectListParams } from '@/types/project';
import * as api from '@/lib/api';

// Mock the API module
vi.mock('@/lib/api');

describe('Project Service', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('getProjects', () => {
        it('should fetch projects list without parameters', async () => {
            const mockProjects: Project[] = [
                {
                    id: 1,
                    name: 'Test Project 1',
                    description: 'Description 1',
                    created_at: '2025-01-01T00:00:00Z',
                    updated_at: '2025-01-01T00:00:00Z',
                },
                {
                    id: 2,
                    name: 'Test Project 2',
                    description: 'Description 2',
                    created_at: '2025-01-01T00:00:00Z',
                    updated_at: '2025-01-01T00:00:00Z',
                },
            ];

            vi.mocked(api.get).mockResolvedValue(mockProjects);

            const result = await getProjects();

            expect(api.get).toHaveBeenCalledWith('/projects/');
            expect(result).toEqual(mockProjects);
        });

        it('should fetch projects list with skip parameter', async () => {
            const mockProjects: Project[] = [
                {
                    id: 3,
                    name: 'Test Project 3',
                    description: null,
                    created_at: '2025-01-01T00:00:00Z',
                    updated_at: '2025-01-01T00:00:00Z',
                },
            ];

            vi.mocked(api.get).mockResolvedValue(mockProjects);

            const params: ProjectListParams = { skip: 10 };
            const result = await getProjects(params);

            expect(api.get).toHaveBeenCalledWith('/projects/?skip=10');
            expect(result).toEqual(mockProjects);
        });

        it('should fetch projects list with limit parameter', async () => {
            const mockProjects: Project[] = [];

            vi.mocked(api.get).mockResolvedValue(mockProjects);

            const params: ProjectListParams = { limit: 5 };
            const result = await getProjects(params);

            expect(api.get).toHaveBeenCalledWith('/projects/?limit=5');
            expect(result).toEqual(mockProjects);
        });

        it('should fetch projects list with both skip and limit parameters', async () => {
            const mockProjects: Project[] = [
                {
                    id: 1,
                    name: 'Test Project',
                    description: null,
                    created_at: '2025-01-01T00:00:00Z',
                    updated_at: '2025-01-01T00:00:00Z',
                },
            ];

            vi.mocked(api.get).mockResolvedValue(mockProjects);

            const params: ProjectListParams = { skip: 10, limit: 5 };
            const result = await getProjects(params);

            expect(api.get).toHaveBeenCalledWith('/projects/?skip=10&limit=5');
            expect(result).toEqual(mockProjects);
        });

        it('should handle API error', async () => {
            const error = new Error('Network error');
            vi.mocked(api.get).mockRejectedValue(error);

            await expect(getProjects()).rejects.toThrow('Network error');
        });
    });

    describe('getProject', () => {
        it('should fetch a single project by id', async () => {
            const mockProject: Project = {
                id: 1,
                name: 'Test Project',
                description: 'Test Description',
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
            };

            vi.mocked(api.get).mockResolvedValue(mockProject);

            const result = await getProject(1);

            expect(api.get).toHaveBeenCalledWith('/projects/1');
            expect(result).toEqual(mockProject);
        });

        it('should handle 404 error when project not found', async () => {
            const error = new Error('Project not found');
            vi.mocked(api.get).mockRejectedValue(error);

            await expect(getProject(999)).rejects.toThrow('Project not found');
        });
    });

    describe('createProject', () => {
        it('should create a new project with name and description', async () => {
            const projectData: ProjectCreate = {
                name: 'New Project',
                description: 'New Description',
            };

            const mockResponse: Project = {
                id: 1,
                name: 'New Project',
                description: 'New Description',
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
            };

            vi.mocked(api.post).mockResolvedValue(mockResponse);

            const result = await createProject(projectData);

            expect(api.post).toHaveBeenCalledWith('/projects/', projectData);
            expect(result).toEqual(mockResponse);
        });

        it('should create a new project with only name', async () => {
            const projectData: ProjectCreate = {
                name: 'New Project',
            };

            const mockResponse: Project = {
                id: 1,
                name: 'New Project',
                description: null,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
            };

            vi.mocked(api.post).mockResolvedValue(mockResponse);

            const result = await createProject(projectData);

            expect(api.post).toHaveBeenCalledWith('/projects/', projectData);
            expect(result).toEqual(mockResponse);
        });

        it('should handle validation error (422)', async () => {
            const projectData: ProjectCreate = {
                name: '',
            };

            const error = new Error('Validation error');
            vi.mocked(api.post).mockRejectedValue(error);

            await expect(createProject(projectData)).rejects.toThrow('Validation error');
        });
    });

    describe('updateProject', () => {
        it('should update an existing project', async () => {
            const projectId = 1;
            const updateData: ProjectCreate = {
                name: 'Updated Project',
                description: 'Updated Description',
            };

            const mockResponse: Project = {
                id: projectId,
                name: 'Updated Project',
                description: 'Updated Description',
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T12:00:00Z',
            };

            vi.mocked(api.put).mockResolvedValue(mockResponse);

            const result = await updateProject(projectId, updateData);

            expect(api.put).toHaveBeenCalledWith(`/projects/${projectId}`, updateData);
            expect(result).toEqual(mockResponse);
        });

        it('should handle 404 error when updating non-existent project', async () => {
            const projectId = 999;
            const updateData: ProjectCreate = {
                name: 'Updated Project',
            };

            const error = new Error('Project not found');
            vi.mocked(api.put).mockRejectedValue(error);

            await expect(updateProject(projectId, updateData)).rejects.toThrow('Project not found');
        });
    });

    describe('deleteProject', () => {
        it('should delete a project by id', async () => {
            const projectId = 1;

            vi.mocked(api.del).mockResolvedValue(undefined);

            await deleteProject(projectId);

            expect(api.del).toHaveBeenCalledWith(`/projects/${projectId}`);
        });

        it('should handle 404 error when deleting non-existent project', async () => {
            const projectId = 999;

            const error = new Error('Project not found');
            vi.mocked(api.del).mockRejectedValue(error);

            await expect(deleteProject(projectId)).rejects.toThrow('Project not found');
        });
    });

    describe('deleteProjects', () => {
        it('should delete multiple projects by ids', async () => {
            const projectIds = [1, 2, 3];

            vi.mocked(api.del).mockResolvedValue(undefined);

            await deleteProjects(projectIds);

            // Should call delete for each project
            expect(api.del).toHaveBeenCalledTimes(3);
            expect(api.del).toHaveBeenNthCalledWith(1, '/projects/1');
            expect(api.del).toHaveBeenNthCalledWith(2, '/projects/2');
            expect(api.del).toHaveBeenNthCalledWith(3, '/projects/3');
        });

        it('should handle empty array', async () => {
            const projectIds: number[] = [];

            await deleteProjects(projectIds);

            expect(api.del).not.toHaveBeenCalled();
        });

        it('should continue deleting even if one fails', async () => {
            const projectIds = [1, 2, 3];

            // Second delete fails
            vi.mocked(api.del)
                .mockResolvedValueOnce(undefined)
                .mockRejectedValueOnce(new Error('Failed to delete'))
                .mockResolvedValueOnce(undefined);

            // Should not throw, but collect errors
            await expect(deleteProjects(projectIds)).rejects.toThrow();

            expect(api.del).toHaveBeenCalledTimes(3);
        });
    });
});
