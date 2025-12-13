import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Card } from "@/components/ui/card";

interface TrendData {
  timestamp: string;
  metric_name: string;
  value: number;
}

interface MiniTrendChartProps {
  errorData: TrendData[];
  integrityData: TrendData[];
}

export function MiniTrendChart({ errorData, integrityData }: MiniTrendChartProps) {
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
  
  const chartData = Array.from(dateMap.values()).slice(-7); // Last 7 days

  return (
    <Card className="p-4 rounded-xl shadow-md border-border/20">
      <h3 className="text-sm font-semibold mb-3" style={{ color: '#7c3aed' }}>
        7-Day Trend: Errors vs Integrity
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="date" 
            stroke="hsl(var(--muted-foreground))"
            fontSize={10}
          />
          <YAxis 
            yAxisId="left"
            stroke="hsl(var(--muted-foreground))"
            fontSize={10}
          />
          <YAxis 
            yAxisId="right"
            orientation="right"
            stroke="hsl(var(--muted-foreground))"
            fontSize={10}
            domain={[0, 100]}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '0.5rem',
              fontSize: '11px',
            }}
          />
          <Legend wrapperStyle={{ fontSize: '11px' }} />
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="errors" 
            stroke="#b91c1c"
            strokeWidth={2}
            dot={{ r: 2 }}
            name="Errors"
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="integrity" 
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 2 }}
            name="Integrity %"
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
