import { Card } from "@/components/ui/card";

interface Metric {
  label: string;
  value: number;
  unit?: string;
  color?: string;
}

interface MetricsCardsProps {
  metrics: Metric[];
}

export function MetricsCards({ metrics }: MetricsCardsProps) {
  const getColorClass = (color?: string) => {
    switch (color) {
      case 'success': return 'text-execution';
      case 'warning': return 'text-pipeline';
      case 'error': return 'text-vision';
      case 'info': return 'text-doctrine';
      default: return 'text-foreground';
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
      {metrics.map((metric, index) => (
        <Card key={index} className="p-4">
          <div className="text-xs text-muted-foreground mb-1">{metric.label}</div>
          <div className={`text-2xl font-bold ${getColorClass(metric.color)}`}>
            {metric.value.toFixed(1)}{metric.unit || '%'}
          </div>
        </Card>
      ))}
    </div>
  );
}
