import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Database, CheckCircle, DollarSign, TrendingUp } from "lucide-react";
import { useTableMetrics } from "@/hooks/useTableMetrics";
import { ComponentId } from "@/components/ComponentId";

export const MetricsHeader = () => {
  const { metrics, isLoading } = useTableMetrics();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <ComponentId id="metrics-pending-card" type="card">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Enrichment</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalPendingEnrichment}</div>
            <p className="text-xs text-muted-foreground">Records awaiting enrichment</p>
          </CardContent>
        </Card>
      </ComponentId>

      <ComponentId id="metrics-validated-card" type="card">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Validated Records</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalValidated}</div>
            <p className="text-xs text-muted-foreground">Total in people_master</p>
          </CardContent>
        </Card>
      </ComponentId>

      <ComponentId id="metrics-cost-card" type="card">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Enrichment Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${metrics.avgEnrichmentCost.toFixed(4)}</div>
            <p className="text-xs text-muted-foreground">Per enrichment operation</p>
          </CardContent>
        </Card>
      </ComponentId>

      <ComponentId id="metrics-monthly-card" type="card">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Updates</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.monthlyChanges}</div>
            <p className="text-xs text-muted-foreground">Changes promoted this period</p>
          </CardContent>
        </Card>
      </ComponentId>
    </div>
  );
};
