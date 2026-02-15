// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

import { z } from 'zod';

/**
 * Error tracking for BIT/CLS scoring sub-hub
 * Table: bit_errors
 */
export const BitErrorsSchema = z.object({
  error_id: z.string().uuid(),
  outreach_id: z.string().uuid().nullable().optional(),
  error_type: z.string(),
  error_message: z.string(),
  created_at: z.string().datetime(),
});

export type BitErrors = z.infer<typeof BitErrorsSchema>;
