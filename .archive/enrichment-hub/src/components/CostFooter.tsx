import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { DollarSign, TrendingUp } from "lucide-react";

export const CostFooter = () => {
  const { data: costStats } = useQuery({
    queryKey: ["cost-stats"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("enrichment_log")
        .select("*")
        .order("created_at", { ascending: false })
        .limit(10);

      if (error) throw error;

      // Calculate totals
      const totalCost = data.reduce((sum, log) => sum + Number(log.cost || 0), 0);
      const totalSuccess = data.reduce((sum, log) => sum + (log.success_count || 0), 0);
      const totalRecords = data.reduce((sum, log) => sum + (log.total_count || 0), 0);
      const successRate = totalRecords > 0 ? ((totalSuccess / totalRecords) * 100).toFixed(1) : "0";

      // Group by tool
      const byTool = data.reduce((acc, log) => {
        if (!acc[log.tool]) {
          acc[log.tool] = { cost: 0, count: 0 };
        }
        acc[log.tool].cost += Number(log.cost || 0);
        acc[log.tool].count += 1;
        return acc;
      }, {} as Record<string, { cost: number; count: number }>);

      return {
        totalCost,
        successRate,
        byTool,
      };
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (!costStats) return null;

  return (
    <footer className="border-t bg-card mt-8">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium">Total Cost:</span>
            <span className="text-lg font-bold text-primary">
              ${costStats.totalCost.toFixed(2)}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-accent" />
            <span className="text-sm font-medium">Success Rate:</span>
            <span className="text-lg font-bold text-accent">{costStats.successRate}%</span>
          </div>

          <div className="flex items-center gap-4">
            {Object.entries(costStats.byTool).map(([tool, stats]) => (
              <div key={tool} className="text-sm">
                <span className="font-medium capitalize">{tool}:</span>{" "}
                <span className="text-muted-foreground">
                  ${stats.cost.toFixed(2)} ({stats.count} runs)
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
};
