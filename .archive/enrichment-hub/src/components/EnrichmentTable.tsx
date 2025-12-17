import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Download, Play, CheckCheck, Loader2 } from "lucide-react";
import { useValidation } from "@/hooks/useValidation";
import { useBatchActions } from "@/hooks/useBatchActions";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { ComponentId } from "@/components/ComponentId";

interface EnrichmentTableProps {
  entity: "people" | "companies";
  state: string;
  data: any[];
  isLoading: boolean;
  page: number;
  pageSize: number;
  totalCount: number;
  onPageChange: (page: number) => void;
}

export const EnrichmentTable = ({
  entity,
  state,
  data,
  isLoading,
  page,
  pageSize,
  totalCount,
  onPageChange,
}: EnrichmentTableProps) => {
  const [selectedRows, setSelectedRows] = useState<string[]>([]);
  const [selectedTool, setSelectedTool] = useState<string>("");
  
  const { toggleValidation } = useValidation(entity);
  const { exportBatch, runWithTool, promoteValidated, isRunning } = useBatchActions(entity, state);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const rowsToSelect = data.map((row) => row.unique_id).slice(0, 50);
      if (data.length > 50) {
        toast.warning("Maximum batch size is 50 records. Selected first 50.");
      }
      setSelectedRows(rowsToSelect);
    } else {
      setSelectedRows([]);
    }
  };

  const handleSelectRow = (rowId: string, checked: boolean) => {
    if (checked) {
      if (selectedRows.length >= 50) {
        toast.warning("Maximum batch size is 50 records");
        return;
      }
      setSelectedRows([...selectedRows, rowId]);
    } else {
      setSelectedRows(selectedRows.filter((id) => id !== rowId));
    }
  };

  const handleExport = () => {
    exportBatch(data);
  };

  const handleRunWithTool = () => {
    if (!selectedTool || selectedRows.length === 0) return;
    runWithTool(selectedTool, selectedRows);
  };

  const handlePromote = () => {
    if (selectedRows.length === 0) return;
    promoteValidated(selectedRows);
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  // Check if field is missing/empty
  const isMissing = (value: any) => !value || value === "";

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No unvalidated records for {state}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Batch Actions */}
      <ComponentId id={`${entity}-${state}-batch-actions`} type="toolbar">
        <div className="flex items-center gap-3 flex-wrap">
          <ComponentId id={`${entity}-${state}-export-btn`} type="button">
            <Button onClick={handleExport} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export Batch (50)
            </Button>
          </ComponentId>

          <div className="flex items-center gap-2">
            <ComponentId id={`${entity}-${state}-tool-dropdown`} type="select">
              <Select value={selectedTool} onValueChange={setSelectedTool}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select tool" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="salesnav">SalesNavigator</SelectItem>
                  <SelectItem value="apollo">Apollo</SelectItem>
                  <SelectItem value="clay">Clay</SelectItem>
                  <SelectItem value="firecrawl">Firecrawl</SelectItem>
                </SelectContent>
              </Select>
            </ComponentId>
            <ComponentId id={`${entity}-${state}-run-btn`} type="button">
              <Button
                onClick={handleRunWithTool}
                disabled={!selectedTool || selectedRows.length === 0 || selectedRows.length > 50 || isRunning}
                size="sm"
              >
                <Play className="h-4 w-4 mr-2" />
                Run with Tool
              </Button>
            </ComponentId>
          </div>

          <ComponentId id={`${entity}-${state}-promote-btn`} type="button">
            <Button
              onClick={handlePromote}
              disabled={selectedRows.length === 0 || selectedRows.length > 50 || isRunning}
              variant="default"
              size="sm"
            >
              <CheckCheck className="h-4 w-4 mr-2" />
              Mark Validated & Promote
            </Button>
          </ComponentId>

          <span className={cn(
            "text-sm ml-auto",
            selectedRows.length > 50 ? "text-destructive font-semibold" : "text-muted-foreground"
          )}>
            {selectedRows.length} selected {selectedRows.length > 50 && "(max 50)"}
          </span>
        </div>
      </ComponentId>

      {/* Table */}
      <ComponentId id={`${entity}-${state}-table`} type="table">
        <div className="border rounded-lg overflow-hidden">
          <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead className="w-12">
                <Checkbox
                  checked={selectedRows.length === data.length}
                  onCheckedChange={handleSelectAll}
                />
              </TableHead>
              <TableHead className="w-12">Valid</TableHead>
              {entity === "people" ? (
                <>
                  <TableHead>ID</TableHead>
                  <TableHead>First Name</TableHead>
                  <TableHead>Last Name</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>LinkedIn</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Source</TableHead>
                </>
              ) : (
                <>
                  <TableHead>ID</TableHead>
                  <TableHead>Company Name</TableHead>
                  <TableHead>Website</TableHead>
                  <TableHead>LinkedIn</TableHead>
                  <TableHead>Industry</TableHead>
                  <TableHead>HQ City</TableHead>
                  <TableHead>Source</TableHead>
                </>
              )}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row) => (
              <TableRow key={row.unique_id} className="hover:bg-muted/50">
                <TableCell>
                  <Checkbox
                    checked={selectedRows.includes(row.unique_id)}
                    onCheckedChange={(checked) =>
                      handleSelectRow(row.unique_id, checked as boolean)
                    }
                  />
                </TableCell>
                <TableCell>
                  <Checkbox
                    checked={row.validated}
                    onCheckedChange={() => toggleValidation(row.unique_id, row.validated)}
                  />
                </TableCell>
                {entity === "people" ? (
                  <>
                    <TableCell className="font-mono text-xs">
                      {row.unique_id.slice(0, 8)}...
                    </TableCell>
                    <TableCell className={cn(isMissing(row.first_name) && "text-destructive font-semibold")}>
                      {row.first_name || "—"}
                    </TableCell>
                    <TableCell className={cn(isMissing(row.last_name) && "text-destructive font-semibold")}>
                      {row.last_name || "—"}
                    </TableCell>
                    <TableCell className={cn(isMissing(row.company_name) && "text-destructive font-semibold")}>
                      {row.company_name || "—"}
                    </TableCell>
                    <TableCell className={cn(isMissing(row.email) && "text-destructive font-semibold")}>
                      {row.email || "—"}
                    </TableCell>
                    <TableCell className={cn(isMissing(row.linkedin_url) && "text-destructive font-semibold")}>
                      {row.linkedin_url ? (
                        <a
                          href={row.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          LinkedIn
                        </a>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className={cn(isMissing(row.title) && "text-destructive font-semibold")}>
                      {row.title || "—"}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {row.validation_source || "—"}
                    </TableCell>
                  </>
                ) : (
                  <>
                    <TableCell className="font-mono text-xs">
                      {row.unique_id.slice(0, 8)}...
                    </TableCell>
                    <TableCell className={cn(isMissing(row.company_name) && "text-destructive font-semibold")}>
                      {row.company_name || "—"}
                    </TableCell>
                    <TableCell className={cn(isMissing(row.website) && "text-destructive font-semibold")}>
                      {row.website ? (
                        <a
                          href={row.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          Website
                        </a>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className={cn(isMissing(row.linkedin_url) && "text-destructive font-semibold")}>
                      {row.linkedin_url ? (
                        <a
                          href={row.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          LinkedIn
                        </a>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className={cn(isMissing(row.industry) && "text-destructive font-semibold")}>
                      {row.industry || "—"}
                    </TableCell>
                    <TableCell className={cn(isMissing(row.hq_city) && "text-destructive font-semibold")}>
                      {row.hq_city || "—"}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {row.validation_source || "—"}
                    </TableCell>
                  </>
                )}
              </TableRow>
            ))}
          </TableBody>
          </Table>
        </div>
      </ComponentId>

      {/* Pagination */}
      {totalPages > 1 && (
        <ComponentId id={`${entity}-${state}-pagination`} type="pagination">
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Page {page + 1} of {totalPages}
            </div>
            <div className="flex gap-2">
              <ComponentId id={`${entity}-${state}-prev-btn`} type="button">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPageChange(page - 1)}
                  disabled={page === 0}
                >
                  Previous
                </Button>
              </ComponentId>
              <ComponentId id={`${entity}-${state}-next-btn`} type="button">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPageChange(page + 1)}
                  disabled={page >= totalPages - 1}
                >
                  Next
                </Button>
              </ComponentId>
            </div>
          </div>
        </ComponentId>
      )}
    </div>
  );
};
