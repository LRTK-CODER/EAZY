import * as api from '@/lib/api';
import type { Project, ProjectCreate, ProjectListParams } from '@/types/project';

/**
 * Fetch list of projects with optional pagination
 */
export const getProjects = async (params?: ProjectListParams): Promise<Project[]> => {
  let url = '/projects/';

  if (params) {
    const queryParams = new URLSearchParams();
    if (params.skip !== undefined) {
      queryParams.append('skip', params.skip.toString());
    }
    if (params.limit !== undefined) {
      queryParams.append('limit', params.limit.toString());
    }

    const queryString = queryParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  return api.get<Project[]>(url);
};

/**
 * Fetch a single project by ID
 */
export const getProject = async (id: number): Promise<Project> => {
  return api.get<Project>(`/projects/${id}`);
};

/**
 * Create a new project
 */
export const createProject = async (data: ProjectCreate): Promise<Project> => {
  return api.post<Project>('/projects/', data);
};

/**
 * Update an existing project
 */
export const updateProject = async (id: number, data: ProjectCreate): Promise<Project> => {
  return api.put<Project>(`/projects/${id}`, data);
};

/**
 * Delete a single project by ID
 */
export const deleteProject = async (id: number): Promise<void> => {
  return api.del<void>(`/projects/${id}`);
};

/**
 * Delete multiple projects by IDs
 * Attempts to delete all projects, throws if any fail
 */
export const deleteProjects = async (ids: number[]): Promise<void> => {
  if (ids.length === 0) {
    return;
  }

  const deletePromises = ids.map(id => api.del(`/projects/${id}`));

  // Wait for all deletions, but throw if any fail
  await Promise.all(deletePromises);
};
