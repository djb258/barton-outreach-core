import React, { useState, useMemo } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Select from '../../../components/ui/Select';
import { MASTER_SCHEMA, SCHEMA_CATEGORIES, getAutoMappingSuggestions } from '../../../constants/masterSchema';

const DataPreviewTable = ({ fileData, onColumnMapping, columnMapping, validationErrors }) => {
  const [showMappingMode, setShowMappingMode] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Enhanced data type detection with more types
  const detectDataType = (value) => {
    if (!value || value === '') return 'empty';
    if (/^[\w\.-]+@[\w\.-]+\.\w+$/?.test(value)) return 'email';
    if (/^[\+]?[\d\s\-\(\)]+$/?.test(value)) return 'phone';
    if (/^https?:\/\//?.test(value)) return 'url';
    if (/^\$[\d,]+\.?\d*$/?.test(value)) return 'currency';
    if (/^\d{4}$/?.test(value)) return 'year';
    if (/^\d{4}-\d{2}-\d{2}/?.test(value)) return 'date';
    if (/^\d+$/?.test(value)) return 'number';
    if (value?.length > 100) return 'longtext';
    return 'text';
  };

  const getDataTypeIcon = (type) => {
    switch (type) {
      case 'email': return 'Mail';
      case 'phone': return 'Phone';
      case 'url': return 'Globe';
      case 'currency': return 'DollarSign';
      case 'year': return 'Calendar';
      case 'date': return 'CalendarDays';
      case 'number': return 'Hash';
      case 'longtext': return 'FileText';
      case 'empty': return 'Minus';
      default: return 'Type';
    }
  };

  const getDataTypeColor = (type) => {
    switch (type) {
      case 'email': return 'text-blue-600';
      case 'phone': return 'text-green-600';
      case 'url': return 'text-purple-600';
      case 'currency': return 'text-emerald-600';
      case 'year': return 'text-orange-600';
      case 'date': return 'text-pink-600';
      case 'number': return 'text-cyan-600';
      case 'longtext': return 'text-indigo-600';
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

  // Enhanced validation with master schema
  const getValidationStatus = (columnIndex, rowIndex, value) => {
    const columnName = previewData?.headers?.[columnIndex];
    const mappedField = columnMapping?.[columnName];
    
    if (!mappedField) return null;
    
    const field = MASTER_SCHEMA?.find(f => f?.value === mappedField);
    if (!field) return null;
    
    // Required field validation
    if (field?.required && (!value || value?.trim() === '')) {
      return { type: 'error', message: 'Required field is empty' };
    }
    
    // Type-specific validation
    switch (field?.type) {
      case 'url':
        if (value && !/^https?:\/\//?.test(value)) {
          return { type: 'warning', message: 'URL should start with http:// or https://' };
        }
        break;
      case 'phone':
        if (value && !/^[\+]?[\d\s\-\(\)]+$/?.test(value)) {
          return { type: 'warning', message: 'Phone format may be invalid' };
        }
        break;
      case 'number':
        if (value && !/^\d+$/?.test(value)) {
          return { type: 'error', message: 'Must be a valid number' };
        }
        break;
      case 'currency':
        if (value && !/^[\$]?[\d,]+\.?\d*$/?.test(value)) {
          return { type: 'warning', message: 'Currency format may be invalid' };
        }
        break;
      case 'date':
        if (value && !/^\d{4}-\d{2}-\d{2}/?.test(value)) {
          return { type: 'warning', message: 'Date should be in YYYY-MM-DD format' };
        }
        break;
    }
    
    return { type: 'success', message: 'Valid data' };
  };

  const handleColumnMappingChange = (columnName, mappedField) => {
    onColumnMapping({
      ...columnMapping,
      [columnName]: mappedField
    });
  };

  // Auto-suggest mappings on file load
  const autoSuggestMappings = () => {
    const suggestions = {};
    previewData?.headers?.forEach(header => {
      const suggestion = getAutoMappingSuggestions(header);
      if (suggestion && !Object.values(columnMapping)?.includes(suggestion)) {
        suggestions[header] = suggestion;
      }
    });
    onColumnMapping({ ...columnMapping, ...suggestions });
  };

  // Filter master schema options
  const getFilteredSchemaOptions = () => {
    let filtered = MASTER_SCHEMA;
    
    if (selectedCategory !== 'all') {
      filtered = filtered?.filter(field => field?.category === selectedCategory);
    }
    
    if (searchTerm) {
      filtered = filtered?.filter(field => 
        field?.label?.toLowerCase()?.includes(searchTerm?.toLowerCase()) ||
        field?.description?.toLowerCase()?.includes(searchTerm?.toLowerCase())
      );
    }
    
    return filtered;
  };

  const getMappingOptions = (columnName) => {
    const usedFields = Object.values(columnMapping)?.filter(field => field && field !== columnMapping?.[columnName]);
    const filteredOptions = getFilteredSchemaOptions();
    
    return [
      { value: '', label: 'No mapping' },
      ...filteredOptions?.map(field => ({
        ...field,
        disabled: usedFields?.includes(field?.value)
      }))
    ];
  };

  // Get mapping statistics
  const getMappingStats = () => {
    const totalFields = MASTER_SCHEMA?.length;
    const mappedFields = Object.values(columnMapping)?.filter(Boolean)?.length;
    const requiredMapped = MASTER_SCHEMA?.filter(field => 
      field?.required && Object.values(columnMapping)?.includes(field?.value)
    )?.length;
    const totalRequired = MASTER_SCHEMA?.filter(field => field?.required)?.length;
    
    return { totalFields, mappedFields, requiredMapped, totalRequired };
  };

  const stats = getMappingStats();

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
            <h3 className="text-sm font-semibold text-foreground">Data Preview & Master Schema Mapping</h3>
            <p className="text-xs text-muted-foreground">
              Showing first 10 rows • {fileData?.length} total records • {stats?.mappedFields}/{stats?.totalFields} fields mapped
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            iconName="Zap"
            iconPosition="left"
            onClick={autoSuggestMappings}
          >
            Auto-Map
          </Button>
          <Button
            variant={showMappingMode ? "default" : "outline"}
            size="sm"
            iconName="Settings"
            iconPosition="left"
            onClick={() => setShowMappingMode(!showMappingMode)}
          >
            {showMappingMode ? 'Hide Mapping' : 'Schema Mapping'}
          </Button>
        </div>
      </div>
      {/* Mapping Statistics */}
      {showMappingMode && (
        <div className="p-4 bg-accent/10 border-b border-border">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="text-center">
              <div className="text-lg font-semibold text-foreground">{stats?.mappedFields}</div>
              <div className="text-xs text-muted-foreground">Fields Mapped</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-success">{stats?.requiredMapped}/{stats?.totalRequired}</div>
              <div className="text-xs text-muted-foreground">Required Fields</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-foreground">{previewData?.headers?.length}</div>
              <div className="text-xs text-muted-foreground">CSV Columns</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-foreground">{stats?.totalFields}</div>
              <div className="text-xs text-muted-foreground">Master Schema</div>
            </div>
          </div>
        </div>
      )}
      {/* Column Mapping Interface */}
      {showMappingMode && (
        <div className="p-4 bg-accent/5 border-b border-border">
          {/* Filter Controls */}
          <div className="flex flex-wrap items-center gap-4 mb-4">
            <div className="flex-1 min-w-64">
              <input
                type="text"
                placeholder="Search master schema fields..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e?.target?.value)}
                className="w-full px-3 py-2 text-sm border border-border rounded-md bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
            <Select
              options={[
                { value: 'all', label: 'All Categories' },
                ...Object.entries(SCHEMA_CATEGORIES)?.map(([key, category]) => ({
                  value: key,
                  label: category?.label
                }))
              ]}
              value={selectedCategory}
              onChange={setSelectedCategory}
              placeholder="Filter by category"
            />
          </div>

          {/* Column Mappings */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {previewData?.headers?.map((header, index) => {
              const sampleValue = previewData?.rows?.[0]?.[header];
              const detectedType = detectDataType(sampleValue);
              const mappedField = columnMapping?.[header];
              const schemaField = MASTER_SCHEMA?.find(f => f?.value === mappedField);
              
              return (
                <div key={index} className="space-y-2 p-3 border border-border rounded-lg bg-background/50">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-medium text-foreground truncate flex-1">
                      {header}
                    </label>
                    <div className="flex items-center space-x-1 ml-2">
                      <Icon 
                        name={getDataTypeIcon(detectedType)} 
                        size={12} 
                        className={getDataTypeColor(detectedType)}
                        title={`Detected: ${detectedType}`}
                      />
                      {schemaField?.required && (
                        <Icon name="Asterisk" size={8} className="text-error" title="Required field" />
                      )}
                    </div>
                  </div>
                  {sampleValue && (
                    <div className="text-xs text-muted-foreground truncate bg-muted/30 px-2 py-1 rounded">
                      Sample: {sampleValue}
                    </div>
                  )}
                  <Select
                    options={getMappingOptions(header)}
                    value={mappedField || ''}
                    onChange={(value) => handleColumnMappingChange(header, value)}
                    placeholder="Select master field"
                  />
                  {schemaField && (
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full bg-${SCHEMA_CATEGORIES?.[schemaField?.category]?.color}-500`} />
                      <span className="text-xs text-muted-foreground">
                        {SCHEMA_CATEGORIES?.[schemaField?.category]?.label}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
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
                const schemaField = MASTER_SCHEMA?.find(f => f?.value === mappedField);
                
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
                          title={`Type: ${dataType}`}
                        />
                        {schemaField?.required && (
                          <Icon name="Asterisk" size={8} className="text-error" title="Required" />
                        )}
                        {mappedField && (
                          <div className="w-2 h-2 bg-success rounded-full" title="Mapped to master schema" />
                        )}
                      </div>
                    </div>
                    {schemaField && (
                      <div className="text-xs text-muted-foreground mt-1 truncate max-w-32">
                        → {schemaField?.label}
                      </div>
                    )}
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
            <span>CSV Columns: {previewData?.headers?.length}</span>
            <span>Mapped: {stats?.mappedFields}/{stats?.totalFields}</span>
            <span className={stats?.requiredMapped === stats?.totalRequired ? 'text-success' : 'text-warning'}>
              Required: {stats?.requiredMapped}/{stats?.totalRequired}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataPreviewTable;