// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

import { z } from 'zod';

/**
 * Error tracking for people intelligence sub-hub
 * Table: people_errors
 */
export const PeopleErrorsSchema = z.object({
  error_id: z.string().uuid(),
  outreach_id: z.string().uuid().nullable().optional(),
  error_type: z.string(),
  error_stage: z.string().nullable().optional(),
  error_message: z.string(),
  retry_strategy: z.string().nullable().optional(),
  created_at: z.string().datetime(),
});

export type PeopleErrors = z.infer<typeof PeopleErrorsSchema>;
