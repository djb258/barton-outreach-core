// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

import { z } from 'zod';

/**
 * DOL bridge table — links outreach companies to DOL Form 5500 filings via EIN. 70,150 records.
 * Table: dol
 */
export const DolSchema = z.object({
  outreach_id: z.string().uuid(),
  ein: z.string(),
  filing_present: z.boolean().nullable().optional(),
  funding_type: z.string().nullable().optional(),
  renewal_month: z.number().int().nullable().optional(),
  outreach_start_month: z.number().int().nullable().optional(),
});

export type Dol = z.infer<typeof DolSchema>;
