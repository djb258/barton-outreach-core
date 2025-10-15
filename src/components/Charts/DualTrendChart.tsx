import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { ChartCard } from "../ChartCard";

interface TrendData {
  timestamp: string;
  metric_name: string;
  value: number;
}

interface DualTrendChartProps {
  errorData: TrendData[];
  integrityData: TrendData[];
}

export function DualTrendChart({ errorData, integrityData }: DualTrendChartProps) {
  // Merge data by date
  const dateMap = new Map();
  
  errorData.forEach(item => {
    const date = new Date(item.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    if (!dateMap.has(date)) {
      dateMap.set(date, { date, errors: 0, integrity: 0 });
    }
    dateMap.get(date).errors = item.value;
  });
  
  integrityData.forEach(item => {
    const date = new Date(item.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    if (!dateMap.has(date)) {
      dateMap.set(date, { date, errors: 0, integrity: 0 });
    }
    dateMap.get(date).integrity = item.value;
  });
  
  const chartData = Array.from(dateMap.values());

  return (
    <ChartCard title="Error Rate vs Integrity Trends">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="date" 
            stroke="hsl(var(--muted-foreground))"
            fontSize={11}
          />
          <YAxis 
            yAxisId="left"
            stroke="hsl(var(--muted-foreground))"
            fontSize={11}
            label={{ value: 'Error Count', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }}
          />
          <YAxis 
            yAxisId="right"
            orientation="right"
            stroke="hsl(var(--muted-foreground))"
            fontSize={11}
            domain={[0, 100]}
            label={{ value: 'Integrity %', angle: 90, position: 'insideRight', style: { fontSize: 10 } }}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '0.5rem',
              fontSize: '12px',
            }}
          />
          <Legend 
            wrapperStyle={{ fontSize: '12px' }}
          />
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="errors" 
            stroke="#b91c1c"
            strokeWidth={2}
            dot={{ fill: '#b91c1c', r: 3 }}
            name="Errors"
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="integrity" 
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 3 }}
            name="Integrity %"
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
