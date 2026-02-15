// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

/**
 * Executive position slots per company — 285,012 slots, 177,757 filled (62.4%). CANONICAL table for people sub-hub.
 * Table: company_slot
 */
export interface CompanySlotRow {
  /** Primary key for the slot record */
  slot_id: string;
  /** FK to outreach.outreach spine table */
  outreach_id: string;
  /** Executive role type (CEO, CFO, HR, CTO, CMO, COO) */
  slot_type: string;
  /** Whether this slot has an assigned person (TRUE = people record linked) */
  is_filled?: boolean | null;
  /** FK to people.people_master.unique_id (Barton ID format 04.04.02.YY.NNNNNN.NNN) */
  person_unique_id?: string | null;
}
