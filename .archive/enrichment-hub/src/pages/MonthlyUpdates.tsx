import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ChangeTable } from "@/components/ChangeTable";
import { useMonthlyUpdates } from "@/hooks/useMonthlyUpdates";
import { supabase } from "@/integrations/supabase/client";
import { NavLink } from "@/components/NavLink";
import { Calendar, Database, DollarSign, CheckCircle } from "lucide-react";
import { ComponentId } from "@/components/ComponentId";

const STATES = ["WV", "PA", "OH", "MD", "VA", "KY"];
const TOOLS = ["Apollo", "Clay", "Firecrawl", "MillionVerify"];

interface UpdateStats {
  records_checked: number;
  changes_found: number;
  promoted: number;
  cost_usd: number;
}

export default function MonthlyUpdates() {
  const [entity, setEntity] = useState<"people" | "companies">("people");
  const [state, setState] = useState<string>("WV");
  const [tool, setTool] = useState<string>("Apollo");
  const [batchSize, setBatchSize] = useState<number>(100);
  const [stats, setStats] = useState<UpdateStats>({
    records_checked: 0,
    changes_found: 0,
    promoted: 0,
    cost_usd: 0,
  });

  const {
    updates,
    isLoading,
    isRunning,
    runUpdateCheck,
    approveUpdate,
    approveAll,
    promoteUpdates,
  } = useMonthlyUpdates(entity);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    const { data } = await supabase
      .from("monthly_update_log")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(10);

    if (data && data.length > 0) {
      const totals = data.reduce(
        (acc, log) => ({
          records_checked: acc.records_checked + (log.records_checked || 0),
          changes_found: acc.changes_found + (log.changes_found || 0),
          promoted: acc.promoted + (log.promoted || 0),
          cost_usd: acc.cost_usd + (Number(log.cost_usd) || 0),
        }),
        { records_checked: 0, changes_found: 0, promoted: 0, cost_usd: 0 }
      );
      setStats(totals);
    }
  };

  const handleRunUpdate = async () => {
    await runUpdateCheck(state, tool, batchSize);
    fetchStats();
  };

  const handlePromoteAll = async () => {
    const approvedIds = updates
      .filter((u) => u.approved)
      .map((u) => u.id);
    
    if (approvedIds.length > 0) {
      await promoteUpdates(approvedIds);
      fetchStats();
    }
  };

  const handlePromote = async (id: string) => {
    await promoteUpdates([id]);
    fetchStats();
  };

  const pendingCount = updates.filter((u) => !u.approved).length;
  const approvedCount = updates.filter((u) => u.approved).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-accent/5">
      <ComponentId id="monthly-header" type="header" path="Monthly Updates > Header">
        <nav className="border-b bg-card/50 backdrop-blur">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center gap-6">
              <h1 className="text-xl font-bold text-foreground">
                SVG Enrichment Workbench
              </h1>
              <div className="flex gap-4">
                <ComponentId id="monthly-nav-enrichment" type="link">
                  <NavLink
                    to="/"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                    activeClassName="text-foreground font-semibold"
                  >
                    Enrichment Queue
                  </NavLink>
                </ComponentId>
                <ComponentId id="monthly-nav-monthly" type="link">
                  <NavLink
                    to="/monthly-updates"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                    activeClassName="text-foreground font-semibold"
                  >
                    Monthly Updates
                  </NavLink>
                </ComponentId>
                <ComponentId id="monthly-nav-dataops" type="link">
                  <NavLink
                    to="/dataops"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                    activeClassName="text-foreground font-semibold"
                  >
                    DataOps Dashboard
                  </NavLink>
                </ComponentId>
              </div>
            </div>
          </div>
        </nav>
      </ComponentId>

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2 text-foreground">
            Monthly Update Console
          </h2>
          <p className="text-muted-foreground">
            Neon Maintenance — Scheduled enrichment checks on validated records
          </p>
        </div>

        {/* Stats Cards */}
        <ComponentId id="monthly-metrics" type="section">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <ComponentId id="monthly-metrics-checked-card" type="card">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">
                    Records Checked
                  </CardTitle>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.records_checked}</div>
                </CardContent>
              </Card>
            </ComponentId>

            <ComponentId id="monthly-metrics-changes-card" type="card">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">
                    Changes Found
                  </CardTitle>
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.changes_found}</div>
                </CardContent>
              </Card>
            </ComponentId>

            <ComponentId id="monthly-metrics-promoted-card" type="card">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Promoted</CardTitle>
                  <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.promoted}</div>
                </CardContent>
              </Card>
            </ComponentId>

            <ComponentId id="monthly-metrics-cost-card" type="card">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    ${stats.cost_usd.toFixed(2)}
                  </div>
                </CardContent>
              </Card>
            </ComponentId>
          </div>
        </ComponentId>

        {/* Control Panel */}
        <ComponentId id="monthly-controls" type="section">
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Run Update Check</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
                <div>
                  <Label htmlFor="entity">Entity</Label>
                  <ComponentId id="monthly-entity-dropdown" type="select">
                    <Select
                      value={entity}
                      onValueChange={(value) =>
                        setEntity(value as "people" | "companies")
                      }
                    >
                      <SelectTrigger id="entity">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="people">People</SelectItem>
                        <SelectItem value="companies">Companies</SelectItem>
                      </SelectContent>
                    </Select>
                  </ComponentId>
                </div>

                <div>
                  <Label htmlFor="state">State</Label>
                  <ComponentId id="monthly-state-dropdown" type="select">
                    <Select value={state} onValueChange={setState}>
                      <SelectTrigger id="state">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {STATES.map((s) => (
                          <SelectItem key={s} value={s}>
                            {s}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </ComponentId>
                </div>

                <div>
                  <Label htmlFor="tool">Tool</Label>
                  <ComponentId id="monthly-tool-dropdown" type="select">
                    <Select value={tool} onValueChange={setTool}>
                      <SelectTrigger id="tool">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {TOOLS.map((t) => (
                          <SelectItem key={t} value={t}>
                            {t}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </ComponentId>
                </div>

                <div>
                  <Label htmlFor="batchSize">Batch Size</Label>
                  <ComponentId id="monthly-batch-input" type="input">
                    <Input
                      id="batchSize"
                      type="number"
                      value={batchSize}
                      onChange={(e) => setBatchSize(parseInt(e.target.value) || 100)}
                      min={1}
                      max={100}
                    />
                  </ComponentId>
                </div>

                <div className="flex items-end">
                  <ComponentId id="monthly-run-btn" type="button">
                    <Button
                      onClick={handleRunUpdate}
                      disabled={isRunning || isLoading}
                      className="w-full"
                    >
                      {isRunning ? "Running..." : "Run Update Check"}
                    </Button>
                  </ComponentId>
                </div>
              </div>

              <div className="flex gap-2 justify-between items-center pt-4 border-t">
                <div className="text-sm text-muted-foreground">
                  {pendingCount} pending • {approvedCount} approved
                </div>
                <div className="flex gap-2">
                  <ComponentId id="monthly-approve-all-btn" type="button">
                    <Button
                      variant="outline"
                      onClick={approveAll}
                      disabled={pendingCount === 0 || isRunning}
                    >
                      Approve All
                    </Button>
                  </ComponentId>
                  <ComponentId id="monthly-promote-btn" type="button">
                    <Button
                      onClick={handlePromoteAll}
                      disabled={approvedCount === 0 || isRunning}
                    >
                      Promote All Approved
                    </Button>
                  </ComponentId>
                </div>
              </div>
            </CardContent>
          </Card>
        </ComponentId>

        {/* Changes Table */}
        <ComponentId id="monthly-changes-table" type="table">
          <Card>
            <CardHeader>
              <CardTitle>Change Review</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="text-center py-8 text-muted-foreground">
                  Loading updates...
                </div>
              ) : (
                <ChangeTable
                  updates={updates}
                  onApprove={approveUpdate}
                  onPromote={handlePromote}
                  isRunning={isRunning}
                />
              )}
            </CardContent>
          </Card>
        </ComponentId>
      </div>
    </div>
  );
}
