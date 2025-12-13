import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { fetchFromMCP } from "@/lib/mcpClient";

interface RecordData {
  unique_id?: string;
  process_id?: string;
  agent?: string;
  message?: string;
  severity?: string;
  status?: string;
  timestamp?: string;
  details?: any;
  entity_type?: string;
  entity_id?: string;
  missing_fields?: string[];
}

interface ErrorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  record: RecordData | null;
  onResolve?: (id: string) => void;
}

export function ErrorModal({ open, onOpenChange, record, onResolve }: ErrorModalProps) {
  if (!record) return null;

  const handleResolve = async () => {
    try {
      if (record.unique_id) {
        await fetchFromMCP(`/firebase/errors/${record.unique_id}/resolve`, {
          method: 'POST',
        });
        toast.success('Record marked as resolved');
        if (onResolve) onResolve(record.unique_id);
      }
      onOpenChange(false);
    } catch (error: any) {
      toast.error('Failed to resolve: ' + error.message);
    }
  };

  const handleRerun = async () => {
    try {
      if (record.unique_id) {
        await fetchFromMCP(`/firebase/errors/${record.unique_id}/rerun`, {
          method: 'POST',
        });
        toast.success('Process re-run initiated');
      }
      onOpenChange(false);
    } catch (error: any) {
      toast.error('Failed to re-run: ' + error.message);
    }
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'text-vision';
      case 'error': return 'text-destructive';
      case 'warning': return 'text-pipeline';
      case 'info': return 'text-doctrine';
      default: return 'text-muted-foreground';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-vision flex items-center gap-2">
            Record Inspector
            {record.severity && (
              <Badge variant="outline" className={getSeverityColor(record.severity)}>
                {record.severity}
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-3">
          {record.unique_id && (
            <Card className="p-3 bg-vision/5">
              <div className="text-xs text-muted-foreground mb-1">Unique ID</div>
              <div className="font-mono text-sm text-foreground">{record.unique_id}</div>
            </Card>
          )}

          {record.process_id && (
            <Card className="p-3">
              <div className="text-xs text-muted-foreground mb-1">Process ID</div>
              <div className="font-mono text-sm">{record.process_id}</div>
            </Card>
          )}
          
          {record.agent && (
            <Card className="p-3">
              <div className="text-xs text-muted-foreground mb-1">Agent</div>
              <div className="font-mono text-sm">{record.agent}</div>
            </Card>
          )}

          {record.entity_type && (
            <Card className="p-3">
              <div className="text-xs text-muted-foreground mb-1">Entity Type</div>
              <div className="font-mono text-sm">{record.entity_type}</div>
            </Card>
          )}

          {record.entity_id && (
            <Card className="p-3">
              <div className="text-xs text-muted-foreground mb-1">Entity ID</div>
              <div className="font-mono text-sm">{record.entity_id}</div>
            </Card>
          )}
          
          {record.message && (
            <Card className="p-3">
              <div className="text-xs text-muted-foreground mb-1">Message</div>
              <div className={`text-sm ${getSeverityColor(record.severity)}`}>{record.message}</div>
            </Card>
          )}

          {record.missing_fields && record.missing_fields.length > 0 && (
            <Card className="p-3">
              <div className="text-xs text-muted-foreground mb-1">Missing Fields</div>
              <div className="flex flex-wrap gap-1 mt-1">
                {record.missing_fields.map((field, idx) => (
                  <Badge key={idx} variant="secondary">{field}</Badge>
                ))}
              </div>
            </Card>
          )}

          {record.status && (
            <Card className="p-3">
              <div className="text-xs text-muted-foreground mb-1">Status</div>
              <Badge variant={record.status === 'open' ? 'destructive' : 'secondary'}>
                {record.status}
              </Badge>
            </Card>
          )}
          
          {record.timestamp && (
            <Card className="p-3">
              <div className="text-xs text-muted-foreground mb-1">Timestamp</div>
              <div className="text-sm">{new Date(record.timestamp).toLocaleString()}</div>
            </Card>
          )}
          
          {record.details && (
            <Card className="p-3">
              <div className="text-xs text-muted-foreground mb-1">Details / Payload</div>
              <pre className="text-xs overflow-auto max-h-48 bg-muted p-2 rounded font-mono">
                {JSON.stringify(record.details, null, 2)}
              </pre>
            </Card>
          )}
          
          <div className="flex gap-2 pt-2">
            <Button 
              variant="default" 
              onClick={handleResolve}
            >
              Mark Resolved
            </Button>
            <Button 
              variant="secondary" 
              onClick={handleRerun}
            >
              Re-Run Process
            </Button>
            <Button 
              variant="outline" 
              onClick={() => onOpenChange(false)}
            >
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
