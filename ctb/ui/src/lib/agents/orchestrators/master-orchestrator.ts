import { Agent, Task, AgentStatus } from '@/lib/heir/types';

export interface OrchestrationPlan {
  id: string;
  project_name: string;
  total_branches: number;
  active_branches: string[];
  dependencies: Record<string, string[]>; // branch_id -> [dependency_branch_ids]
  execution_order: string[];
  estimated_duration_ms: number;
}

export interface BranchStatus {
  branch_id: string;
  orchestrator_id: string;
  status: 'idle' | 'initializing' | 'processing' | 'waiting' | 'completed' | 'error';
  current_step?: string;
  progress_percentage: number;
  estimated_completion_ms?: number;
  error_count: number;
  last_activity: Date;
}

export interface CrossBranchMessage {
  id: string;
  from_branch: string;
  to_branch: string;
  message_type: 'data_ready' | 'error' | 'request_status' | 'priority_change';
  payload: any;
  timestamp: Date;
  requires_response: boolean;
}

export class MasterOrchestrator {
  private agentInfo: Agent;
  private branchOrchestrators: Map<string, any> = new Map();
  private branchStatuses: Map<string, BranchStatus> = new Map();
  private messageQueue: CrossBranchMessage[] = [];
  private executionPlans: Map<string, OrchestrationPlan> = new Map();

  constructor() {
    this.agentInfo = {
      id: 'barton-master-orchestrator',
      name: 'Barton Master Orchestrator',
      role: 'orchestrator',
      category: 'global',
      description: 'Overall coordination for Barton Outreach Core project across all branches',
      capabilities: [
        'Cross-branch workflow coordination',
        'Resource allocation and prioritization',
        'Global error handling and recovery',
        'Project-level metrics and reporting',
        'Dependency management between branches',
        'Load balancing and throttling',
        'Real-time status monitoring'
      ],
      status: 'idle'
    };

    this.initializeBranchStatuses();
  }

  // ============================================
  // Branch Registration & Management
  // ============================================

  registerBranchOrchestrator(branchId: string, orchestrator: any): void {
    this.branchOrchestrators.set(branchId, orchestrator);
    
    // Initialize branch status
    this.branchStatuses.set(branchId, {
      branch_id: branchId,
      orchestrator_id: orchestrator.getId(),
      status: 'idle',
      progress_percentage: 0,
      error_count: 0,
      last_activity: new Date()
    });

    console.log(`✅ Registered branch orchestrator: ${branchId}`);
  }

  private initializeBranchStatuses(): void {
    // Initialize all known branches for Barton Outreach Core
    const branches = [
      '00-data-ingestion',
      '01-lead-intake',
      '02-messaging',
      '03-delivery',
      '04-scheduling',
      '05-feedback',
      '06-compliance',
      '07-data-vault'
    ];

    branches.forEach(branchId => {
      this.branchStatuses.set(branchId, {
        branch_id: branchId,
        orchestrator_id: `${branchId}-orchestrator`,
        status: 'idle',
        progress_percentage: 0,
        error_count: 0,
        last_activity: new Date()
      });
    });
  }

  // ============================================
  // Workflow Orchestration
  // ============================================

  async executeWorkflow(workflowType: 'full_pipeline' | 'lead_only' | 'messaging_only' | 'custom', config?: any): Promise<void> {
    this.agentInfo.status = 'processing';

    try {
      const plan = this.createExecutionPlan(workflowType, config);
      await this.executeOrchestrationPlan(plan);
      
      this.agentInfo.status = 'completed';
      console.log(`✅ Workflow '${workflowType}' completed successfully`);
    } catch (error) {
      this.agentInfo.status = 'error';
      console.error(`❌ Workflow '${workflowType}' failed:`, error);
      await this.handleGlobalError(error);
    }
  }

  private createExecutionPlan(workflowType: string, config?: any): OrchestrationPlan {
    const plan: OrchestrationPlan = {
      id: `plan-${Date.now()}`,
      project_name: 'barton-outreach-core',
      total_branches: 0,
      active_branches: [],
      dependencies: {},
      execution_order: [],
      estimated_duration_ms: 0
    };

    switch (workflowType) {
      case 'full_pipeline':
        plan.active_branches = ['00-data-ingestion', '01-lead-intake', '02-messaging', '03-delivery'];
        plan.dependencies = {
          '01-lead-intake': ['00-data-ingestion'],
          '02-messaging': ['01-lead-intake'],
          '03-delivery': ['02-messaging']
        };
        plan.execution_order = ['00-data-ingestion', '01-lead-intake', '02-messaging', '03-delivery'];
        plan.estimated_duration_ms = 300000; // 5 minutes
        break;

      case 'lead_only':
        plan.active_branches = ['00-data-ingestion', '01-lead-intake'];
        plan.dependencies = {
          '01-lead-intake': ['00-data-ingestion']
        };
        plan.execution_order = ['00-data-ingestion', '01-lead-intake'];
        plan.estimated_duration_ms = 120000; // 2 minutes
        break;

      case 'messaging_only':
        plan.active_branches = ['02-messaging'];
        plan.dependencies = {};
        plan.execution_order = ['02-messaging'];
        plan.estimated_duration_ms = 60000; // 1 minute
        break;

      default:
        throw new Error(`Unknown workflow type: ${workflowType}`);
    }

    plan.total_branches = plan.active_branches.length;
    this.executionPlans.set(plan.id, plan);
    return plan;
  }

  private async executeOrchestrationPlan(plan: OrchestrationPlan): Promise<void> {
    console.log(`🚀 Executing orchestration plan: ${plan.id}`);
    console.log(`📊 Branches: ${plan.active_branches.join(', ')}`);

    // Execute branches in dependency order
    for (const branchId of plan.execution_order) {
      await this.executeBranch(branchId, plan);
    }
  }

  private async executeBranch(branchId: string, plan: OrchestrationPlan): Promise<void> {
    // Check dependencies
    const dependencies = plan.dependencies[branchId] || [];
    for (const depBranch of dependencies) {
      await this.waitForBranchCompletion(depBranch);
    }

    // Update status
    this.updateBranchStatus(branchId, 'processing');

    // Get branch orchestrator
    const orchestrator = this.branchOrchestrators.get(branchId);
    if (!orchestrator) {
      throw new Error(`No orchestrator found for branch: ${branchId}`);
    }

    try {
      console.log(`⚡ Starting branch: ${branchId}`);
      await orchestrator.execute();
      
      this.updateBranchStatus(branchId, 'completed', 100);
      console.log(`✅ Completed branch: ${branchId}`);
    } catch (error) {
      this.updateBranchStatus(branchId, 'error');
      throw new Error(`Branch ${branchId} failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async waitForBranchCompletion(branchId: string): Promise<void> {
    const maxWaitMs = 300000; // 5 minutes
    const pollIntervalMs = 1000; // 1 second
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitMs) {
      const status = this.branchStatuses.get(branchId);
      if (status?.status === 'completed') {
        return;
      }
      if (status?.status === 'error') {
        throw new Error(`Dependency branch ${branchId} failed`);
      }

      await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
    }

    throw new Error(`Timeout waiting for branch ${branchId} to complete`);
  }

  // ============================================
  // Cross-Branch Communication
  // ============================================

  async sendMessage(message: CrossBranchMessage): Promise<void> {
    this.messageQueue.push(message);
    
    // Route message to target branch
    const targetOrchestrator = this.branchOrchestrators.get(message.to_branch);
    if (targetOrchestrator && targetOrchestrator.receiveMessage) {
      await targetOrchestrator.receiveMessage(message);
    }

    console.log(`📨 Message sent: ${message.from_branch} → ${message.to_branch} (${message.message_type})`);
  }

  async broadcastMessage(message: Omit<CrossBranchMessage, 'to_branch'>): Promise<void> {
    for (const branchId of this.branchOrchestrators.keys()) {
      if (branchId !== message.from_branch) {
        await this.sendMessage({
          ...message,
          to_branch: branchId
        });
      }
    }
  }

  // ============================================
  // Status Management
  // ============================================

  updateBranchStatus(branchId: string, status: BranchStatus['status'], progress?: number): void {
    const currentStatus = this.branchStatuses.get(branchId);
    if (currentStatus) {
      currentStatus.status = status;
      currentStatus.last_activity = new Date();
      if (progress !== undefined) {
        currentStatus.progress_percentage = progress;
      }
      if (status === 'error') {
        currentStatus.error_count++;
      }
    }
  }

  getProjectStatus(): {
    overall_status: string;
    overall_progress: number;
    branches: BranchStatus[];
    active_plan?: OrchestrationPlan;
  } {
    const branches = Array.from(this.branchStatuses.values());
    const activeBranches = branches.filter(b => b.status !== 'idle');
    
    let overallStatus = 'idle';
    if (activeBranches.some(b => b.status === 'error')) {
      overallStatus = 'error';
    } else if (activeBranches.some(b => b.status === 'processing')) {
      overallStatus = 'processing';
    } else if (activeBranches.length > 0 && activeBranches.every(b => b.status === 'completed')) {
      overallStatus = 'completed';
    }

    const overallProgress = branches.length > 0 
      ? branches.reduce((sum, b) => sum + b.progress_percentage, 0) / branches.length 
      : 0;

    const activePlan = Array.from(this.executionPlans.values()).find(p => 
      p.active_branches.some(branchId => {
        const status = this.branchStatuses.get(branchId);
        return status && status.status !== 'idle' && status.status !== 'completed';
      })
    );

    return {
      overall_status: overallStatus,
      overall_progress: Math.round(overallProgress),
      branches,
      active_plan: activePlan
    };
  }

  // ============================================
  // Error Handling & Recovery
  // ============================================

  private async handleGlobalError(error: any): Promise<void> {
    console.error(`🚨 Global error in Master Orchestrator:`, error);

    // Notify all active branches to pause/cleanup
    await this.broadcastMessage({
      id: `error-${Date.now()}`,
      from_branch: 'master',
      message_type: 'error',
      payload: {
        error_message: error instanceof Error ? error.message : 'Unknown error',
        action: 'pause_and_cleanup'
      },
      timestamp: new Date(),
      requires_response: false
    });

    // Update all processing branches to error state
    for (const [branchId, status] of this.branchStatuses) {
      if (status.status === 'processing') {
        this.updateBranchStatus(branchId, 'error');
      }
    }

    // Log to global error system (when implemented)
    // await globalErrorLogger.log({...})
  }

  async retryFailedBranch(branchId: string): Promise<void> {
    const status = this.branchStatuses.get(branchId);
    if (!status || status.status !== 'error') {
      throw new Error(`Branch ${branchId} is not in error state`);
    }

    console.log(`🔄 Retrying failed branch: ${branchId}`);
    
    // Reset status
    this.updateBranchStatus(branchId, 'idle', 0);
    
    // Re-execute branch
    const orchestrator = this.branchOrchestrators.get(branchId);
    if (orchestrator) {
      try {
        this.updateBranchStatus(branchId, 'processing');
        await orchestrator.execute();
        this.updateBranchStatus(branchId, 'completed', 100);
        console.log(`✅ Successfully retried branch: ${branchId}`);
      } catch (error) {
        this.updateBranchStatus(branchId, 'error');
        throw error;
      }
    }
  }

  // ============================================
  // Public Interface
  // ============================================

  getAgentInfo(): Agent {
    return { ...this.agentInfo };
  }

  getMessageHistory(): CrossBranchMessage[] {
    return [...this.messageQueue];
  }

  async shutdown(): Promise<void> {
    console.log('🛑 Shutting down Master Orchestrator...');
    
    // Notify all branches to cleanup
    await this.broadcastMessage({
      id: `shutdown-${Date.now()}`,
      from_branch: 'master',
      message_type: 'request_status',
      payload: { action: 'shutdown' },
      timestamp: new Date(),
      requires_response: false
    });

    // Clear all state
    this.branchOrchestrators.clear();
    this.messageQueue = [];
    this.executionPlans.clear();
    
    this.agentInfo.status = 'idle';
    console.log('✅ Master Orchestrator shutdown complete');
  }
}

// ============================================
// Factory Function
// ============================================

export function createBartonMasterOrchestrator(): MasterOrchestrator {
  return new MasterOrchestrator();
}