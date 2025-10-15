import { Card } from "@/components/ui/card";

interface IntegrityRingProps {
  value: number;
  label: string;
  color?: string;
}

export function IntegrityRing({ value, label, color = "text-doctrine" }: IntegrityRingProps) {
  const circumference = 2 * Math.PI * 40;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <Card className="p-4 flex flex-col items-center justify-center">
      <svg className="w-24 h-24" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="hsl(var(--muted))"
          strokeWidth="8"
        />
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform="rotate(-90 50 50)"
          className={color}
        />
        <text
          x="50"
          y="50"
          textAnchor="middle"
          dy="0.3em"
          className="text-xl font-bold fill-foreground"
        >
          {value}%
        </text>
      </svg>
      <div className="text-xs text-muted-foreground mt-2 text-center">{label}</div>
    </Card>
  );
}
