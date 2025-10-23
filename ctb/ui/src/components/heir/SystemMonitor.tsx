import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useHEIRContext } from './HEIRContext';
import { Activity, Users, ListTodo, CheckCircle } from 'lucide-react';

export function SystemMonitor() {
  const { agents, tasks, systemStatus, getSystemStatus } = useHEIRContext();
  const [stats, setStats] = useState({
    activeAgents: 0,
    idleAgents: 0,
    activeTasks: 0,
    completedTasks: 0,
    queuedTasks: 0
  });

  useEffect(() => {
    const updateStats = () => {
      const status = getSystemStatus();
      
      const activeAgentCount = agents.filter(a => 
        a.status === 'active' || a.status === 'processing'
      ).length;
      
      const idleAgentCount = agents.filter(a => 
        a.status === 'idle' || a.status === 'completed'
      ).length;
      
      const activeTaskCount = status.activeTasks.length;
      const completedTaskCount = tasks.filter(t => t.status === 'completed').length;
      const queuedTaskCount = status.queuedTasks.length;

      setStats({
        activeAgents: activeAgentCount,
        idleAgents: idleAgentCount,
        activeTasks: activeTaskCount,
        completedTasks: completedTaskCount,
        queuedTasks: queuedTaskCount
      });
    };

    updateStats();
    const interval = setInterval(updateStats, 2000);
    return () => clearInterval(interval);
  }, [agents, tasks, getSystemStatus]);

  const getSystemStatusBadge = () => {
    switch (systemStatus) {
      case 'ready':
        return <Badge variant="secondary" className="animate-pulse">Ready</Badge>;
      case 'processing':
        return <Badge variant="default" className="animate-pulse">Processing</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      case 'initializing':
      default:
        return <Badge variant="outline">Initializing</Badge>;
    }
  };

  const utilizationRate = agents.length > 0 
    ? (stats.activeAgents / agents.length) * 100 
    : 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>System Monitor</CardTitle>
          {getSystemStatusBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Agents</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="default">{stats.activeAgents} Active</Badge>
              <Badge variant="outline">{stats.idleAgents} Idle</Badge>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <ListTodo className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Tasks</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="default">{stats.activeTasks} Active</Badge>
              <Badge variant="secondary">{stats.queuedTasks} Queued</Badge>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">System Utilization</span>
            <span className="font-medium">{utilizationRate.toFixed(1)}%</span>
          </div>
          <Progress value={utilizationRate} className="h-2" />
        </div>

        <div className="grid grid-cols-3 gap-2 pt-2 border-t">
          <div className="text-center">
            <div className="text-2xl font-bold">{agents.length}</div>
            <div className="text-xs text-muted-foreground">Total Agents</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{tasks.length}</div>
            <div className="text-xs text-muted-foreground">Total Tasks</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.completedTasks}</div>
            <div className="text-xs text-muted-foreground">Completed</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}