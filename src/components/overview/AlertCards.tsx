import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface Alert {
  id: string;
  severity: string;
  message: string;
  source: string;
  timestamp: string;
}

interface AlertCardsProps {
  alerts: Alert[];
}

export function AlertCards({ alerts }: AlertCardsProps) {
  const navigate = useNavigate();

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'error':
        return 'bg-vision text-vision-foreground';
      case 'warning':
        return 'bg-pipeline text-pipeline-foreground';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const getRouteForSource = (source: string) => {
    if (source.includes('error') || source.includes('validate')) return '/';
    if (source.includes('analytic') || source.includes('doctrine')) return '/analytics';
    if (source.includes('outbound') || source.includes('bilato')) return '/messaging';
    return '/';
  };

  return (
    <Card className="p-4 rounded-xl shadow-md border-border/20 bg-vision/5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-vision flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          Active Alerts
        </h3>
        <Badge variant="destructive">{alerts.length}</Badge>
      </div>

      <div className="space-y-2">
        {alerts.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4">
            No active alerts - all systems nominal
          </div>
        ) : (
          alerts.slice(0, 3).map((alert) => (
            <Card 
              key={alert.id} 
              className="p-3 border border-border/50 hover:border-border transition-all animate-fade-in"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="secondary" className={getSeverityColor(alert.severity)}>
                      {alert.severity}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-xs text-foreground mb-2">{alert.message}</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate(getRouteForSource(alert.source))}
                    className="h-7 text-xs"
                  >
                    View Details
                    <ArrowRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </Card>
  );
}
