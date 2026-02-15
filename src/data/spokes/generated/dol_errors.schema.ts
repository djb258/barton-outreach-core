// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

import { z } from 'zod';

/**
 * Error tracking for DOL filings sub-hub
 * Table: dol_errors
 */
export const DolErrorsSchema = z.object({
  error_id: z.string().uuid(),
  outreach_id: z.string().uuid().nullable().optional(),
  error_type: z.string(),
  error_message: z.string(),
  created_at: z.string().datetime(),
});

export type DolErrors = z.infer<typeof DolErrorsSchema>;
