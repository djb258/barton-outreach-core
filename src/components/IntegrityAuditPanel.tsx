import { Card } from "@/components/ui/card";
import { IntegrityRing } from "./IntegrityRing";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface IntegrityData {
  average: number;
  processes: Array<{
    name: string;
    integrity: number;
  }>;
}

interface IntegrityAuditPanelProps {
  integrity: IntegrityData;
}

export function IntegrityAuditPanel({ integrity }: IntegrityAuditPanelProps) {
  const getBarColor = (value: number) => {
    if (value >= 98) return 'hsl(var(--status-online))'; // Green
    if (value >= 95) return 'hsl(var(--status-warning))'; // Yellow
    return 'hsl(var(--status-error))'; // Red
  };

  return (
    <Card className="p-4 bg-doctrine/5 rounded-xl shadow-md border-border/20">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-doctrine">Integrity Audit</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="flex justify-center items-center">
          <IntegrityRing 
            value={integrity.average} 
            label="Overall Integrity" 
            color="text-doctrine"
          />
        </div>

        <div className="md:col-span-2">
          <div className="text-xs text-muted-foreground mb-2">Integrity by Process</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={integrity.processes} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis 
                type="number" 
                domain={[0, 100]} 
                stroke="hsl(var(--muted-foreground))"
                fontSize={10}
              />
              <YAxis 
                type="category" 
                dataKey="name" 
                width={100}
                stroke="hsl(var(--muted-foreground))"
                fontSize={10}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '0.5rem',
                  fontSize: '12px',
                }}
                formatter={(value: number) => [`${value.toFixed(1)}%`, 'Integrity']}
              />
              <Bar dataKey="integrity" radius={[0, 4, 4, 0]}>
                {integrity.processes.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.integrity)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <div className="flex items-center justify-between mt-2 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-status-online" />
              <span className="text-muted-foreground">&gt;98%</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-status-warning" />
              <span className="text-muted-foreground">95-98%</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-status-error" />
              <span className="text-muted-foreground">&lt;95%</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
