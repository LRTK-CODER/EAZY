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
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: number) => [...projectKeys.details(), id] as const,
};

/**
 * Hook to fetch list of projects with optional pagination
 */
export const useProjects = (params?: ProjectListParams) => {
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: () => projectService.getProjects(params),
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
