import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { ChartCard } from "../ChartCard";

interface TrendData {
  timestamp: string;
  metric_name: string;
  value: number;
}

interface ErrorTrendChartProps {
  data: TrendData[];
}

export function ErrorTrendChart({ data }: ErrorTrendChartProps) {
  // Transform data for recharts
  const chartData = data.map(item => ({
    date: new Date(item.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    errors: item.value,
  }));

  return (
    <ChartCard title="Error Rate Over Time">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="date" 
            stroke="hsl(var(--muted-foreground))"
            fontSize={11}
          />
          <YAxis 
            stroke="hsl(var(--muted-foreground))"
            fontSize={11}
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
            type="monotone" 
            dataKey="errors" 
            stroke="#b91c1c"
            strokeWidth={2}
            dot={{ fill: '#b91c1c', r: 3 }}
            name="Error Count"
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
