import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet';
import Header from '../../components/ui/Header';
import DoctrinalMetadataDisplay from '../../components/ui/DoctrinalMetadataDisplay';
import SystemHealthIndicator from '../../components/ui/SystemHealthIndicator';
import WorkflowProgressTracker from '../../components/ui/WorkflowProgressTracker';
import AdminSidebar from './components/AdminSidebar';
import UserManagementTab from './components/UserManagementTab';
import WorkflowConfigurationTab from './components/WorkflowConfigurationTab';
import SystemMonitoringTab from './components/SystemMonitoringTab';
import SecurityTab from './components/SecurityTab';
import IntegrationManagementTab from './components/IntegrationManagementTab';
import Icon from '../../components/AppIcon';
import Button from '../../components/ui/Button';

const SystemAdministrationPanel = () => {
  const [activeTab, setActiveTab] = useState('user-management');
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event?.ctrlKey) {
        switch (event?.key?.toLowerCase()) {
          case 'u':
            event?.preventDefault();
            setActiveTab('user-management');
            break;
          case 'w':
            event?.preventDefault();
            setActiveTab('workflow-configuration');
            break;
          case 'm':
            event?.preventDefault();
            setActiveTab('system-monitoring');
            break;
          case 's':
            event?.preventDefault();
            setActiveTab('security');
            break;
          case 'i':
            event?.preventDefault();
            setActiveTab('integration-management');
            break;
          default:
            break;
        }
      }
      
      if (event?.key === 'F3') {
        event?.preventDefault();
        // Global search functionality would be implemented here
        console.log('Global search activated');
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const getTabTitle = (tabId) => {
    const titles = {
      'user-management': 'User Management',
      'workflow-configuration': 'Workflow Configuration',
      'system-monitoring': 'System Monitoring',
      'security': 'Security Settings',
      'integration-management': 'Integration Management'
    };
    return titles?.[tabId] || 'Administration';
  };

  const getTabDescription = (tabId) => {
    const descriptions = {
      'user-management': 'Manage user accounts, roles, permissions, and access control across the platform',
      'workflow-configuration': 'Configure workflow steps, processing rules, and integration endpoints',
      'system-monitoring': 'Monitor system performance, health metrics, and real-time operational status',
      'security': 'Configure security policies, SSO settings, and review audit logs',
      'integration-management': 'Manage external integrations, API keys, and connection health'
    };
    return descriptions?.[tabId] || 'System administration and configuration';
  };

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'user-management':
        return <UserManagementTab />;
      case 'workflow-configuration':
        return <WorkflowConfigurationTab />;
      case 'system-monitoring':
        return <SystemMonitoringTab />;
      case 'security':
        return <SecurityTab />;
      case 'integration-management':
        return <IntegrationManagementTab />;
      default:
        return <UserManagementTab />;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Helmet>
        <title>System Administration Panel - Outreach Process Manager</title>
        <meta name="description" content="Comprehensive system administration panel for managing users, workflows, security, and integrations in the outreach process automation platform." />
      </Helmet>

      <Header />

      <div className="flex h-screen pt-16">
        {/* Desktop Sidebar */}
        <div className="hidden lg:block">
          <AdminSidebar 
            activeTab={activeTab} 
            onTabChange={setActiveTab}
          />
        </div>

        {/* Mobile Sidebar Overlay */}
        {isMobileSidebarOpen && (
          <div className="lg:hidden fixed inset-0 z-50 flex">
            <div 
              className="fixed inset-0 bg-black/50" 
              onClick={() => setIsMobileSidebarOpen(false)}
            />
            <div className="relative">
              <AdminSidebar 
                activeTab={activeTab} 
                onTabChange={(tab) => {
                  setActiveTab(tab);
                  setIsMobileSidebarOpen(false);
                }}
              />
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Bar with Metadata */}
          <div className="bg-card border-b border-border px-6 py-4">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div className="flex items-center space-x-4">
                {/* Mobile Menu Button */}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsMobileSidebarOpen(true)}
                  className="lg:hidden"
                >
                  <Icon name="Menu" size={20} />
                </Button>

                <div>
                  <h1 className="text-2xl font-bold text-foreground">{getTabTitle(activeTab)}</h1>
                  <p className="text-sm text-muted-foreground">{getTabDescription(activeTab)}</p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <DoctrinalMetadataDisplay
                  uniqueId="ADM-2025-001"
                  processId="SYS-ADMIN"
                  altitude="STRATEGIC"
                  className="hidden xl:flex"
                />
                <SystemHealthIndicator />
                <WorkflowProgressTracker
                  currentStep={8}
                  totalSteps={9}
                  workflowId="ADM-2025-001"
                  processId="SYS-ADMIN"
                  altitude="STRATEGIC"
                  className="hidden lg:flex"
                />
              </div>
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-6">
              {renderActiveTab()}
            </div>
          </div>

          {/* Footer */}
          <div className="bg-card border-t border-border px-6 py-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <div className="flex items-center space-x-2">
                  <Icon name="Shield" size={14} />
                  <span>Admin Session Active</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Icon name="Clock" size={14} />
                  <span>Session expires in 45 minutes</span>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" iconName="HelpCircle">
                  Help
                </Button>
                <Button variant="outline" size="sm" iconName="MessageSquare">
                  Support
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemAdministrationPanel;