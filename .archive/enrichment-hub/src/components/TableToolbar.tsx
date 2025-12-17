import { Button } from "@/components/ui/button";
import { RefreshCw, Download } from "lucide-react";
import { exportToCSV } from "@/lib/exportUtils";
import { ComponentId } from "@/components/ComponentId";

interface TableToolbarProps {
  onRefresh: () => void;
  data: any[];
  tableName: string;
  isLoading?: boolean;
}

export const TableToolbar = ({
  onRefresh,
  data,
  tableName,
  isLoading,
}: TableToolbarProps) => {
  const handleExport = () => {
    exportToCSV(data, tableName);
  };

  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex gap-2">
        <ComponentId id={`${tableName}-refresh-btn`} type="button">
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </ComponentId>
        <ComponentId id={`${tableName}-export-btn`} type="button">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            disabled={!data || data.length === 0}
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </ComponentId>
      </div>
    </div>
  );
};
