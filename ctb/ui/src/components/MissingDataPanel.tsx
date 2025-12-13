import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { RefreshCw } from "lucide-react";
import { fetchFromMCP } from "@/lib/mcpClient";
import { toast } from "sonner";

interface MissingDataRecord {
  entity_type: string;
  entity_id: string;
  missing_fields: string[];
  status: string;
  detected_at: string;
}

interface MissingDataPanelProps {
  missing: MissingDataRecord[];
  onSelectRecord: (record: MissingDataRecord) => void;
  onRetrySuccess: () => void;
}

export function MissingDataPanel({ missing, onSelectRecord, onRetrySuccess }: MissingDataPanelProps) {
  const openCount = missing.filter(m => m.status === 'open').length;

  const handleRetry = async (entityId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetchFromMCP(`/firebase/missing/retry/${entityId}`, {
        method: 'POST',
      });
      toast.success('Retry queued successfully');
      onRetrySuccess();
    } catch (error: any) {
      toast.error('Failed to queue retry: ' + error.message);
    }
  };

  return (
    <Card className="p-4 bg-pipeline/5 rounded-xl shadow-md border-border/20">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-pipeline">Missing Data Registry</h3>
          <Badge variant="destructive">{openCount} Open</Badge>
        </div>
        <Badge variant="outline">{missing.length} Total</Badge>
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs">Entity Type</TableHead>
              <TableHead className="text-xs">Entity ID</TableHead>
              <TableHead className="text-xs">Missing Fields</TableHead>
              <TableHead className="text-xs">Status</TableHead>
              <TableHead className="text-xs">Detected At</TableHead>
              <TableHead className="text-xs">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {missing.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground text-sm">
                  No missing data records
                </TableCell>
              </TableRow>
            ) : (
              missing.map((record, idx) => (
                <TableRow
                  key={idx}
                  onClick={() => onSelectRecord(record)}
                  className="hover:bg-pipeline/10 cursor-pointer"
                >
                  <TableCell className="text-xs">{record.entity_type}</TableCell>
                  <TableCell className="text-xs font-mono">{record.entity_id}</TableCell>
                  <TableCell className="text-xs">
                    <div className="flex flex-wrap gap-1">
                      {record.missing_fields.slice(0, 3).map((field, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {field}
                        </Badge>
                      ))}
                      {record.missing_fields.length > 3 && (
                        <Badge variant="secondary" className="text-xs">
                          +{record.missing_fields.length - 3}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-xs">
                    <Badge variant={record.status === 'open' ? 'destructive' : 'secondary'}>
                      {record.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs">
                    {new Date(record.detected_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-xs">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => handleRetry(record.entity_id, e)}
                      className="h-7"
                    >
                      <RefreshCw className="w-3 h-3 mr-1" />
                      Retry
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
