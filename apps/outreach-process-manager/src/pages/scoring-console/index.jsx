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
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  TargetIcon,
  LightningBoltIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  UpdateIcon,
  CheckCircledIcon,
  ExclamationTriangleIcon,
  ActivityLogIcon,
  BarChartIcon,
  GearIcon,
  ReloadIcon
} from '@radix-ui/react-icons';

// Import shared workflow sidebar
import { WorkflowSidebar } from '@/components/shared/workflow-sidebar';

const ScoringConsole = () => {
  // State management
  const [leadScoring, setLeadScoring] = useState({
    avg_score: 0,
    total_leads: 0,
    hot_leads: 0,
    distribution: {
      hot: 0,
      warm: 0,
      cool: 0,
      cold: 0
    }
  });

  const [bitSignals, setBitSignals] = useState([]);
  const [optimizationHistory, setOptimizationHistory] = useState([]);
  const [topLeads, setTopLeads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [optimizing, setOptimizing] = useState(false);

  // Fetch scoring data
  useEffect(() => {
    fetchScoringData();
    fetchBitSignals();
    fetchOptimizationHistory();
    fetchTopLeads();

    // Auto-refresh every 2 minutes
    const interval = setInterval(() => {
      fetchScoringData();
      fetchBitSignals();
    }, 120000);

    return () => clearInterval(interval);
  }, []);

  const fetchScoringData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/scoring-stats');
      const data = await response.json();

      if (data.status === 'success') {
        setLeadScoring(data.scoring_stats || {});
      }
    } catch (err) {
      console.error('Failed to fetch scoring data:', err);
      setError('Failed to load scoring data');
    } finally {
      setLoading(false);
    }
  };

  const fetchBitSignals = async () => {
    try {
      const response = await fetch('/api/bit-signals-list');
      const data = await response.json();

      if (data.status === 'success') {
        setBitSignals(data.signals || []);
      }
    } catch (err) {
      console.error('Failed to fetch BIT signals:', err);
    }
  };

  const fetchOptimizationHistory = async () => {
    try {
      const response = await fetch('/api/optimization-history');
      const data = await response.json();

      if (data.status === 'success') {
        setOptimizationHistory(data.history || []);
      }
    } catch (err) {
      console.error('Failed to fetch optimization history:', err);
    }
  };

  const fetchTopLeads = async () => {
    try {
      const response = await fetch('/api/top-leads');
      const data = await response.json();

      if (data.status === 'success') {
        setTopLeads(data.leads || []);
      }
    } catch (err) {
      console.error('Failed to fetch top leads:', err);
    }
  };

  const handleOptimizeBITSignals = async (dryRun = false) => {
    try {
      setOptimizing(true);
      setError(null);

      const response = await fetch('/api/bit-signal-optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trigger_type: 'manual',
          optimization_window: 90,
          min_sample_size: 10,
          dry_run: dryRun
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        await fetchBitSignals();
        await fetchOptimizationHistory();

        if (!dryRun) {
          setError(null);
        }
      } else {
        setError(data.message || 'Failed to optimize BIT signals');
      }
    } catch (err) {
      console.error('Failed to optimize BIT signals:', err);
      setError('Failed to optimize BIT signals');
    } finally {
      setOptimizing(false);
    }
  };

  const getLeadTemperatureBadge = (temperature) => {
    const config = {
      Hot: { variant: 'destructive', icon: '🔥' },
      Warm: { variant: 'warning', icon: '🟡' },
      Cool: { variant: 'secondary', icon: '🔵' },
      Cold: { variant: 'outline', icon: '❄️' }
    };

    const { variant, icon } = config[temperature] || config.Cold;
    return (
      <Badge variant={variant}>
        <span className="mr-1">{icon}</span>
        {temperature}
      </Badge>
    );
  };

  const getSignalCategoryIcon = (category) => {
    const icons = {
      funding: '💰',
      hiring: '👥',
      technology: '💻',
      news: '📰',
      engagement: '🎯',
      competitor: '⚔️',
      regulatory: '📋',
      financial: '📈'
    };

    return icons[category] || '📊';
  };

  const getWeightChangeIcon = (change) => {
    if (change > 5) return <TrendingUpIcon className="w-4 h-4 text-green-600" />;
    if (change < -5) return <TrendingDownIcon className="w-4 h-4 text-red-600" />;
    return <UpdateIcon className="w-4 h-4 text-gray-500" />;
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Workflow Sidebar - Step 8 highlighted */}
      <WorkflowSidebar currentStep={8} />

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Scoring & Triggers Console
            </h1>
            <p className="text-gray-500">
              Step 8: Lead Scoring + Trigger Optimization - Attribution-driven model tuning
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

          {/* Lead Scoring Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Average Lead Score
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{leadScoring.avg_score}</div>
                <Progress value={leadScoring.avg_score} className="mt-2" />
                <p className="text-xs text-gray-500 mt-1">Out of 100</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Hot Leads
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {leadScoring.hot_leads}
                </div>
                <p className="text-xs text-gray-500 mt-1">Score ≥ 85</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Total Leads Scored
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {leadScoring.total_leads}
                </div>
                <p className="text-xs text-gray-500 mt-1">With current model</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Score Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Hot: {leadScoring.distribution?.hot || 0}</span>
                    <span>Warm: {leadScoring.distribution?.warm || 0}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Cool: {leadScoring.distribution?.cool || 0}</span>
                    <span>Cold: {leadScoring.distribution?.cold || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Console Tabs */}
          <Tabs defaultValue="scoring" className="space-y-4">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="scoring">Lead Scoring</TabsTrigger>
              <TabsTrigger value="signals">BIT Signals</TabsTrigger>
              <TabsTrigger value="optimization">Optimization</TabsTrigger>
              <TabsTrigger value="models">Model History</TabsTrigger>
            </TabsList>

            {/* Lead Scoring Tab */}
            <TabsContent value="scoring" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <div>
                      <CardTitle>Top Scoring Leads</CardTitle>
                      <CardDescription>
                        Highest scored leads from firmographics, engagement, and intent
                      </CardDescription>
                    </div>
                    <Button onClick={fetchTopLeads} variant="outline" size="sm">
                      <ReloadIcon className="mr-2 h-4 w-4" />
                      Refresh
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Lead</TableHead>
                        <TableHead>Company</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Temperature</TableHead>
                        <TableHead>Breakdown</TableHead>
                        <TableHead>Last Updated</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {topLeads.map((lead, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <div>
                              <div className="font-medium">
                                {lead.first_name} {lead.last_name}
                              </div>
                              <div className="text-xs text-gray-500 font-mono">
                                {lead.person_unique_id}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div>
                              <div className="font-medium">{lead.company_name}</div>
                              <div className="text-xs text-gray-500">{lead.industry}</div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-lg font-bold">{lead.score}</div>
                          </TableCell>
                          <TableCell>
                            {getLeadTemperatureBadge(lead.lead_temperature)}
                          </TableCell>
                          <TableCell className="text-xs">
                            <div>Firmographics: {lead.firmographics_score}</div>
                            <div>Engagement: {lead.engagement_score}</div>
                            <div>Intent: {lead.intent_score}</div>
                          </TableCell>
                          <TableCell className="text-xs">
                            {new Date(lead.last_scored_at).toLocaleDateString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            {/* BIT Signals Tab */}
            <TabsContent value="signals" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <div>
                      <CardTitle>BIT Signal Weights</CardTitle>
                      <CardDescription>
                        Current signal weights and effectiveness scores
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => handleOptimizeBITSignals(true)}
                        variant="outline"
                        disabled={optimizing}
                      >
                        <GearIcon className="mr-2 h-4 w-4" />
                        Preview Optimization
                      </Button>
                      <Button
                        onClick={() => handleOptimizeBITSignals(false)}
                        disabled={optimizing}
                      >
                        {optimizing ? (
                          <ReloadIcon className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <LightningBoltIcon className="mr-2 h-4 w-4" />
                        )}
                        Optimize Weights
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Signal</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead>Weight</TableHead>
                        <TableHead>Effectiveness</TableHead>
                        <TableHead>Conversion Rate</TableHead>
                        <TableHead>Last Optimized</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {bitSignals.map((signal) => (
                        <TableRow key={signal.signal_name}>
                          <TableCell>
                            <div className="font-medium">{signal.signal_name}</div>
                            <div className="text-xs text-gray-500">
                              {signal.signal_description}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <span>{getSignalCategoryIcon(signal.signal_category)}</span>
                              <span className="capitalize">{signal.signal_category}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <span className="font-bold">{signal.weight}</span>
                              <Progress value={signal.weight} className="w-16 h-2" />
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={signal.effectiveness_score >= 70 ? 'success' :
                                      signal.effectiveness_score >= 50 ? 'warning' : 'destructive'}
                            >
                              {signal.effectiveness_score}%
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {signal.conversion_rate ? `${signal.conversion_rate.toFixed(1)}%` : 'N/A'}
                          </TableCell>
                          <TableCell className="text-xs">
                            {signal.last_optimized
                              ? new Date(signal.last_optimized).toLocaleDateString()
                              : 'Never'
                            }
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Optimization Tab */}
            <TabsContent value="optimization" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Optimization History</CardTitle>
                  <CardDescription>
                    Version history and performance of model optimizations
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Version</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Changes</TableHead>
                        <TableHead>Performance</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Created</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {optimizationHistory.map((version) => (
                        <TableRow key={version.id}>
                          <TableCell className="font-mono text-sm">
                            {version.version}
                          </TableCell>
                          <TableCell>
                            <Badge variant={version.model_type === 'BIT' ? 'destructive' : 'default'}>
                              {version.model_type}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs">
                            <div>Signals: {version.signals_changed || 0}</div>
                            <div>Avg Change: {version.avg_weight_change || 0}%</div>
                          </TableCell>
                          <TableCell>
                            {version.closed_won_correlation && (
                              <div className="text-xs">
                                <div>Win Rate: {version.closed_won_correlation}%</div>
                                <div>Loss Rate: {version.closed_lost_correlation}%</div>
                              </div>
                            )}
                          </TableCell>
                          <TableCell>
                            {version.is_active ? (
                              <Badge variant="success">Active</Badge>
                            ) : (
                              <Badge variant="secondary">Inactive</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-xs">
                            {new Date(version.created_at).toLocaleDateString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Model History Tab */}
            <TabsContent value="models" className="space-y-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* PLE Model Card */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TargetIcon className="w-5 h-5" />
                      PLE Scoring Model
                    </CardTitle>
                    <CardDescription>
                      Promoted Lead Engagement scoring model
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold mb-2">Current Weights:</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span>Firmographics (30%)</span>
                            <Progress value={30} className="w-20 h-2" />
                          </div>
                          <div className="flex justify-between">
                            <span>Engagement (25%)</span>
                            <Progress value={25} className="w-20 h-2" />
                          </div>
                          <div className="flex justify-between">
                            <span>Intent Signals (36%)</span>
                            <Progress value={36} className="w-20 h-2" />
                          </div>
                          <div className="flex justify-between">
                            <span>Attribution (9%)</span>
                            <Progress value={9} className="w-20 h-2" />
                          </div>
                        </div>
                      </div>
                      <div>
                        <h4 className="font-semibold mb-2">Model Version:</h4>
                        <Badge variant="outline">v1.0.0</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* BIT Model Card */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <LightningBoltIcon className="w-5 h-5" />
                      BIT Signal Model
                    </CardTitle>
                    <CardDescription>
                      Business Intelligence Trigger optimization
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold mb-2">Top Signals:</h4>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span>Demo Request</span>
                            <Badge variant="destructive">95</Badge>
                          </div>
                          <div className="flex justify-between">
                            <span>Competitor Switch</span>
                            <Badge variant="destructive">90</Badge>
                          </div>
                          <div className="flex justify-between">
                            <span>Series A+ Funding</span>
                            <Badge variant="warning">85</Badge>
                          </div>
                          <div className="flex justify-between">
                            <span>Tech Stack Match</span>
                            <Badge variant="warning">80</Badge>
                          </div>
                        </div>
                      </div>
                      <div>
                        <h4 className="font-semibold mb-2">Last Optimization:</h4>
                        <div className="text-xs text-gray-600">
                          {optimizationHistory[0]?.created_at
                            ? new Date(optimizationHistory[0].created_at).toLocaleDateString()
                            : 'Never'
                          }
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>

          {/* Doctrine Compliance Footer */}
          <div className="mt-8 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-2 text-blue-700">
              <CheckCircledIcon className="w-5 h-5" />
              <span className="font-semibold">Attribution-Driven Optimization</span>
            </div>
            <p className="text-sm text-blue-600 mt-2">
              All scoring models and signal weights are version-locked for auditability.
              Optimization is driven exclusively by Closed-Won/Lost attribution outcomes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScoringConsole;