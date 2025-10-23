import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { IMOManifest } from '@/lib/imo/types';
import { CheckCircle2, Circle, Clock } from 'lucide-react';

interface IMOOverviewProps {
  manifest: IMOManifest;
}

export function IMOOverview({ manifest }: IMOOverviewProps) {
  const calculateOverallProgress = () => {
    let totalDone = 0;
    let totalWip = 0;
    let totalStages = 0;

    Object.values(manifest.buckets).forEach(bucket => {
      if (bucket) {
        bucket.stages.forEach(stage => {
          totalStages++;
          if (stage.status === 'done') totalDone++;
          if (stage.status === 'wip') totalWip++;
        });
      }
    });

    const percentage = totalStages > 0 ? ((totalDone + totalWip * 0.5) / totalStages) * 100 : 0;
    return { percentage, done: totalDone, wip: totalWip, total: totalStages };
  };

  const progress = calculateOverallProgress();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'wip':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      default:
        return <Circle className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            {manifest.meta.app_name}
            <Badge variant="outline">{manifest.meta.stage || 'Planning'}</Badge>
          </CardTitle>
          <CardDescription>
            IMO Blueprint Progress Tracker
            {manifest.doctrine?.unique_id && (
              <span className="block text-xs mt-1">ID: {manifest.doctrine.unique_id}</span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Overall Progress</span>
                <span>{Math.round(progress.percentage)}%</span>
              </div>
              <Progress value={progress.percentage} className="h-3" />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>{progress.done} done</span>
                <span>{progress.wip} in progress</span>
                <span>{progress.total - progress.done - progress.wip} todo</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(manifest.buckets).map(([key, bucket]) => {
          if (!bucket) return null;
          
          const bucketProgress = bucket.progress || {
            done: bucket.stages.filter(s => s.status === 'done').length,
            wip: bucket.stages.filter(s => s.status === 'wip').length,
            todo: bucket.stages.filter(s => s.status === 'todo').length,
            total: bucket.stages.length,
          };

          return (
            <Card key={key}>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">{bucket.name}</CardTitle>
                <CardDescription className="text-xs">
                  {bucketProgress.done}/{bucketProgress.total} completed
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {bucket.stages.map(stage => (
                    <div key={stage.id} className="flex items-center gap-2">
                      {getStatusIcon(stage.status)}
                      <span className="text-sm">{stage.name}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}