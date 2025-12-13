import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface ErrorRecord {
  timestamp: string;
  process_id: string;
  agent: string;
  message: string;
  severity: string;
  status: string;
  unique_id: string;
}

interface MasterErrorLogProps {
  errors: ErrorRecord[];
  onSelectError: (error: ErrorRecord) => void;
}

export function MasterErrorLog({ errors, onSelectError }: MasterErrorLogProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-vision text-vision-foreground';
      case 'error':
        return 'bg-destructive text-destructive-foreground';
      case 'warning':
        return 'bg-pipeline text-pipeline-foreground';
      case 'info':
        return 'bg-doctrine text-doctrine-foreground';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const getRowBgColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'hover:bg-vision/10 cursor-pointer';
      case 'error':
        return 'hover:bg-destructive/10 cursor-pointer';
      case 'warning':
        return 'hover:bg-pipeline/10 cursor-pointer';
      case 'info':
        return 'hover:bg-doctrine/10 cursor-pointer';
      default:
        return 'hover:bg-muted/50 cursor-pointer';
    }
  };

  return (
    <Card className="p-4 bg-vision/5 rounded-xl shadow-md border-border/20">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-vision">Master Error Log</h3>
        <Badge variant="outline">{errors.length} Records</Badge>
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs">Timestamp</TableHead>
              <TableHead className="text-xs">Process ID</TableHead>
              <TableHead className="text-xs">Agent</TableHead>
              <TableHead className="text-xs">Message</TableHead>
              <TableHead className="text-xs">Severity</TableHead>
              <TableHead className="text-xs">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {errors.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground text-sm">
                  No errors recorded
                </TableCell>
              </TableRow>
            ) : (
              errors.map((error) => (
                <TableRow
                  key={error.unique_id}
                  onClick={() => onSelectError(error)}
                  className={getRowBgColor(error.severity)}
                >
                  <TableCell className="text-xs font-mono">
                    {new Date(error.timestamp).toLocaleTimeString()}
                  </TableCell>
                  <TableCell className="text-xs">{error.process_id}</TableCell>
                  <TableCell className="text-xs">{error.agent}</TableCell>
                  <TableCell className="text-xs max-w-xs truncate">{error.message}</TableCell>
                  <TableCell className="text-xs">
                    <Badge variant="secondary" className={getSeverityColor(error.severity)}>
                      {error.severity}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs">
                    <Badge variant={error.status === 'open' ? 'destructive' : 'secondary'}>
                      {error.status}
                    </Badge>
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
