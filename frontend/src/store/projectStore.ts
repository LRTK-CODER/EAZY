import { create } from "zustand";
import { api } from "@/lib/api";
import type { Project, ProjectCreateRequest } from "@/types/project";

interface ProjectStore {
    projects: Project[];
    isLoading: boolean;
    error: string | null;
    fetchProjects: () => Promise<void>;
    createProject: (data: ProjectCreateRequest) => Promise<void>;
}

export const useProjectStore = create<ProjectStore>((set) => ({
    projects: [],
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
            throw error; // Re-throw for UI handling
        }
    },
}));
