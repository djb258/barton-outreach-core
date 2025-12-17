import { useQuery, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { useEffect } from "react";

export const useEnrichmentData = (
  entity: "people" | "companies",
  state: string,
  page: number,
  pageSize: number
) => {
  const queryClient = useQueryClient();
  const tableName =
    entity === "people" ? "people_needs_enrichment" : "company_needs_enrichment";

  // Fetch data
  const { data, isLoading } = useQuery({
    queryKey: [tableName, state, page],
    queryFn: async () => {
      const from = page * pageSize;
      const to = from + pageSize - 1;

      const { data, error } = await supabase
        .from(tableName)
        .select("*")
        .eq("state", state)
        .eq("validated", false)
        .order("updated_at", { ascending: false })
        .range(from, to);

      if (error) throw error;
      return data;
    },
  });

  // Fetch count
  const { data: count } = useQuery({
    queryKey: [tableName, state, "count"],
    queryFn: async () => {
      const { count, error } = await supabase
        .from(tableName)
        .select("*", { count: "exact", head: true })
        .eq("state", state)
        .eq("validated", false);

      if (error) throw error;
      return count;
    },
  });

  // Set up realtime subscription
  useEffect(() => {
    const channel = supabase
      .channel(`${tableName}-${state}`)
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: tableName,
          filter: `state=eq.${state}`,
        },
        () => {
          // Invalidate queries when data changes
          queryClient.invalidateQueries({ queryKey: [tableName, state] });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [tableName, state, queryClient]);

  return { data, isLoading, count };
};
