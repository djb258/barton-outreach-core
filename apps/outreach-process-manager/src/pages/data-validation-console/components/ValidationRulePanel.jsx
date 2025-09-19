import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';
import Select from '../../../components/ui/Select';
import { Checkbox } from '../../../components/ui/Checkbox';

const ValidationRulePanel = ({ onRuleChange, onTestRule }) => {
  const [expandedCategories, setExpandedCategories] = useState(['data-quality']);
  const [selectedRule, setSelectedRule] = useState(null);
  const [customLogic, setCustomLogic] = useState('');

  const ruleCategories = [
    {
      id: 'data-quality',
      name: 'Data Quality Rules',
      icon: 'Shield',
      rules: [
        {
          id: 'email-validation',
          name: 'Email Format Validation',
          description: 'Validates email addresses using RFC 5322 standards',
          severity: 'critical',
          enabled: true,
          conditions: 'email MATCHES regex pattern',
          action: 'flag_invalid'
        },
        {
          id: 'phone-validation',
          name: 'Phone Number Validation',
          description: 'Validates phone numbers for US/International formats',
          severity: 'warning',
          enabled: true,
          conditions: 'phone MATCHES E.164 format',
          action: 'normalize_format'
        },
        {
          id: 'duplicate-detection',
          name: 'Duplicate Record Detection',
          description: 'Identifies duplicate companies based on domain/name',
          severity: 'critical',
          enabled: true,
          conditions: 'domain OR company_name DUPLICATE',
          action: 'merge_records'
        }
      ]
    },
    {
      id: 'business-rules',
      name: 'Business Logic Rules',
      icon: 'Briefcase',
      rules: [
        {
          id: 'company-size-validation',
          name: 'Company Size Validation',
          description: 'Validates employee count ranges and revenue data',
          severity: 'warning',
          enabled: true,
          conditions: 'employee_count > 0 AND revenue > 0',
          action: 'flag_review'
        },
        {
          id: 'industry-classification',
          name: 'Industry Classification',
          description: 'Validates and standardizes industry codes',
          severity: 'info',
          enabled: false,
          conditions: 'industry IN predefined_list',
          action: 'auto_classify'
        }
      ]
    },
    {
      id: 'compliance',
      name: 'Compliance Rules',
      icon: 'FileCheck',
      rules: [
        {
          id: 'gdpr-compliance',
          name: 'GDPR Compliance Check',
          description: 'Ensures data collection compliance for EU contacts',
          severity: 'critical',
          enabled: true,
          conditions: 'country IN eu_countries AND consent = true',
          action: 'require_consent'
        },
        {
          id: 'do-not-contact',
          name: 'Do Not Contact List',
          description: 'Checks against internal suppression lists',
          severity: 'critical',
          enabled: true,
          conditions: 'email NOT IN suppression_list',
          action: 'exclude_record'
        }
      ]
    }
  ];

  const severityOptions = [
    { value: 'critical', label: 'Critical' },
    { value: 'warning', label: 'Warning' },
    { value: 'info', label: 'Info' }
  ];

  const actionOptions = [
    { value: 'flag_invalid', label: 'Flag as Invalid' },
    { value: 'flag_review', label: 'Flag for Review' },
    { value: 'auto_correct', label: 'Auto Correct' },
    { value: 'exclude_record', label: 'Exclude Record' },
    { value: 'require_consent', label: 'Require Consent' }
  ];

  const toggleCategory = (categoryId) => {
    setExpandedCategories(prev => 
      prev?.includes(categoryId) 
        ? prev?.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const selectRule = (rule) => {
    setSelectedRule(rule);
    setCustomLogic(rule?.conditions);
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-error bg-error/10';
      case 'warning': return 'text-warning bg-warning/10';
      case 'info': return 'text-accent bg-accent/10';
      default: return 'text-muted-foreground bg-muted';
    }
  };

  const handleRuleUpdate = (ruleId, updates) => {
    onRuleChange?.(ruleId, updates);
  };

  const handleTestRule = () => {
    if (selectedRule) {
      onTestRule?.(selectedRule?.id, customLogic);
    }
  };

  return (
    <div className="h-full flex flex-col bg-card border-r border-border">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-foreground">Validation Rules</h2>
          <Button variant="outline" size="sm" iconName="Plus" iconPosition="left">
            New Rule
          </Button>
        </div>
        <div className="text-sm text-muted-foreground">
          Configure and manage data validation rules
        </div>
      </div>
      {/* Rule Categories */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-3">
          {ruleCategories?.map((category) => (
            <div key={category?.id} className="border border-border rounded-lg">
              <button
                onClick={() => toggleCategory(category?.id)}
                className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors duration-200"
              >
                <div className="flex items-center space-x-3">
                  <Icon name={category?.icon} size={16} color="var(--color-muted-foreground)" />
                  <span className="text-sm font-medium text-foreground">{category?.name}</span>
                  <span className="text-xs text-muted-foreground">
                    ({category?.rules?.length} rules)
                  </span>
                </div>
                <Icon 
                  name={expandedCategories?.includes(category?.id) ? "ChevronDown" : "ChevronRight"} 
                  size={16} 
                  color="var(--color-muted-foreground)" 
                />
              </button>

              {expandedCategories?.includes(category?.id) && (
                <div className="border-t border-border">
                  {category?.rules?.map((rule) => (
                    <div
                      key={rule?.id}
                      className={`
                        p-3 border-b border-border last:border-b-0 cursor-pointer
                        transition-colors duration-200 hover:bg-muted/30
                        ${selectedRule?.id === rule?.id ? 'bg-accent/5 border-l-2 border-l-accent' : ''}
                      `}
                      onClick={() => selectRule(rule)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-sm font-medium text-foreground">{rule?.name}</span>
                            <div className={`px-2 py-0.5 rounded text-xs font-medium ${getSeverityColor(rule?.severity)}`}>
                              {rule?.severity}
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground leading-relaxed">
                            {rule?.description}
                          </p>
                        </div>
                        <Checkbox
                          checked={rule?.enabled}
                          onChange={(e) => handleRuleUpdate(rule?.id, { enabled: e?.target?.checked })}
                          size="sm"
                          className="ml-2"
                        />
                      </div>
                      <div className="text-xs font-data text-muted-foreground bg-muted/50 p-2 rounded">
                        {rule?.conditions}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      {/* Rule Editor */}
      {selectedRule && (
        <div className="border-t border-border p-4 bg-muted/20">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">Edit Rule</h3>
              <Button variant="ghost" size="sm" iconName="X" onClick={() => setSelectedRule(null)} />
            </div>

            <Input
              label="Rule Name"
              value={selectedRule?.name}
              onChange={(e) => setSelectedRule(prev => ({ ...prev, name: e?.target?.value }))}
              className="text-xs"
            />

            <Select
              label="Severity"
              options={severityOptions}
              value={selectedRule?.severity}
              onChange={(value) => setSelectedRule(prev => ({ ...prev, severity: value }))}
              className="text-xs"
            />

            <div>
              <label className="text-xs font-medium text-foreground mb-2 block">
                Custom Logic
              </label>
              <textarea
                value={customLogic}
                onChange={(e) => setCustomLogic(e?.target?.value)}
                className="w-full h-20 px-3 py-2 text-xs font-data bg-input border border-border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Enter validation logic..."
              />
            </div>

            <Select
              label="Action"
              options={actionOptions}
              value={selectedRule?.action}
              onChange={(value) => setSelectedRule(prev => ({ ...prev, action: value }))}
              className="text-xs"
            />

            <div className="flex space-x-2">
              <Button variant="outline" size="sm" onClick={handleTestRule} iconName="Play">
                Test Rule
              </Button>
              <Button variant="default" size="sm" iconName="Save">
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ValidationRulePanel;