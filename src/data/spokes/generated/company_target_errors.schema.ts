// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

import { z } from 'zod';

/**
 * Error tracking for company target sub-hub
 * Table: company_target_errors
 */
export const CompanyTargetErrorsSchema = z.object({
  error_id: z.string().uuid(),
  outreach_id: z.string().uuid().nullable().optional(),
  error_type: z.string(),
  error_message: z.string(),
  created_at: z.string().datetime(),
});

export type CompanyTargetErrors = z.infer<typeof CompanyTargetErrorsSchema>;
