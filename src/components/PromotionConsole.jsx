import React, { useState, useEffect, useCallback } from 'react';
import { httpsCallable } from 'firebase/functions';
import { functions } from '../firebase/config';

const PromotionConsole = () => {
  const [promotionData, setPromotionData] = useState({
    companies: [],
    persons: [],
    selectedCompanies: [],
    selectedPersons: []
  });

  const [promotionStatus, setPromotionStatus] = useState({
    isPromoting: false,
    currentProcess: null,
    stats: null,
    errors: [],
    logs: []
  });

  const [filters, setFilters] = useState({
    recordType: 'all',
    validationStatus: 'validated',
    dateRange: 'today',
    searchTerm: ''
  });

  const [ui, setUi] = useState({
    showAdvancedFilters: false,
    selectedTab: 'companies',
    showLogs: false,
    showErrors: false
  });

  const promoteCompany = httpsCallable(functions, 'promoteCompany');
  const promotePerson = httpsCallable(functions, 'promotePerson');
  const getPromotionStatus = httpsCallable(functions, 'getPromotionStatus');

  useEffect(() => {
    loadValidatedRecords();
  }, [filters]);

  const loadValidatedRecords = async () => {
    try {
      // Mock data loading - replace with actual Firebase query
      const mockCompanies = [
        {
          unique_id: 'CMP-INT-001',
          company_name: 'Microsoft Corporation',
          domain: 'microsoft.com',
          industry: 'Technology',
          validation_status: 'validated',
          validated_at: '2025-01-15T10:30:00Z'
        },
        {
          unique_id: 'CMP-INT-002',
          company_name: 'Google LLC',
          domain: 'google.com',
          industry: 'Technology',
          validation_status: 'validated',
          validated_at: '2025-01-15T11:15:00Z'
        }
      ];

      const mockPersons = [
        {
          unique_id: 'PER-INT-001',
          first_name: 'Satya',
          last_name: 'Nadella',
          email: 'satya@microsoft.com',
          company_unique_id: 'CMP-INT-001',
          validation_status: 'validated',
          validated_at: '2025-01-15T10:45:00Z'
        },
        {
          unique_id: 'PER-INT-002',
          first_name: 'Sundar',
          last_name: 'Pichai',
          email: 'sundar@google.com',
          company_unique_id: 'CMP-INT-002',
          validation_status: 'validated',
          validated_at: '2025-01-15T11:30:00Z'
        }
      ];

      setPromotionData(prev => ({
        ...prev,
        companies: mockCompanies,
        persons: mockPersons
      }));

    } catch (error) {
      console.error('Failed to load validated records:', error);
    }
  };

  const handleSelectRecord = (type, recordId, selected) => {
    const selectionKey = type === 'company' ? 'selectedCompanies' : 'selectedPersons';

    setPromotionData(prev => ({
      ...prev,
      [selectionKey]: selected
        ? [...prev[selectionKey], recordId]
        : prev[selectionKey].filter(id => id !== recordId)
    }));
  };

  const handleSelectAll = (type) => {
    const recordsKey = type === 'company' ? 'companies' : 'persons';
    const selectionKey = type === 'company' ? 'selectedCompanies' : 'selectedPersons';

    setPromotionData(prev => ({
      ...prev,
      [selectionKey]: prev[recordsKey].map(record => record.unique_id)
    }));
  };

  const handleClearSelection = (type) => {
    const selectionKey = type === 'company' ? 'selectedCompanies' : 'selectedPersons';

    setPromotionData(prev => ({
      ...prev,
      [selectionKey]: []
    }));
  };

  const startPromotion = async (type) => {
    const selectedKey = type === 'company' ? 'selectedCompanies' : 'selectedPersons';
    const recordsKey = type === 'company' ? 'companies' : 'persons';
    const selectedIds = promotionData[selectedKey];

    if (selectedIds.length === 0) {
      alert(`Please select ${type} records to promote`);
      return;
    }

    const selectedRecords = promotionData[recordsKey].filter(
      record => selectedIds.includes(record.unique_id)
    );

    setPromotionStatus(prev => ({
      ...prev,
      isPromoting: true,
      currentProcess: `promote-${type}-${Date.now()}`,
      errors: [],
      logs: []
    }));

    try {
      const promotionFunction = type === 'company' ? promoteCompany : promotePerson;
      const payload = type === 'company'
        ? { companyRecords: selectedRecords }
        : { personRecords: selectedRecords };

      const result = await promotionFunction(payload);

      setPromotionStatus(prev => ({
        ...prev,
        isPromoting: false,
        stats: result.data.stats,
        errors: result.data.errors || [],
        logs: result.data.logs || []
      }));

      // Refresh the records list
      await loadValidatedRecords();

      // Clear selections
      handleClearSelection(type);

    } catch (error) {
      console.error(`${type} promotion failed:`, error);
      setPromotionStatus(prev => ({
        ...prev,
        isPromoting: false,
        errors: [{ error: error.message }]
      }));
    }
  };

  const checkPromotionStatus = async () => {
    if (!promotionStatus.currentProcess) return;

    try {
      const result = await getPromotionStatus({
        processId: promotionStatus.currentProcess
      });

      setPromotionStatus(prev => ({
        ...prev,
        stats: result.data.stats,
        logs: result.data.logs
      }));

    } catch (error) {
      console.error('Status check failed:', error);
    }
  };

  const filteredCompanies = promotionData.companies.filter(company => {
    if (filters.searchTerm && !company.company_name.toLowerCase().includes(filters.searchTerm.toLowerCase())) {
      return false;
    }
    return true;
  });

  const filteredPersons = promotionData.persons.filter(person => {
    if (filters.searchTerm &&
        !`${person.first_name} ${person.last_name}`.toLowerCase().includes(filters.searchTerm.toLowerCase()) &&
        !person.email.toLowerCase().includes(filters.searchTerm.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <div className="promotion-console">
      <div className="console-header">
        <h1>🚀 Step 4: Promotion Console</h1>
        <p>Promote validated records to master tables</p>
      </div>

      {/* Status Panel */}
      {promotionStatus.isPromoting && (
        <div className="status-panel promoting">
          <div className="status-content">
            <div className="loading-spinner"></div>
            <span>Promoting records...</span>
            <button onClick={checkPromotionStatus} className="btn-status">
              Check Status
            </button>
          </div>
        </div>
      )}

      {promotionStatus.stats && (
        <div className="status-panel completed">
          <h3>Promotion Results</h3>
          <div className="stats-grid">
            <div className="stat">
              <span className="stat-value">{promotionStatus.stats.promoted}</span>
              <span className="stat-label">Promoted</span>
            </div>
            <div className="stat">
              <span className="stat-value">{promotionStatus.stats.failed}</span>
              <span className="stat-label">Failed</span>
            </div>
            <div className="stat">
              <span className="stat-value">{promotionStatus.stats.duplicates || 0}</span>
              <span className="stat-label">Duplicates</span>
            </div>
            <div className="stat">
              <span className="stat-value">{promotionStatus.stats.relationshipsPreserved || 0}</span>
              <span className="stat-label">Relationships</span>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <div className="filter-row">
          <input
            type="text"
            placeholder="Search records..."
            value={filters.searchTerm}
            onChange={(e) => setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
            className="search-input"
          />

          <select
            value={filters.validationStatus}
            onChange={(e) => setFilters(prev => ({ ...prev, validationStatus: e.target.value }))}
            className="filter-select"
          >
            <option value="validated">Validated Only</option>
            <option value="all">All Status</option>
            <option value="pending">Pending Validation</option>
          </select>

          <button
            onClick={() => setUi(prev => ({ ...prev, showAdvancedFilters: !prev.showAdvancedFilters }))}
            className="btn-secondary"
          >
            Advanced Filters
          </button>
        </div>

        {ui.showAdvancedFilters && (
          <div className="advanced-filters">
            <select
              value={filters.dateRange}
              onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
              className="filter-select"
            >
              <option value="today">Today</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
              <option value="all">All Time</option>
            </select>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="tabs-section">
        <div className="tab-buttons">
          <button
            className={`tab-button ${ui.selectedTab === 'companies' ? 'active' : ''}`}
            onClick={() => setUi(prev => ({ ...prev, selectedTab: 'companies' }))}
          >
            Companies ({filteredCompanies.length})
          </button>
          <button
            className={`tab-button ${ui.selectedTab === 'persons' ? 'active' : ''}`}
            onClick={() => setUi(prev => ({ ...prev, selectedTab: 'persons' }))}
          >
            Persons ({filteredPersons.length})
          </button>
        </div>
      </div>

      {/* Companies Tab */}
      {ui.selectedTab === 'companies' && (
        <div className="records-section">
          <div className="section-header">
            <h3>Company Records</h3>
            <div className="section-actions">
              <span className="selection-count">
                {promotionData.selectedCompanies.length} selected
              </span>
              <button
                onClick={() => handleSelectAll('company')}
                className="btn-secondary"
                disabled={filteredCompanies.length === 0}
              >
                Select All
              </button>
              <button
                onClick={() => handleClearSelection('company')}
                className="btn-secondary"
                disabled={promotionData.selectedCompanies.length === 0}
              >
                Clear Selection
              </button>
              <button
                onClick={() => startPromotion('company')}
                className="btn-primary"
                disabled={promotionData.selectedCompanies.length === 0 || promotionStatus.isPromoting}
              >
                Promote Selected Companies
              </button>
            </div>
          </div>

          <div className="records-table">
            <div className="table-header">
              <div className="table-cell">Select</div>
              <div className="table-cell">Company Name</div>
              <div className="table-cell">Domain</div>
              <div className="table-cell">Industry</div>
              <div className="table-cell">Validated At</div>
              <div className="table-cell">Status</div>
            </div>

            {filteredCompanies.map(company => (
              <div key={company.unique_id} className="table-row">
                <div className="table-cell">
                  <input
                    type="checkbox"
                    checked={promotionData.selectedCompanies.includes(company.unique_id)}
                    onChange={(e) => handleSelectRecord('company', company.unique_id, e.target.checked)}
                  />
                </div>
                <div className="table-cell">{company.company_name}</div>
                <div className="table-cell">{company.domain}</div>
                <div className="table-cell">{company.industry}</div>
                <div className="table-cell">
                  {new Date(company.validated_at).toLocaleDateString()}
                </div>
                <div className="table-cell">
                  <span className={`status-badge ${company.validation_status}`}>
                    {company.validation_status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Persons Tab */}
      {ui.selectedTab === 'persons' && (
        <div className="records-section">
          <div className="section-header">
            <h3>Person Records</h3>
            <div className="section-actions">
              <span className="selection-count">
                {promotionData.selectedPersons.length} selected
              </span>
              <button
                onClick={() => handleSelectAll('person')}
                className="btn-secondary"
                disabled={filteredPersons.length === 0}
              >
                Select All
              </button>
              <button
                onClick={() => handleClearSelection('person')}
                className="btn-secondary"
                disabled={promotionData.selectedPersons.length === 0}
              >
                Clear Selection
              </button>
              <button
                onClick={() => startPromotion('person')}
                className="btn-primary"
                disabled={promotionData.selectedPersons.length === 0 || promotionStatus.isPromoting}
              >
                Promote Selected Persons
              </button>
            </div>
          </div>

          <div className="records-table">
            <div className="table-header">
              <div className="table-cell">Select</div>
              <div className="table-cell">Name</div>
              <div className="table-cell">Email</div>
              <div className="table-cell">Company</div>
              <div className="table-cell">Validated At</div>
              <div className="table-cell">Status</div>
            </div>

            {filteredPersons.map(person => (
              <div key={person.unique_id} className="table-row">
                <div className="table-cell">
                  <input
                    type="checkbox"
                    checked={promotionData.selectedPersons.includes(person.unique_id)}
                    onChange={(e) => handleSelectRecord('person', person.unique_id, e.target.checked)}
                  />
                </div>
                <div className="table-cell">
                  {person.first_name} {person.last_name}
                </div>
                <div className="table-cell">{person.email}</div>
                <div className="table-cell">
                  {person.company_unique_id ? (
                    <span className="company-link">{person.company_unique_id}</span>
                  ) : (
                    <span className="no-company">No company</span>
                  )}
                </div>
                <div className="table-cell">
                  {new Date(person.validated_at).toLocaleDateString()}
                </div>
                <div className="table-cell">
                  <span className={`status-badge ${person.validation_status}`}>
                    {person.validation_status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Panel */}
      {promotionStatus.errors.length > 0 && (
        <div className="error-panel">
          <h3>Promotion Errors</h3>
          {promotionStatus.errors.map((error, index) => (
            <div key={index} className="error-item">
              <strong>Record ID:</strong> {error.recordId}<br />
              <strong>Error:</strong> {error.error}
            </div>
          ))}
        </div>
      )}

      <style jsx>{`
        .promotion-console {
          padding: 20px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .console-header {
          margin-bottom: 30px;
          text-align: center;
        }

        .console-header h1 {
          color: #2c3e50;
          margin-bottom: 10px;
        }

        .status-panel {
          margin: 20px 0;
          padding: 20px;
          border-radius: 8px;
          border: 1px solid #ddd;
        }

        .status-panel.promoting {
          background-color: #fff3cd;
          border-color: #ffc107;
        }

        .status-panel.completed {
          background-color: #d4edda;
          border-color: #28a745;
        }

        .status-content {
          display: flex;
          align-items: center;
          gap: 15px;
        }

        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid #f3f3f3;
          border-top: 2px solid #007bff;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 20px;
          margin-top: 15px;
        }

        .stat {
          text-align: center;
          padding: 15px;
          background: white;
          border-radius: 8px;
          border: 1px solid #ddd;
        }

        .stat-value {
          display: block;
          font-size: 24px;
          font-weight: bold;
          color: #2c3e50;
        }

        .stat-label {
          display: block;
          font-size: 12px;
          color: #6c757d;
          margin-top: 5px;
        }

        .filters-section {
          margin: 20px 0;
          padding: 20px;
          background: #f8f9fa;
          border-radius: 8px;
        }

        .filter-row {
          display: flex;
          gap: 15px;
          align-items: center;
          flex-wrap: wrap;
        }

        .search-input {
          flex: 1;
          min-width: 300px;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .filter-select {
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          background: white;
        }

        .advanced-filters {
          margin-top: 15px;
          padding-top: 15px;
          border-top: 1px solid #ddd;
        }

        .tabs-section {
          margin: 20px 0;
        }

        .tab-buttons {
          display: flex;
          border-bottom: 2px solid #ddd;
        }

        .tab-button {
          padding: 12px 24px;
          border: none;
          background: none;
          cursor: pointer;
          border-bottom: 3px solid transparent;
          font-weight: 500;
        }

        .tab-button.active {
          border-bottom-color: #007bff;
          color: #007bff;
        }

        .records-section {
          margin: 20px 0;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding: 15px 0;
          border-bottom: 1px solid #ddd;
        }

        .section-actions {
          display: flex;
          gap: 10px;
          align-items: center;
        }

        .selection-count {
          font-size: 14px;
          color: #6c757d;
          margin-right: 10px;
        }

        .records-table {
          border: 1px solid #ddd;
          border-radius: 8px;
          overflow-x: auto;
        }

        .table-header, .table-row {
          display: grid;
          grid-template-columns: 60px 2fr 1.5fr 1fr 1fr 100px;
          min-width: 800px;
        }

        .table-header {
          background: #f8f9fa;
          font-weight: bold;
          border-bottom: 1px solid #ddd;
        }

        .table-row {
          border-bottom: 1px solid #eee;
        }

        .table-row:hover {
          background: #f8f9fa;
        }

        .table-cell {
          padding: 12px;
          display: flex;
          align-items: center;
          border-right: 1px solid #eee;
        }

        .table-cell:last-child {
          border-right: none;
        }

        .status-badge {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: bold;
          text-transform: uppercase;
        }

        .status-badge.validated {
          background: #d4edda;
          color: #155724;
        }

        .status-badge.pending {
          background: #fff3cd;
          color: #856404;
        }

        .company-link {
          color: #007bff;
          text-decoration: underline;
          cursor: pointer;
        }

        .no-company {
          color: #6c757d;
          font-style: italic;
        }

        .error-panel {
          margin: 20px 0;
          padding: 20px;
          background: #f8d7da;
          border: 1px solid #f5c6cb;
          border-radius: 8px;
        }

        .error-item {
          margin: 10px 0;
          padding: 10px;
          background: white;
          border-radius: 4px;
        }

        .btn-primary {
          background: #007bff;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
        }

        .btn-primary:hover:not(:disabled) {
          background: #0056b3;
        }

        .btn-primary:disabled {
          background: #6c757d;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: #6c757d;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 4px;
          cursor: pointer;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #545b62;
        }

        .btn-secondary:disabled {
          background: #adb5bd;
          cursor: not-allowed;
        }

        .btn-status {
          background: #17a2b8;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 4px;
          cursor: pointer;
        }

        .btn-status:hover {
          background: #138496;
        }
      `}</style>
    </div>
  );
};

export default PromotionConsole;