/**
 * Task status enum - represents the current state of a task
 */
export const TaskStatus = {
  /** Task is queued and waiting to be executed */
  PENDING: "pending",
  /** Task is currently being executed */
  RUNNING: "running",
  /** Task has completed successfully */
  COMPLETED: "completed",
  /** Task has failed during execution */
  FAILED: "failed"
} as const;

/**
 * Task status type derived from TaskStatus values
 */
export type TaskStatus = typeof TaskStatus[keyof typeof TaskStatus];

/**
 * Task type enum - defines the type of task to be executed
 */
export const TaskType = {
  /** Web crawling task - discovers and maps website structure */
  CRAWL: "crawl",
  /** Security scanning task - performs vulnerability assessment */
  SCAN: "scan"
} as const;

/**
 * Task type derived from TaskType values
 */
export type TaskType = typeof TaskType[keyof typeof TaskType];

/**
 * Task entity returned from the backend API
 * Represents an asynchronous job for crawling or scanning
 */
export interface Task {
  /** Unique identifier for the task */
  id: number;
  /** ID of the project this task belongs to */
  project_id: number;
  /** ID of the target being processed (nullable - some tasks may not have a specific target) */
  target_id: number | null;
  /** Type of task (crawl or scan) */
  type: TaskType;
  /** Current status of the task */
  status: TaskStatus;
  /** JSON string containing task execution results (nullable until task completes) */
  result: string | null;
  /** ISO 8601 timestamp when the task was created */
  created_at: string;
  /** ISO 8601 timestamp when the task was last updated */
  updated_at: string;
}
