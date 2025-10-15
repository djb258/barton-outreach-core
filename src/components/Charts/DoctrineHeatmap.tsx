import { Card } from "@/components/ui/card";
import { Tooltip } from "@/components/ui/tooltip";

interface DoctrineData {
  timestamp: string;
  metric_name: string;
  value: number;
  process_id?: string;
  schema_version?: string;
}

interface DoctrineHeatmapProps {
  data: DoctrineData[];
}

export function DoctrineHeatmap({ data }: DoctrineHeatmapProps) {
  // Group data by process_id and schema_version
  const processes = Array.from(new Set(data.map(d => d.process_id || 'Unknown')));
  const versions = Array.from(new Set(data.map(d => d.schema_version || 'v1.0')));
  
  // If no structured data, create a mock grid
  const gridData = processes.length > 0 && versions.length > 0 
    ? data 
    : Array.from({ length: 8 }, (_, i) => 
        Array.from({ length: 4 }, (_, j) => ({
          process_id: ['Intake', 'Parse', 'Validate', 'Enrich', 'PLE', 'Slot', 'Verify', 'BIT'][i],
          schema_version: `v${j + 1}.0`,
          value: 85 + Math.random() * 15,
        }))
      ).flat();

  const getColor = (value: number) => {
    if (value >= 95) return 'bg-status-online';
    if (value >= 90) return 'bg-status-warning';
    return 'bg-status-error';
  };

  const getOpacity = (value: number) => {
    const normalized = (value - 85) / 15; // Normalize between 85-100
    return Math.max(0.3, Math.min(1, normalized));
  };

  const processesDisplay = processes.length > 0 ? processes : ['Intake', 'Parse', 'Validate', 'Enrich', 'PLE', 'Slot', 'Verify', 'BIT'];
  const versionsDisplay = versions.length > 0 ? versions : ['v1.0', 'v2.0', 'v3.0', 'v4.0'];

  return (
    <Card className="p-4 bg-doctrine/5 rounded-xl shadow-md border-border/20">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-doctrine mb-1">Doctrine Compliance Heatmap</h3>
        <p className="text-xs text-muted-foreground">Process compliance by schema version</p>
      </div>

      <div className="overflow-x-auto">
        <div className="inline-grid gap-1" style={{ 
          gridTemplateColumns: `120px repeat(${versionsDisplay.length}, 60px)` 
        }}>
          {/* Header row */}
          <div className="text-xs font-semibold text-muted-foreground p-2"></div>
          {versionsDisplay.map((version) => (
            <div key={version} className="text-xs font-semibold text-muted-foreground text-center p-2">
              {version}
            </div>
          ))}
          
          {/* Data rows */}
          {processesDisplay.map((process) => (
            <>
              <div key={`label-${process}`} className="text-xs font-medium text-foreground p-2 flex items-center">
                {process}
              </div>
              {versionsDisplay.map((version) => {
                const cell = Array.isArray(gridData) 
                  ? gridData.find(d => 
                      (d.process_id || 'Unknown') === process && 
                      (d.schema_version || 'v1.0') === version
                    )
                  : null;
                const value = cell?.value || (85 + Math.random() * 15);
                
                return (
                  <div
                    key={`${process}-${version}`}
                    className={`aspect-square rounded flex items-center justify-center text-xs font-bold ${getColor(value)} cursor-pointer hover:scale-105 transition-transform`}
                    style={{ opacity: getOpacity(value) }}
                    title={`${process} - ${version}: ${value.toFixed(1)}%`}
                  >
                    {value.toFixed(0)}
                  </div>
                );
              })}
            </>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between mt-4 text-xs">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-status-online" />
            <span className="text-muted-foreground">≥95%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-status-warning" />
            <span className="text-muted-foreground">90-95%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-status-error" />
            <span className="text-muted-foreground">&lt;90%</span>
          </div>
        </div>
        <span className="text-muted-foreground">Hover cells for details</span>
      </div>
    </Card>
  );
}
