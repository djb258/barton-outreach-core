import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Card } from "@/components/ui/card";

interface OutboundMetrics {
  instantly: number;
  heyreach: number;
}

interface OutboundSummaryProps {
  metrics: OutboundMetrics;
}

export function OutboundSummary({ metrics }: OutboundSummaryProps) {
  const data = [
    { channel: 'Instantly', rate: metrics.instantly },
    { channel: 'HeyReach', rate: metrics.heyreach },
  ];

  return (
    <Card className="p-4 rounded-xl shadow-md border-border/20">
      <h3 className="text-sm font-semibold mb-3 text-execution">
        Outbound Performance Summary
      </h3>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-execution/10 rounded-lg">
          <div className="text-xs text-muted-foreground mb-1">Instantly Reply</div>
          <div className="text-xl font-bold text-execution">{metrics.instantly.toFixed(1)}%</div>
        </div>
        <div className="p-3 bg-doctrine/10 rounded-lg">
          <div className="text-xs text-muted-foreground mb-1">HeyReach Reply</div>
          <div className="text-xl font-bold text-doctrine">{metrics.heyreach.toFixed(1)}%</div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="channel" 
            stroke="hsl(var(--muted-foreground))"
            fontSize={10}
          />
          <YAxis 
            stroke="hsl(var(--muted-foreground))"
            fontSize={10}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '0.5rem',
              fontSize: '11px',
            }}
            formatter={(value: number) => `${value.toFixed(1)}%`}
          />
          <Bar 
            dataKey="rate" 
            radius={[4, 4, 0, 0]}
          >
            {data.map((entry, index) => (
              <Bar 
                key={index}
                dataKey="rate"
                fill={index === 0 ? 'hsl(var(--execution-green))' : 'hsl(var(--doctrine-blue))'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
