// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

/**
 * Operational spine — all sub-hubs FK to outreach_id. Mints outreach_id, registers in CL.
 * Table: outreach
 */
export interface OutreachRow {
  /** Universal join key — minted here, propagated to all sub-hub tables */
  outreach_id: string;
  /** FK to cl.company_identity — links outreach record to sovereign identity */
  sovereign_company_id: string;
  /** Workflow state of outreach lifecycle (INIT, ACTIVE, COMPLETED, ARCHIVED) */
  status: string;
  /** When the outreach record was created */
  created_at: string;
  /** When the outreach record was last updated */
  updated_at: string;
}
