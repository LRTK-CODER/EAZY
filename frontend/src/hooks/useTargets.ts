import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as targetService from '@/services/targetService';
import type { Target, TargetCreate, TargetUpdate, TargetListParams } from '@/types/target';

/**
 * Query key factory for targets
 * Provides consistent query keys for caching and invalidation
 */
export const targetKeys = {
  all: (projectId: number) => ['targets', projectId] as const,
  lists: () => ['targets', 'list'] as const,
  list: (projectId: number, params?: TargetListParams) =>
    [...targetKeys.lists(), projectId, params] as const,
  details: () => ['targets', 'detail'] as const,
  detail: (projectId: number, targetId: number) =>
    [...targetKeys.details(), projectId, targetId] as const,
};

/**
 * Hook to fetch list of targets for a project with optional pagination
 */
export const useTargets = (projectId: number, params?: TargetListParams) => {
  return useQuery({
    queryKey: targetKeys.list(projectId, params),
    queryFn: () => targetService.getTargets(projectId, params),
    enabled: !!projectId, // Only run query if projectId is truthy
  });
};

/**
 * Hook to fetch a single target by ID
 */
export const useTarget = (projectId: number, targetId: number) => {
  return useQuery({
    queryKey: targetKeys.detail(projectId, targetId),
    queryFn: () => targetService.getTarget(projectId, targetId),
    enabled: !!projectId && !!targetId, // Only run query if both IDs are truthy
  });
};

/**
 * Hook to create a new target for a project
 */
export const useCreateTarget = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: number; data: TargetCreate }) =>
      targetService.createTarget(projectId, data),
    onSuccess: () => {
      // Invalidate all target lists to refetch
      queryClient.invalidateQueries({ queryKey: targetKeys.lists() });
    },
  });
};

/**
 * Hook to update an existing target
 */
export const useUpdateTarget = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, targetId, data }: { projectId: number; targetId: number; data: TargetUpdate }) =>
      targetService.updateTarget(projectId, targetId, data),
    onSuccess: (updatedTarget: Target) => {
      // Invalidate the specific target detail
      queryClient.invalidateQueries({
        queryKey: targetKeys.detail(updatedTarget.project_id, updatedTarget.id)
      });
      // Invalidate all target lists
      queryClient.invalidateQueries({ queryKey: targetKeys.lists() });
    },
  });
};

/**
 * Hook to delete a target by ID
 */
export const useDeleteTarget = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, targetId }: { projectId: number; targetId: number }) =>
      targetService.deleteTarget(projectId, targetId),
    onSuccess: (_data, variables) => {
      // Invalidate all target queries for this project
      queryClient.invalidateQueries({ queryKey: targetKeys.all(variables.projectId) });
    },
  });
};

/**
 * Hook to trigger a scan task for a target
 */
export const useTriggerScan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, targetId }: { projectId: number; targetId: number }) =>
      targetService.triggerScan(projectId, targetId),
    onSuccess: (_data, variables) => {
      // Invalidate the specific target detail to refetch updated scan status
      queryClient.invalidateQueries({
        queryKey: targetKeys.detail(variables.projectId, variables.targetId)
      });
    },
  });
};
