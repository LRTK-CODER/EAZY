import { create } from "zustand";
import { api } from "@/lib/api";
import type { Project, ProjectCreateRequest } from "@/types/project";
import type { Target, TargetCreateRequest } from "@/types/target";
import type { ApiKey, ApiKeyCreateRequest, LLMConfig, LLMConfigCreateRequest } from "@/types/llm";

interface ProjectStore {
    projects: Project[];
    targets: Target[];
    currentLLMConfig: LLMConfig | null;
    apiKeys: ApiKey[];
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
    fetchLLMConfig: (projectId: number) => Promise<void>;
    upsertLLMConfig: (projectId: number, data: LLMConfigCreateRequest) => Promise<void>;
    fetchApiKeys: () => Promise<void>;
    createApiKey: (data: ApiKeyCreateRequest) => Promise<void>;
    deleteApiKey: (id: number) => Promise<void>;
}

export const useProjectStore = create<ProjectStore>((set) => ({
    projects: [],
    targets: [],
    currentLLMConfig: null,
    apiKeys: [],
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

    fetchLLMConfig: async (projectId: number) => {
        set({ isLoading: true, error: null, currentLLMConfig: null });
        try {
            const response = await api.get<LLMConfig>(`/projects/${projectId}/llm-config`);
            set({ currentLLMConfig: response.data, isLoading: false });
        } catch (error: any) {
            // 404 is expected if config not exists
            if (error.response?.status === 404) {
                set({ currentLLMConfig: null, isLoading: false });
            } else {
                set({ isLoading: false, error: "Failed to fetch LLM config" });
                console.error(error);
            }
        }
    },

    upsertLLMConfig: async (projectId: number, data: LLMConfigCreateRequest) => {
        set({ isLoading: true, error: null });
        try {
            await api.post<LLMConfig>(`/projects/${projectId}/llm-config`, data);
            await useProjectStore.getState().fetchLLMConfig(projectId);
        } catch (error) {
            set({ isLoading: false, error: "Failed to save LLM config" });
            console.error(error);
            throw error;
        }
    },

    fetchApiKeys: async () => {
        // Don't set global loading true to avoid flickering whole page if used in dialog
        try {
            const response = await api.get<ApiKey[]>(`/api-keys/`);
            set({ apiKeys: response.data });
        } catch (error) {
            console.error("Failed to fetch API keys", error);
        }
    },

    createApiKey: async (data: ApiKeyCreateRequest) => {
        set({ isLoading: true, error: null });
        try {
            await api.post<ApiKey>(`/api-keys/`, data);
            await useProjectStore.getState().fetchApiKeys();
            set({ isLoading: false });
        } catch (error) {
            set({ isLoading: false, error: "Failed to create API key" });
            console.error(error);
            throw error;
        }
    },

    deleteApiKey: async (id: number) => {
        set({ isLoading: true, error: null });
        try {
            await api.delete(`/api-keys/${id}`);
            await useProjectStore.getState().fetchApiKeys();
            set({ isLoading: false });
        } catch (error) {
            set({ isLoading: false, error: "Failed to delete API key" });
            console.error(error);
            throw error;
        }
    },
}));
