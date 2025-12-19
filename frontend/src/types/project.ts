export interface Project {
    id: number;
    name: string;
    description?: string;
    created_at: string;
}

export interface ProjectCreateRequest {
    name: string;
    description?: string;
}
