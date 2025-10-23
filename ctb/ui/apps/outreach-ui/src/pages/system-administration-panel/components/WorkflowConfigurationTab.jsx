import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';
import Select from '../../../components/ui/Select';

const WorkflowConfigurationTab = () => {
  const [selectedWorkflow, setSelectedWorkflow] = useState('outreach-pipeline');
  const [isDragging, setIsDragging] = useState(false);

  const workflowOptions = [
    { value: 'outreach-pipeline', label: 'Outreach Pipeline' },
    { value: 'data-validation', label: 'Data Validation Workflow' },
    { value: 'campaign-setup', label: 'Campaign Setup Process' }
  ];

  const workflowSteps = [
    {
      id: 'data-intake',
      name: 'Data Intake',
      description: 'CSV upload and initial processing',
      icon: 'Database',
      status: 'active',
      processingTime: '2-5 minutes',
      rules: ['File size < 50MB', 'CSV format validation', 'Column mapping']
    },
    {
      id: 'data-validation',
      name: 'Data Validation',
      description: 'Schema validation and quality checks',
      icon: 'CheckCircle',
      status: 'active',
      processingTime: '1-3 minutes',
      rules: ['Email format validation', 'Required field checks', 'Duplicate detection']
    },
    {
      id: 'quality-assessment',
      name: 'Quality Assessment',
      description: 'Data quality scoring and enrichment',
      icon: 'Shield',
      status: 'active',
      processingTime: '3-7 minutes',
      rules: ['Data completeness score', 'Contact verification', 'Company matching']
    },
    {
      id: 'data-enrichment',
      name: 'Data Enrichment',
      description: 'External data source integration',
      icon: 'Plus',
      status: 'active',
      processingTime: '5-10 minutes',
      rules: ['LinkedIn profile matching', 'Company size lookup', 'Industry classification']
    },
    {
      id: 'segmentation',
      name: 'Segmentation',
      description: 'Audience segmentation and targeting',
      icon: 'Filter',
      status: 'active',
      processingTime: '2-4 minutes',
      rules: ['Industry-based grouping', 'Company size segments', 'Geographic clustering']
    },
    {
      id: 'campaign-setup',
      name: 'Campaign Setup',
      description: 'Campaign configuration and scheduling',
      icon: 'Target',
      status: 'active',
      processingTime: '1-2 minutes',
      rules: ['Template selection', 'Send schedule', 'Tracking configuration']
    },
    {
      id: 'review-approval',
      name: 'Review & Approval',
      description: 'Manual review and approval process',
      icon: 'Eye',
      status: 'active',
      processingTime: 'Manual',
      rules: ['Content review', 'Compliance check', 'Manager approval']
    },
    {
      id: 'deployment',
      name: 'Deployment',
      description: 'Campaign deployment and execution',
      icon: 'Send',
      status: 'active',
      processingTime: '1-5 minutes',
      rules: ['Email delivery', 'Tracking activation', 'Response monitoring']
    },
    {
      id: 'monitoring',
      name: 'Monitoring',
      description: 'Real-time campaign monitoring',
      icon: 'Activity',
      status: 'active',
      processingTime: 'Continuous',
      rules: ['Delivery tracking', 'Response monitoring', 'Performance analytics']
    }
  ];

  const integrationEndpoints = [
    {
      id: 'composio-mcp',
      name: 'Composio MCP',
      type: 'Database',
      status: 'connected',
      url: 'https://api.composio.dev/v1/mcp',
      lastSync: '2025-09-19T15:30:00Z'
    },
    {
      id: 'neon-database',
      name: 'Neon Database',
      type: 'Storage',
      status: 'connected',
      url: 'postgresql://neon.tech/marketing',
      lastSync: '2025-09-19T15:35:00Z'
    },
    {
      id: 'linkedin-api',
      name: 'LinkedIn Sales Navigator',
      type: 'Enrichment',
      status: 'warning',
      url: 'https://api.linkedin.com/v2/',
      lastSync: '2025-09-19T14:20:00Z'
    },
    {
      id: 'sendgrid-api',
      name: 'SendGrid Email API',
      type: 'Delivery',
      status: 'connected',
      url: 'https://api.sendgrid.com/v3/',
      lastSync: '2025-09-19T15:38:00Z'
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'text-success bg-success/10';
      case 'warning': return 'text-warning bg-warning/10';
      case 'error': return 'text-error bg-error/10';
      case 'disconnected': return 'text-muted-foreground bg-muted';
      default: return 'text-muted-foreground bg-muted';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected': return 'CheckCircle';
      case 'warning': return 'AlertTriangle';
      case 'error': return 'XCircle';
      case 'disconnected': return 'Circle';
      default: return 'Circle';
    }
  };

  return (
    <div className="space-y-6">
      {/* Workflow Selection */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center space-x-4">
          <Select
            label="Select Workflow"
            options={workflowOptions}
            value={selectedWorkflow}
            onChange={setSelectedWorkflow}
            className="w-64"
          />
          <Button variant="outline" iconName="Copy" iconPosition="left">
            Clone Workflow
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" iconName="Download" iconPosition="left">
            Export Config
          </Button>
          <Button variant="default" iconName="Save" iconPosition="left">
            Save Changes
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Workflow Pipeline Editor */}
        <div className="xl:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-foreground">Pipeline Steps</h3>
            <Button variant="outline" size="sm" iconName="Plus" iconPosition="left">
              Add Step
            </Button>
          </div>

          <div className="bg-card border border-border rounded-lg p-6">
            <div className="space-y-4">
              {workflowSteps?.map((step, index) => (
                <div key={step?.id} className="relative">
                  <div className="flex items-center space-x-4 p-4 bg-muted/30 border border-border rounded-lg hover:bg-muted/50 transition-colors cursor-move">
                    <div className="flex items-center justify-center w-10 h-10 bg-accent/10 text-accent rounded-lg">
                      <Icon name={step?.icon} size={20} />
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-foreground">{step?.name}</h4>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-muted-foreground">{step?.processingTime}</span>
                          <Button variant="ghost" size="icon" iconName="Settings" />
                          <Button variant="ghost" size="icon" iconName="GripVertical" />
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{step?.description}</p>
                      
                      <div className="flex flex-wrap gap-1 mt-2">
                        {step?.rules?.slice(0, 2)?.map((rule, ruleIndex) => (
                          <span key={ruleIndex} className="inline-flex items-center px-2 py-1 rounded text-xs bg-accent/10 text-accent">
                            {rule}
                          </span>
                        ))}
                        {step?.rules?.length > 2 && (
                          <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-muted text-muted-foreground">
                            +{step?.rules?.length - 2} more
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {index < workflowSteps?.length - 1 && (
                    <div className="flex justify-center my-2">
                      <Icon name="ArrowDown" size={16} color="var(--color-muted-foreground)" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Integration Management */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-foreground">Integration Endpoints</h3>
            <Button variant="outline" size="sm" iconName="Plus" iconPosition="left">
              Add Endpoint
            </Button>
          </div>

          <div className="space-y-3">
            {integrationEndpoints?.map((endpoint) => (
              <div key={endpoint?.id} className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className={`
                      flex items-center justify-center w-8 h-8 rounded-lg
                      ${getStatusColor(endpoint?.status)}
                    `}>
                      <Icon name={getStatusIcon(endpoint?.status)} size={16} />
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground">{endpoint?.name}</h4>
                      <p className="text-xs text-muted-foreground">{endpoint?.type}</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" iconName="Settings" />
                </div>
                
                <div className="space-y-2">
                  <div className="text-xs font-data text-muted-foreground break-all">
                    {endpoint?.url}
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Last sync:</span>
                    <span className="font-data text-foreground">
                      {new Date(endpoint.lastSync)?.toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2 mt-3">
                  <Button variant="outline" size="sm" iconName="RefreshCw">
                    Test
                  </Button>
                  <Button variant="outline" size="sm" iconName="Activity">
                    Logs
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {/* Processing Rules */}
          <div className="bg-card border border-border rounded-lg p-4">
            <h4 className="font-medium text-foreground mb-3">Global Processing Rules</h4>
            <div className="space-y-3">
              <Input
                label="Max File Size (MB)"
                type="number"
                value="50"
                className="w-full"
              />
              <Input
                label="Processing Timeout (minutes)"
                type="number"
                value="30"
                className="w-full"
              />
              <Input
                label="Retry Attempts"
                type="number"
                value="3"
                className="w-full"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowConfigurationTab;