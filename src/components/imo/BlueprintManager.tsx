import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Save, Eye, Settings, FileText, Target, Zap } from 'lucide-react';

interface BlueprintStage {
  id: string;
  name: string;
  status: 'todo' | 'wip' | 'done';
  description?: string;
}

interface BlueprintBucket {
  id: string;
  name: string;
  stages: BlueprintStage[];
}

interface BlueprintManifest {
  meta: {
    app_name: string;
    stage: string;
    created_at?: string;
  };
  doctrine: {
    unique_id?: string;
    process_id?: string;
    blueprint_version_hash?: string;
    schema_version?: string;
  };
  buckets: BlueprintBucket[];
}

interface ProgressStats {
  total: number;
  done: number;
  wip: number;
  todo: number;
  progress_percentage: number;
}

const BlueprintManager: React.FC = () => {
  const [manifest, setManifest] = useState<BlueprintManifest | null>(null);
  const [progressStats, setProgressStats] = useState<ProgressStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedBucket, setSelectedBucket] = useState<string>('overview');
  const [activeTab, setActiveTab] = useState('overview');

  // Load initial manifest
  useEffect(() => {
    loadManifest();
  }, []);

  const loadManifest = async () => {
    setLoading(true);
    try {
      // Try to load from API or create default
      const defaultManifest: BlueprintManifest = {
        meta: {
          app_name: "Barton Outreach Core",
          stage: "overview",
          created_at: new Date().toISOString()
        },
        doctrine: {
          schema_version: "HEIR/1.0"
        },
        buckets: [
          {
            id: 'input',
            name: 'Input Collection',
            stages: [
              { id: 'requirements', name: 'Requirements Gathering', status: 'todo' },
              { id: 'stakeholder', name: 'Stakeholder Analysis', status: 'todo' },
              { id: 'constraints', name: 'Constraints Definition', status: 'todo' }
            ]
          },
          {
            id: 'middle',
            name: 'Processing & Analysis',
            stages: [
              { id: 'analysis', name: 'Data Analysis', status: 'todo' },
              { id: 'design', name: 'Solution Design', status: 'todo' },
              { id: 'validation', name: 'Design Validation', status: 'todo' }
            ]
          },
          {
            id: 'output',
            name: 'Delivery & Implementation',
            stages: [
              { id: 'implementation', name: 'Implementation Plan', status: 'todo' },
              { id: 'testing', name: 'Testing Strategy', status: 'todo' },
              { id: 'deployment', name: 'Deployment Plan', status: 'todo' }
            ]
          }
        ]
      };
      setManifest(defaultManifest);
      calculateProgress(defaultManifest);
    } catch (error) {
      console.error('Error loading manifest:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateProgress = (manifest: BlueprintManifest) => {
    const allStages = manifest.buckets.flatMap(bucket => bucket.stages);
    const stats: ProgressStats = {
      total: allStages.length,
      done: allStages.filter(s => s.status === 'done').length,
      wip: allStages.filter(s => s.status === 'wip').length,
      todo: allStages.filter(s => s.status === 'todo').length,
      progress_percentage: 0
    };
    stats.progress_percentage = stats.total > 0 ? (stats.done / stats.total) * 100 : 0;
    setProgressStats(stats);
  };

  const saveManifest = async () => {
    if (!manifest) return;
    
    setSaving(true);
    try {
      const response = await fetch('/api/ssot/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ssot: manifest })
      });
      
      if (response.ok) {
        const updated = await response.json();
        setManifest(updated.ssot);
        calculateProgress(updated.ssot);
      }
    } catch (error) {
      console.error('Error saving manifest:', error);
    } finally {
      setSaving(false);
    }
  };

  const updateStageStatus = (bucketId: string, stageId: string, status: 'todo' | 'wip' | 'done') => {
    if (!manifest) return;
    
    const updatedManifest = { ...manifest };
    const bucket = updatedManifest.buckets.find(b => b.id === bucketId);
    if (bucket) {
      const stage = bucket.stages.find(s => s.id === stageId);
      if (stage) {
        stage.status = status;
        setManifest(updatedManifest);
        calculateProgress(updatedManifest);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'done': return 'bg-green-500';
      case 'wip': return 'bg-yellow-500';
      default: return 'bg-gray-300';
    }
  };

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'done': return 'default';
      case 'wip': return 'secondary';
      default: return 'outline';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading blueprint...</span>
      </div>
    );
  }

  if (!manifest) {
    return (
      <Alert>
        <AlertDescription>
          Failed to load blueprint manifest. Please try refreshing the page.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{manifest.meta.app_name}</h2>
          <p className="text-muted-foreground">Blueprint Management System</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={saveManifest} disabled={saving}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            Save Blueprint
          </Button>
        </div>
      </div>

      {/* Progress Overview */}
      {progressStats && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Overall Progress
            </CardTitle>
            <CardDescription>
              {progressStats.done} of {progressStats.total} stages completed
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Progress value={progressStats.progress_percentage} className="mb-4" />
            <div className="flex gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span>Done: {progressStats.done}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <span>In Progress: {progressStats.wip}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-gray-300"></div>
                <span>To Do: {progressStats.todo}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="input" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Input
          </TabsTrigger>
          <TabsTrigger value="middle" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Middle
          </TabsTrigger>
          <TabsTrigger value="output" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Output
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {manifest.buckets.map((bucket) => (
              <Card key={bucket.id}>
                <CardHeader>
                  <CardTitle className="text-lg">{bucket.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {bucket.stages.map((stage) => (
                      <div key={stage.id} className="flex items-center justify-between p-2 border rounded">
                        <span className="text-sm">{stage.name}</span>
                        <Badge variant={getStatusBadgeVariant(stage.status)}>
                          {stage.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {['input', 'middle', 'output'].map((bucketId) => {
          const bucket = manifest.buckets.find(b => b.id === bucketId);
          if (!bucket) return null;

          return (
            <TabsContent key={bucketId} value={bucketId} className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{bucket.name}</CardTitle>
                  <CardDescription>
                    Manage stages for the {bucket.name.toLowerCase()} phase
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {bucket.stages.map((stage) => (
                    <div key={stage.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{stage.name}</h4>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant={stage.status === 'todo' ? 'default' : 'outline'}
                            onClick={() => updateStageStatus(bucket.id, stage.id, 'todo')}
                          >
                            Todo
                          </Button>
                          <Button
                            size="sm"
                            variant={stage.status === 'wip' ? 'default' : 'outline'}
                            onClick={() => updateStageStatus(bucket.id, stage.id, 'wip')}
                          >
                            WIP
                          </Button>
                          <Button
                            size="sm"
                            variant={stage.status === 'done' ? 'default' : 'outline'}
                            onClick={() => updateStageStatus(bucket.id, stage.id, 'done')}
                          >
                            Done
                          </Button>
                        </div>
                      </div>
                      {stage.description && (
                        <p className="text-sm text-muted-foreground">{stage.description}</p>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>
          );
        })}
      </Tabs>

      {/* HEIR Doctrine Info */}
      {manifest.doctrine && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">HEIR Doctrine</CardTitle>
          </CardHeader>
          <CardContent className="text-xs space-y-1">
            {manifest.doctrine.unique_id && (
              <div>Unique ID: {manifest.doctrine.unique_id}</div>
            )}
            {manifest.doctrine.process_id && (
              <div>Process ID: {manifest.doctrine.process_id}</div>
            )}
            {manifest.doctrine.schema_version && (
              <div>Schema: {manifest.doctrine.schema_version}</div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default BlueprintManager;