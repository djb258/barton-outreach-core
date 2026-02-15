// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

import { z } from 'zod';

/**
 * Operational spine — all sub-hubs FK to outreach_id. Mints outreach_id, registers in CL.
 * Table: outreach
 */
export const OutreachSchema = z.object({
  outreach_id: z.string().uuid(),
  sovereign_company_id: z.string().uuid(),
  status: z.string(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});

export type Outreach = z.infer<typeof OutreachSchema>;
