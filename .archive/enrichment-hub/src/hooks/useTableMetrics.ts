import { useEffect, useState } from "react";
import { supabase } from "@/integrations/supabase/client";

export interface TableMetrics {
  totalPendingEnrichment: number;
  totalValidated: number;
  avgEnrichmentCost: number;
  monthlyChanges: number;
}

export const useTableMetrics = () => {
  const [metrics, setMetrics] = useState<TableMetrics>({
    totalPendingEnrichment: 0,
    totalValidated: 0,
    avgEnrichmentCost: 0,
    monthlyChanges: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      setIsLoading(true);
      try {
        // Count pending enrichment (people)
        const { count: peopleCount } = await supabase
          .from("people_needs_enrichment")
          .select("*", { count: "exact", head: true });

        // Count pending enrichment (companies)
        const { count: companyCount } = await supabase
          .from("company_needs_enrichment")
          .select("*", { count: "exact", head: true });

        // Count validated records (people_master)
        const { count: validatedCount } = await supabase
          .from("people_master" as any)
          .select("*", { count: "exact", head: true });

        // Average enrichment cost
        const { data: costData } = await supabase
          .from("enrichment_log")
          .select("cost");

        const avgCost =
          costData && costData.length > 0
            ? costData.reduce((sum, row) => sum + (row.cost || 0), 0) / costData.length
            : 0;

        // Monthly changes count
        const { count: monthlyCount } = await supabase
          .from("monthly_update_log")
          .select("*", { count: "exact", head: true });

        setMetrics({
          totalPendingEnrichment: (peopleCount || 0) + (companyCount || 0),
          totalValidated: validatedCount || 0,
          avgEnrichmentCost: avgCost,
          monthlyChanges: monthlyCount || 0,
        });
      } catch (error) {
        console.error("Error fetching metrics:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  return { metrics, isLoading };
};
