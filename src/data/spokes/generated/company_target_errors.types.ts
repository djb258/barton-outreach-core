// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

/**
 * Error tracking for company target sub-hub
 * Table: company_target_errors
 */
export interface CompanyTargetErrorsRow {
  /** Primary key for error record */
  error_id: string;
  /** FK to spine (nullable — error may occur before entity exists) */
  outreach_id?: string | null;
  /** Discriminator column — classifies the error */
  error_type: string;
  /** Human-readable error description */
  error_message: string;
  /** When the error was recorded */
  created_at: string;
}
