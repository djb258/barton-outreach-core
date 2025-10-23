import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Agent } from '@/lib/heir/types';
import { Activity, Bot, CheckCircle, AlertCircle, Clock } from 'lucide-react';

interface AgentCardProps {
  agent: Agent;
  onSelect?: (agent: Agent) => void;
}

export function AgentCard({ agent, onSelect }: AgentCardProps) {
  const getStatusIcon = () => {
    switch (agent.status) {
      case 'active':
      case 'processing':
        return <Activity className="h-4 w-4 text-green-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-blue-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'idle':
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getRoleBadgeVariant = () => {
    switch (agent.role) {
      case 'orchestrator':
        return 'default';
      case 'manager':
        return 'secondary';
      case 'specialist':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const getStatusBadgeVariant = () => {
    switch (agent.status) {
      case 'active':
      case 'processing':
        return 'default';
      case 'completed':
        return 'secondary';
      case 'error':
        return 'destructive';
      case 'idle':
      default:
        return 'outline';
    }
  };

  return (
    <Card 
      className="hover:shadow-lg transition-shadow cursor-pointer"
      onClick={() => onSelect?.(agent)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">{agent.name}</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <Badge variant={getStatusBadgeVariant()}>{agent.status}</Badge>
          </div>
        </div>
        <CardDescription className="mt-1">{agent.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2 mb-3">
          <Badge variant={getRoleBadgeVariant()}>{agent.role}</Badge>
          <Badge variant="outline">{agent.category}</Badge>
        </div>
        
        {agent.capabilities && agent.capabilities.length > 0 && (
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Capabilities:</p>
            <ul className="text-sm text-muted-foreground list-disc list-inside">
              {agent.capabilities.slice(0, 3).map((capability, index) => (
                <li key={index} className="truncate">{capability}</li>
              ))}
              {agent.capabilities.length > 3 && (
                <li className="text-xs">+{agent.capabilities.length - 3} more</li>
              )}
            </ul>
          </div>
        )}

        {agent.metrics && (
          <div className="mt-3 pt-3 border-t grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Tasks:</span>
              <span className="ml-1 font-medium">{agent.metrics.tasksCompleted}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Success:</span>
              <span className="ml-1 font-medium">{agent.metrics.successRate}%</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}