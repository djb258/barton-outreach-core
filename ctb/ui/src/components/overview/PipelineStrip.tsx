import { Card } from "@/components/ui/card";
import { CheckCircle, AlertCircle, Clock } from "lucide-react";

interface PipelineStage {
  name: string;
  status: 'online' | 'warning' | 'error' | 'offline';
}

interface PipelineStripProps {
  stages: PipelineStage[];
}

export function PipelineStrip({ stages }: PipelineStripProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-status-online';
      case 'warning': return 'bg-status-warning';
      case 'error': return 'bg-status-error';
      case 'offline': return 'bg-status-offline';
      default: return 'bg-muted';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle className="w-4 h-4 text-status-online" />;
      case 'warning': return <Clock className="w-4 h-4 text-status-warning" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-status-error" />;
      case 'offline': return <AlertCircle className="w-4 h-4 text-status-offline" />;
      default: return null;
    }
  };

  const healthPercentage = (stages.filter(s => s.status === 'online').length / stages.length) * 100;

  return (
    <Card className="p-4 rounded-xl shadow-md border-border/20">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-pipeline">Pipeline Status</h3>
        <span className="text-xs text-muted-foreground">{healthPercentage.toFixed(0)}% Healthy</span>
      </div>

      {/* Progress Bar */}
      <div className="mb-4 h-2 bg-muted rounded-full overflow-hidden">
        <div 
          className="h-full bg-status-online transition-all duration-500"
          style={{ width: `${healthPercentage}%` }}
        />
      </div>

      {/* Stage Dots */}
      <div className="flex items-center justify-between gap-1">
        {stages.map((stage, idx) => (
          <div key={idx} className="flex flex-col items-center flex-1">
            <div className="relative">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${getStatusColor(stage.status)} transition-all duration-300 hover:scale-110`}
                title={`${stage.name}: ${stage.status}`}
              >
                {getStatusIcon(stage.status)}
              </div>
              {idx < stages.length - 1 && (
                <div className="absolute top-1/2 left-full w-full h-0.5 bg-border transform -translate-y-1/2" />
              )}
            </div>
            <span className="text-xs text-muted-foreground mt-2 text-center">{stage.name}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
