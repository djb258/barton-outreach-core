import { Card } from "@/components/ui/card";
import { AlertCircle, Database, Shield, MessageSquare } from "lucide-react";

interface SnapshotData {
  openErrors: number;
  missingRecords: number;
  integrityScore: number;
  outboundReplyRate: number;
}

interface SystemSnapshotProps {
  data: SnapshotData;
}

export function SystemSnapshot({ data }: SystemSnapshotProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card className="p-4 rounded-xl shadow-md border-l-4 border-vision bg-vision/5">
        <div className="flex items-center justify-between mb-2">
          <AlertCircle className="w-5 h-5 text-vision" />
          <span className="text-xs text-muted-foreground">Control</span>
        </div>
        <div className="text-2xl font-bold text-vision">{data.openErrors}</div>
        <div className="text-xs text-muted-foreground mt-1">Open Errors</div>
      </Card>

      <Card className="p-4 rounded-xl shadow-md border-l-4 border-pipeline bg-pipeline/5">
        <div className="flex items-center justify-between mb-2">
          <Database className="w-5 h-5 text-pipeline" />
          <span className="text-xs text-muted-foreground">Data</span>
        </div>
        <div className="text-2xl font-bold text-pipeline">{data.missingRecords}</div>
        <div className="text-xs text-muted-foreground mt-1">Missing Records</div>
      </Card>

      <Card className="p-4 rounded-xl shadow-md border-l-4 border-doctrine bg-doctrine/5">
        <div className="flex items-center justify-between mb-2">
          <Shield className="w-5 h-5 text-doctrine" />
          <span className="text-xs text-muted-foreground">Integrity</span>
        </div>
        <div className="text-2xl font-bold text-doctrine">{data.integrityScore.toFixed(1)}%</div>
        <div className="text-xs text-muted-foreground mt-1">Integrity Score</div>
      </Card>

      <Card className="p-4 rounded-xl shadow-md border-l-4 border-execution bg-execution/5">
        <div className="flex items-center justify-between mb-2">
          <MessageSquare className="w-5 h-5 text-execution" />
          <span className="text-xs text-muted-foreground">Outbound</span>
        </div>
        <div className="text-2xl font-bold text-execution">{data.outboundReplyRate.toFixed(1)}%</div>
        <div className="text-xs text-muted-foreground mt-1">Reply Rate</div>
      </Card>
    </div>
  );
}
