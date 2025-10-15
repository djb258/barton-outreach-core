import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { ChartCard } from "../ChartCard";

interface LatencyData {
  timestamp: string;
  metric_name: string;
  value: number;
  stage?: string;
}

interface LatencyChartProps {
  data: LatencyData[];
}

export function LatencyChart({ data }: LatencyChartProps) {
  // Group by timestamp and stage
  const dateMap = new Map();
  
  data.forEach(item => {
    const date = new Date(item.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    if (!dateMap.has(date)) {
      dateMap.set(date, { 
        date, 
        intake: 0, 
        promotion: 0, 
        ple: 0, 
        bit: 0 
      });
    }
    const stage = item.stage?.toLowerCase() || 'intake';
    dateMap.get(date)[stage] = item.value;
  });
  
  const chartData = Array.from(dateMap.values());

  // If no data, generate mock data
  const displayData = chartData.length > 0 ? chartData : Array.from({ length: 30 }, (_, i) => ({
    date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    intake: 2 + Math.random() * 2,
    promotion: 5 + Math.random() * 3,
    ple: 8 + Math.random() * 4,
    bit: 12 + Math.random() * 5,
  }));

  return (
    <ChartCard title="Pipeline Latency Metrics (Average Seconds)">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={displayData}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="date" 
            stroke="hsl(var(--muted-foreground))"
            fontSize={11}
          />
          <YAxis 
            stroke="hsl(var(--muted-foreground))"
            fontSize={11}
            label={{ value: 'Seconds', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '0.5rem',
              fontSize: '12px',
            }}
            formatter={(value: number) => `${value.toFixed(2)}s`}
          />
          <Legend 
            wrapperStyle={{ fontSize: '12px' }}
          />
          <Line 
            type="monotone" 
            dataKey="intake" 
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', r: 2 }}
            name="Intake"
          />
          <Line 
            type="monotone" 
            dataKey="promotion" 
            stroke="#facc15"
            strokeWidth={2}
            dot={{ fill: '#facc15', r: 2 }}
            name="Promotion"
          />
          <Line 
            type="monotone" 
            dataKey="ple" 
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 2 }}
            name="PLE"
          />
          <Line 
            type="monotone" 
            dataKey="bit" 
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ fill: '#ef4444', r: 2 }}
            name="BIT"
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
