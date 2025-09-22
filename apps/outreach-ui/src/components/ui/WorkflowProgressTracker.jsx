import React, { useState } from 'react';
import Icon from '../AppIcon';

const WorkflowProgressTracker = ({ 
  currentStep = 2, 
  totalSteps = 9, 
  workflowId = 'WF-2025-001',
  processId = 'PRC-001',
  altitude = 'OPERATIONAL',
  className = '' 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const workflowSteps = [
    { id: 1, name: 'Data Intake', status: 'completed', icon: 'Database' },
    { id: 2, name: 'Data Validation', status: 'active', icon: 'CheckCircle' },
    { id: 3, name: 'Quality Assessment', status: 'pending', icon: 'Shield' },
    { id: 4, name: 'Data Enrichment', status: 'pending', icon: 'Plus' },
    { id: 5, name: 'Segmentation', status: 'pending', icon: 'Filter' },
    { id: 6, name: 'Campaign Setup', status: 'pending', icon: 'Target' },
    { id: 7, name: 'Review & Approval', status: 'pending', icon: 'Eye' },
    { id: 8, name: 'Deployment', status: 'pending', icon: 'Send' },
    { id: 9, name: 'Monitoring', status: 'pending', icon: 'Activity' }
  ];

  const getStepStatus = (stepId) => {
    if (stepId < currentStep) return 'completed';
    if (stepId === currentStep) return 'active';
    return 'pending';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-success bg-success/10';
      case 'active': return 'text-accent bg-accent/10';
      case 'pending': return 'text-muted-foreground bg-muted';
      default: return 'text-muted-foreground bg-muted';
    }
  };

  const getAltitudeBadgeColor = (altitude) => {
    switch (altitude) {
      case 'OPERATIONAL': return 'bg-success text-success-foreground';
      case 'TACTICAL': return 'bg-warning text-warning-foreground';
      case 'STRATEGIC': return 'bg-primary text-primary-foreground';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const progressPercentage = ((currentStep - 1) / (totalSteps - 1)) * 100;

  return (
    <div className={`flex items-center space-x-4 ${className}`}>
      {/* Compact Progress Display */}
      <div className="flex items-center space-x-3">
        {/* Workflow ID */}
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-muted rounded-md">
          <Icon name="Hash" size={12} color="var(--color-muted-foreground)" />
          <span className="text-xs font-data text-muted-foreground">
            {workflowId}
          </span>
        </div>

        {/* Process ID */}
        <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 bg-muted rounded-md">
          <Icon name="Workflow" size={12} color="var(--color-muted-foreground)" />
          <span className="text-xs font-data text-muted-foreground">
            {processId}
          </span>
        </div>

        {/* Current Step Progress */}
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-accent/10 text-accent rounded-md">
          <Icon name="Activity" size={12} />
          <span className="text-xs font-medium">
            {currentStep}/{totalSteps}
          </span>
        </div>

        {/* Altitude Badge */}
        <div className={`px-2 py-1 rounded text-xs font-medium ${getAltitudeBadgeColor(altitude)}`}>
          {altitude}
        </div>

        {/* Expand/Collapse Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-1.5 rounded-md hover:bg-muted transition-colors duration-200"
          aria-label={isExpanded ? 'Collapse workflow details' : 'Expand workflow details'}
        >
          <Icon 
            name={isExpanded ? "ChevronUp" : "ChevronDown"} 
            size={14} 
            color="var(--color-muted-foreground)" 
          />
        </button>
      </div>
      {/* Expanded Progress Details */}
      {isExpanded && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-card border border-border rounded-lg shadow-modal z-[1010] animate-slide-in">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-foreground">Workflow Progress</h3>
              <div className="text-xs text-muted-foreground">
                {Math.round(progressPercentage)}% Complete
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-muted rounded-full h-2 mb-4">
              <div 
                className="bg-accent h-2 rounded-full transition-all duration-300 ease-micro"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>

            {/* Step List */}
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {workflowSteps?.map((step) => {
                const status = getStepStatus(step?.id);
                return (
                  <div
                    key={step?.id}
                    className={`
                      flex items-center space-x-3 p-2 rounded-md transition-colors duration-200
                      ${status === 'active' ? 'bg-accent/5' : ''}
                    `}
                  >
                    <div className={`
                      flex items-center justify-center w-6 h-6 rounded-full text-xs
                      ${getStatusColor(status)}
                    `}>
                      {status === 'completed' ? (
                        <Icon name="Check" size={12} />
                      ) : status === 'active' ? (
                        <Icon name={step?.icon} size={12} />
                      ) : (
                        <span>{step?.id}</span>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className={`
                        text-sm font-medium
                        ${status === 'active' ? 'text-accent' : 
                          status === 'completed' ? 'text-success' : 'text-muted-foreground'}
                      `}>
                        {step?.name}
                      </div>
                    </div>
                    {status === 'active' && (
                      <div className="w-2 h-2 bg-accent rounded-full animate-pulse-gentle" />
                    )}
                  </div>
                );
              })}
            </div>

            {/* Metadata Footer */}
            <div className="mt-4 pt-3 border-t border-border">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-muted-foreground">Started:</span>
                  <span className="ml-1 font-data">2025-09-19</span>
                </div>
                <div>
                  <span className="text-muted-foreground">ETA:</span>
                  <span className="ml-1 font-data">2025-09-21</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowProgressTracker;