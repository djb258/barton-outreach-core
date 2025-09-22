import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';
import Select from '../../../components/ui/Select';

const IntegrationManagementTab = () => {
  const [selectedIntegration, setSelectedIntegration] = useState('');
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);

  const integrations = [
    {
      id: 'composio-mcp',
      name: 'Composio MCP',
      type: 'Database Integration',
      status: 'connected',
      version: '2.1.4',
      lastSync: '2025-09-19T15:35:00Z',
      description: 'Model Context Protocol integration for database operations',
      endpoint: 'https://api.composio.dev/v1/mcp',
      rateLimits: {
        requests: 1000,
        window: '1 hour',
        current: 247
      },
      health: {
        uptime: 99.8,
        avgResponse: 145,
        errorRate: 0.2
      }
    },
    {
      id: 'neon-database',
      name: 'Neon PostgreSQL',
      type: 'Primary Database',
      status: 'connected',
      version: '15.4',
      lastSync: '2025-09-19T15:38:00Z',
      description: 'Primary database for marketing data storage',
      endpoint: 'postgresql://neon.tech:5432/marketing',
      rateLimits: {
        connections: 100,
        window: 'concurrent',
        current: 45
      },
      health: {
        uptime: 99.9,
        avgResponse: 23,
        errorRate: 0.1
      }
    },
    {
      id: 'linkedin-api',
      name: 'LinkedIn Sales Navigator',
      type: 'Data Enrichment',
      status: 'warning',
      version: '2.0',
      lastSync: '2025-09-19T14:20:00Z',
      description: 'Professional profile and company data enrichment',
      endpoint: 'https://api.linkedin.com/v2/',
      rateLimits: {
        requests: 500,
        window: '1 hour',
        current: 487
      },
      health: {
        uptime: 97.2,
        avgResponse: 890,
        errorRate: 2.8
      }
    },
    {
      id: 'sendgrid-api',
      name: 'SendGrid Email API',
      type: 'Email Delivery',
      status: 'connected',
      version: '3.0',
      lastSync: '2025-09-19T15:30:00Z',
      description: 'Transactional and marketing email delivery service',
      endpoint: 'https://api.sendgrid.com/v3/',
      rateLimits: {
        emails: 10000,
        window: '1 day',
        current: 2340
      },
      health: {
        uptime: 99.5,
        avgResponse: 234,
        errorRate: 0.5
      }
    },
    {
      id: 'hubspot-crm',
      name: 'HubSpot CRM',
      type: 'CRM Integration',
      status: 'disconnected',
      version: '1.0',
      lastSync: '2025-09-18T10:15:00Z',
      description: 'Customer relationship management system integration',
      endpoint: 'https://api.hubapi.com/crm/v3/',
      rateLimits: {
        requests: 1000,
        window: '10 minutes',
        current: 0
      },
      health: {
        uptime: 0,
        avgResponse: 0,
        errorRate: 100
      }
    }
  ];

  const apiKeys = [
    {
      id: 1,
      name: 'Production API Key',
      service: 'Composio MCP',
      created: '2025-09-01T10:00:00Z',
      lastUsed: '2025-09-19T15:30:00Z',
      permissions: ['read', 'write'],
      status: 'active'
    },
    {
      id: 2,
      name: 'LinkedIn Integration Key',
      service: 'LinkedIn API',
      created: '2025-08-15T14:30:00Z',
      lastUsed: '2025-09-19T14:20:00Z',
      permissions: ['read'],
      status: 'warning'
    },
    {
      id: 3,
      name: 'SendGrid Delivery Key',
      service: 'SendGrid API',
      created: '2025-07-20T09:15:00Z',
      lastUsed: '2025-09-19T15:25:00Z',
      permissions: ['send'],
      status: 'active'
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

  const getHealthColor = (value, type) => {
    if (type === 'uptime') {
      if (value >= 99) return 'text-success';
      if (value >= 95) return 'text-warning';
      return 'text-error';
    }
    if (type === 'errorRate') {
      if (value <= 1) return 'text-success';
      if (value <= 5) return 'text-warning';
      return 'text-error';
    }
    return 'text-foreground';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp)?.toLocaleString();
  };

  const getRateLimitPercentage = (current, limit) => {
    return (current / limit) * 100;
  };

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-semibold text-foreground">Integration Management</h2>
          <div className="flex items-center space-x-2 px-3 py-1.5 bg-success/10 text-success rounded-md">
            <Icon name="CheckCircle" size={12} />
            <span className="text-xs font-medium">4 of 5 Connected</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" iconName="RefreshCw" iconPosition="left">
            Sync All
          </Button>
          <Button variant="default" iconName="Plus" iconPosition="left">
            Add Integration
          </Button>
        </div>
      </div>
      {/* Integration Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {integrations?.map((integration) => (
          <div key={integration?.id} className="bg-card border border-border rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`
                  flex items-center justify-center w-12 h-12 rounded-lg
                  ${getStatusColor(integration?.status)}
                `}>
                  <Icon name={getStatusIcon(integration?.status)} size={20} />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{integration?.name}</h3>
                  <p className="text-sm text-muted-foreground">{integration?.type}</p>
                </div>
              </div>
              <div className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(integration?.status)}`}>
                {integration?.status}
              </div>
            </div>

            <p className="text-sm text-muted-foreground mb-4">{integration?.description}</p>

            {/* Health Metrics */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className={`text-lg font-bold ${getHealthColor(integration?.health?.uptime, 'uptime')}`}>
                  {integration?.health?.uptime}%
                </div>
                <div className="text-xs text-muted-foreground">Uptime</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-foreground">
                  {integration?.health?.avgResponse}ms
                </div>
                <div className="text-xs text-muted-foreground">Avg Response</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-bold ${getHealthColor(integration?.health?.errorRate, 'errorRate')}`}>
                  {integration?.health?.errorRate}%
                </div>
                <div className="text-xs text-muted-foreground">Error Rate</div>
              </div>
            </div>

            {/* Rate Limits */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-foreground">Rate Limits</span>
                <span className="text-xs text-muted-foreground">
                  {integration?.rateLimits?.current} / {integration?.rateLimits?.requests} {integration?.rateLimits?.window}
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    getRateLimitPercentage(integration?.rateLimits?.current, integration?.rateLimits?.requests) > 80 
                      ? 'bg-error' 
                      : getRateLimitPercentage(integration?.rateLimits?.current, integration?.rateLimits?.requests) > 60 
                        ? 'bg-warning' :'bg-success'
                  }`}
                  style={{ 
                    width: `${getRateLimitPercentage(integration?.rateLimits?.current, integration?.rateLimits?.requests)}%` 
                  }}
                />
              </div>
            </div>

            {/* Connection Details */}
            <div className="space-y-2 mb-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Version:</span>
                <span className="font-data text-foreground">{integration?.version}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Last Sync:</span>
                <span className="font-data text-foreground">
                  {formatTimestamp(integration?.lastSync)}
                </span>
              </div>
              <div className="text-sm">
                <span className="text-muted-foreground">Endpoint:</span>
                <div className="font-data text-foreground text-xs break-all mt-1">
                  {integration?.endpoint}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-2">
              <Button 
                variant="outline" 
                size="sm" 
                iconName="RefreshCw"
                disabled={integration?.status === 'disconnected'}
              >
                Test
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                iconName="Settings"
              >
                Configure
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                iconName="Activity"
              >
                Logs
              </Button>
            </div>
          </div>
        ))}
      </div>
      {/* API Keys Management */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">API Keys</h3>
          <Button 
            variant="default" 
            iconName="Plus" 
            iconPosition="left"
            onClick={() => setShowApiKeyModal(true)}
          >
            Generate Key
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="text-left p-3 font-medium text-foreground">Name</th>
                <th className="text-left p-3 font-medium text-foreground">Service</th>
                <th className="text-left p-3 font-medium text-foreground">Permissions</th>
                <th className="text-left p-3 font-medium text-foreground">Created</th>
                <th className="text-left p-3 font-medium text-foreground">Last Used</th>
                <th className="text-left p-3 font-medium text-foreground">Status</th>
                <th className="w-24 p-3 font-medium text-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {apiKeys?.map((key) => (
                <tr key={key?.id} className="border-b border-border hover:bg-muted/30 transition-colors">
                  <td className="p-3 font-medium text-foreground">{key?.name}</td>
                  <td className="p-3 text-muted-foreground">{key?.service}</td>
                  <td className="p-3">
                    <div className="flex flex-wrap gap-1">
                      {key?.permissions?.map((permission) => (
                        <span
                          key={permission}
                          className="inline-flex items-center px-2 py-1 rounded text-xs bg-accent/10 text-accent"
                        >
                          {permission}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="p-3 text-sm font-data text-muted-foreground">
                    {formatTimestamp(key?.created)}
                  </td>
                  <td className="p-3 text-sm font-data text-muted-foreground">
                    {formatTimestamp(key?.lastUsed)}
                  </td>
                  <td className="p-3">
                    <div className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusColor(key?.status)}`}>
                      {key?.status}
                    </div>
                  </td>
                  <td className="p-3">
                    <div className="flex items-center space-x-1">
                      <Button variant="ghost" size="icon" iconName="Eye" />
                      <Button variant="ghost" size="icon" iconName="Trash2" />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {/* Rate Limiting Policies */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Rate Limiting Policies</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <Input
              label="Default Request Limit"
              type="number"
              value="1000"
              description="Requests per hour for standard integrations"
            />
            <Input
              label="Burst Limit"
              type="number"
              value="100"
              description="Maximum requests in a 1-minute window"
            />
            <Input
              label="Retry Delay (seconds)"
              type="number"
              value="60"
              description="Delay before retrying failed requests"
            />
          </div>
          
          <div className="space-y-4">
            <Select
              label="Rate Limit Strategy"
              options={[
                { value: 'fixed-window', label: 'Fixed Window' },
                { value: 'sliding-window', label: 'Sliding Window' },
                { value: 'token-bucket', label: 'Token Bucket' }
              ]}
              value="sliding-window"
            />
            <Input
              label="Timeout Duration (seconds)"
              type="number"
              value="30"
              description="Request timeout for external APIs"
            />
            <div className="flex items-center space-x-2 pt-2">
              <Button variant="outline" size="sm">
                Reset Limits
              </Button>
              <Button variant="default" size="sm">
                Save Policy
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntegrationManagementTab;