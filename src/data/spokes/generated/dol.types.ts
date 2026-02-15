// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

/**
 * DOL bridge table — links outreach companies to DOL Form 5500 filings via EIN. 70,150 records.
 * Table: dol
 */
export interface DolRow {
  /** FK to outreach.outreach spine table */
  outreach_id: string;
  /** Employer Identification Number (9-digit, no dashes) */
  ein: string;
  /** Whether a Form 5500 filing exists for this EIN */
  filing_present?: boolean | null;
  /** Benefit funding classification (pension_only, fully_insured, self_funded) */
  funding_type?: string | null;
  /** Plan year begin month (1-12) */
  renewal_month?: number | null;
  /** 5 months before renewal month (1-12) — when to begin outreach */
  outreach_start_month?: number | null;
}
