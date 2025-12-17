import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, X } from "lucide-react";

interface MonthlyUpdate {
  id: string;
  unique_id: string;
  field_changed: string;
  old_value: string | null;
  new_value: string | null;
  source: string;
  approved: boolean;
  created_at: string;
  updated_at: string;
}

interface ChangeTableProps {
  updates: MonthlyUpdate[];
  onApprove: (id: string) => void;
  onPromote: (id: string) => void;
  isRunning?: boolean;
}

export const ChangeTable = ({
  updates,
  onApprove,
  onPromote,
  isRunning = false,
}: ChangeTableProps) => {
  if (updates.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No updates found. Run an update check to see changes.
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Record ID</TableHead>
          <TableHead>Field Changed</TableHead>
          <TableHead>Old Value</TableHead>
          <TableHead>New Value</TableHead>
          <TableHead>Source</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {updates.map((update) => (
          <TableRow key={update.id}>
            <TableCell className="font-mono text-xs">
              {update.unique_id.slice(0, 8)}
            </TableCell>
            <TableCell className="font-medium">{update.field_changed}</TableCell>
            <TableCell>
              <span className="text-destructive line-through">
                {update.old_value || "—"}
              </span>
            </TableCell>
            <TableCell>
              <span className="text-success font-medium">
                {update.new_value || "—"}
              </span>
            </TableCell>
            <TableCell>
              <Badge variant="secondary">{update.source}</Badge>
            </TableCell>
            <TableCell>
              {update.approved ? (
                <Badge variant="default" className="gap-1">
                  <Check className="h-3 w-3" /> Approved
                </Badge>
              ) : (
                <Badge variant="outline" className="gap-1">
                  <X className="h-3 w-3" /> Pending
                </Badge>
              )}
            </TableCell>
            <TableCell>
              <div className="flex gap-2">
                {!update.approved && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onApprove(update.id)}
                    disabled={isRunning}
                  >
                    Approve
                  </Button>
                )}
                {update.approved && (
                  <Button
                    size="sm"
                    onClick={() => onPromote(update.id)}
                    disabled={isRunning}
                  >
                    Promote
                  </Button>
                )}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};
