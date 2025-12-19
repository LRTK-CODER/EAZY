import type { Target } from "./target";

export interface Project {
    id: number;
    name: string;
    description?: string;
    targets?: Target[];
    created_at: string;
}

export interface ProjectCreateRequest {
    name: string;
    description?: string;
}
