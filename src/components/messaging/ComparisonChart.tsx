import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Card } from "@/components/ui/card";

interface ComparisonData {
  metric: string;
  instantly: number;
  heyreach: number;
}

interface ComparisonChartProps {
  instantlyMetrics: { openRate?: number; replyRate?: number; bounceRate?: number };
  heyreachMetrics: { connectionRate?: number; replyRate?: number; rejectRate?: number };
}

export function ComparisonChart({ instantlyMetrics, heyreachMetrics }: ComparisonChartProps) {
  const data: ComparisonData[] = [
    {
      metric: 'Reply Rate',
      instantly: instantlyMetrics.replyRate || 0,
      heyreach: heyreachMetrics.replyRate || 0,
    },
    {
      metric: 'Engagement',
      instantly: instantlyMetrics.openRate || 0,
      heyreach: heyreachMetrics.connectionRate || 0,
    },
  ];

  return (
    <Card className="p-4 rounded-xl shadow-md border-border/20">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-execution">Channel Performance Comparison</h3>
        <p className="text-xs text-muted-foreground">Reply rates across platforms</p>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="metric" 
            stroke="hsl(var(--muted-foreground))"
            fontSize={11}
          />
          <YAxis 
            stroke="hsl(var(--muted-foreground))"
            fontSize={11}
            label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '0.5rem',
              fontSize: '12px',
            }}
            formatter={(value: number) => `${value.toFixed(1)}%`}
          />
          <Legend 
            wrapperStyle={{ fontSize: '12px' }}
          />
          <Bar 
            dataKey="instantly" 
            fill="hsl(var(--execution-green))" 
            radius={[4, 4, 0, 0]}
            name="Instantly"
          />
          <Bar 
            dataKey="heyreach" 
            fill="hsl(var(--doctrine-blue))" 
            radius={[4, 4, 0, 0]}
            name="HeyReach"
          />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
