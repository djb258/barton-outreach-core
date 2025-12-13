import { useEffect, useState } from "react";
import { format } from "date-fns";
import { CalendarIcon, RefreshCw } from "lucide-react";
import { fetchFromMCP } from "@/lib/mcpClient";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { DualTrendChart } from "@/components/Charts/DualTrendChart";
import { DoctrineHeatmap } from "@/components/Charts/DoctrineHeatmap";
import { LatencyChart } from "@/components/Charts/LatencyChart";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export default function Analytics() {
  const [errorTrend, setErrorTrend] = useState<any[]>([]);
  const [integrityTrend, setIntegrityTrend] = useState<any[]>([]);
  const [doctrine, setDoctrine] = useState<any[]>([]);
  const [latency, setLatency] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [startDate, setStartDate] = useState<Date | undefined>(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  );
  const [endDate, setEndDate] = useState<Date | undefined>(new Date());

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      
      // Fetch data from MCP endpoints with fallback to mock data
      const [errorData, integrityData, doctrineData, latencyData] = await Promise.all([
        fetchFromMCP('/firebase/analytics/errors-trend').catch(() => 
          Array.from({ length: 30 }, (_, i) => ({
            timestamp: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString(),
            metric_name: 'errors',
            value: Math.floor(Math.random() * 50) + 10,
          }))
        ),
        fetchFromMCP('/firebase/analytics/integrity-trend').catch(() =>
          Array.from({ length: 30 }, (_, i) => ({
            timestamp: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString(),
            metric_name: 'integrity',
            value: 75 + Math.random() * 20,
          }))
        ),
        fetchFromMCP('/firebase/analytics/doctrine').catch(() =>
          Array.from({ length: 32 }, (_, i) => ({
            timestamp: new Date().toISOString(),
            metric_name: 'doctrine_compliance',
            value: 85 + Math.random() * 15,
            process_id: ['Intake', 'Parse', 'Validate', 'Enrich', 'PLE', 'Slot', 'Verify', 'BIT'][i % 8],
            schema_version: `v${Math.floor(i / 8) + 1}.0`,
          }))
        ),
        fetchFromMCP('/firebase/analytics/latency').catch(() =>
          Array.from({ length: 30 }, (_, i) => {
            const date = new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000);
            return ['intake', 'promotion', 'ple', 'bit'].map(stage => ({
              timestamp: date.toISOString(),
              metric_name: 'latency',
              value: stage === 'intake' ? 2 + Math.random() * 2 :
                     stage === 'promotion' ? 5 + Math.random() * 3 :
                     stage === 'ple' ? 8 + Math.random() * 4 :
                     12 + Math.random() * 5,
              stage,
            }));
          }).flat()
        ),
      ]);
      
      setErrorTrend(errorData);
      setIntegrityTrend(integrityData);
      setDoctrine(doctrineData);
      setLatency(latencyData);
      setLastUpdated(new Date());
    } catch (error: any) {
      toast.error('Failed to load analytics: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [startDate, endDate]);

  const handleQuickRange = (days: number) => {
    setEndDate(new Date());
    setStartDate(new Date(Date.now() - days * 24 * 60 * 60 * 1000));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-muted-foreground">Loading Analytics...</div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4 max-w-7xl mx-auto">
      <div className="border-l-4 border-doctrine pl-3 mb-6">
        <h1 className="text-2xl font-bold text-foreground">Analytics & Doctrine Intelligence</h1>
        <p className="text-sm text-muted-foreground">Long-term reliability, integrity, and performance insights</p>
      </div>

      {/* Date Range Picker & Quick Filters */}
      <Card className="p-4 bg-doctrine/5 rounded-xl shadow-md border-border/20">
        <div className="flex flex-col md:flex-row gap-3 items-start md:items-center justify-between">
          <div className="flex gap-2 flex-wrap">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => handleQuickRange(7)}
            >
              Last 7 Days
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => handleQuickRange(30)}
            >
              Last 30 Days
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => handleQuickRange(90)}
            >
              Last 90 Days
            </Button>
          </div>

          <div className="flex gap-2 items-center">
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className={cn(
                    "justify-start text-left font-normal",
                    !startDate && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {startDate ? format(startDate, "PPP") : <span>Start date</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={startDate}
                  onSelect={setStartDate}
                  initialFocus
                  className={cn("p-3 pointer-events-auto")}
                />
              </PopoverContent>
            </Popover>

            <span className="text-muted-foreground text-sm">to</span>

            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className={cn(
                    "justify-start text-left font-normal",
                    !endDate && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {endDate ? format(endDate, "PPP") : <span>End date</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={endDate}
                  onSelect={setEndDate}
                  initialFocus
                  className={cn("p-3 pointer-events-auto")}
                />
              </PopoverContent>
            </Popover>

            <Button 
              size="sm" 
              onClick={loadAnalytics}
              variant="default"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </Card>

      {/* Section A: Dual Trend Chart */}
      <div className="bg-vision/5 rounded-xl p-1">
        <DualTrendChart errorData={errorTrend} integrityData={integrityTrend} />
      </div>

      {/* Section B: Doctrine Compliance Heatmap */}
      <DoctrineHeatmap data={doctrine} />

      {/* Section C: Latency Metrics */}
      <div className="bg-pipeline/5 rounded-xl p-1">
        <LatencyChart data={latency} />
      </div>

      {/* Footer */}
      <div className="text-xs text-muted-foreground text-center pt-4 flex items-center justify-center gap-2">
        <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
        <Badge variant="outline" className="text-xs">Manual Refresh</Badge>
      </div>
    </div>
  );
}
