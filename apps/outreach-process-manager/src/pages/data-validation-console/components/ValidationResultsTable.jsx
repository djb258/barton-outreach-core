import React, { useState, useMemo } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import { Checkbox } from '../../../components/ui/Checkbox';

const ValidationResultsTable = ({ data, onBulkAction, onRecordEdit, onRecordApprove }) => {
  const [selectedRecords, setSelectedRecords] = useState(new Set());
  const [sortConfig, setSortConfig] = useState({ key: 'validation_score', direction: 'desc' });
  const [editingRecord, setEditingRecord] = useState(null);

  const mockValidationData = [
    {
      id: 'WF-2025-001-001',
      company_name: 'TechCorp Solutions Inc.',
      email: 'contact@techcorp.com',
      phone: '+1-555-0123',
      domain: 'techcorp.com',
      industry: 'Technology',
      employee_count: 250,
      validation_score: 95,
      status: 'passed',
      issues: [],
      rules_applied: ['email-validation', 'phone-validation', 'duplicate-detection'],
      last_validated: '2025-09-19T15:35:00Z'
    },
    {
      id: 'WF-2025-001-002',
      company_name: 'Global Marketing Ltd',
      email: 'info@globalmarketing',
      phone: '555-0124',
      domain: 'globalmarketing.com',
      industry: 'Marketing',
      employee_count: 45,
      validation_score: 72,
      status: 'warning',
      issues: [
        { rule: 'email-validation', severity: 'critical', message: 'Invalid email format - missing TLD' },
        { rule: 'phone-validation', severity: 'warning', message: 'Phone number missing country code' }
      ],
      rules_applied: ['email-validation', 'phone-validation', 'company-size-validation'],
      last_validated: '2025-09-19T15:34:45Z'
    },
    {
      id: 'WF-2025-001-003',
      company_name: 'Innovate Systems',
      email: 'hello@innovatesys.com',
      phone: '+44-20-7946-0958',
      domain: 'innovatesys.com',
      industry: 'Software',
      employee_count: 120,
      validation_score: 88,
      status: 'passed',
      issues: [
        { rule: 'gdpr-compliance', severity: 'info', message: 'EU contact - consent verification required' }
      ],
      rules_applied: ['email-validation', 'phone-validation', 'gdpr-compliance'],
      last_validated: '2025-09-19T15:34:30Z'
    },
    {
      id: 'WF-2025-001-004',
      company_name: 'DataFlow Analytics',
      email: 'contact@dataflow.io',
      phone: '+1-555-0125',
      domain: 'dataflow.io',
      industry: 'Analytics',
      employee_count: 75,
      validation_score: 45,
      status: 'failed',
      issues: [
        { rule: 'duplicate-detection', severity: 'critical', message: 'Duplicate record found - merge required' },
        { rule: 'do-not-contact', severity: 'critical', message: 'Email found in suppression list' }
      ],
      rules_applied: ['email-validation', 'duplicate-detection', 'do-not-contact'],
      last_validated: '2025-09-19T15:34:15Z'
    },
    {
      id: 'WF-2025-001-005',
      company_name: 'CloudTech Ventures',
      email: 'team@cloudtech.co',
      phone: '+1-555-0126',
      domain: 'cloudtech.co',
      industry: 'Cloud Services',
      employee_count: 180,
      validation_score: 91,
      status: 'passed',
      issues: [],
      rules_applied: ['email-validation', 'phone-validation', 'company-size-validation'],
      last_validated: '2025-09-19T15:34:00Z'
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'passed': return 'text-success bg-success/10';
      case 'warning': return 'text-warning bg-warning/10';
      case 'failed': return 'text-error bg-error/10';
      default: return 'text-muted-foreground bg-muted';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'passed': return 'CheckCircle';
      case 'warning': return 'AlertTriangle';
      case 'failed': return 'XCircle';
      default: return 'Circle';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-error';
      case 'warning': return 'text-warning';
      case 'info': return 'text-accent';
      default: return 'text-muted-foreground';
    }
  };

  const sortedData = useMemo(() => {
    const dataToSort = data || mockValidationData;
    return [...dataToSort]?.sort((a, b) => {
      const aValue = a?.[sortConfig?.key];
      const bValue = b?.[sortConfig?.key];
      
      if (sortConfig?.direction === 'asc') {
        return aValue > bValue ? 1 : -1;
      }
      return aValue < bValue ? 1 : -1;
    });
  }, [data, sortConfig]);

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev?.key === key && prev?.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedRecords(new Set(sortedData.map(record => record.id)));
    } else {
      setSelectedRecords(new Set());
    }
  };

  const handleSelectRecord = (recordId, checked) => {
    const newSelected = new Set(selectedRecords);
    if (checked) {
      newSelected?.add(recordId);
    } else {
      newSelected?.delete(recordId);
    }
    setSelectedRecords(newSelected);
  };

  const handleBulkAction = (action) => {
    onBulkAction?.(action, Array.from(selectedRecords));
    setSelectedRecords(new Set());
  };

  const handleInlineEdit = (record, field, value) => {
    onRecordEdit?.(record?.id, { [field]: value });
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp)?.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="h-full flex flex-col bg-card">
      {/* Bulk Actions Bar */}
      {selectedRecords?.size > 0 && (
        <div className="p-3 bg-accent/5 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-sm font-medium text-foreground">
                {selectedRecords?.size} records selected
              </span>
              <div className="flex space-x-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  iconName="Check"
                  onClick={() => handleBulkAction('approve')}
                >
                  Approve
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  iconName="X"
                  onClick={() => handleBulkAction('reject')}
                >
                  Reject
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  iconName="RefreshCw"
                  onClick={() => handleBulkAction('revalidate')}
                >
                  Re-validate
                </Button>
              </div>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              iconName="X"
              onClick={() => setSelectedRecords(new Set())}
            />
          </div>
        </div>
      )}
      {/* Table Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-foreground">Validation Results</h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">
              {sortedData?.length} records
            </span>
            <Button variant="outline" size="sm" iconName="Download">
              Export
            </Button>
          </div>
        </div>
      </div>
      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-xs">
          <thead className="sticky top-0 bg-muted/50 border-b border-border">
            <tr>
              <th className="w-12 p-2 text-left">
                <Checkbox
                  checked={selectedRecords?.size === sortedData?.length && sortedData?.length > 0}
                  onChange={(e) => handleSelectAll(e?.target?.checked)}
                  size="sm"
                />
              </th>
              <th 
                className="p-2 text-left font-medium text-foreground cursor-pointer hover:bg-muted/70"
                onClick={() => handleSort('company_name')}
              >
                <div className="flex items-center space-x-1">
                  <span>Company</span>
                  <Icon name="ArrowUpDown" size={12} />
                </div>
              </th>
              <th className="p-2 text-left font-medium text-foreground">Contact</th>
              <th className="p-2 text-left font-medium text-foreground">Industry</th>
              <th 
                className="p-2 text-left font-medium text-foreground cursor-pointer hover:bg-muted/70"
                onClick={() => handleSort('validation_score')}
              >
                <div className="flex items-center space-x-1">
                  <span>Score</span>
                  <Icon name="ArrowUpDown" size={12} />
                </div>
              </th>
              <th 
                className="p-2 text-left font-medium text-foreground cursor-pointer hover:bg-muted/70"
                onClick={() => handleSort('status')}
              >
                <div className="flex items-center space-x-1">
                  <span>Status</span>
                  <Icon name="ArrowUpDown" size={12} />
                </div>
              </th>
              <th className="p-2 text-left font-medium text-foreground">Issues</th>
              <th className="p-2 text-left font-medium text-foreground">Last Validated</th>
              <th className="p-2 text-left font-medium text-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedData?.map((record) => (
              <tr 
                key={record?.id} 
                className="border-b border-border hover:bg-muted/30 transition-colors duration-200"
              >
                <td className="p-2">
                  <Checkbox
                    checked={selectedRecords?.has(record?.id)}
                    onChange={(e) => handleSelectRecord(record?.id, e?.target?.checked)}
                    size="sm"
                  />
                </td>
                <td className="p-2">
                  <div>
                    <div className="font-medium text-foreground">{record?.company_name}</div>
                    <div className="text-muted-foreground">{record?.domain}</div>
                    <div className="text-muted-foreground">{record?.employee_count} employees</div>
                  </div>
                </td>
                <td className="p-2">
                  <div>
                    <div className="text-foreground">{record?.email}</div>
                    <div className="text-muted-foreground">{record?.phone}</div>
                  </div>
                </td>
                <td className="p-2">
                  <span className="text-foreground">{record?.industry}</span>
                </td>
                <td className="p-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-12 h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-300 ${
                          record?.validation_score >= 80 ? 'bg-success' :
                          record?.validation_score >= 60 ? 'bg-warning' : 'bg-error'
                        }`}
                        style={{ width: `${record?.validation_score}%` }}
                      />
                    </div>
                    <span className="font-medium text-foreground">{record?.validation_score}%</span>
                  </div>
                </td>
                <td className="p-2">
                  <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded text-xs font-medium ${getStatusColor(record?.status)}`}>
                    <Icon name={getStatusIcon(record?.status)} size={10} />
                    <span className="capitalize">{record?.status}</span>
                  </div>
                </td>
                <td className="p-2">
                  {record?.issues?.length > 0 ? (
                    <div className="space-y-1">
                      {record?.issues?.slice(0, 2)?.map((issue, index) => (
                        <div key={index} className="flex items-start space-x-1">
                          <Icon 
                            name={issue?.severity === 'critical' ? 'AlertCircle' : 'AlertTriangle'} 
                            size={10} 
                            className={getSeverityColor(issue?.severity)}
                          />
                          <span className="text-muted-foreground leading-tight">
                            {issue?.message?.substring(0, 40)}...
                          </span>
                        </div>
                      ))}
                      {record?.issues?.length > 2 && (
                        <div className="text-muted-foreground">
                          +{record?.issues?.length - 2} more
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-success">No issues</span>
                  )}
                </td>
                <td className="p-2">
                  <span className="text-muted-foreground font-data">
                    {formatTimestamp(record?.last_validated)}
                  </span>
                </td>
                <td className="p-2">
                  <div className="flex space-x-1">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      iconName="Edit"
                      onClick={() => setEditingRecord(record)}
                    />
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      iconName="Check"
                      onClick={() => onRecordApprove?.(record?.id)}
                    />
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      iconName="RefreshCw"
                      onClick={() => handleBulkAction('revalidate')}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* Pagination */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Showing 1-{sortedData?.length} of {sortedData?.length} records
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm" disabled>
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled>
              Next
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ValidationResultsTable;