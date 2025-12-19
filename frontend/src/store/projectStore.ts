import { create } from "zustand";
import { api } from "@/lib/api";
import type { Project, ProjectCreateRequest } from "@/types/project";
import type { Target, TargetCreateRequest } from "@/types/target";

interface ProjectStore {
    projects: Project[];
    targets: Target[]; // Current project's targets
    isLoading: boolean;
    error: string | null;
    fetchProjects: () => Promise<void>;
    createProject: (data: ProjectCreateRequest) => Promise<void>;
    updateProject: (id: number, data: ProjectCreateRequest) => Promise<void>;
    deleteProject: (id: number) => Promise<void>;
    fetchTargets: (projectId: number) => Promise<void>;
    createTarget: (projectId: number, data: TargetCreateRequest) => Promise<void>;
    updateTarget: (projectId: number, targetId: number, data: TargetCreateRequest) => Promise<void>;
    deleteTarget: (projectId: number, targetId: number) => Promise<void>;
}

export const useProjectStore = create<ProjectStore>((set) => ({
    projects: [],
    targets: [],
    isLoading: false,
    error: null,

    fetchProjects: async () => {
        set({ isLoading: true, error: null });
        try {
            const response = await api.get<Project[]>("/projects/");
            set({ projects: response.data, isLoading: false });
        } catch (error) {
            set({ isLoading: false, error: "Failed to fetch projects" });
            console.error(error);
        }
    },

    createProject: async (data: ProjectCreateRequest) => {
        set({ isLoading: true, error: null });
        try {
            await api.post<Project>("/projects/", data);
            await useProjectStore.getState().fetchProjects(); // Refresh list
        } catch (error) {
            set({ isLoading: false, error: "Failed to create project" });
            console.error(error);
            throw error;
        }
    },

    updateProject: async (id: number, data: ProjectCreateRequest) => {
        set({ isLoading: true, error: null });
        try {
            await api.put<Project>(`/projects/${id}`, data);
            await useProjectStore.getState().fetchProjects();
        } catch (error) {
            set({ isLoading: false, error: "Failed to update project" });
            console.error(error);
            throw error;
        }
    },

    deleteProject: async (id: number) => {
        set({ isLoading: true, error: null });
        try {
            await api.delete(`/projects/${id}`);
            await useProjectStore.getState().fetchProjects();
        } catch (error) {
            set({ isLoading: false, error: "Failed to delete project" });
            console.error(error);
            throw error;
        }
    },

    fetchTargets: async (projectId: number) => {
        set({ isLoading: true, error: null });
        try {
            const response = await api.get<Target[]>(`/projects/${projectId}/targets`);
            set({ targets: response.data, isLoading: false });
        } catch (error) {
            set({ isLoading: false, error: "Failed to fetch targets" });
            console.error(error);
        }
    },

    createTarget: async (projectId: number, data: TargetCreateRequest) => {
        set({ isLoading: true, error: null });
        try {
            await api.post<Target>(`/projects/${projectId}/targets`, data);
            await useProjectStore.getState().fetchTargets(projectId);
        } catch (error) {
            set({ isLoading: false, error: "Failed to create target" });
            console.error(error);
            throw error;
        }
    },

    updateTarget: async (projectId: number, targetId: number, data: TargetCreateRequest) => {
        set({ isLoading: true, error: null });
        try {
            await api.put<Target>(`/projects/${projectId}/targets/${targetId}`, data);
            await useProjectStore.getState().fetchTargets(projectId);
        } catch (error) {
            set({ isLoading: false, error: "Failed to update target" });
            console.error(error);
            throw error;
        }
    },

    deleteTarget: async (projectId: number, targetId: number) => {
        set({ isLoading: true, error: null });
        try {
            await api.delete(`/projects/${projectId}/targets/${targetId}`);
            await useProjectStore.getState().fetchTargets(projectId);
        } catch (error) {
            set({ isLoading: false, error: "Failed to delete target" });
            console.error(error);
            throw error;
        }
    },
}));
