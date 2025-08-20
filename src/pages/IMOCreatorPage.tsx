import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { IMOOverview } from '@/components/imo/IMOOverview';
import { IMOBucketEditor } from '@/components/imo/IMOBucketEditor';
import { IMOHEIRStatus } from '@/components/imo/IMOHEIRStatus';
import { IMOService } from '@/lib/imo/imo-service';
import { IMOManifest, IMOBucket } from '@/lib/imo/types';
import { Save, RefreshCw, FileText, Shield } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export default function IMOCreatorPage() {
  const [manifest, setManifest] = useState<IMOManifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const imoService = new IMOService();
  const { toast } = useToast();

  useEffect(() => {
    loadManifest();
  }, []);

  const loadManifest = async () => {
    setLoading(true);
    try {
      const loadedManifest = await imoService.loadManifest('barton-outreach');
      setManifest(loadedManifest);
    } catch (error) {
      console.error('Failed to load manifest:', error);
      const defaultManifest = await imoService.loadManifest('default');
      setManifest(defaultManifest);
    } finally {
      setLoading(false);
    }
  };

  const saveManifest = async () => {
    if (!manifest) return;
    
    setSaving(true);
    try {
      await imoService.saveManifest(manifest, 'barton-outreach');
      toast({
        title: 'Manifest Saved',
        description: 'Your IMO manifest has been saved successfully.',
      });
    } catch (error) {
      toast({
        title: 'Save Failed',
        description: 'Failed to save the manifest. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const stampDoctrineIds = async () => {
    if (!manifest) return;
    
    try {
      const stampedManifest = await imoService.stampDoctrineIds(manifest);
      setManifest(stampedManifest);
      toast({
        title: 'Doctrine IDs Stamped',
        description: 'Unique IDs have been generated for this manifest.',
      });
    } catch (error) {
      toast({
        title: 'Stamping Failed',
        description: 'Failed to generate doctrine IDs.',
        variant: 'destructive',
      });
    }
  };

  const updateBucket = (bucketType: 'input' | 'middle' | 'output', updatedBucket: IMOBucket) => {
    if (!manifest) return;
    
    const updatedManifest = {
      ...manifest,
      buckets: {
        ...manifest.buckets,
        [bucketType]: updatedBucket,
      },
      meta: {
        ...manifest.meta,
        updated: new Date().toISOString(),
      },
    };
    
    setManifest(updatedManifest);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading IMO Creator...</p>
        </div>
      </div>
    );
  }

  if (!manifest) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card>
          <CardContent className="pt-6">
            <p>Failed to load manifest. Please refresh the page.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">IMO Creator</h1>
            <p className="text-muted-foreground mt-2">
              Blueprint planning with HEIR/MCP integration
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={stampDoctrineIds}>
              <Shield className="h-4 w-4 mr-2" />
              Stamp IDs
            </Button>
            <Button variant="outline" onClick={loadManifest}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Reload
            </Button>
            <Button onClick={saveManifest} disabled={saving}>
              <Save className="h-4 w-4 mr-2" />
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="input">Input</TabsTrigger>
          <TabsTrigger value="middle">Middle</TabsTrigger>
          <TabsTrigger value="output">Output</TabsTrigger>
          <TabsTrigger value="heir">HEIR/MCP</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <IMOOverview manifest={manifest} />
        </TabsContent>

        <TabsContent value="input">
          {manifest.buckets.input && (
            <IMOBucketEditor
              bucket={manifest.buckets.input}
              bucketType="input"
              onUpdate={(bucket) => updateBucket('input', bucket)}
            />
          )}
        </TabsContent>

        <TabsContent value="middle">
          {manifest.buckets.middle && (
            <IMOBucketEditor
              bucket={manifest.buckets.middle}
              bucketType="middle"
              onUpdate={(bucket) => updateBucket('middle', bucket)}
            />
          )}
        </TabsContent>

        <TabsContent value="output">
          {manifest.buckets.output && (
            <IMOBucketEditor
              bucket={manifest.buckets.output}
              bucketType="output"
              onUpdate={(bucket) => updateBucket('output', bucket)}
            />
          )}
        </TabsContent>

        <TabsContent value="heir">
          <IMOHEIRStatus 
            manifest={manifest} 
            onEnrichManifest={setManifest}
          />
        </TabsContent>
      </Tabs>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Manifest Details
          </CardTitle>
          <CardDescription>Technical information about this IMO blueprint</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">App Name:</span> {manifest.meta.app_name}
            </div>
            <div>
              <span className="font-medium">Stage:</span> {manifest.meta.stage || 'N/A'}
            </div>
            <div>
              <span className="font-medium">Created:</span> {manifest.meta.created ? new Date(manifest.meta.created).toLocaleString() : 'N/A'}
            </div>
            <div>
              <span className="font-medium">Updated:</span> {manifest.meta.updated ? new Date(manifest.meta.updated).toLocaleString() : 'N/A'}
            </div>
            {manifest.doctrine?.unique_id && (
              <div className="col-span-2">
                <span className="font-medium">Unique ID:</span> {manifest.doctrine.unique_id}
              </div>
            )}
            {manifest.doctrine?.process_id && (
              <div className="col-span-2">
                <span className="font-medium">Process ID:</span> {manifest.doctrine.process_id}
              </div>
            )}
            {manifest.doctrine?.schema_version && (
              <div>
                <span className="font-medium">Schema:</span> {manifest.doctrine.schema_version}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}