// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

/**
 * Error tracking for people intelligence sub-hub
 * Table: people_errors
 */
export interface PeopleErrorsRow {
  /** Primary key for error record */
  error_id: string;
  /** FK to spine (nullable — error may occur before entity exists) */
  outreach_id?: string | null;
  /** Discriminator column (validation, ambiguity, conflict, missing_data, stale_data, external_fail) */
  error_type: string;
  /** Pipeline stage where error occurred (slot_creation, slot_fill, etc.) */
  error_stage?: string | null;
  /** Human-readable error description */
  error_message: string;
  /** How to handle retry (manual_fix, auto_retry, discard) */
  retry_strategy?: string | null;
  /** When the error was recorded */
  created_at: string;
}
