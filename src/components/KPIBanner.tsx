import { Card } from "@/components/ui/card";

interface KPIBannerProps {
  integrity: number;
  uptime: number;
  throughput: number;
}

export function KPIBanner({ integrity, uptime, throughput }: KPIBannerProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mb-4">
      <Card className="p-3 border-vision">
        <div className="text-xs text-muted-foreground mb-1">System Integrity</div>
        <div className="text-2xl font-bold text-vision">{integrity.toFixed(1)}%</div>
      </Card>
      
      <Card className="p-3 border-execution">
        <div className="text-xs text-muted-foreground mb-1">Uptime</div>
        <div className="text-2xl font-bold text-execution">{uptime.toFixed(1)}%</div>
      </Card>
      
      <Card className="p-3 border-pipeline">
        <div className="text-xs text-muted-foreground mb-1">Daily Throughput</div>
        <div className="text-2xl font-bold text-pipeline">{throughput}</div>
      </Card>
    </div>
  );
}
