// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

/**
 * Contact and executive data — 182,946 records. SUPPORTING table (ADR-020) for people sub-hub.
 * Table: people_master
 */
export interface PeopleMasterRow {
  /** Barton person identifier (04.04.02.YY.NNNNNN.NNN format, immutable) */
  unique_id: string;
  /** Person first name from Hunter, Clay, or manual enrichment */
  first_name: string;
  /** Person last name from Hunter, Clay, or manual enrichment */
  last_name: string;
  /** Person email address */
  email?: string | null;
  /** Whether email was checked via Million Verifier (TRUE = checked) */
  email_verified?: boolean | null;
  /** Whether email is safe to send outreach (TRUE = VALID verified) */
  outreach_ready?: boolean | null;
  /** Person LinkedIn profile URL */
  linkedin_url?: string | null;
}
