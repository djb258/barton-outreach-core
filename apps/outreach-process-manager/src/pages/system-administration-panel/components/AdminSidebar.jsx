import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const AdminSidebar = ({ activeTab, onTabChange }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const adminSections = [
    {
      id: 'user-management',
      label: 'User Management',
      icon: 'Users',
      shortcut: 'Ctrl+U',
      description: 'Manage users, roles, and permissions'
    },
    {
      id: 'workflow-configuration',
      label: 'Workflow Config',
      icon: 'Workflow',
      shortcut: 'Ctrl+W',
      description: 'Configure workflow steps and rules'
    },
    {
      id: 'system-monitoring',
      label: 'System Monitoring',
      icon: 'Activity',
      shortcut: 'Ctrl+M',
      description: 'Monitor system performance and health'
    },
    {
      id: 'security',
      label: 'Security',
      icon: 'Shield',
      shortcut: 'Ctrl+S',
      description: 'Security settings and audit logs'
    },
    {
      id: 'integration-management',
      label: 'Integrations',
      icon: 'Plug',
      shortcut: 'Ctrl+I',
      description: 'Manage external integrations and APIs'
    }
  ];

  const emergencyActions = [
    {
      id: 'emergency-stop',
      label: 'Emergency Stop',
      icon: 'AlertTriangle',
      color: 'text-error',
      description: 'Stop all processing immediately'
    },
    {
      id: 'backup-now',
      label: 'Backup Now',
      icon: 'Download',
      color: 'text-warning',
      description: 'Create immediate system backup'
    },
    {
      id: 'system-restart',
      label: 'System Restart',
      icon: 'RotateCcw',
      color: 'text-accent',
      description: 'Restart system services'
    }
  ];

  const systemStats = [
    { label: 'Active Users', value: '247', icon: 'Users' },
    { label: 'System Load', value: '45%', icon: 'Cpu' },
    { label: 'Disk Usage', value: '67%', icon: 'HardDrive' },
    { label: 'Uptime', value: '99.8%', icon: 'Clock' }
  ];

  return (
    <div className={`bg-card border-r border-border transition-all duration-300 ${isCollapsed ? 'w-16' : 'w-80'} flex flex-col h-full`}>
      {/* Sidebar Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div>
              <h2 className="text-lg font-semibold text-foreground">Admin Panel</h2>
              <p className="text-sm text-muted-foreground">System Administration</p>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="ml-auto"
          >
            <Icon name={isCollapsed ? "ChevronRight" : "ChevronLeft"} size={16} />
          </Button>
        </div>
      </div>
      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-2">
          {!isCollapsed && (
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
              Administration
            </div>
          )}
          
          {adminSections?.map((section) => (
            <button
              key={section?.id}
              onClick={() => onTabChange(section?.id)}
              className={`
                w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-left
                transition-all duration-200 ease-micro
                ${activeTab === section?.id
                  ? 'bg-accent text-accent-foreground shadow-elevation-1'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                }
              `}
              title={isCollapsed ? section?.label : section?.description}
            >
              <Icon name={section?.icon} size={18} />
              {!isCollapsed && (
                <div className="flex-1">
                  <div className="font-medium">{section?.label}</div>
                  <div className="text-xs opacity-80">{section?.shortcut}</div>
                </div>
              )}
            </button>
          ))}
        </div>

        {/* Emergency Actions */}
        {!isCollapsed && (
          <div className="p-4 border-t border-border">
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
              Emergency Actions
            </div>
            <div className="space-y-2">
              {emergencyActions?.map((action) => (
                <button
                  key={action?.id}
                  className={`
                    w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left
                    transition-all duration-200 ease-micro
                    hover:bg-muted/50 ${action?.color}
                  `}
                  title={action?.description}
                >
                  <Icon name={action?.icon} size={16} />
                  <span className="text-sm font-medium">{action?.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* System Stats */}
        {!isCollapsed && (
          <div className="p-4 border-t border-border">
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
              System Status
            </div>
            <div className="space-y-3">
              {systemStats?.map((stat) => (
                <div key={stat?.label} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Icon name={stat?.icon} size={14} color="var(--color-muted-foreground)" />
                    <span className="text-sm text-muted-foreground">{stat?.label}</span>
                  </div>
                  <span className="text-sm font-medium text-foreground">{stat?.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      {/* Footer */}
      <div className="p-4 border-t border-border">
        {!isCollapsed ? (
          <div className="text-center">
            <div className="text-xs text-muted-foreground mb-2">
              Press F3 for global search
            </div>
            <Button variant="outline" size="sm" fullWidth iconName="Search">
              Global Search
            </Button>
          </div>
        ) : (
          <Button variant="outline" size="icon" iconName="Search" />
        )}
      </div>
    </div>
  );
};

export default AdminSidebar;