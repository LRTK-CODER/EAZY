/**
 * Asset Types and Interfaces
 * Matches backend AssetRead schema exactly
 */

/**
 * Asset type enum - represents the type of attack surface
 */
export enum AssetType {
  /** URL endpoint */
  URL = 'url',
  /** HTML Form */
  FORM = 'form',
  /** XHR/Fetch API request */
  XHR = 'xhr'
}

/**
 * Asset source enum - where the asset was discovered
 */
export enum AssetSource {
  /** Found in HTML */
  HTML = 'html',
  /** Found in JavaScript */
  JS = 'js',
  /** Found via network monitoring */
  NETWORK = 'network',
  /** Found in DOM */
  DOM = 'dom'
}

/**
 * Asset entity returned from the backend API
 * Represents a discovered attack surface (URL, Form, or XHR endpoint)
 */
export interface Asset {
  /** Unique identifier */
  id: number;
  /** Target ID this asset belongs to */
  target_id: number;
  /** SHA256 content hash for deduplication (max 64 chars) */
  content_hash: string;
  /** Type of attack surface */
  type: AssetType;
  /** Discovery source */
  source: AssetSource;
  /** HTTP method (e.g., GET, POST) */
  method: string;
  /** Full URL (max 2048 chars) */
  url: string;
  /** URL path (max 2048 chars) */
  path: string;
  /** Request specification (JSONB) - headers, body, cookies */
  request_spec: Record<string, unknown> | null;
  /** Response specification (JSONB) - status, headers, body */
  response_spec: Record<string, unknown> | null;
  /** Parsed parameters (JSONB) - name, type, location, value */
  parameters: Record<string, unknown> | null;
  /** ID of the last task that discovered this asset */
  last_task_id: number | null;
  /** ISO 8601 datetime when first discovered */
  first_seen_at: string;
  /** ISO 8601 datetime when last seen */
  last_seen_at: string;
}
