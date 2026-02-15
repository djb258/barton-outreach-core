// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

import { z } from 'zod';

/**
 * Authoritative company list for outreach — 95,837 records. Source of company identity within outreach hub.
 * Table: company_target
 */
export const CompanyTargetSchema = z.object({
  outreach_id: z.string().uuid(),
  company_unique_id: z.string(),
  source: z.string().nullable().optional(),
});

export type CompanyTarget = z.infer<typeof CompanyTargetSchema>;
