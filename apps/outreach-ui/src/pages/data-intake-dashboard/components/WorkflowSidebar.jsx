import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

import DoctrinalMetadataDisplay from '../../../components/ui/DoctrinalMetadataDisplay';

const WorkflowSidebar = ({ 
  currentStep = 1, 
  workflowId = 'WF-2025-001',
  processId = 'PRC-001',
  onNextStep,
  canProceed = false
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const workflowSteps = [
    { id: 1, name: 'Data Intake', description: 'Upload and preview company data', icon: 'Database', status: 'active' },
    { id: 2, name: 'Data Validation', description: 'Validate data quality and format', icon: 'CheckCircle', status: 'pending' },
    { id: 3, name: 'Quality Assessment', description: 'Assess data completeness', icon: 'Shield', status: 'pending' },
    { id: 4, name: 'Data Enrichment', description: 'Enhance with additional data', icon: 'Plus', status: 'pending' },
    { id: 5, name: 'Segmentation', description: 'Segment prospects by criteria', icon: 'Filter', status: 'pending' },
    { id: 6, name: 'Campaign Setup', description: 'Configure outreach campaigns', icon: 'Target', status: 'pending' },
    { id: 7, name: 'Review & Approval', description: 'Final review before deployment', icon: 'Eye', status: 'pending' },
    { id: 8, name: 'Deployment', description: 'Deploy to outreach systems', icon: 'Send', status: 'pending' }
  ];

  const getStepStatus = (stepId) => {
    if (stepId < currentStep) return 'completed';
    if (stepId === currentStep) return 'active';
    return 'pending';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-success bg-success/10 border-success/20';
      case 'active': return 'text-accent bg-accent/10 border-accent/20';
      case 'pending': return 'text-muted-foreground bg-muted border-border';
      default: return 'text-muted-foreground bg-muted border-border';
    }
  };

  const progressPercentage = ((currentStep - 1) / (workflowSteps?.length - 1)) * 100;

  return (
    <div className={`
      bg-card border-l border-border transition-all duration-300 ease-micro
      ${isExpanded ? 'w-80' : 'w-16'}
    `}>
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          {isExpanded && (
            <div>
              <h2 className="text-sm font-semibold text-foreground">Workflow Progress</h2>
              <p className="text-xs text-muted-foreground">IMO Process Pipeline</p>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsExpanded(!isExpanded)}
            className="shrink-0"
          >
            <Icon name={isExpanded ? "ChevronRight" : "ChevronLeft"} size={16} />
          </Button>
        </div>
      </div>
      {/* Doctrinal Metadata */}
      {isExpanded && (
        <div className="p-4 border-b border-border bg-muted/30">
          <DoctrinalMetadataDisplay
            uniqueId={workflowId}
            processId={processId}
            altitude="OPERATIONAL"
            className="flex-col space-y-2 space-x-0"
          />
        </div>
      )}
      {/* Progress Bar */}
      {isExpanded && (
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-foreground">Overall Progress</span>
            <span className="text-xs text-muted-foreground">{Math.round(progressPercentage)}%</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div 
              className="bg-accent h-2 rounded-full transition-all duration-500 ease-micro"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      )}
      {/* Workflow Steps */}
      <div className="flex-1 overflow-y-auto">
        {isExpanded ? (
          <div className="p-4 space-y-3">
            {workflowSteps?.map((step, index) => {
              const status = getStepStatus(step?.id);
              return (
                <div
                  key={step?.id}
                  className={`
                    relative p-3 rounded-lg border transition-all duration-200
                    ${getStatusColor(status)}
                    ${status === 'active' ? 'shadow-elevation-1' : ''}
                  `}
                >
                  {/* Step Number & Icon */}
                  <div className="flex items-start space-x-3">
                    <div className={`
                      flex items-center justify-center w-8 h-8 rounded-full text-xs font-medium
                      ${status === 'completed' ? 'bg-success text-success-foreground' :
                        status === 'active' ? 'bg-accent text-accent-foreground' :
                        'bg-muted text-muted-foreground'}
                    `}>
                      {status === 'completed' ? (
                        <Icon name="Check" size={14} />
                      ) : (
                        <span>{step?.id}</span>
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-medium text-foreground truncate">
                          {step?.name}
                        </h3>
                        {status === 'active' && (
                          <div className="w-2 h-2 bg-accent rounded-full animate-pulse-gentle" />
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                        {step?.description}
                      </p>
                    </div>
                  </div>
                  {/* Connection Line */}
                  {index < workflowSteps?.length - 1 && (
                    <div className={`
                      absolute left-7 top-11 w-0.5 h-6 
                      ${status === 'completed' ? 'bg-success/30' : 'bg-border'}
                    `} />
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-2 space-y-2">
            {workflowSteps?.map((step) => {
              const status = getStepStatus(step?.id);
              return (
                <div
                  key={step?.id}
                  className={`
                    flex items-center justify-center w-12 h-12 rounded-lg
                    ${getStatusColor(status)}
                  `}
                  title={step?.name}
                >
                  {status === 'completed' ? (
                    <Icon name="Check" size={16} />
                  ) : (
                    <Icon name={step?.icon} size={16} />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
      {/* Next Step Button */}
      {isExpanded && (
        <div className="p-4 border-t border-border">
          <Button
            variant="default"
            fullWidth
            iconName="ArrowRight"
            iconPosition="right"
            disabled={!canProceed}
            onClick={onNextStep}
          >
            Next Step
          </Button>
          
          {!canProceed && (
            <p className="text-xs text-muted-foreground mt-2 text-center">
              Complete current step to proceed
            </p>
          )}
        </div>
      )}
      {/* Keyboard Shortcuts */}
      {isExpanded && (
        <div className="p-4 border-t border-border bg-muted/30">
          <h4 className="text-xs font-medium text-foreground mb-2">Shortcuts</h4>
          <div className="space-y-1 text-xs text-muted-foreground">
            <div className="flex items-center justify-between">
              <span>Upload file</span>
              <kbd className="px-1.5 py-0.5 bg-muted rounded font-data">Ctrl+U</kbd>
            </div>
            <div className="flex items-center justify-between">
              <span>Ingest data</span>
              <kbd className="px-1.5 py-0.5 bg-muted rounded font-data">Enter</kbd>
            </div>
            <div className="flex items-center justify-between">
              <span>Next step</span>
              <kbd className="px-1.5 py-0.5 bg-muted rounded font-data">Ctrl+→</kbd>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowSidebar;