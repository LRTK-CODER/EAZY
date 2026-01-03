import * as api from '@/lib/api';
import type { Target, TargetCreate, TargetUpdate, TargetListParams, ScanTriggerResponse } from '@/types/target';

/**
 * Fetch list of targets for a project with optional pagination
 */
export const getTargets = async (projectId: number, params?: TargetListParams): Promise<Target[]> => {
  const url = `/projects/${projectId}/targets/`;

  if (params) {
    return api.get<Target[]>(url, params);
  }

  return api.get<Target[]>(url);
};

/**
 * Fetch a single target by ID
 */
export const getTarget = async (projectId: number, targetId: number): Promise<Target> => {
  return api.get<Target>(`/projects/${projectId}/targets/${targetId}`);
};

/**
 * Create a new target for a project
 */
export const createTarget = async (projectId: number, data: TargetCreate): Promise<Target> => {
  return api.post<Target>(`/projects/${projectId}/targets/`, data);
};

/**
 * Update an existing target
 */
export const updateTarget = async (projectId: number, targetId: number, data: TargetUpdate): Promise<Target> => {
  return api.patch<Target>(`/projects/${projectId}/targets/${targetId}`, data);
};

/**
 * Delete a target by ID
 */
export const deleteTarget = async (projectId: number, targetId: number): Promise<void> => {
  return api.del<void>(`/projects/${projectId}/targets/${targetId}`);
};

/**
 * Trigger a scan task for a target
 */
export const triggerScan = async (projectId: number, targetId: number): Promise<ScanTriggerResponse> => {
  return api.post<ScanTriggerResponse>(`/projects/${projectId}/targets/${targetId}/scan`);
};
