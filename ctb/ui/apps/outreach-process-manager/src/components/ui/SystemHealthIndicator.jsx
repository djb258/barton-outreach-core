import React, { useState, useEffect } from 'react';
import Icon from '../AppIcon';

const SystemHealthIndicator = ({ className = '' }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [systemStatus, setSystemStatus] = useState({
    overall: 'healthy',
    database: 'healthy',
    api: 'healthy',
    queue: 'healthy',
    mcp: 'healthy',
    lastUpdate: new Date()
  });

  // Simulate real-time status updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate occasional status changes for demo
      const statuses = ['healthy', 'warning', 'error'];
      const randomStatus = Math.random() > 0.9 ? statuses?.[Math.floor(Math.random() * statuses?.length)] : 'healthy';
      
      setSystemStatus(prev => ({
        ...prev,
        lastUpdate: new Date(),
        // Occasionally change one component status
        ...(Math.random() > 0.95 && {
          queue: randomStatus
        })
      }));
    }, 5000);

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

  const getOverallStatus = () => {
    const statuses = [systemStatus?.database, systemStatus?.api, systemStatus?.queue, systemStatus?.mcp];
    
    if (statuses?.includes('error')) return 'error';
    if (statuses?.includes('warning')) return 'warning';
    if (statuses?.includes('offline')) return 'warning';
    return 'healthy';
  };

  const overallStatus = getOverallStatus();

  const systemComponents = [
    {
      name: 'Database',
      status: systemStatus?.database,
      description: 'Primary data storage and retrieval',
      icon: 'Database'
    },
    {
      name: 'API Gateway',
      status: systemStatus?.api,
      description: 'External service connections',
      icon: 'Globe'
    },
    {
      name: 'Processing Queue',
      status: systemStatus?.queue,
      description: 'Background task processing',
      icon: 'Clock'
    },
    {
      name: 'Composio MCP',
      status: systemStatus?.mcp,
      description: 'Model Context Protocol integration',
      icon: 'Cpu'
    }
  ];

  const formatLastUpdate = (date) => {
    return date?.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className={`relative flex items-center ${className}`}>
      {/* Main Status Indicator */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`
          flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium
          transition-all duration-200 ease-micro hover:shadow-elevation-1
          ${getStatusColor(overallStatus)}
        `}
        title="System Health Status"
      >
        <div className="relative">
          <Icon name={getStatusIcon(overallStatus)} size={12} />
          {overallStatus === 'healthy' && (
            <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-success rounded-full animate-pulse-gentle" />
          )}
        </div>
        <span className="hidden sm:inline">
          {overallStatus === 'healthy' ? 'Online' : 
           overallStatus === 'warning' ? 'Warning' : 'Error'}
        </span>
        <Icon name="ChevronDown" size={10} />
      </button>
      {/* Expanded Status Panel */}
      {isExpanded && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-card border border-border rounded-lg shadow-modal z-[1010] animate-slide-in">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-foreground">System Health</h3>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-muted-foreground">
                  Updated: {formatLastUpdate(systemStatus?.lastUpdate)}
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
                  System Status: {overallStatus?.charAt(0)?.toUpperCase() + overallStatus?.slice(1)}
                </div>
                <div className="text-xs opacity-80">
                  All critical systems operational
                </div>
              </div>
            </div>

            {/* Component Status List */}
            <div className="space-y-2">
              {systemComponents?.map((component) => (
                <div
                  key={component?.name}
                  className="flex items-center space-x-3 p-2 rounded-md hover:bg-muted/50 transition-colors duration-200"
                >
                  <div className={`
                    flex items-center justify-center w-8 h-8 rounded-md
                    ${getStatusColor(component?.status)}
                  `}>
                    <Icon name={component?.icon} size={14} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-foreground">
                        {component?.name}
                      </span>
                      <div className={`
                        flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-medium
                        ${getStatusColor(component?.status)}
                      `}>
                        <Icon name={getStatusIcon(component?.status)} size={10} />
                        <span className="capitalize">{component?.status}</span>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {component?.description}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="mt-4 pt-3 border-t border-border">
              <div className="flex items-center justify-between">
                <button className="text-xs text-accent hover:text-accent/80 transition-colors duration-200">
                  View Detailed Logs
                </button>
                <button className="text-xs text-accent hover:text-accent/80 transition-colors duration-200">
                  Refresh Status
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemHealthIndicator;