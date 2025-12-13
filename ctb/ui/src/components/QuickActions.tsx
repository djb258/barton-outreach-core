import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { RefreshCw, CheckCircle } from "lucide-react";

interface QuickActionsProps {
  onSyncValidator: () => void;
  onRefreshPipeline: () => void;
}

export function QuickActions({ onSyncValidator, onRefreshPipeline }: QuickActionsProps) {
  return (
    <Card className="p-3">
      <div className="text-xs font-semibold text-muted-foreground mb-2">Quick Actions</div>
      <div className="flex gap-2">
        <Button 
          variant="secondary" 
          size="sm" 
          onClick={onSyncValidator}
          className="flex-1"
        >
          <CheckCircle className="w-4 h-4 mr-1" />
          Sync Validator
        </Button>
        <Button 
          variant="secondary" 
          size="sm" 
          onClick={onRefreshPipeline}
          className="flex-1"
        >
          <RefreshCw className="w-4 h-4 mr-1" />
          Refresh Pipeline
        </Button>
      </div>
    </Card>
  );
}
