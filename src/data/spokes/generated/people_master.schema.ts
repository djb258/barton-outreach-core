// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

import { z } from 'zod';

/**
 * Contact and executive data — 182,946 records. SUPPORTING table (ADR-020) for people sub-hub.
 * Table: people_master
 */
export const PeopleMasterSchema = z.object({
  unique_id: z.string(),
  first_name: z.string(),
  last_name: z.string(),
  email: z.string().nullable().optional(),
  email_verified: z.boolean().nullable().optional(),
  outreach_ready: z.boolean().nullable().optional(),
  linkedin_url: z.string().nullable().optional(),
});

export type PeopleMaster = z.infer<typeof PeopleMasterSchema>;
