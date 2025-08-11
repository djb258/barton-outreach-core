export type AgentRole = 'orchestrator' | 'manager' | 'specialist';
export type AgentStatus = 'idle' | 'active' | 'processing' | 'error' | 'completed';
export type TaskPriority = 'critical' | 'high' | 'medium' | 'low';

export interface Agent {
  id: string;
  name: string;
  role: AgentRole;
  category: string;
  description: string;
  capabilities: string[];
  status: AgentStatus;
  lastActive?: Date;
  metrics?: AgentMetrics;
}

export interface AgentMetrics {
  tasksCompleted: number;
  successRate: number;
  averageResponseTime: number;
  errorCount: number;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  assignedTo?: string;
  priority: TaskPriority;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, unknown>;
}

export interface HEIRContext {
  agents: Agent[];
  tasks: Task[];
  activeAgent?: Agent;
  systemStatus: 'initializing' | 'ready' | 'processing' | 'error';
}

export interface AgentCommunication {
  from: string;
  to: string;
  message: string;
  timestamp: Date;
  type: 'request' | 'response' | 'notification' | 'error';
}

export interface SystemConfiguration {
  enableAutoScaling: boolean;
  maxConcurrentAgents: number;
  defaultTimeout: number;
  retryPolicy: {
    maxRetries: number;
    backoffMultiplier: number;
  };
}