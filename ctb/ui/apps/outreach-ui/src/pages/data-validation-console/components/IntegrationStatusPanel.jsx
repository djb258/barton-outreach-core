import React, { useState, useEffect } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const IntegrationStatusPanel = ({ className = '' }) => {
  const [integrationStatus, setIntegrationStatus] = useState({
    businessRuleEngine: {
      status: 'healthy',
      lastSync: '2025-09-19T15:38:30Z',
      rulesLoaded: 47,
      responseTime: 120
    },
    dataEnrichmentAPI: {
      status: 'warning',
      lastSync: '2025-09-19T15:35:15Z',
      recordsEnriched: 1247,
      responseTime: 850
    },
    complianceChecker: {
      status: 'healthy',
      lastSync: '2025-09-19T15:39:00Z',
      checksCompleted: 892,
      responseTime: 95
    },
    composioMCP: {
      status: 'healthy',
      lastSync: '2025-09-19T15:39:15Z',
      recordsProcessed: 2156,
      responseTime: 45
    }
  });

  const [expandedPanel, setExpandedPanel] = useState(null);

  useEffect(() => {
    // Simulate real-time status updates
    const interval = setInterval(() => {
      setIntegrationStatus(prev => ({
        ...prev,
        composioMCP: {
          ...prev?.composioMCP,
          lastSync: new Date()?.toISOString(),
          recordsProcessed: prev?.composioMCP?.recordsProcessed + Math.floor(Math.random() * 5)
        }
      }));
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-success bg-success/10';
      case 'warning': return 'text-warning bg-warning/10';
      case 'error': return 'text-error bg-error/10';
      case 'offline': return 'text-muted-foreground bg-muted';
      default: return 'text-muted-foreground bg-muted';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return 'CheckCircle';
      case 'warning': return 'AlertTriangle';
      case 'error': return 'XCircle';
      case 'offline': return 'Circle';
      default: return 'Circle';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date?.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatResponseTime = (ms) => {
    return ms < 1000 ? `${ms}ms` : `${(ms / 1000)?.toFixed(1)}s`;
  };

  const integrationServices = [
    {
      id: 'businessRuleEngine',
      name: 'Business Rule Engine',
      description: 'Validates data against business logic rules',
      icon: 'Briefcase',
      data: integrationStatus?.businessRuleEngine,
      metrics: [
        { label: 'Rules Loaded', value: integrationStatus?.businessRuleEngine?.rulesLoaded },
        { label: 'Response Time', value: formatResponseTime(integrationStatus?.businessRuleEngine?.responseTime) }
      ]
    },
    {
      id: 'dataEnrichmentAPI',
      name: 'Data Enrichment API',
      description: 'Enriches company data with external sources',
      icon: 'Database',
      data: integrationStatus?.dataEnrichmentAPI,
      metrics: [
        { label: 'Records Enriched', value: integrationStatus?.dataEnrichmentAPI?.recordsEnriched },
        { label: 'Response Time', value: formatResponseTime(integrationStatus?.dataEnrichmentAPI?.responseTime) }
      ]
    },
    {
      id: 'complianceChecker',
      name: 'Compliance Checker',
      description: 'Ensures GDPR and regulatory compliance',
      icon: 'Shield',
      data: integrationStatus?.complianceChecker,
      metrics: [
        { label: 'Checks Completed', value: integrationStatus?.complianceChecker?.checksCompleted },
        { label: 'Response Time', value: formatResponseTime(integrationStatus?.complianceChecker?.responseTime) }
      ]
    },
    {
      id: 'composioMCP',
      name: 'Composio MCP',
      description: 'Model Context Protocol integration',
      icon: 'Cpu',
      data: integrationStatus?.composioMCP,
      metrics: [
        { label: 'Records Processed', value: integrationStatus?.composioMCP?.recordsProcessed },
        { label: 'Response Time', value: formatResponseTime(integrationStatus?.composioMCP?.responseTime) }
      ]
    }
  ];

  const togglePanel = (serviceId) => {
    setExpandedPanel(expandedPanel === serviceId ? null : serviceId);
  };

  const refreshService = (serviceId) => {
    // Simulate service refresh
    setIntegrationStatus(prev => ({
      ...prev,
      [serviceId]: {
        ...prev?.[serviceId],
        lastSync: new Date()?.toISOString()
      }
    }));
  };

  return (
    <div className={`bg-card border border-border rounded-lg ${className}`}>
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Icon name="Zap" size={20} color="var(--color-accent)" />
            <div>
              <h3 className="text-lg font-semibold text-foreground">Integration Status</h3>
              <p className="text-sm text-muted-foreground">External service connections and API responses</p>
            </div>
          </div>
          <Button variant="outline" size="sm" iconName="RefreshCw">
            Refresh All
          </Button>
        </div>
      </div>
      <div className="p-4 space-y-3">
        {integrationServices?.map((service) => (
          <div key={service?.id} className="border border-border rounded-lg">
            <div
              className="flex items-center justify-between p-3 cursor-pointer hover:bg-muted/30 transition-colors duration-200"
              onClick={() => togglePanel(service?.id)}
            >
              <div className="flex items-center space-x-3">
                <div className={`
                  flex items-center justify-center w-10 h-10 rounded-md
                  ${getStatusColor(service?.data?.status)}
                `}>
                  <Icon name={service?.icon} size={16} />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-foreground">{service?.name}</span>
                    <div className={`
                      flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-medium
                      ${getStatusColor(service?.data?.status)}
                    `}>
                      <Icon name={getStatusIcon(service?.data?.status)} size={10} />
                      <span className="capitalize">{service?.data?.status}</span>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">{service?.description}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <div className="text-xs text-muted-foreground">Last Sync</div>
                  <div className="text-xs font-data text-foreground">
                    {formatTimestamp(service?.data?.lastSync)}
                  </div>
                </div>
                <Icon 
                  name={expandedPanel === service?.id ? "ChevronUp" : "ChevronDown"} 
                  size={16} 
                  color="var(--color-muted-foreground)" 
                />
              </div>
            </div>

            {expandedPanel === service?.id && (
              <div className="border-t border-border p-3 bg-muted/10">
                <div className="grid grid-cols-2 gap-4 mb-4">
                  {service?.metrics?.map((metric, index) => (
                    <div key={index} className="text-center p-2 bg-card rounded border border-border">
                      <div className="text-lg font-semibold text-foreground">{metric?.value}</div>
                      <div className="text-xs text-muted-foreground">{metric?.label}</div>
                    </div>
                  ))}
                </div>

                {/* Service-specific details */}
                {service?.id === 'businessRuleEngine' && (
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-foreground">Active Rules:</div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div className="p-2 bg-success/10 text-success rounded">Email: 15 rules</div>
                      <div className="p-2 bg-warning/10 text-warning rounded">Phone: 8 rules</div>
                      <div className="p-2 bg-accent/10 text-accent rounded">Company: 24 rules</div>
                    </div>
                  </div>
                )}

                {service?.id === 'dataEnrichmentAPI' && (
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-foreground">Enrichment Sources:</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2 bg-card border border-border rounded">
                        <div className="font-medium">Clearbit API</div>
                        <div className="text-muted-foreground">Company data</div>
                      </div>
                      <div className="p-2 bg-card border border-border rounded">
                        <div className="font-medium">ZoomInfo API</div>
                        <div className="text-muted-foreground">Contact info</div>
                      </div>
                    </div>
                  </div>
                )}

                {service?.id === 'complianceChecker' && (
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-foreground">Compliance Status:</div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div className="p-2 bg-success/10 text-success rounded">GDPR: ✓</div>
                      <div className="p-2 bg-success/10 text-success rounded">CCPA: ✓</div>
                      <div className="p-2 bg-warning/10 text-warning rounded">CAN-SPAM: ⚠</div>
                    </div>
                  </div>
                )}

                {service?.id === 'composioMCP' && (
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-foreground">MCP Status:</div>
                    <div className="p-2 bg-card border border-border rounded text-xs">
                      <div className="flex justify-between">
                        <span>Database Connection:</span>
                        <span className="text-success">Active</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Queue Processing:</span>
                        <span className="text-success">Running</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Memory Usage:</span>
                        <span className="text-warning">78%</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-end space-x-2 mt-4">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    iconName="RefreshCw"
                    onClick={() => refreshService(service?.id)}
                  >
                    Refresh
                  </Button>
                  <Button variant="outline" size="sm" iconName="Settings">
                    Configure
                  </Button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      {/* Overall Status Summary */}
      <div className="p-4 border-t border-border bg-muted/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Icon name="Activity" size={16} color="var(--color-success)" />
            <span className="text-sm font-medium text-foreground">System Integration Health</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-success rounded-full animate-pulse-gentle" />
            <span className="text-sm text-success">All Systems Operational</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntegrationStatusPanel;