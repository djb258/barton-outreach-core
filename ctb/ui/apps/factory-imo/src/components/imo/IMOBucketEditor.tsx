import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { IMOBucket, IMOStage } from '@/lib/imo/types';
import { Plus, Trash2, Edit2, Save, X } from 'lucide-react';

interface IMOBucketEditorProps {
  bucket: IMOBucket;
  bucketType: 'input' | 'middle' | 'output';
  onUpdate: (bucket: IMOBucket) => void;
}

export function IMOBucketEditor({ bucket, bucketType, onUpdate }: IMOBucketEditorProps) {
  const [editingStage, setEditingStage] = useState<string | null>(null);
  const [stageForm, setStageForm] = useState<Partial<IMOStage>>({});
  const [isAddingStage, setIsAddingStage] = useState(false);

  const handleStatusChange = (stageId: string, status: IMOStage['status']) => {
    const updatedStages = bucket.stages.map(stage =>
      stage.id === stageId ? { ...stage, status } : stage
    );
    onUpdate({ ...bucket, stages: updatedStages });
  };

  const handleEditStage = (stage: IMOStage) => {
    setEditingStage(stage.id);
    setStageForm(stage);
  };

  const handleSaveStage = () => {
    if (!editingStage) return;
    
    const updatedStages = bucket.stages.map(stage =>
      stage.id === editingStage ? { ...stage, ...stageForm } as IMOStage : stage
    );
    onUpdate({ ...bucket, stages: updatedStages });
    setEditingStage(null);
    setStageForm({});
  };

  const handleAddStage = () => {
    if (!stageForm.name) return;
    
    const newStage: IMOStage = {
      id: `stage-${Date.now()}`,
      name: stageForm.name || '',
      status: 'todo',
      description: stageForm.description,
      tasks: stageForm.tasks,
    };
    
    onUpdate({ ...bucket, stages: [...bucket.stages, newStage] });
    setIsAddingStage(false);
    setStageForm({});
  };

  const handleDeleteStage = (stageId: string) => {
    const updatedStages = bucket.stages.filter(stage => stage.id !== stageId);
    onUpdate({ ...bucket, stages: updatedStages });
  };

  const getBucketColor = () => {
    switch (bucketType) {
      case 'input':
        return 'border-blue-500';
      case 'middle':
        return 'border-yellow-500';
      case 'output':
        return 'border-green-500';
      default:
        return 'border-gray-500';
    }
  };

  return (
    <Card className={`${getBucketColor()} border-2`}>
      <CardHeader>
        <CardTitle>{bucket.name}</CardTitle>
        <CardDescription>
          Manage stages for the {bucketType} phase
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {bucket.stages.map(stage => (
            <div key={stage.id} className="border rounded-lg p-4">
              {editingStage === stage.id ? (
                <div className="space-y-3">
                  <Input
                    value={stageForm.name || ''}
                    onChange={(e) => setStageForm({ ...stageForm, name: e.target.value })}
                    placeholder="Stage name"
                  />
                  <Textarea
                    value={stageForm.description || ''}
                    onChange={(e) => setStageForm({ ...stageForm, description: e.target.value })}
                    placeholder="Stage description"
                    rows={2}
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={handleSaveStage}>
                      <Save className="h-4 w-4 mr-1" /> Save
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setEditingStage(null)}>
                      <X className="h-4 w-4 mr-1" /> Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{stage.name}</h4>
                    <div className="flex items-center gap-2">
                      <Select
                        value={stage.status}
                        onValueChange={(value) => handleStatusChange(stage.id, value as IMOStage['status'])}
                      >
                        <SelectTrigger className="w-24 h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="todo">Todo</SelectItem>
                          <SelectItem value="wip">WIP</SelectItem>
                          <SelectItem value="done">Done</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleEditStage(stage)}
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteStage(stage.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  {stage.description && (
                    <p className="text-sm text-muted-foreground">{stage.description}</p>
                  )}
                </div>
              )}
            </div>
          ))}

          {isAddingStage ? (
            <div className="border rounded-lg p-4 space-y-3">
              <Input
                value={stageForm.name || ''}
                onChange={(e) => setStageForm({ ...stageForm, name: e.target.value })}
                placeholder="New stage name"
              />
              <Textarea
                value={stageForm.description || ''}
                onChange={(e) => setStageForm({ ...stageForm, description: e.target.value })}
                placeholder="Stage description"
                rows={2}
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={handleAddStage}>
                  <Save className="h-4 w-4 mr-1" /> Add Stage
                </Button>
                <Button size="sm" variant="outline" onClick={() => {
                  setIsAddingStage(false);
                  setStageForm({});
                }}>
                  <X className="h-4 w-4 mr-1" /> Cancel
                </Button>
              </div>
            </div>
          ) : (
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setIsAddingStage(true)}
            >
              <Plus className="h-4 w-4 mr-2" /> Add Stage
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}