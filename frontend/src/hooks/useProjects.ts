import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as projectService from '@/services/projectService';
import type { Project, ProjectCreate, ProjectListParams } from '@/types/project';

/**
 * Query key factory for projects
 * Provides consistent query keys for caching and invalidation
 */
export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (params?: ProjectListParams) => [...projectKeys.lists(), params] as const,
  archived: (params?: ProjectListParams) => [...projectKeys.all, 'archived', params] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: number) => [...projectKeys.details(), id] as const,
};

/**
 * Hook to fetch list of projects with optional pagination
 */
export const useProjects = (params?: ProjectListParams, enabled = true) => {
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: () => projectService.getProjects(params),
    enabled,
  });
};

/**
 * Hook to fetch a single project by ID
 */
export const useProject = (id: number) => {
  return useQuery({
    queryKey: projectKeys.detail(id),
    queryFn: () => projectService.getProject(id),
    enabled: !!id, // Only run query if id is truthy
  });
};

/**
 * Hook to create a new project
 */
export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ProjectCreate) => projectService.createProject(data),
    onSuccess: () => {
      // Invalidate all project lists to refetch
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
    },
  });
};

/**
 * Hook to update an existing project
 */
export const useUpdateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ProjectCreate }) =>
      projectService.updateProject(id, data),
    onSuccess: (updatedProject: Project) => {
      // Invalidate the specific project detail
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(updatedProject.id) });
      // Invalidate all project lists
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
    },
  });
};

/**
 * Hook to delete a single project
 */
export const useDeleteProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => projectService.deleteProject(id),
    onSuccess: () => {
      // Invalidate all project queries to refetch
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
};

/**
 * Hook to delete multiple projects
 */
export const useDeleteProjects = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) => projectService.deleteProjects(ids),
    onSuccess: () => {
      // Invalidate all project queries to refetch
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
};

/**
 * Hook to fetch archived projects
 */
export const useArchivedProjects = (params?: ProjectListParams) => {
  return useQuery({
    queryKey: projectKeys.archived(params),
    queryFn: () => projectService.getArchivedProjects(params),
  });
};

/**
 * Hook to restore a single archived project
 */
export const useRestoreProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => projectService.restoreProject(id),
    onSuccess: () => {
      // Invalidate all project queries to refetch
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
};

/**
 * Hook to restore multiple archived projects
 */
export const useRestoreProjects = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) => projectService.restoreProjects(ids),
    onSuccess: () => {
      // Invalidate all project queries to refetch
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
};

/**
 * Hook to permanently delete a project
 */
export const useDeletePermanent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => projectService.deletePermanent(id),
    onSuccess: () => {
      // Invalidate all project queries to refetch
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
};

/**
 * Hook to permanently delete multiple projects
 */
export const useDeletePermanentBulk = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) => projectService.deletePermanentBulk(ids),
    onSuccess: () => {
      // Invalidate all project queries to refetch
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
};
