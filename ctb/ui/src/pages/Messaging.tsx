import { useState, useEffect } from "react";
import { fetchFromMCP } from "@/lib/mcpClient";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BilatoTemplateList } from "@/components/messaging/BilatoTemplateList";
import { BilatoEditor } from "@/components/messaging/BilatoEditor";
import { MetricsCards } from "@/components/messaging/MetricsCards";
import { CampaignTable } from "@/components/messaging/CampaignTable";
import { OutboundErrorFeed } from "@/components/messaging/OutboundErrorFeed";
import { ComparisonChart } from "@/components/messaging/ComparisonChart";
import { toast } from "sonner";
import { RefreshCw, Plus, Eye, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface Template {
  id: string;
  title: string;
  subject: string;
  status: 'active' | 'draft' | 'archived';
  content: string;
}

export default function Messaging() {
  const [bilato, setBilato] = useState<Template[]>([]);
  const [instantly, setInstantly] = useState<any>(null);
  const [heyreach, setHeyreach] = useState<any>(null);
  const [errors, setErrors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      
      const [templatesData, instantlyData, heyreachData, errorsData] = await Promise.all([
        fetchFromMCP('/firebase/bilato/templates').catch(() => [
          {
            id: 'tpl_001',
            title: 'Welcome Sequence Day 1',
            subject: 'Welcome to {{company}}!',
            status: 'active',
            content: 'Hi {{first_name}},\n\nWelcome to our platform! We\'re excited to have you here.\n\nBest regards,\nThe Team'
          },
          {
            id: 'tpl_002',
            title: 'Follow-up Email',
            subject: 'Quick question, {{first_name}}',
            status: 'active',
            content: 'Hi {{first_name}},\n\nI wanted to follow up on our previous conversation...\n\nLooking forward to hearing from you.'
          },
          {
            id: 'tpl_003',
            title: 'Re-engagement Campaign',
            subject: 'We miss you at {{company}}',
            status: 'draft',
            content: 'Hi {{first_name}},\n\nIt\'s been a while since we last connected...'
          }
        ]),
        fetchFromMCP('/firebase/instantly/metrics').catch(() => ({
          openRate: 42.3,
          replyRate: 8.7,
          bounceRate: 2.1,
          campaigns: [
            { id: '1', name: 'Q4 Outreach Wave 1', status: 'active', sent: 1250, opened: 520, replied: 95, created_at: new Date().toISOString() },
            { id: '2', name: 'Follow-up Sequence', status: 'active', sent: 850, opened: 380, replied: 72, created_at: new Date(Date.now() - 86400000).toISOString() },
            { id: '3', name: 'Re-engagement Series', status: 'paused', sent: 650, opened: 210, replied: 45, created_at: new Date(Date.now() - 172800000).toISOString() },
          ]
        })),
        fetchFromMCP('/firebase/heyreach/metrics').catch(() => ({
          connectionRate: 31.5,
          replyRate: 12.3,
          rejectRate: 5.8,
          campaigns: [
            { id: '1', name: 'LinkedIn Outreach A', status: 'running', sent: 320, replied: 42, created_at: new Date().toISOString() },
            { id: '2', name: 'Targeted Connection Drive', status: 'running', sent: 280, replied: 35, created_at: new Date(Date.now() - 86400000).toISOString() },
            { id: '3', name: 'Industry Leaders', status: 'completed', sent: 150, replied: 19, created_at: new Date(Date.now() - 259200000).toISOString() },
          ]
        })),
        fetchFromMCP('/firebase/errors?source=outbound').catch(() => [
          {
            id: 'err_001',
            timestamp: new Date().toISOString(),
            source: 'instantly',
            message: 'Rate limit exceeded on domain validation',
            severity: 'warning'
          },
          {
            id: 'err_002',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            source: 'heyreach',
            message: 'Connection request failed: Profile not accessible',
            severity: 'error'
          }
        ]),
      ]);
      
      setBilato(templatesData);
      setInstantly(instantlyData);
      setHeyreach(heyreachData);
      setErrors(errorsData);
      setLastUpdated(new Date());
    } catch (error: any) {
      toast.error('Failed to load messaging data: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Optional auto-refresh for metrics only (60s)
    const timer = setInterval(() => {
      fetchFromMCP('/firebase/instantly/metrics').then(setInstantly).catch(() => {});
      fetchFromMCP('/firebase/heyreach/metrics').then(setHeyreach).catch(() => {});
    }, 60000);

    return () => clearInterval(timer);
  }, []);

  const handleSendTest = async (templateId: string) => {
    try {
      await fetchFromMCP('/firebase/bilato/send-test', {
        method: 'POST',
        body: JSON.stringify({ template_id: templateId }),
      });
      toast.success('Test message sent via Bilato MCP relay!');
    } catch (error: any) {
      toast.error('Failed to send test: ' + error.message);
    }
  };

  const handleSaveTemplate = async (template: Template) => {
    try {
      await fetchFromMCP('/firebase/bilato/templates/update', {
        method: 'POST',
        body: JSON.stringify(template),
      });
      toast.success('Template saved successfully');
      setIsEditing(false);
      setEditingTemplate(null);
      loadData();
    } catch (error: any) {
      toast.error('Failed to save template: ' + error.message);
    }
  };

  const handlePreview = (template: Template) => {
    setPreviewTemplate(template);
    setIsPreviewOpen(true);
  };

  const renderPreviewContent = (content: string) => {
    return content
      .replace(/{{first_name}}/g, 'John')
      .replace(/{{last_name}}/g, 'Doe')
      .replace(/{{company}}/g, 'Acme Corp')
      .replace(/{{title}}/g, 'CEO')
      .replace(/{{industry}}/g, 'Technology');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-muted-foreground">Loading Messaging...</div>
      </div>
    );
  }

  const instantlyMetrics = [
    { label: 'Open Rate', value: instantly?.openRate || 0, color: 'info' },
    { label: 'Reply Rate', value: instantly?.replyRate || 0, color: 'success' },
    { label: 'Bounce Rate', value: instantly?.bounceRate || 0, color: 'error' },
  ];

  const heyreachMetrics = [
    { label: 'Connection Rate', value: heyreach?.connectionRate || 0, color: 'info' },
    { label: 'Reply Rate', value: heyreach?.replyRate || 0, color: 'success' },
    { label: 'Reject Rate', value: heyreach?.rejectRate || 0, color: 'error' },
  ];

  return (
    <div className="p-4 space-y-4 max-w-7xl mx-auto">
      <div className="border-l-4 border-execution pl-3 mb-6">
        <h1 className="text-2xl font-bold text-foreground">Messaging & Outbound Performance</h1>
        <p className="text-sm text-muted-foreground">Template management and cross-channel analytics</p>
      </div>

      <Tabs defaultValue="bilato" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="bilato">Bilato</TabsTrigger>
          <TabsTrigger value="instantly">Instantly</TabsTrigger>
          <TabsTrigger value="heyreach">HeyReach</TabsTrigger>
        </TabsList>

        <TabsContent value="bilato" className="space-y-4 mt-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-execution">Template Management</h2>
            <div className="flex gap-2">
              <Button 
                size="sm" 
                onClick={() => {
                  setEditingTemplate(null);
                  setIsEditing(true);
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                New Template
              </Button>
              <Button variant="outline" size="sm" onClick={loadData}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>

          {isEditing ? (
            <BilatoEditor
              template={editingTemplate}
              onSave={handleSaveTemplate}
              onCancel={() => {
                setIsEditing(false);
                setEditingTemplate(null);
              }}
            />
          ) : (
            <BilatoTemplateList
              templates={bilato}
              onEdit={(template) => {
                setEditingTemplate(template);
                setIsEditing(true);
              }}
              onPreview={handlePreview}
              onSendTest={handleSendTest}
            />
          )}

          <OutboundErrorFeed errors={errors} source="bilato" />
        </TabsContent>

        <TabsContent value="instantly" className="space-y-4 mt-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-execution">Instantly Analytics</h2>
            <Button variant="outline" size="sm" onClick={loadData}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>

          <MetricsCards metrics={instantlyMetrics} />
          
          <CampaignTable 
            campaigns={instantly?.campaigns || []} 
            title="Recent Campaigns"
          />

          <OutboundErrorFeed errors={errors} source="instantly" />
        </TabsContent>

        <TabsContent value="heyreach" className="space-y-4 mt-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-execution">HeyReach Analytics</h2>
            <Button variant="outline" size="sm" onClick={loadData}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>

          <MetricsCards metrics={heyreachMetrics} />
          
          <CampaignTable 
            campaigns={heyreach?.campaigns || []} 
            title="Recent Campaigns"
          />

          <OutboundErrorFeed errors={errors} source="heyreach" />
        </TabsContent>
      </Tabs>

      {/* Unified Comparison Chart */}
      <ComparisonChart
        instantlyMetrics={{
          openRate: instantly?.openRate,
          replyRate: instantly?.replyRate,
          bounceRate: instantly?.bounceRate,
        }}
        heyreachMetrics={{
          connectionRate: heyreach?.connectionRate,
          replyRate: heyreach?.replyRate,
          rejectRate: heyreach?.rejectRate,
        }}
      />

      <div className="text-xs text-muted-foreground text-center pt-4 flex items-center justify-center gap-2">
        <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
        <Badge variant="outline" className="text-xs">Auto-refresh: 60s</Badge>
      </div>

      {/* Preview Dialog */}
      <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-execution">Template Preview</DialogTitle>
          </DialogHeader>
          
          {previewTemplate && (
            <div className="space-y-4">
              <Card className="p-3 bg-muted/50">
                <div className="text-xs text-muted-foreground mb-1">Subject</div>
                <div className="text-sm font-medium">
                  {renderPreviewContent(previewTemplate.subject)}
                </div>
              </Card>

              <Card className="p-4 bg-card">
                <div className="text-xs text-muted-foreground mb-2">Message Body</div>
                <div className="text-sm whitespace-pre-wrap">
                  {renderPreviewContent(previewTemplate.content)}
                </div>
              </Card>

              <div className="flex justify-between items-center pt-2">
                <p className="text-xs text-muted-foreground">
                  Variables have been replaced with sample data
                </p>
                <Button variant="outline" onClick={() => setIsPreviewOpen(false)}>
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
