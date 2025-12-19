export interface Target {
    id: number;
    project_id: number;
    name: string;
    url: string;
    created_at: string;
}

export interface TargetCreateRequest {
    name: string;
    url: string;
}
