// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

/**
 * Error tracking for BIT/CLS scoring sub-hub
 * Table: bit_errors
 */
export interface BitErrorsRow {
  /** Primary key for error record */
  error_id: string;
  /** FK to spine (nullable — error may occur before entity exists) */
  outreach_id?: string | null;
  /** Discriminator column — classifies the scoring error */
  error_type: string;
  /** Human-readable error description */
  error_message: string;
  /** When the error was recorded */
  created_at: string;
}
