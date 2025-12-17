import { supabase } from "@/integrations/supabase/client";

// Neon tables are accessed via the same Supabase/Postgres connection
// since Supabase can connect to external Postgres databases

export interface NeonPerson {
  unique_id: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  email?: string;
  linkedin_url?: string;
  title?: string;
  state?: string;
  validated?: boolean;
}

export interface NeonCompany {
  unique_id: string;
  company_name?: string;
  website?: string;
  linkedin_url?: string;
  industry?: string;
  hq_city?: string;
  state?: string;
  validated?: boolean;
}

export async function fetchValidatedPeople(
  state: string,
  limit: number = 100
): Promise<NeonPerson[]> {
  // In a real implementation, this would query the Neon database
  // For now, we'll use Supabase as a placeholder
  const { data, error } = await supabase
    .from("people_needs_enrichment")
    .select("*")
    .eq("validated", true)
    .eq("state", state)
    .limit(limit);

  if (error) throw error;
  return data || [];
}

export async function fetchValidatedCompanies(
  state: string,
  limit: number = 100
): Promise<NeonCompany[]> {
  // In a real implementation, this would query the Neon database
  // For now, we'll use Supabase as a placeholder
  const { data, error } = await supabase
    .from("company_needs_enrichment")
    .select("*")
    .eq("validated", true)
    .eq("state", state)
    .limit(limit);

  if (error) throw error;
  return data || [];
}
