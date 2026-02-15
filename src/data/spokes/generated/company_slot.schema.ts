// AUTO-GENERATED FROM column_registry.yml — DO NOT EDIT

import { z } from 'zod';

/**
 * Executive position slots per company — 285,012 slots, 177,757 filled (62.4%). CANONICAL table for people sub-hub.
 * Table: company_slot
 */
export const CompanySlotSchema = z.object({
  slot_id: z.string().uuid(),
  outreach_id: z.string().uuid(),
  slot_type: z.string(),
  is_filled: z.boolean().nullable().optional(),
  person_unique_id: z.string().nullable().optional(),
});

export type CompanySlot = z.infer<typeof CompanySlotSchema>;
