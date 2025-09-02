import { useState, useEffect, useCallback } from 'react';
import { Agent, Task, HEIRContext, TaskPriority, AgentCommunication } from '@/lib/heir/types';
import { agentRegistry } from '@/lib/heir/agent-registry';
import { OrchestrationEngine } from '@/lib/heir/orchestration-engine';

const orchestrationEngine = new OrchestrationEngine();

export function useHEIR() {
  const [context, setContext] = useState<HEIRContext>({
    agents: [],
    tasks: [],
    systemStatus: 'initializing'
  });
  
  const [communications, setCommunications] = useState<AgentCommunication[]>([]);

  const initializeSystem = useCallback(() => {
    agentRegistry.forEach(agent => {
      orchestrationEngine.registerAgent(agent);
    });

    setContext({
      agents: agentRegistry,
      tasks: [],
      systemStatus: 'ready'
    });
  }, []);

  useEffect(() => {
    initializeSystem();
  }, [initializeSystem]);

  const createTask = useCallback(async (
    title: string,
    description: string,
    priority: TaskPriority = 'medium'
  ): Promise<Task> => {
    const task: Task = {
      id: `task-${Date.now()}`,
      title,
      description,
      priority,
      status: 'pending',
      createdAt: new Date(),
      updatedAt: new Date()
    };

    const assignedAgent = await orchestrationEngine.assignTask(task);
    
    setContext(prev => ({
      ...prev,
      tasks: [...prev.tasks, task],
      activeAgent: assignedAgent || undefined
    }));

    return task;
  }, []);

  const completeTask = useCallback(async (taskId: string, agentId: string) => {
    await orchestrationEngine.completeTask(taskId, agentId);
    
    setContext(prev => ({
      ...prev,
      tasks: prev.tasks.map(task => 
        task.id === taskId 
          ? { ...task, status: 'completed', updatedAt: new Date() }
          : task
      )
    }));
  }, []);

  const getSystemStatus = useCallback(() => {
    return orchestrationEngine.getSystemStatus();
  }, []);

  const getCommunicationHistory = useCallback(() => {
    const history = orchestrationEngine.getCommunicationHistory();
    setCommunications(history);
    return history;
  }, []);

  const getAgentStatus = useCallback((agentId: string): Agent | undefined => {
    return context.agents.find(agent => agent.id === agentId);
  }, [context.agents]);

  const updateAgentStatus = useCallback((agentId: string, status: Agent['status']) => {
    setContext(prev => ({
      ...prev,
      agents: prev.agents.map(agent =>
        agent.id === agentId ? { ...agent, status } : agent
      )
    }));
  }, []);

  return {
    context,
    agents: context.agents,
    tasks: context.tasks,
    systemStatus: context.systemStatus,
    communications,
    createTask,
    completeTask,
    getSystemStatus,
    getCommunicationHistory,
    getAgentStatus,
    updateAgentStatus,
    initializeSystem
  };
}