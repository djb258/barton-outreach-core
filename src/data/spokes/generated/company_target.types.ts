// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

/**
 * Authoritative company list for outreach — 95,837 records. Source of company identity within outreach hub.
 * Table: company_target
 */
export interface CompanyTargetRow {
  /** FK to outreach.outreach spine table */
  outreach_id: string;
  /** Barton company identifier (04.04.01.YY.NNNNNN format) */
  company_unique_id: string;
  /** CL source system that originated this company record */
  source?: string | null;
}
