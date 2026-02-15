// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

import { z } from 'zod';

/**
 * CLS authorization scores per company — 13,226 records
 * Table: bit_scores
 */
export const BitScoresSchema = z.object({
  outreach_id: z.string().uuid(),
});

export type BitScores = z.infer<typeof BitScoresSchema>;
