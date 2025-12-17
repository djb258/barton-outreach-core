import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MetricsHeader } from "@/components/MetricsHeader";
import { EditableGrid } from "@/components/EditableGrid";
import { TableToolbar } from "@/components/TableToolbar";
import { useSupabaseTable } from "@/hooks/useSupabaseTable";
import { NavLink } from "@/components/NavLink";
import { ComponentId } from "@/components/ComponentId";

const DataOpsDashboard = () => {
  // People needs enrichment table
  const peopleTable = useSupabaseTable({
    tableName: "people_needs_enrichment",
    pageSize: 500,
    orderBy: "created_at",
    orderAscending: false,
  });

  // Company needs enrichment table
  const companyTable = useSupabaseTable({
    tableName: "company_needs_enrichment",
    pageSize: 500,
    orderBy: "created_at",
    orderAscending: false,
  });

  // Enrichment log table
  const enrichmentLogTable = useSupabaseTable({
    tableName: "enrichment_log",
    pageSize: 500,
    orderBy: "created_at",
    orderAscending: false,
  });

  // Monthly update log table
  const monthlyUpdateTable = useSupabaseTable({
    tableName: "monthly_update_log",
    pageSize: 500,
    orderBy: "created_at",
    orderAscending: false,
  });

  // Define columns for each table
  const peopleColumns = [
    "id",
    "state",
    "email",
    "linkedin_url",
    "first_name",
    "last_name",
    "title",
    "validated",
    "created_at",
  ];

  const companyColumns = [
    "id",
    "state",
    "company_name",
    "company_domain",
    "company_linkedin_url",
    "validated",
    "created_at",
  ];

  const enrichmentLogColumns = [
    "id",
    "entity_id",
    "tool",
    "cost",
    "status",
    "created_at",
  ];

  const monthlyUpdateLogColumns = [
    "id",
    "entity_id",
    "entity_type",
    "change_type",
    "old_value",
    "new_value",
    "created_at",
  ];

  // Define editable columns
  const peopleEditableColumns = ["email", "linkedin_url", "first_name", "last_name", "title"];
  const companyEditableColumns = ["company_name", "company_domain", "company_linkedin_url"];
  const enrichmentLogEditableColumns: string[] = [];
  const monthlyUpdateEditableColumns: string[] = [];

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        {/* Header */}
        <ComponentId id="dataops-header" type="section" path="DataOps Dashboard > Header">
          <div className="mb-8">
            <div className="flex items-center gap-4 mb-4">
              <ComponentId id="dataops-nav-back-link" type="link">
                <NavLink to="/">← Back to Home</NavLink>
              </ComponentId>
            </div>
            <h1 className="text-4xl font-bold mb-2">DataOps Dashboard</h1>
            <p className="text-muted-foreground">
              View, edit, and analyze enrichment data with spreadsheet-style interface
            </p>
          </div>
        </ComponentId>

        {/* Metrics */}
        <ComponentId id="dataops-metrics" type="section">
          <MetricsHeader />
        </ComponentId>

        {/* Tables */}
        <ComponentId id="dataops-tabs" type="tabs" path="DataOps Dashboard > Tabs">
          <Tabs defaultValue="people" className="space-y-6">
            <ComponentId id="dataops-tabs-list" type="list">
              <TabsList className="grid w-full grid-cols-4">
                <ComponentId id="dataops-tab-people" type="tab-trigger">
                  <TabsTrigger value="people">People Enrichment</TabsTrigger>
                </ComponentId>
                <ComponentId id="dataops-tab-companies" type="tab-trigger">
                  <TabsTrigger value="companies">Company Enrichment</TabsTrigger>
                </ComponentId>
                <ComponentId id="dataops-tab-enrichment" type="tab-trigger">
                  <TabsTrigger value="enrichment">Enrichment Logs</TabsTrigger>
                </ComponentId>
                <ComponentId id="dataops-tab-monthly" type="tab-trigger">
                  <TabsTrigger value="monthly">Monthly Updates</TabsTrigger>
                </ComponentId>
              </TabsList>
            </ComponentId>

          {/* People Needs Enrichment */}
          <TabsContent value="people" className="space-y-4">
            <ComponentId id="dataops-people-toolbar" type="toolbar">
              <TableToolbar
                onRefresh={peopleTable.refresh}
                data={peopleTable.data}
                tableName="people_needs_enrichment"
                isLoading={peopleTable.isLoading}
              />
            </ComponentId>
            <ComponentId id="dataops-people-grid" type="grid">
              <EditableGrid
                data={peopleTable.data}
                columns={peopleColumns}
                editableColumns={peopleEditableColumns}
                onCellEdit={peopleTable.updateCell}
                page={peopleTable.page}
                pageSize={peopleTable.pageSize}
                totalCount={peopleTable.totalCount}
                onPageChange={peopleTable.setPage}
                isLoading={peopleTable.isLoading}
              />
            </ComponentId>
          </TabsContent>

          {/* Company Needs Enrichment */}
          <TabsContent value="companies" className="space-y-4">
            <ComponentId id="dataops-companies-toolbar" type="toolbar">
              <TableToolbar
                onRefresh={companyTable.refresh}
                data={companyTable.data}
                tableName="company_needs_enrichment"
                isLoading={companyTable.isLoading}
              />
            </ComponentId>
            <ComponentId id="dataops-companies-grid" type="grid">
              <EditableGrid
                data={companyTable.data}
                columns={companyColumns}
                editableColumns={companyEditableColumns}
                onCellEdit={companyTable.updateCell}
                page={companyTable.page}
                pageSize={companyTable.pageSize}
                totalCount={companyTable.totalCount}
                onPageChange={companyTable.setPage}
                isLoading={companyTable.isLoading}
              />
            </ComponentId>
          </TabsContent>

          {/* Enrichment Log */}
          <TabsContent value="enrichment" className="space-y-4">
            <ComponentId id="dataops-enrichment-toolbar" type="toolbar">
              <TableToolbar
                onRefresh={enrichmentLogTable.refresh}
                data={enrichmentLogTable.data}
                tableName="enrichment_log"
                isLoading={enrichmentLogTable.isLoading}
              />
            </ComponentId>
            <ComponentId id="dataops-enrichment-grid" type="grid">
              <EditableGrid
                data={enrichmentLogTable.data}
                columns={enrichmentLogColumns}
                editableColumns={enrichmentLogEditableColumns}
                onCellEdit={enrichmentLogTable.updateCell}
                page={enrichmentLogTable.page}
                pageSize={enrichmentLogTable.pageSize}
                totalCount={enrichmentLogTable.totalCount}
                onPageChange={enrichmentLogTable.setPage}
                isLoading={enrichmentLogTable.isLoading}
              />
            </ComponentId>
          </TabsContent>

          {/* Monthly Update Log */}
          <TabsContent value="monthly" className="space-y-4">
            <ComponentId id="dataops-monthly-toolbar" type="toolbar">
              <TableToolbar
                onRefresh={monthlyUpdateTable.refresh}
                data={monthlyUpdateTable.data}
                tableName="monthly_update_log"
                isLoading={monthlyUpdateTable.isLoading}
              />
            </ComponentId>
            <ComponentId id="dataops-monthly-grid" type="grid">
              <EditableGrid
                data={monthlyUpdateTable.data}
                columns={monthlyUpdateLogColumns}
                editableColumns={monthlyUpdateEditableColumns}
                onCellEdit={monthlyUpdateTable.updateCell}
                page={monthlyUpdateTable.page}
                pageSize={monthlyUpdateTable.pageSize}
                totalCount={monthlyUpdateTable.totalCount}
                onPageChange={monthlyUpdateTable.setPage}
                isLoading={monthlyUpdateTable.isLoading}
              />
            </ComponentId>
          </TabsContent>
          </Tabs>
        </ComponentId>
      </div>
    </div>
  );
};

export default DataOpsDashboard;
