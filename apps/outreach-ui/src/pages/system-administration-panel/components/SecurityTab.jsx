import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';
import Select from '../../../components/ui/Select';
import { Checkbox } from '../../../components/ui/Checkbox';

const SecurityTab = () => {
  const [ssoEnabled, setSsoEnabled] = useState(true);
  const [mfaRequired, setMfaRequired] = useState(true);
  const [sessionTimeout, setSessionTimeout] = useState('30');
  const [passwordPolicy, setPasswordPolicy] = useState('strong');

  const ssoProviders = [
    { value: 'azure-ad', label: 'Azure Active Directory' },
    { value: 'google-workspace', label: 'Google Workspace' },
    { value: 'okta', label: 'Okta' },
    { value: 'auth0', label: 'Auth0' }
  ];

  const passwordPolicyOptions = [
    { value: 'basic', label: 'Basic (8+ characters)' },
    { value: 'strong', label: 'Strong (12+ chars, mixed case, numbers, symbols)' },
    { value: 'enterprise', label: 'Enterprise (16+ chars, all requirements)' }
  ];

  const securityEvents = [
    {
      id: 1,
      type: 'login_failure',
      user: 'john.doe@company.com',
      timestamp: '2025-09-19T15:25:00Z',
      ip: '192.168.1.100',
      severity: 'medium',
      description: 'Multiple failed login attempts'
    },
    {
      id: 2,
      type: 'permission_change',
      user: 'admin@company.com',
      timestamp: '2025-09-19T14:30:00Z',
      ip: '10.0.0.50',
      severity: 'high',
      description: 'Admin permissions granted to user'
    },
    {
      id: 3,
      type: 'data_export',
      user: 'sarah.johnson@company.com',
      timestamp: '2025-09-19T13:45:00Z',
      ip: '192.168.1.75',
      severity: 'low',
      description: 'Large dataset exported'
    },
    {
      id: 4,
      type: 'api_key_created',
      user: 'system@company.com',
      timestamp: '2025-09-19T12:15:00Z',
      ip: '127.0.0.1',
      severity: 'medium',
      description: 'New API key generated for integration'
    }
  ];

  const rolePermissions = [
    {
      role: 'Administrator',
      permissions: {
        'User Management': true,
        'System Configuration': true,
        'Data Access': true,
        'API Management': true,
        'Security Settings': true,
        'Audit Logs': true,
        'Workflow Management': true,
        'Integration Management': true
      }
    },
    {
      role: 'Manager',
      permissions: {
        'User Management': false,
        'System Configuration': false,
        'Data Access': true,
        'API Management': false,
        'Security Settings': false,
        'Audit Logs': true,
        'Workflow Management': true,
        'Integration Management': false
      }
    },
    {
      role: 'Analyst',
      permissions: {
        'User Management': false,
        'System Configuration': false,
        'Data Access': true,
        'API Management': false,
        'Security Settings': false,
        'Audit Logs': false,
        'Workflow Management': false,
        'Integration Management': false
      }
    }
  ];

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'text-error bg-error/10';
      case 'medium': return 'text-warning bg-warning/10';
      case 'low': return 'text-success bg-success/10';
      default: return 'text-muted-foreground bg-muted';
    }
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'login_failure': return 'AlertTriangle';
      case 'permission_change': return 'Shield';
      case 'data_export': return 'Download';
      case 'api_key_created': return 'Key';
      default: return 'Activity';
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp)?.toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* Security Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-success/10 text-success rounded-lg">
              <Icon name="Shield" size={20} />
            </div>
            <div>
              <div className="text-2xl font-bold text-foreground">98.5%</div>
              <div className="text-sm text-muted-foreground">Security Score</div>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-accent/10 text-accent rounded-lg">
              <Icon name="Users" size={20} />
            </div>
            <div>
              <div className="text-2xl font-bold text-foreground">247</div>
              <div className="text-sm text-muted-foreground">Active Sessions</div>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-warning/10 text-warning rounded-lg">
              <Icon name="AlertTriangle" size={20} />
            </div>
            <div>
              <div className="text-2xl font-bold text-foreground">12</div>
              <div className="text-sm text-muted-foreground">Security Alerts</div>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-error/10 text-error rounded-lg">
              <Icon name="XCircle" size={20} />
            </div>
            <div>
              <div className="text-2xl font-bold text-foreground">3</div>
              <div className="text-sm text-muted-foreground">Failed Logins</div>
            </div>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* SSO Configuration */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">SSO Configuration</h3>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${ssoEnabled ? 'bg-success' : 'bg-muted-foreground'}`} />
              <span className="text-sm text-muted-foreground">
                {ssoEnabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-foreground">Enable SSO</div>
                <div className="text-sm text-muted-foreground">Allow single sign-on authentication</div>
              </div>
              <Checkbox
                checked={ssoEnabled}
                onChange={(e) => setSsoEnabled(e?.target?.checked)}
              />
            </div>

            <Select
              label="SSO Provider"
              options={ssoProviders}
              value="azure-ad"
              disabled={!ssoEnabled}
              className="w-full"
            />

            <Input
              label="SSO Domain"
              type="text"
              value="company.com"
              disabled={!ssoEnabled}
              className="w-full"
            />

            <div className="flex items-center space-x-2 pt-2">
              <Button variant="outline" size="sm" iconName="TestTube">
                Test Connection
              </Button>
              <Button variant="default" size="sm" iconName="Save">
                Save Configuration
              </Button>
            </div>
          </div>
        </div>

        {/* Session Management */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">Session Management</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-foreground">Require MFA</div>
                <div className="text-sm text-muted-foreground">Multi-factor authentication required</div>
              </div>
              <Checkbox
                checked={mfaRequired}
                onChange={(e) => setMfaRequired(e?.target?.checked)}
              />
            </div>

            <Input
              label="Session Timeout (minutes)"
              type="number"
              value={sessionTimeout}
              onChange={(e) => setSessionTimeout(e?.target?.value)}
              className="w-full"
            />

            <Select
              label="Password Policy"
              options={passwordPolicyOptions}
              value={passwordPolicy}
              onChange={setPasswordPolicy}
              className="w-full"
            />

            <div className="bg-muted/30 p-3 rounded-lg">
              <div className="text-sm font-medium text-foreground mb-2">Current Policy Requirements:</div>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>• Minimum 12 characters</li>
                <li>• Mixed case letters</li>
                <li>• Numbers and symbols</li>
                <li>• No common passwords</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      {/* Role-Based Permissions */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">Role-Based Permissions</h3>
          <Button variant="outline" iconName="Plus" iconPosition="left">
            Add Role
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="text-left p-3 font-medium text-foreground">Permission</th>
                {rolePermissions?.map((role) => (
                  <th key={role?.role} className="text-center p-3 font-medium text-foreground min-w-32">
                    {role?.role}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.keys(rolePermissions?.[0]?.permissions)?.map((permission) => (
                <tr key={permission} className="border-b border-border hover:bg-muted/30">
                  <td className="p-3 font-medium text-foreground">{permission}</td>
                  {rolePermissions?.map((role) => (
                    <td key={role?.role} className="p-3 text-center">
                      <div className="flex justify-center">
                        <Checkbox
                          checked={role?.permissions?.[permission]}
                          onChange={() => {}}
                        />
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {/* Security Events */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">Recent Security Events</h3>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" iconName="Filter">
              Filter
            </Button>
            <Button variant="outline" size="sm" iconName="Download">
              Export
            </Button>
          </div>
        </div>

        <div className="space-y-3">
          {securityEvents?.map((event) => (
            <div key={event?.id} className="flex items-center space-x-4 p-3 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors">
              <div className={`
                flex items-center justify-center w-10 h-10 rounded-lg
                ${getSeverityColor(event?.severity)}
              `}>
                <Icon name={getEventIcon(event?.type)} size={16} />
              </div>
              
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-foreground">{event?.description}</span>
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(event?.severity)}`}>
                    {event?.severity}
                  </div>
                </div>
                <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                  <span>User: {event?.user}</span>
                  <span>IP: {event?.ip}</span>
                  <span>{formatTimestamp(event?.timestamp)}</span>
                </div>
              </div>
              
              <Button variant="ghost" size="icon" iconName="ExternalLink" />
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
          <span className="text-sm text-muted-foreground">
            Showing 4 of 47 security events
          </span>
          <Button variant="outline" size="sm">
            View All Events
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SecurityTab;