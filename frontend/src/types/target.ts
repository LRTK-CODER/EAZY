/**
 * Target scope enum - defines how far the crawler should explore from the target URL
 */
export const TargetScope = {
  /** Crawl only the specified domain */
  DOMAIN: "DOMAIN",
  /** Crawl domain and all subdomains */
  SUBDOMAIN: "SUBDOMAIN",
  /** Crawl only the exact URL provided */
  URL_ONLY: "URL_ONLY"
} as const;

/**
 * Target scope type derived from TargetScope values
 */
export type TargetScope = typeof TargetScope[keyof typeof TargetScope];

/**
 * Target entity returned from the backend API
 */
export interface Target {
  id: number;
  project_id: number;
  name: string;
  url: string;
  description: string | null;
  scope: TargetScope;
  created_at: string;
  updated_at: string;
}

/**
 * Data required to create a new target
 */
export interface TargetCreate {
  name: string;
  url: string;
  description?: string;
  scope?: TargetScope;
}

/**
 * Data required to update an existing target
 * All fields are optional
 */
export interface TargetUpdate {
  name?: string;
  url?: string;
  description?: string;
  scope?: TargetScope;
}

/**
 * Query parameters for fetching targets list
 */
export interface TargetListParams {
  skip?: number;
  limit?: number;
}

/**
 * Response returned when triggering a scan task
 */
export interface ScanTriggerResponse {
  status: string;
  task_id: number;
}
