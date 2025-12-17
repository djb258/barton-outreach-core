import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { ComponentId } from "@/components/ComponentId";

interface EditableGridProps {
  data: any[];
  columns: string[];
  editableColumns: string[];
  onCellEdit: (recordId: string, fieldName: string, newValue: any, oldValue: any) => void;
  page: number;
  pageSize: number;
  totalCount: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
}

export const EditableGrid = ({
  data,
  columns,
  editableColumns,
  onCellEdit,
  page,
  pageSize,
  totalCount,
  onPageChange,
  isLoading,
}: EditableGridProps) => {
  const [editingCell, setEditingCell] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const totalPages = Math.ceil(totalCount / pageSize);

  const handleDoubleClick = (recordId: string, fieldName: string, currentValue: any) => {
    if (!editableColumns.includes(fieldName)) return;
    setEditingCell(`${recordId}-${fieldName}`);
    setEditValue(currentValue?.toString() || "");
  };

  const handleSave = (recordId: string, fieldName: string, oldValue: any) => {
    if (editValue !== oldValue?.toString()) {
      onCellEdit(recordId, fieldName, editValue, oldValue);
    }
    setEditingCell(null);
  };

  const handleKeyDown = (
    e: React.KeyboardEvent,
    recordId: string,
    fieldName: string,
    oldValue: any
  ) => {
    if (e.key === "Enter") {
      handleSave(recordId, fieldName, oldValue);
    } else if (e.key === "Escape") {
      setEditingCell(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 border rounded-lg">
        <div className="text-muted-foreground">No records found</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="border rounded-lg overflow-hidden">
        <div className="max-h-[600px] overflow-auto">
          <Table>
            <TableHeader className="sticky top-0 bg-muted">
              <TableRow>
                {columns.map((col) => (
                  <TableHead key={col} className="whitespace-nowrap">
                    {col}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((row, rowIndex) => (
                <TableRow
                  key={row.id || rowIndex}
                  className={rowIndex % 2 === 0 ? "bg-background" : "bg-muted/30"}
                >
                  {columns.map((col) => {
                    const cellKey = `${row.id}-${col}`;
                    const isEditing = editingCell === cellKey;
                    const isEditable = editableColumns.includes(col);
                    const value = row[col];

                    return (
                      <TableCell
                        key={col}
                        onDoubleClick={() => handleDoubleClick(row.id, col, value)}
                        className={`${
                          isEditable ? "cursor-pointer hover:bg-accent/50" : ""
                        } whitespace-nowrap`}
                      >
                        {isEditing ? (
                          <Input
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onBlur={() => handleSave(row.id, col, value)}
                            onKeyDown={(e) => handleKeyDown(e, row.id, col, value)}
                            autoFocus
                            className="h-8 w-full"
                          />
                        ) : (
                          <span className="block truncate max-w-xs">
                            {value?.toString() || "-"}
                          </span>
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Pagination */}
      <ComponentId id="grid-pagination" type="pagination">
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Showing {page * pageSize + 1} to {Math.min((page + 1) * pageSize, totalCount)} of{" "}
            {totalCount} records
          </div>
          <div className="flex gap-2">
            <ComponentId id="grid-prev-btn" type="button">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(page - 1)}
                disabled={page === 0}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
            </ComponentId>
            <ComponentId id="grid-next-btn" type="button">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(page + 1)}
                disabled={page >= totalPages - 1}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </ComponentId>
          </div>
        </div>
      </ComponentId>
    </div>
  );
};
