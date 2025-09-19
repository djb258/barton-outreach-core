import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const SystemMonitoringTab = () => {
  const [timeRange, setTimeRange] = useState('1h');
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Mock real-time data
  const [systemMetrics, setSystemMetrics] = useState({
    cpu: 45.2,
    memory: 67.8,
    disk: 34.5,
    network: 12.3
  });

  // Generate mock time series data
  const generateTimeSeriesData = () => {
    const now = new Date();
    const data = [];
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 5 * 60 * 1000);
      data?.push({
        time: time?.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        cpu: Math.random() * 30 + 30,
        memory: Math.random() * 20 + 60,
        network: Math.random() * 15 + 5,
        apiResponse: Math.random() * 100 + 50
      });
    }
    return data;
  };

  const [performanceData] = useState(generateTimeSeriesData());

  const errorData = [
    { name: 'API Errors', value: 12, color: '#DC2626' },
    { name: 'Database Errors', value: 3, color: '#D97706' },
    { name: 'Network Errors', value: 7, color: '#059669' },
    { name: 'Validation Errors', value: 25, color: '#3B82F6' }
  ];

  const connectionPools = [
    {
      name: 'Primary Database',
      active: 45,
      idle: 15,
      max: 100,
      status: 'healthy'
    },
    {
      name: 'Redis Cache',
      active: 23,
      idle: 27,
      max: 50,
      status: 'healthy'
    },
    {
      name: 'Composio MCP',
      active: 8,
      idle: 12,
      max: 20,
      status: 'warning'
    }
  ];

  const apiEndpoints = [
    {
      endpoint: '/api/v1/data-intake',
      requests: 1247,
      avgResponse: 145,
      errorRate: 0.8,
      status: 'healthy'
    },
    {
      endpoint: '/api/v1/validation',
      requests: 892,
      avgResponse: 89,
      errorRate: 1.2,
      status: 'healthy'
    },
    {
      endpoint: '/api/v1/composio/sync',
      requests: 234,
      avgResponse: 567,
      errorRate: 3.4,
      status: 'warning'
    },
    {
      endpoint: '/api/v1/export',
      requests: 156,
      avgResponse: 2340,
      errorRate: 0.5,
      status: 'healthy'
    }
  ];

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemMetrics(prev => ({
        cpu: Math.max(0, Math.min(100, prev?.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.max(0, Math.min(100, prev?.memory + (Math.random() - 0.5) * 5)),
        disk: Math.max(0, Math.min(100, prev?.disk + (Math.random() - 0.5) * 2)),
        network: Math.max(0, Math.min(100, prev?.network + (Math.random() - 0.5) * 8))
      }));
      setLastUpdate(new Date());
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getMetricColor = (value, type) => {
    if (type === 'cpu' || type === 'memory') {
      if (value > 80) return 'text-error';
      if (value > 60) return 'text-warning';
      return 'text-success';
    }
    return 'text-accent';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-success bg-success/10';
      case 'warning': return 'text-warning bg-warning/10';
      case 'error': return 'text-error bg-error/10';
      default: return 'text-muted-foreground bg-muted';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Icon name="Activity" size={16} color="var(--color-accent)" />
            <span className="text-sm font-medium text-foreground">System Monitoring</span>
          </div>
          <div className="text-xs text-muted-foreground">
            Last updated: {lastUpdate?.toLocaleTimeString()}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e?.target?.value)}
            className="px-3 py-1.5 text-sm border border-border rounded-md bg-background"
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
          <Button variant="outline" size="sm" iconName="RefreshCw">
            Refresh
          </Button>
        </div>
      </div>
      {/* System Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Icon name="Cpu" size={16} color="var(--color-accent)" />
              <span className="text-sm font-medium text-foreground">CPU Usage</span>
            </div>
            <span className={`text-lg font-bold ${getMetricColor(systemMetrics?.cpu, 'cpu')}`}>
              {systemMetrics?.cpu?.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                systemMetrics?.cpu > 80 ? 'bg-error' : 
                systemMetrics?.cpu > 60 ? 'bg-warning' : 'bg-success'
              }`}
              style={{ width: `${systemMetrics?.cpu}%` }}
            />
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Icon name="HardDrive" size={16} color="var(--color-accent)" />
              <span className="text-sm font-medium text-foreground">Memory</span>
            </div>
            <span className={`text-lg font-bold ${getMetricColor(systemMetrics?.memory, 'memory')}`}>
              {systemMetrics?.memory?.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                systemMetrics?.memory > 80 ? 'bg-error' : 
                systemMetrics?.memory > 60 ? 'bg-warning' : 'bg-success'
              }`}
              style={{ width: `${systemMetrics?.memory}%` }}
            />
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Icon name="Database" size={16} color="var(--color-accent)" />
              <span className="text-sm font-medium text-foreground">Disk Usage</span>
            </div>
            <span className="text-lg font-bold text-success">
              {systemMetrics?.disk?.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div 
              className="h-2 rounded-full bg-success transition-all duration-300"
              style={{ width: `${systemMetrics?.disk}%` }}
            />
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Icon name="Wifi" size={16} color="var(--color-accent)" />
              <span className="text-sm font-medium text-foreground">Network I/O</span>
            </div>
            <span className="text-lg font-bold text-accent">
              {systemMetrics?.network?.toFixed(1)} MB/s
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            ↑ 8.4 MB/s ↓ 3.9 MB/s
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Performance Chart */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">Performance Trends</h3>
            <div className="flex items-center space-x-4 text-xs">
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-accent rounded-full" />
                <span className="text-muted-foreground">CPU</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-success rounded-full" />
                <span className="text-muted-foreground">Memory</span>
              </div>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis 
                  dataKey="time" 
                  stroke="var(--color-muted-foreground)"
                  fontSize={12}
                />
                <YAxis 
                  stroke="var(--color-muted-foreground)"
                  fontSize={12}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'var(--color-card)',
                    border: '1px solid var(--color-border)',
                    borderRadius: '8px'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="cpu" 
                  stackId="1"
                  stroke="var(--color-accent)" 
                  fill="var(--color-accent)"
                  fillOpacity={0.3}
                />
                <Area 
                  type="monotone" 
                  dataKey="memory" 
                  stackId="2"
                  stroke="var(--color-success)" 
                  fill="var(--color-success)"
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* API Response Times */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">API Response Times</h3>
            <Button variant="outline" size="sm" iconName="ExternalLink">
              View Details
            </Button>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis 
                  dataKey="time" 
                  stroke="var(--color-muted-foreground)"
                  fontSize={12}
                />
                <YAxis 
                  stroke="var(--color-muted-foreground)"
                  fontSize={12}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'var(--color-card)',
                    border: '1px solid var(--color-border)',
                    borderRadius: '8px'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="apiResponse" 
                  stroke="var(--color-accent)" 
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Connection Pools */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">Database Connection Pools</h3>
          <div className="space-y-4">
            {connectionPools?.map((pool) => (
              <div key={pool?.name} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">{pool?.name}</span>
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(pool?.status)}`}>
                    {pool?.status}
                  </div>
                </div>
                <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                  <span>Active: {pool?.active}</span>
                  <span>•</span>
                  <span>Idle: {pool?.idle}</span>
                  <span>•</span>
                  <span>Max: {pool?.max}</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="flex h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-accent"
                      style={{ width: `${(pool?.active / pool?.max) * 100}%` }}
                    />
                    <div 
                      className="bg-success"
                      style={{ width: `${(pool?.idle / pool?.max) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* API Endpoints Status */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">API Endpoints</h3>
          <div className="space-y-3">
            {apiEndpoints?.map((api) => (
              <div key={api?.endpoint} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-data text-foreground">{api?.endpoint}</span>
                    <div className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(api?.status)}`}>
                      {api?.status}
                    </div>
                  </div>
                  <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                    <span>{api?.requests} req/h</span>
                    <span>{api?.avgResponse}ms avg</span>
                    <span className={api?.errorRate > 2 ? 'text-error' : 'text-success'}>
                      {api?.errorRate}% errors
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemMonitoringTab;