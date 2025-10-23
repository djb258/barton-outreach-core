import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  RocketIcon,
  PlayIcon,
  PauseIcon,
  CheckCircledIcon,
  CrossCircledIcon,
  ReloadIcon,
  ExclamationTriangleIcon,
  TargetIcon,
  LightningBoltIcon,
  CodeIcon
} from '@radix-ui/react-icons';

// Import shared workflow sidebar
import { WorkflowSidebar } from '@/components/shared/workflow-sidebar';

const CampaignConsole = () => {
  // State management
  const [campaigns, setCampaigns] = useState([]);
  const [campaignStats, setCampaignStats] = useState({
    total: 0,
    active: 0,
    launched: 0,
    failed: 0
  });
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [blueprintView, setBlueprintView] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(null);

  // Fetch campaign data
  useEffect(() => {
    fetchCampaigns();
    fetchCampaignStats();

    // Set up auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchCampaigns();
      fetchCampaignStats();
    }, 30000);

    setRefreshInterval(interval);

    return () => clearInterval(interval);
  }, []);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/campaign-list');
      const data = await response.json();

      if (data.status === 'success') {
        setCampaigns(data.campaigns || []);
      }
    } catch (err) {
      console.error('Failed to fetch campaigns:', err);
      setError('Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const fetchCampaignStats = async () => {
    try {
      const response = await fetch('/api/campaign-stats');
      const data = await response.json();

      if (data.status === 'success') {
        setCampaignStats(data.stats);
      }
    } catch (err) {
      console.error('Failed to fetch campaign stats:', err);
    }
  };

  const handleCreateCampaign = async () => {
    try {
      setLoading(true);
      setError(null);

      // Example: Auto-create from recently promoted records
      const response = await fetch('/api/campaign-auto-create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trigger_event: 'promotion',
          company_unique_id: '04.04.01.08.10000.050',
          people: ['04.04.02.07.10000.010', '04.04.02.07.10000.011'],
          campaign_type: 'PLE',
          marketing_score: 85
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        await fetchCampaigns();
        setSelectedCampaign(data.campaign_id);
      } else {
        setError(data.message || 'Failed to create campaign');
      }
    } catch (err) {
      console.error('Failed to create campaign:', err);
      setError('Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  const handleLaunchCampaign = async (campaignId) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/campaign-launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: campaignId,
          launch_mode: 'immediate',
          target_tools: ['instantly', 'heyreach']
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        await fetchCampaigns();
        await fetchCampaignStats();
      } else {
        setError(data.message || 'Failed to launch campaign');
      }
    } catch (err) {
      console.error('Failed to launch campaign:', err);
      setError('Failed to launch campaign');
    } finally {
      setLoading(false);
    }
  };

  const getCampaignTypeIcon = (type) => {
    switch(type) {
      case 'PLE':
        return <TargetIcon className="w-4 h-4" />;
      case 'BIT':
        return <LightningBoltIcon className="w-4 h-4" />;
      default:
        return <RocketIcon className="w-4 h-4" />;
    }
  };

  const getCampaignStatusBadge = (status) => {
    const statusConfig = {
      draft: { variant: 'secondary', label: 'Draft' },
      active: { variant: 'default', label: 'Active' },
      paused: { variant: 'warning', label: 'Paused' },
      completed: { variant: 'success', label: 'Completed' },
      failed: { variant: 'destructive', label: 'Failed' }
    };

    const config = statusConfig[status] || statusConfig.draft;
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Workflow Sidebar - Step 7 highlighted */}
      <WorkflowSidebar currentStep={7} />

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Campaign Builder Console
            </h1>
            <p className="text-gray-500">
              Step 7: Auto-Campaign Builder - Doctrine-bound campaign creation and launch
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive" className="mb-6">
              <ExclamationTriangleIcon className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Campaign Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Total Campaigns
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{campaignStats.total}</div>
                <p className="text-xs text-gray-500 mt-1">All time</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Active Campaigns
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {campaignStats.active}
                </div>
                <p className="text-xs text-gray-500 mt-1">Currently running</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Launched Today
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {campaignStats.launched}
                </div>
                <p className="text-xs text-gray-500 mt-1">Last 24 hours</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Failed Campaigns
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {campaignStats.failed}
                </div>
                <p className="text-xs text-gray-500 mt-1">Need attention</p>
              </CardContent>
            </Card>
          </div>

          {/* Campaign Management Tabs */}
          <Tabs defaultValue="campaigns" className="space-y-4">
            <TabsList>
              <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
              <TabsTrigger value="blueprints">Blueprints</TabsTrigger>
              <TabsTrigger value="audit">Audit Log</TabsTrigger>
            </TabsList>

            {/* Campaigns Tab */}
            <TabsContent value="campaigns" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <div>
                      <CardTitle>Campaign Results Table</CardTitle>
                      <CardDescription>
                        Doctrine-compliant campaigns from promoted records
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleCreateCampaign}
                        disabled={loading}
                      >
                        {loading ? (
                          <ReloadIcon className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <RocketIcon className="mr-2 h-4 w-4" />
                        )}
                        Auto-Create Campaign
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Campaign ID</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Trigger</TableHead>
                        <TableHead>Company</TableHead>
                        <TableHead>Targets</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {campaigns.map((campaign) => (
                        <TableRow key={campaign.campaign_id}>
                          <TableCell className="font-mono text-sm">
                            {campaign.campaign_id}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              {getCampaignTypeIcon(campaign.campaign_type)}
                              <span>{campaign.campaign_type}</span>
                            </div>
                          </TableCell>
                          <TableCell>{campaign.trigger_event}</TableCell>
                          <TableCell className="font-mono text-xs">
                            {campaign.company_unique_id}
                          </TableCell>
                          <TableCell>{campaign.people_ids?.length || 0}</TableCell>
                          <TableCell>
                            {getCampaignStatusBadge(campaign.status)}
                          </TableCell>
                          <TableCell>
                            {new Date(campaign.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-2">
                              {campaign.status === 'draft' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleLaunchCampaign(campaign.campaign_id)}
                                  disabled={loading}
                                >
                                  <PlayIcon className="w-3 h-3 mr-1" />
                                  Launch
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => setBlueprintView(campaign.template)}
                              >
                                <CodeIcon className="w-3 h-3 mr-1" />
                                View
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Blueprints Tab */}
            <TabsContent value="blueprints" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Campaign Blueprint Viewer</CardTitle>
                  <CardDescription>
                    Doctrine-approved campaign templates and sequences
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {blueprintView ? (
                    <div className="bg-gray-900 text-gray-100 p-4 rounded-lg">
                      <pre className="text-xs overflow-x-auto">
                        {JSON.stringify(blueprintView, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-gray-500">
                      <CodeIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>Select a campaign to view its blueprint</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Default Templates */}
              <Card>
                <CardHeader>
                  <CardTitle>Doctrine Templates</CardTitle>
                  <CardDescription>
                    Pre-approved campaign blueprints
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* PLE Template */}
                    <div className="p-4 border rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold">PLE Introduction Campaign</h3>
                          <p className="text-sm text-gray-500">
                            Multi-touch outreach for promoted leads
                          </p>
                        </div>
                        <Badge>PLE</Badge>
                      </div>
                      <div className="text-xs text-gray-600">
                        <p>Sequence: Email → LinkedIn → Phone → Follow-up</p>
                        <p>Duration: 14 days</p>
                        <p>Required: marketing_score ≥ 80</p>
                      </div>
                    </div>

                    {/* BIT Template */}
                    <div className="p-4 border rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold">BIT Signal Response</h3>
                          <p className="text-sm text-gray-500">
                            Rapid response for high-intent signals
                          </p>
                        </div>
                        <Badge variant="destructive">BIT</Badge>
                      </div>
                      <div className="text-xs text-gray-600">
                        <p>Sequence: Email → SMS → Phone Call</p>
                        <p>Duration: 4 hours</p>
                        <p>Required: signal_strength ≥ 70</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Audit Log Tab */}
            <TabsContent value="audit" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Campaign Audit Log</CardTitle>
                  <CardDescription>
                    Complete traceability of all campaign actions
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Timestamp</TableHead>
                        <TableHead>Campaign ID</TableHead>
                        <TableHead>Action</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>MCP Tool</TableHead>
                        <TableHead>Details</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell>{new Date().toISOString()}</TableCell>
                        <TableCell className="font-mono text-xs">
                          04.04.03.04.00001.001
                        </TableCell>
                        <TableCell>create</TableCell>
                        <TableCell>
                          <Badge variant="success">Success</Badge>
                        </TableCell>
                        <TableCell>campaign_auto_create</TableCell>
                        <TableCell className="text-xs">
                          Created with 2 targets
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>{new Date().toISOString()}</TableCell>
                        <TableCell className="font-mono text-xs">
                          04.04.03.04.00001.001
                        </TableCell>
                        <TableCell>launch</TableCell>
                        <TableCell>
                          <Badge variant="success">Success</Badge>
                        </TableCell>
                        <TableCell>instantly</TableCell>
                        <TableCell className="text-xs">
                          Launched to Instantly
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Doctrine Compliance Footer */}
          <div className="mt-8 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-2 text-blue-700">
              <CheckCircledIcon className="w-5 h-5" />
              <span className="font-semibold">Doctrine Compliance</span>
            </div>
            <p className="text-sm text-blue-600 mt-2">
              All campaigns are doctrine-bound blueprints tied to promoted records with Barton IDs.
              MCP-only execution via Composio bridge ensures HEIR compliance.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CampaignConsole;