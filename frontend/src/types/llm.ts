export interface ApiKey {
    id: number;
    name: string;
    provider: string; // "openai", "anthropic"
    api_base?: string;
    created_at: string;
}

export interface ApiKeyCreateRequest {
    name: string;
    provider: string;
    key: string;
    api_base?: string;
}

export interface LLMConfig {
    id: number;
    project_id: number;
    api_key_id: number;
    model_name: string;
    created_at: string;
    updated_at?: string;
}

export interface LLMConfigCreateRequest {
    api_key_id: number;
    model_name: string;
}
