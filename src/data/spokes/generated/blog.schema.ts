// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

import { z } from 'zod';

/**
 * Blog content signals per outreach company — 95,004 records
 * Table: blog
 */
export const BlogSchema = z.object({
  outreach_id: z.string().uuid(),
});

export type Blog = z.infer<typeof BlogSchema>;
