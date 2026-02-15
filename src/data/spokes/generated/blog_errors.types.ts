// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

/**
 * Error tracking for blog content sub-hub
 * Table: blog_errors
 */
export interface BlogErrorsRow {
  /** Primary key for error record */
  error_id: string;
  /** FK to spine (nullable — error may occur before entity exists) */
  outreach_id?: string | null;
  /** Discriminator column — classifies the blog error (e.g., BLOG_MISSING) */
  error_type: string;
  /** Human-readable error description */
  error_message: string;
  /** When the error was recorded */
  created_at: string;
}
