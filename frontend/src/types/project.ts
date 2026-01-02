/**
 * Project entity returned from the backend API
 */
export interface Project {
  id: number;
  name: string;
  description: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Data required to create a new project
 */
export interface ProjectCreate {
  name: string;
  description?: string;
}

/**
 * Data required to update an existing project
 * Same structure as ProjectCreate
 */
export type ProjectUpdate = ProjectCreate;

/**
 * Query parameters for fetching projects list
 */
export interface ProjectListParams {
  skip?: number;
  limit?: number;
}
