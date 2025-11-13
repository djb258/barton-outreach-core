import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { RefreshCw, ChevronRight } from 'lucide-react';
import { routerApi } from '@/lib/router/routerApi';
import { formatRelativeTime, formatDuration, getStatusColor } from '@/lib/router/routerUtils';
import { toast } from '@/hooks/use-toast';
import type { RecipeRun } from '@/types/router';

export const RunsHistory = () => {
  const [runs, setRuns] = useState<RecipeRun[]>([]);
  const [loading, setLoading] = useState(true);

  const loadRuns = async () => {
    try {
      setLoading(true);
      // Note: Backend needs to implement GET /api/runs endpoint
      // For now, this will fail gracefully
      const data = await routerApi.request<RecipeRun[]>('/api/runs');
      setRuns(data);
    } catch (error) {
      // Silently fail for now since endpoint may not exist yet
      console.error('Failed to load runs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRuns();
  }, []);

  const handleViewDetails = async (runId: string) => {
    try {
      const run = await routerApi.getRun(runId);
      const logs = await routerApi.getRunLogs(runId);
      
      toast({
        title: `Run ${runId}`,
        description: (
          <div className="space-y-2 text-sm">
            <p><strong>Status:</strong> {run.status}</p>
            <p><strong>Duration:</strong> {formatDuration(run.duration_ms)}</p>
            <p><strong>Logs:</strong> {logs.length} entries</p>
          </div>
        ),
      });
    } catch (error) {
      toast({
        title: 'Failed to Load Run Details',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  return (
    <Card className="border-tool-router/30">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-tool-router">Execution History</CardTitle>
            <CardDescription>Recent recipe runs and validations</CardDescription>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={loadRuns}
            disabled={loading}
            className="border-tool-router/30"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {runs.length === 0 && !loading ? (
          <div className="text-center py-8 text-muted-foreground">
            No execution history yet. Start routing data to see runs here.
          </div>
        ) : (
          <div className="space-y-3">
            {runs.map((run) => (
              <div
                key={run.id}
                className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
              >
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge className={getStatusColor(run.status)}>
                      {run.status}
                    </Badge>
                    <span className="font-mono text-xs text-muted-foreground">
                      {run.process_id}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Started {formatRelativeTime(run.started_at)}
                    {run.duration_ms && ` • ${formatDuration(run.duration_ms)}`}
                  </div>
                  {run.error_message && (
                    <div className="text-sm text-red-500">
                      {run.error_message}
                    </div>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleViewDetails(run.id)}
                  className="text-tool-router"
                >
                  Details
                  <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
