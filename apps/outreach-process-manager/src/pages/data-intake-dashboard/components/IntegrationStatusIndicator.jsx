import React, { useState, useEffect } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const IntegrationStatusIndicator = ({ className = '' }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState({
    composioMcp: 'connected',
    neonDatabase: 'connected',
    claudeCode: 'connected',
    lastHealthCheck: new Date(),
    responseTime: '127ms'
  });

  // Simulate real-time status updates
  useEffect(() => {
    const interval = setInterval(() => {
      setConnectionStatus(prev => ({
        ...prev,
        lastHealthCheck: new Date(),
        responseTime: `${Math.floor(Math.random() * 200 + 50)}ms`
      }));
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const integrationServices = [
    {
      name: 'Composio MCP',
      status: connectionStatus?.composioMcp,
      description: 'Model Context Protocol integration layer',
      icon: 'Cpu',
      endpoint: 'mcp://composio.local:8080'
    },
    {
      name: 'Neon Database',
      status: connectionStatus?.neonDatabase,
      description: 'Primary data storage for marketing.company_raw_intake',
      icon: 'Database',
      endpoint: 'postgresql://neon.tech:5432'
    },
    {
      name: 'Claude Code',
      status: connectionStatus?.claudeCode,
      description: 'AI processing layer for data validation',
      icon: 'Brain',
      endpoint: 'https://api.anthropic.com/v1'
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'text-success bg-success/10';
      case 'connecting': return 'text-warning bg-warning/10';
      case 'disconnected': return 'text-error bg-error/10';
      case 'maintenance': return 'text-muted-foreground bg-muted';
      default: return 'text-muted-foreground bg-muted';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected': return 'CheckCircle';
      case 'connecting': return 'Clock';
      case 'disconnected': return 'XCircle';
      case 'maintenance': return 'Wrench';
      default: return 'Circle';
    }
  };

  const getOverallStatus = () => {
    const statuses = [connectionStatus?.composioMcp, connectionStatus?.neonDatabase, connectionStatus?.claudeCode];
    
    if (statuses?.includes('disconnected')) return 'disconnected';
    if (statuses?.includes('connecting')) return 'connecting';
    if (statuses?.includes('maintenance')) return 'maintenance';
    return 'connected';
  };

  const overallStatus = getOverallStatus();

  const formatLastCheck = (date) => {
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  };

  return (
    <div className={`relative flex items-center ${className}`}>
      {/* Main Status Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`
          flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium
          transition-all duration-200 ease-micro hover:shadow-elevation-1
          ${getStatusColor(overallStatus)}
        `}
        title="Integration Status"
      >
        <div className="relative">
          <Icon name={getStatusIcon(overallStatus)} size={12} />
          {overallStatus === 'connected' && (
            <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-success rounded-full animate-pulse-gentle" />
          )}
        </div>
        <span className="hidden sm:inline">
          {overallStatus === 'connected' ? 'All Systems' : 
           overallStatus === 'connecting' ? 'Connecting' : 
           overallStatus === 'maintenance' ? 'Maintenance' : 'Issues Detected'}
        </span>
        <Icon name="ChevronDown" size={10} />
      </button>
      {/* Expanded Status Panel */}
      {isExpanded && (
        <div className="absolute top-full right-0 mt-2 w-96 bg-card border border-border rounded-lg shadow-modal z-[1010] animate-slide-in">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-foreground">Integration Status</h3>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-muted-foreground">
                  {formatLastCheck(connectionStatus?.lastHealthCheck)}
                </span>
                <button
                  onClick={() => setIsExpanded(false)}
                  className="p-1 rounded-md hover:bg-muted transition-colors duration-200"
                >
                  <Icon name="X" size={14} color="var(--color-muted-foreground)" />
                </button>
              </div>
            </div>

            {/* Overall Status */}
            <div className={`
              flex items-center space-x-3 p-3 rounded-md mb-4
              ${getStatusColor(overallStatus)}
            `}>
              <Icon name={getStatusIcon(overallStatus)} size={16} />
              <div className="flex-1">
                <div className="text-sm font-medium">
                  Integration Status: {overallStatus?.charAt(0)?.toUpperCase() + overallStatus?.slice(1)}
                </div>
                <div className="text-xs opacity-80">
                  Response time: {connectionStatus?.responseTime}
                </div>
              </div>
            </div>

            {/* Service Status List */}
            <div className="space-y-3">
              {integrationServices?.map((service) => (
                <div
                  key={service?.name}
                  className="flex items-start space-x-3 p-3 rounded-md hover:bg-muted/50 transition-colors duration-200"
                >
                  <div className={`
                    flex items-center justify-center w-10 h-10 rounded-md
                    ${getStatusColor(service?.status)}
                  `}>
                    <Icon name={service?.icon} size={16} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-foreground">
                        {service?.name}
                      </span>
                      <div className={`
                        flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-medium
                        ${getStatusColor(service?.status)}
                      `}>
                        <Icon name={getStatusIcon(service?.status)} size={10} />
                        <span className="capitalize">{service?.status}</span>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground mb-2">
                      {service?.description}
                    </div>
                    <div className="text-xs font-data text-muted-foreground bg-muted/50 px-2 py-1 rounded truncate">
                      {service?.endpoint}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Connection Details */}
            <div className="mt-4 pt-3 border-t border-border">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-muted-foreground">Last Check:</span>
                  <span className="ml-1 font-data text-foreground">
                    {connectionStatus?.lastHealthCheck?.toLocaleTimeString()}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Avg Response:</span>
                  <span className="ml-1 font-data text-foreground">
                    {connectionStatus?.responseTime}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Uptime:</span>
                  <span className="ml-1 font-data text-success">99.9%</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Region:</span>
                  <span className="ml-1 font-data text-foreground">US-East-1</span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-4 pt-3 border-t border-border">
              <div className="flex items-center justify-between">
                <Button
                  variant="ghost"
                  size="sm"
                  iconName="RefreshCw"
                  iconPosition="left"
                  onClick={() => {
                    setConnectionStatus(prev => ({
                      ...prev,
                      lastHealthCheck: new Date()
                    }));
                  }}
                >
                  Refresh Status
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  iconName="ExternalLink"
                  iconPosition="right"
                >
                  View Logs
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationStatusIndicator;