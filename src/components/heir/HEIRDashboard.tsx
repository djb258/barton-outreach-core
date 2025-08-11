import React, { useState } from 'react';
import { useHEIRContext } from './HEIRContext';
import { TaskPriority } from '@/lib/heir/types';
import { AgentCard } from './AgentCard';
import { TaskList } from './TaskList';
import { SystemMonitor } from './SystemMonitor';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { 
  Building2, 
  Users, 
  Plus,
  Activity, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Brain,
  Shield
} from 'lucide-react';

const HEIRDashboard: React.FC = () => {
  const { 
    agents, 
    tasks, 
    systemStatus, 
    createTask, 
    completeTask,
    getCommunicationHistory,
    getAgentStatus,
    updateAgentStatus
  } = useHEIRContext();
  
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showCreateTask, setShowCreateTask] = useState(false);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [taskPriority, setTaskPriority] = useState('medium');

  if (systemStatus === 'initializing') {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Building2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Initializing HEIR Agent System...</p>
        </div>
      </div>
    );
  }

  if (systemStatus === 'error') {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <XCircle className="h-8 w-8 text-destructive mx-auto mb-4" />
          <p className="text-destructive">Failed to load HEIR system</p>
        </div>
      </div>
    );
  }

  const handleCreateTask = async () => {
    if (taskTitle && taskDescription) {
      await createTask(taskTitle, taskDescription, taskPriority as TaskPriority);
      setTaskTitle('');
      setTaskDescription('');
      setTaskPriority('medium');
      setShowCreateTask(false);
    }
  };

  const orchestrators = agents.filter(a => a.role === 'orchestrator');
  const managers = agents.filter(a => a.role === 'manager');
  const specialists = agents.filter(a => a.role === 'specialist');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Building2 className="h-8 w-8" />
            HEIR Agent System
          </h1>
          <p className="text-muted-foreground">
            Hierarchical Execution Intelligence & Repair - Barton Outreach Core
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setShowCreateTask(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Task
          </Button>
          <Shield className="h-5 w-5 text-blue-500" />
          <Badge variant="secondary">{systemStatus}</Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Orchestrators</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{orchestrators.length}</div>
            <p className="text-xs text-muted-foreground">
              {orchestrators.filter(a => a.status === 'active' || a.status === 'processing').length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Managers</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{managers.length}</div>
            <p className="text-xs text-muted-foreground">
              {managers.filter(a => a.status === 'active' || a.status === 'processing').length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Specialists</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{specialists.length}</div>
            <p className="text-xs text-muted-foreground">
              {specialists.filter(a => a.status === 'active' || a.status === 'processing').length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tasks.length}</div>
            <p className="text-xs text-muted-foreground">
              {tasks.filter(t => t.status === 'completed').length} completed
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Tabs defaultValue="orchestrators" className="space-y-4">
            <TabsList>
              <TabsTrigger value="orchestrators">Orchestrators</TabsTrigger>
              <TabsTrigger value="managers">Managers</TabsTrigger>
              <TabsTrigger value="specialists">Specialists</TabsTrigger>
              <TabsTrigger value="tasks">Tasks</TabsTrigger>
            </TabsList>

            <TabsContent value="orchestrators" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {orchestrators.map((agent) => (
                  <AgentCard 
                    key={agent.id} 
                    agent={agent} 
                    onSelect={setSelectedAgent}
                  />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="managers" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {managers.map((agent) => (
                  <AgentCard 
                    key={agent.id} 
                    agent={agent} 
                    onSelect={setSelectedAgent}
                  />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="specialists" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {specialists.map((agent) => (
                  <AgentCard 
                    key={agent.id} 
                    agent={agent} 
                    onSelect={setSelectedAgent}
                  />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="tasks" className="space-y-4">
              <TaskList tasks={tasks} />
            </TabsContent>
          </Tabs>
        </div>

        <div className="space-y-6">
          <SystemMonitor />
        </div>
      </div>

      <Dialog open={showCreateTask} onOpenChange={setShowCreateTask}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Task</DialogTitle>
            <DialogDescription>
              Create a task to be assigned to an available agent in the HEIR system.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={taskTitle}
                onChange={(e) => setTaskTitle(e.target.value)}
                placeholder="Enter task title"
              />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                placeholder="Enter task description"
              />
            </div>
            <div>
              <Label htmlFor="priority">Priority</Label>
              <Select value={taskPriority} onValueChange={setTaskPriority}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateTask(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateTask}>Create Task</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default HEIRDashboard;
