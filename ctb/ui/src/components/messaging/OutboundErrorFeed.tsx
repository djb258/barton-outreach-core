import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircle } from "lucide-react";

interface ErrorRecord {
  id: string;
  timestamp: string;
  source: string;
  message: string;
  severity: string;
}

interface OutboundErrorFeedProps {
  errors: ErrorRecord[];
  source?: string;
}

export function OutboundErrorFeed({ errors, source }: OutboundErrorFeedProps) {
  const filteredErrors = source 
    ? errors.filter(e => e.source === source)
    : errors;

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'error':
        return 'text-vision';
      case 'warning':
        return 'text-pipeline';
      default:
        return 'text-muted-foreground';
    }
  };

  return (
    <Card className="p-4 rounded-xl shadow-md border-border/20 bg-vision/5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-vision">Error Feed</h3>
        <Badge variant="destructive">{filteredErrors.length}</Badge>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {filteredErrors.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4">
            No recent errors
          </div>
        ) : (
          filteredErrors.slice(0, 10).map((error) => (
            <div
              key={error.id}
              className="p-3 bg-card rounded border border-border/50 hover:border-border transition-colors"
            >
              <div className="flex items-start gap-2">
                <AlertCircle className={`w-4 h-4 mt-0.5 ${getSeverityColor(error.severity)}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline" className="text-xs">
                      {error.source}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(error.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-xs text-foreground">{error.message}</p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
