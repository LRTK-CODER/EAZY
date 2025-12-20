export interface ScanJob {
    id: number;
    target_id: number;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped';
    start_time: string;
    end_time?: string;
    stats: {
        pages_visited: number;
        queue_size: number;
        endpoints_found: number;
    };
    endpoints?: CrawledEndpoint[];
}

export interface CrawledEndpoint {
    method: string;
    url: string;
    parameters?: Array<{ name: string; type: string; location: string; value?: string }>;
    params?: Record<string, string>;
    source?: string;
    timestamp?: string;
    spec_hash?: string;
}

export interface CrawlerStats {
    pages_visited: number;
    queue_size: number;
    forms_found: number;
    endpoints_found: number;
}
