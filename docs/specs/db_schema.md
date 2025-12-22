# **DB Schema**

This document serves as the **SINGLE SOURCE OF TRUTH** for the database schema.
All changes to the database structure must be reflected here first.

## **Overview**
- **DBMS**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migration Tool**: Alembic (To be configured)

## **Tables**

### 1. `projects`
Encapsulates a logical grouping of targets and configurations.

| Column | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | NO | PK | Primary Key |
| `name` | String | NO | | Unique Project Name |
| `description` | String | YES | | Optional description |
| `created_at` | DateTime | YES | `now()` | Creation timestamp |

### 2. `targets`
Represents a specific URL or asset to be scanned within a project.

| Column | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | NO | PK | Primary Key |
| `project_id` | Integer | NO | | FK -> `projects.id` |
| `name` | String | NO | | Target Name |
| `url` | String | NO | | Base URL of the target |
| `created_at` | DateTime | YES | `now()` | Creation timestamp |

### 3. `scan_jobs`
Tracks the execution of a scanning process.

| Column | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | NO | PK | Primary Key |
| `target_id` | Integer | NO | | FK -> `targets.id` |
| `status` | String | YES | `'pending'` | pending, running, completed, failed, stopped |
| `start_time` | DateTime | YES | `now()` | Execution start time |
| `end_time` | DateTime | YES | | Execution end time |
| `stats` | JSON | YES | `{}` | Summary statistics (pages visited, etc.) |

### 4. `endpoints`
Discovered API endpoints or pages during a scan.

| Column | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | NO | PK | Primary Key |
| `target_id` | Integer | NO | | FK -> `targets.id` |
| `method` | String | NO | | HTTP Method (GET, POST, etc.) |
| `path` | String | NO | | URL Path |
| `source` | String | YES | | Discovery source (network, html_form, etc.) |
| `description` | Text | YES | | Optional description |
| `spec_hash` | String | YES | | Hash for deduplication |
| `created_at` | DateTime | YES | `now()` | Discovery timestamp |
| `updated_at` | DateTime | YES | | Last update timestamp |

### 5. `parameters`
Input parameters associated with an endpoint.

| Column | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | NO | PK | Primary Key |
| `endpoint_id` | Integer | NO | | FK -> `endpoints.id` |
| `name` | String | NO | | Parameter Name |
| `location` | String | NO | | query, path, body, header |
| `type` | String | YES | | projected data type |

### 6. `api_keys`
Stores credentials for external services (LLMs, etc.).

| Column | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | NO | PK | Primary Key |
| `name` | String | NO | | User-friendly alias |
| `provider` | String | NO | | e.g., "openai", "anthropic" |
| `category` | String | NO | `'LLM'` | e.g., "LLM", "MCP" |
| `key` | String | NO | | Encrypted API Key |
| `api_base` | String | YES | | Optional custom base URL |
| `created_at` | DateTime | YES | `now()` | Creation timestamp |
| `updated_at` | DateTime | YES | | Last update timestamp |

### 7. `llm_configs`
Project-specific LLM settings.

| Column | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | NO | PK | Primary Key |
| `project_id` | Integer | NO | | FK -> `projects.id` (Unique) |
| `api_key_id` | Integer | YES | | FK -> `api_keys.id` |
| `model_name` | String | NO | | e.g., "gpt-4o" |
| `created_at` | DateTime | YES | `now()` | Creation timestamp |
| `updated_at` | DateTime | YES | | Last update timestamp |

## **Relationships**

*   **Project 1:N Target**: A project can have multiple targets.
*   **Project 1:1 LLMConfig**: A project has one LLM configuration.
*   **Target 1:N ScanJob**: A target can be scanned multiple times.
*   **Target 1:N Endpoint**: A target has multiple discovered endpoints.
*   **Endpoint 1:N Parameter**: An endpoint can have multiple parameters.
*   **ScanJob M:N Endpoint**: Junction table `scan_job_endpoints` tracks which endpoints were found in a specific scan.
