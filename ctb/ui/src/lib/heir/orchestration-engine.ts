import { Agent, Task, AgentCommunication, TaskPriority } from './types';
import { getAgentById, getAgentsByRole } from './agent-registry';

export class OrchestrationEngine {
  private activeTasks: Map<string, Task> = new Map();
  private agentStates: Map<string, Agent> = new Map();
  private communicationLog: AgentCommunication[] = [];
  private taskQueue: Task[] = [];

  constructor() {
    this.initialize();
  }

  private initialize() {
    console.log('HEIR Orchestration Engine initializing...');
  }

  async assignTask(task: Task): Promise<Agent | null> {
    const availableAgents = this.getAvailableAgents();
    
    if (availableAgents.length === 0) {
      this.taskQueue.push(task);
      return null;
    }

    const selectedAgent = this.selectOptimalAgent(availableAgents, task);
    if (selectedAgent) {
      await this.delegateToAgent(selectedAgent, task);
      return selectedAgent;
    }

    return null;
  }

  private getAvailableAgents(): Agent[] {
    const agents: Agent[] = [];
    this.agentStates.forEach(agent => {
      if (agent.status === 'idle' || agent.status === 'completed') {
        agents.push(agent);
      }
    });
    return agents;
  }

  private selectOptimalAgent(agents: Agent[], task: Task): Agent | null {
    let bestAgent: Agent | null = null;
    let bestScore = -1;

    for (const agent of agents) {
      const score = this.calculateAgentScore(agent, task);
      if (score > bestScore) {
        bestScore = score;
        bestAgent = agent;
      }
    }

    return bestAgent;
  }

  private calculateAgentScore(agent: Agent, task: Task): number {
    let score = 0;

    if (agent.role === 'orchestrator' && task.priority === 'critical') {
      score += 30;
    }

    if (agent.role === 'manager' && (task.priority === 'high' || task.priority === 'medium')) {
      score += 20;
    }

    if (agent.role === 'specialist') {
      score += 10;
    }

    if (agent.metrics) {
      score += agent.metrics.successRate * 10;
      score -= agent.metrics.errorCount * 2;
    }

    return score;
  }

  private async delegateToAgent(agent: Agent, task: Task): Promise<void> {
    agent.status = 'processing';
    task.assignedTo = agent.id;
    task.status = 'in-progress';
    
    this.activeTasks.set(task.id, task);
    this.agentStates.set(agent.id, agent);

    const communication: AgentCommunication = {
      from: 'orchestration-engine',
      to: agent.id,
      message: `Task ${task.id} assigned: ${task.description}`,
      timestamp: new Date(),
      type: 'request'
    };
    
    this.communicationLog.push(communication);
  }

  async completeTask(taskId: string, agentId: string): Promise<void> {
    const task = this.activeTasks.get(taskId);
    const agent = this.agentStates.get(agentId);

    if (task && agent) {
      task.status = 'completed';
      task.updatedAt = new Date();
      
      agent.status = 'completed';
      if (!agent.metrics) {
        agent.metrics = {
          tasksCompleted: 0,
          successRate: 100,
          averageResponseTime: 0,
          errorCount: 0
        };
      }
      agent.metrics.tasksCompleted++;

      this.activeTasks.delete(taskId);

      const communication: AgentCommunication = {
        from: agentId,
        to: 'orchestration-engine',
        message: `Task ${taskId} completed successfully`,
        timestamp: new Date(),
        type: 'response'
      };
      
      this.communicationLog.push(communication);

      this.processNextTask();
    }
  }

  private processNextTask(): void {
    if (this.taskQueue.length > 0) {
      const nextTask = this.taskQueue.shift();
      if (nextTask) {
        this.assignTask(nextTask);
      }
    }
  }

  getSystemStatus() {
    return {
      activeTasks: Array.from(this.activeTasks.values()),
      queuedTasks: this.taskQueue,
      activeAgents: Array.from(this.agentStates.values()).filter(a => a.status === 'processing'),
      communicationLog: this.communicationLog.slice(-50)
    };
  }

  getCommunicationHistory(limit: number = 100): AgentCommunication[] {
    return this.communicationLog.slice(-limit);
  }

  registerAgent(agent: Agent): void {
    this.agentStates.set(agent.id, agent);
    console.log(`Agent registered: ${agent.name} (${agent.role})`);
  }

  unregisterAgent(agentId: string): void {
    this.agentStates.delete(agentId);
    console.log(`Agent unregistered: ${agentId}`);
  }
}