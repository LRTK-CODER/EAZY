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
  return api.patch<Project>(`/projects/${id}`, data);
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

/**
 * Fetch archived projects
 */
export const getArchivedProjects = async (params?: ProjectListParams): Promise<Project[]> => {
  let url = '/projects/?archived=true';

  if (params) {
    const queryParams = new URLSearchParams();
    queryParams.append('archived', 'true');
    if (params.skip !== undefined) {
      queryParams.append('skip', params.skip.toString());
    }
    if (params.limit !== undefined) {
      queryParams.append('limit', params.limit.toString());
    }
    url = `/projects/?${queryParams.toString()}`;
  }

  return api.get<Project[]>(url);
};

/**
 * Permanently delete a project (hard delete)
 * Used only in Archived page
 */
export const deletePermanent = async (id: number): Promise<void> => {
  return api.del<void>(`/projects/${id}?permanent=true`);
};

/**
 * Restore an archived project
 */
export const restoreProject = async (id: number): Promise<void> => {
  return api.patch<void>(`/projects/${id}/restore`);
};

/**
 * Bulk restore projects
 */
export const restoreProjects = async (ids: number[]): Promise<void> => {
  if (ids.length === 0) return;
  const restorePromises = ids.map(id => api.patch(`/projects/${id}/restore`));
  await Promise.all(restorePromises);
};

/**
 * Bulk permanent delete projects
 */
export const deletePermanentBulk = async (ids: number[]): Promise<void> => {
  if (ids.length === 0) return;
  const deletePromises = ids.map(id => api.del(`/projects/${id}?permanent=true`));
  await Promise.all(deletePromises);
};
