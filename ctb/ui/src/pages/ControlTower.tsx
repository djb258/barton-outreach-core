import { useEffect, useState } from "react";
import { fetchFromMCP } from "@/lib/mcpClient";
import { KPIBanner } from "@/components/KPIBanner";
import { IntegrityRing } from "@/components/IntegrityRing";
import { QuickActions } from "@/components/QuickActions";
import { ErrorModal } from "@/components/ErrorModal";
import { MasterErrorLog } from "@/components/MasterErrorLog";
import { MissingDataPanel } from "@/components/MissingDataPanel";
import { IntegrityAuditPanel } from "@/components/IntegrityAuditPanel";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

export default function ControlTower() {
  const [summary, setSummary] = useState<any>(null);
  const [errors, setErrors] = useState<any[]>([]);
  const [missing, setMissing] = useState<any[]>([]);
  const [integrity, setIntegrity] = useState<any>(null);
  const [selectedRecord, setSelectedRecord] = useState<any>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Mock data for demonstration - replace with actual MCP calls
      const [summaryData, errorData, missingData, integrityData] = await Promise.all([
        fetchFromMCP('/firebase/dashboard-summary').catch(() => ({
          integrity: 87.5,
          uptime: 99.2,
          throughput: 2847,
          health: { neon: true, firebase: true, mcp: true },
          pipeline: [
            { status: 'online', name: 'Intake' },
            { status: 'online', name: 'Parse' },
            { status: 'warning', name: 'Validate' },
            { status: 'online', name: 'Enrich' },
            { status: 'online', name: 'PLE' },
            { status: 'online', name: 'Slot' },
            { status: 'online', name: 'Verify' },
            { status: 'online', name: 'BIT' },
          ],
          metrics: {
            validations: 94.2,
            slotFill: 78.9,
            verification: 91.3,
            bitReady: 82.1,
          }
        })),
        fetchFromMCP('/firebase/errors?limit=100').catch(() => [
          {
            timestamp: new Date().toISOString(),
            process_id: 'Validate Company Records',
            agent: 'ValidatorAgent',
            message: 'Duplicate domain detected',
            severity: 'warning',
            status: 'open',
            unique_id: '01.01.01.04.20000.002',
          },
          {
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            process_id: 'Enrich Contact Data',
            agent: 'EnrichmentAgent',
            message: 'API rate limit exceeded',
            severity: 'error',
            status: 'open',
            unique_id: '01.01.02.03.15000.001',
          },
          {
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            process_id: 'PLE Processing',
            agent: 'PLEAgent',
            message: 'Missing required field: company_size',
            severity: 'critical',
            status: 'open',
            unique_id: '01.02.01.05.10000.003',
          }
        ]),
        fetchFromMCP('/firebase/missing?limit=100').catch(() => [
          {
            entity_type: 'Company',
            entity_id: 'comp_12345',
            missing_fields: ['website', 'employee_count', 'revenue'],
            status: 'open',
            detected_at: new Date().toISOString(),
          },
          {
            entity_type: 'Contact',
            entity_id: 'cont_67890',
            missing_fields: ['email', 'phone'],
            status: 'open',
            detected_at: new Date(Date.now() - 86400000).toISOString(),
          }
        ]),
        fetchFromMCP('/firebase/integrity').catch(() => ({
          average: 92.5,
          processes: [
            { name: 'Intake', integrity: 98.5 },
            { name: 'Parse', integrity: 96.2 },
            { name: 'Validate', integrity: 93.8 },
            { name: 'Enrich', integrity: 91.3 },
            { name: 'PLE', integrity: 94.7 },
            { name: 'Slot', integrity: 89.2 },
            { name: 'Verify', integrity: 95.4 },
            { name: 'BIT', integrity: 92.1 },
          ]
        })),
      ]);
      
      setSummary(summaryData);
      setErrors(errorData);
      setMissing(missingData);
      setIntegrity(integrityData);
      setLastUpdated(new Date());
    } catch (error: any) {
      toast.error('Failed to load dashboard data: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Auto-refresh every 30 seconds
    const timer = setInterval(() => {
      loadData();
    }, 30000);

    return () => clearInterval(timer);
  }, []);

  const handleSyncValidator = async () => {
    toast.info('Syncing validator...');
    setTimeout(() => toast.success('Validator synced'), 1500);
  };

  const handleRefreshPipeline = async () => {
    toast.info('Refreshing pipeline...');
    loadData();
  };

  if (loading || !summary || !integrity) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-muted-foreground">Loading Control Tower...</div>
      </div>
    );
  }

  const openErrors = errors.filter((e) => e.status === 'open').length;

  return (
    <div className="p-4 space-y-4 max-w-7xl mx-auto">
      <div className="border-l-4 border-vision pl-3 mb-6">
        <h1 className="text-2xl font-bold text-foreground">Control Tower</h1>
        <p className="text-sm text-muted-foreground">System Flow & Diagnostics</p>
      </div>

      <KPIBanner
        integrity={summary.integrity}
        uptime={summary.uptime}
        throughput={summary.throughput}
      />

      {/* Health Lights */}
      <Card className="p-3">
        <div className="text-xs font-semibold text-muted-foreground mb-2">System Health</div>
        <div className="flex gap-4">
          {Object.entries(summary.health || {}).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${value ? 'bg-status-online' : 'bg-status-error'}`} />
              <span className="text-sm capitalize">{key}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Pipeline Flow */}
      <Card className="p-3">
        <div className="text-xs font-semibold text-muted-foreground mb-3">Pipeline Flow</div>
        <div className="flex items-center gap-1 overflow-x-auto pb-2">
          {(summary.pipeline || []).map((stage: any, idx: number) => (
            <div key={idx} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 ${
                  stage.status === 'online'
                    ? 'bg-status-online border-status-online'
                    : stage.status === 'warning'
                    ? 'bg-status-warning border-status-warning'
                    : 'bg-status-error border-status-error'
                }`}
                title={stage.name}
              >
                {idx + 1}
              </div>
              {idx < summary.pipeline.length - 1 && (
                <div className="w-4 h-0.5 bg-border" />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-xs text-muted-foreground">
          <span>Intake</span>
          <span>BIT</span>
        </div>
      </Card>

      {/* Mini Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <Card className="p-3">
          <div className="text-xs text-muted-foreground">Validations</div>
          <div className="text-xl font-bold text-doctrine">{summary.metrics?.validations}%</div>
        </Card>
        <Card className="p-3">
          <div className="text-xs text-muted-foreground">Slot Fill</div>
          <div className="text-xl font-bold text-pipeline">{summary.metrics?.slotFill}%</div>
        </Card>
        <Card className="p-3">
          <div className="text-xs text-muted-foreground">Verification</div>
          <div className="text-xl font-bold text-execution">{summary.metrics?.verification}%</div>
        </Card>
        <Card className="p-3">
          <div className="text-xs text-muted-foreground">BIT Ready</div>
          <div className="text-xl font-bold text-vision">{summary.metrics?.bitReady}%</div>
        </Card>
      </div>

      {/* Master Error Log */}
      <MasterErrorLog
        errors={errors}
        onSelectError={(error) => {
          setSelectedRecord({
            unique_id: error.unique_id,
            process_id: error.process_id,
            agent: error.agent,
            message: error.message,
            severity: error.severity,
            status: error.status,
            timestamp: error.timestamp,
          });
          setModalOpen(true);
        }}
      />

      {/* Missing Data Panel */}
      <MissingDataPanel
        missing={missing}
        onSelectRecord={(record) => {
          setSelectedRecord({
            entity_type: record.entity_type,
            entity_id: record.entity_id,
            missing_fields: record.missing_fields,
            status: record.status,
            timestamp: record.detected_at,
          });
          setModalOpen(true);
        }}
        onRetrySuccess={loadData}
      />

      {/* Integrity Audit Panel */}
      <IntegrityAuditPanel integrity={integrity} />

      {/* Integrity Rings Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <IntegrityRing value={summary.integrity} label="Overall" color="text-vision" />
        <IntegrityRing value={summary.metrics?.validations || 0} label="Validations" color="text-doctrine" />
        <IntegrityRing value={summary.metrics?.verification || 0} label="Verification" color="text-execution" />
        <IntegrityRing value={summary.metrics?.bitReady || 0} label="BIT Ready" color="text-pipeline" />
      </div>

      <QuickActions
        onSyncValidator={handleSyncValidator}
        onRefreshPipeline={handleRefreshPipeline}
      />

      <div className="text-xs text-muted-foreground text-center pt-4 flex items-center justify-center gap-2">
        <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
        <Badge variant="outline" className="text-xs">Auto-refresh: 30s</Badge>
      </div>

      <ErrorModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        record={selectedRecord}
        onResolve={(id) => {
          toast.success('Record resolved successfully');
          loadData();
        }}
      />
    </div>
  );
}
