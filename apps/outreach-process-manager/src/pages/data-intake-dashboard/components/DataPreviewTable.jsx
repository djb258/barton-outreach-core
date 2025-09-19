import React, { useState, useMemo } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Select from '../../../components/ui/Select';

const DataPreviewTable = ({ fileData, onColumnMapping, columnMapping, validationErrors }) => {
  const [showMappingMode, setShowMappingMode] = useState(false);

  const requiredFields = [
    { value: 'company_name', label: 'Company Name', required: true },
    { value: 'email', label: 'Email Address', required: true },
    { value: 'phone', label: 'Phone Number', required: false },
    { value: 'website', label: 'Website', required: false },
    { value: 'industry', label: 'Industry', required: false },
    { value: 'location', label: 'Location', required: false }
  ];

  const detectDataType = (value) => {
    if (!value || value === '') return 'empty';
    if (/^[\w\.-]+@[\w\.-]+\.\w+$/?.test(value)) return 'email';
    if (/^[\+]?[\d\s\-\(\)]+$/?.test(value)) return 'phone';
    if (/^https?:\/\//?.test(value)) return 'url';
    if (/^\d+$/?.test(value)) return 'number';
    if (/^\d{4}-\d{2}-\d{2}/?.test(value)) return 'date';
    return 'text';
  };

  const getDataTypeIcon = (type) => {
    switch (type) {
      case 'email': return 'Mail';
      case 'phone': return 'Phone';
      case 'url': return 'Globe';
      case 'number': return 'Hash';
      case 'date': return 'Calendar';
      case 'empty': return 'Minus';
      default: return 'Type';
    }
  };

  const getDataTypeColor = (type) => {
    switch (type) {
      case 'email': return 'text-blue-600';
      case 'phone': return 'text-green-600';
      case 'url': return 'text-purple-600';
      case 'number': return 'text-orange-600';
      case 'date': return 'text-pink-600';
      case 'empty': return 'text-gray-400';
      default: return 'text-gray-600';
    }
  };

  const previewData = useMemo(() => {
    if (!fileData || !fileData?.length) return { headers: [], rows: [] };
    
    const headers = Object.keys(fileData?.[0]);
    const rows = fileData?.slice(0, 10);
    
    return { headers, rows };
  }, [fileData]);

  const getValidationStatus = (columnIndex, rowIndex, value) => {
    const columnName = previewData?.headers?.[columnIndex];
    const mappedField = columnMapping?.[columnName];
    
    if (!mappedField) return null;
    
    const field = requiredFields?.find(f => f?.value === mappedField);
    if (!field) return null;
    
    if (field?.required && (!value || value?.trim() === '')) {
      return { type: 'error', message: 'Required field is empty' };
    }
    
    if (mappedField === 'email' && value && !/^[\w\.-]+@[\w\.-]+\.\w+$/?.test(value)) {
      return { type: 'error', message: 'Invalid email format' };
    }
    
    if (mappedField === 'phone' && value && !/^[\+]?[\d\s\-\(\)]+$/?.test(value)) {
      return { type: 'warning', message: 'Phone format may be invalid' };
    }
    
    return { type: 'success', message: 'Valid data' };
  };

  const handleColumnMappingChange = (columnName, mappedField) => {
    onColumnMapping({
      ...columnMapping,
      [columnName]: mappedField
    });
  };

  const getMappingOptions = (columnName) => {
    const usedFields = Object.values(columnMapping)?.filter(field => field && field !== columnMapping?.[columnName]);
    
    return [
      { value: '', label: 'No mapping' },
      ...requiredFields?.map(field => ({
        ...field,
        disabled: usedFields?.includes(field?.value)
      }))
    ];
  };

  if (!fileData || !fileData?.length) {
    return (
      <div className="w-full bg-card border border-border rounded-lg p-8 text-center">
        <Icon name="Table" size={48} color="var(--color-muted-foreground)" />
        <h3 className="text-lg font-semibold text-foreground mt-4 mb-2">No Data Preview</h3>
        <p className="text-sm text-muted-foreground">
          Upload a CSV file to see data preview and column mapping options
        </p>
      </div>
    );
  }

  return (
    <div className="w-full bg-card border border-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-muted/30">
        <div className="flex items-center space-x-3">
          <Icon name="Table" size={20} color="var(--color-foreground)" />
          <div>
            <h3 className="text-sm font-semibold text-foreground">Data Preview</h3>
            <p className="text-xs text-muted-foreground">
              Showing first 10 rows • {fileData?.length} total records
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant={showMappingMode ? "default" : "outline"}
            size="sm"
            iconName="Settings"
            iconPosition="left"
            onClick={() => setShowMappingMode(!showMappingMode)}
          >
            {showMappingMode ? 'Hide Mapping' : 'Column Mapping'}
          </Button>
        </div>
      </div>
      {/* Column Mapping Interface */}
      {showMappingMode && (
        <div className="p-4 bg-accent/5 border-b border-border">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {previewData?.headers?.map((header, index) => (
              <div key={index} className="space-y-2">
                <label className="text-xs font-medium text-foreground">
                  {header}
                  <span className="text-muted-foreground ml-1">
                    ({detectDataType(previewData?.rows?.[0]?.[header])})
                  </span>
                </label>
                <Select
                  options={getMappingOptions(header)}
                  value={columnMapping?.[header] || ''}
                  onChange={(value) => handleColumnMappingChange(header, value)}
                  placeholder="Select mapping"
                />
              </div>
            ))}
          </div>
        </div>
      )}
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="w-12 px-3 py-2 text-left text-xs font-medium text-muted-foreground">
                #
              </th>
              {previewData?.headers?.map((header, index) => {
                const sampleValue = previewData?.rows?.[0]?.[header];
                const dataType = detectDataType(sampleValue);
                const mappedField = columnMapping?.[header];
                const isRequired = mappedField && requiredFields?.find(f => f?.value === mappedField)?.required;
                
                return (
                  <th key={index} className="px-3 py-2 text-left">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-medium text-foreground truncate max-w-32">
                        {header}
                      </span>
                      <div className="flex items-center space-x-1">
                        <Icon 
                          name={getDataTypeIcon(dataType)} 
                          size={12} 
                          className={getDataTypeColor(dataType)}
                        />
                        {isRequired && (
                          <Icon name="Asterisk" size={8} className="text-error" />
                        )}
                        {mappedField && (
                          <div className="w-2 h-2 bg-success rounded-full" title="Mapped field" />
                        )}
                      </div>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {previewData?.rows?.map((row, rowIndex) => (
              <tr key={rowIndex} className="border-t border-border hover:bg-muted/20">
                <td className="px-3 py-2 text-xs text-muted-foreground font-data">
                  {rowIndex + 1}
                </td>
                {previewData?.headers?.map((header, colIndex) => {
                  const value = row?.[header];
                  const validation = getValidationStatus(colIndex, rowIndex, value);
                  
                  return (
                    <td key={colIndex} className="px-3 py-2 relative group">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-foreground truncate max-w-32 font-data">
                          {value || '-'}
                        </span>
                        {validation && (
                          <div className="relative">
                            <Icon 
                              name={validation?.type === 'error' ? 'XCircle' : 
                                    validation?.type === 'warning' ? 'AlertTriangle' : 'CheckCircle'} 
                              size={12} 
                              className={validation?.type === 'error' ? 'text-error' : 
                                        validation?.type === 'warning' ? 'text-warning' : 'text-success'}
                            />
                            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
                              {validation?.message}
                            </div>
                          </div>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* Footer */}
      <div className="p-3 border-t border-border bg-muted/30">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            Preview showing {Math.min(10, fileData?.length)} of {fileData?.length} records
          </span>
          <div className="flex items-center space-x-4">
            <span>Columns: {previewData?.headers?.length}</span>
            <span>Mapped: {Object.values(columnMapping)?.filter(Boolean)?.length}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataPreviewTable;