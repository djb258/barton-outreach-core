import React, { useState, useEffect } from 'react';
import { OutreachCompany, OutreachContact } from '@/lib/outreach/types';

interface CompanyManagerProps {
  onCompanySelect?: (company: OutreachCompany) => void;
}

export function CompanyManager({ onCompanySelect }: CompanyManagerProps) {
  const [companies, setCompanies] = useState<OutreachCompany[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<OutreachCompany | null>(null);
  const [contacts, setContacts] = useState<OutreachContact[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterColor, setFilterColor] = useState<string>('all');

  useEffect(() => {
    loadCompanies();
  }, []);

  useEffect(() => {
    if (selectedCompany) {
      loadContacts(selectedCompany.company_id);
    }
  }, [selectedCompany]);

  const loadCompanies = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/outreach/companies?limit=100');
      if (response.ok) {
        const data = await response.json();
        setCompanies(data);
      }
    } catch (error) {
      console.error('Error loading companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadContacts = async (companyId: number) => {
    try {
      const response = await fetch(`/api/outreach/contacts?company_id=${companyId}&limit=50`);
      if (response.ok) {
        const data = await response.json();
        setContacts(data);
      }
    } catch (error) {
      console.error('Error loading contacts:', error);
    }
  };

  const handleCompanyClick = (company: OutreachCompany) => {
    setSelectedCompany(company);
    if (onCompanySelect) {
      onCompanySelect(company);
    }
  };

  const getDotColorIcon = (color: string) => {
    switch (color) {
      case 'green': return '🟢';
      case 'yellow': return '🟡';
      case 'red': return '🔴';
      default: return '⚫';
    }
  };

  const filteredCompanies = companies.filter(company => {
    const matchesSearch = company.company_name?.toLowerCase().includes(searchTerm.toLowerCase()) || false;
    const matchesColor = filterColor === 'all' || company.dot_color === filterColor;
    return matchesSearch && matchesColor;
  });

  const getStatusBadge = (color: string) => {
    const labels = {
      green: 'Verified',
      yellow: 'Pending',
      red: 'Issues',
      gray: 'New'
    };
    return labels[color as keyof typeof labels] || 'Unknown';
  };

  return (
    <div className="company-manager">
      <div className="manager-header">
        <h2>Company Management</h2>
        <div className="controls">
          <div className="search-box">
            <input
              type="text"
              placeholder="Search companies..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <select
            value={filterColor}
            onChange={(e) => setFilterColor(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="green">Verified</option>
            <option value="yellow">Pending</option>
            <option value="red">Issues</option>
            <option value="gray">New</option>
          </select>
        </div>
      </div>

      <div className="manager-content">
        <div className="companies-list">
          <h3>Companies ({filteredCompanies.length})</h3>
          
          {loading && <div className="loading">Loading companies...</div>}
          
          <div className="companies-grid">
            {filteredCompanies.map(company => (
              <div
                key={company.company_id}
                className={`company-card ${selectedCompany?.company_id === company.company_id ? 'selected' : ''}`}
                onClick={() => handleCompanyClick(company)}
              >
                <div className="company-header">
                  <div className="company-name">{company.company_name}</div>
                  <div className="company-status">
                    <span className="dot-icon">{getDotColorIcon(company.dot_color)}</span>
                    <span className="status-label">{getStatusBadge(company.dot_color)}</span>
                  </div>
                </div>
                
                <div className="company-details">
                  {company.ein && <div>EIN: {company.ein}</div>}
                  {company.renewal_month && (
                    <div>Renewal: Month {company.renewal_month}</div>
                  )}
                  {company.next_renewal && (
                    <div>Next: {new Date(company.next_renewal).toLocaleDateString()}</div>
                  )}
                </div>

                {company.slot_name && (
                  <div className="slot-info">
                    <strong>{company.slot_name}</strong>
                    {company.slot_updated && (
                      <small> • Updated {new Date(company.slot_updated).toLocaleDateString()}</small>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {filteredCompanies.length === 0 && !loading && (
            <div className="empty-state">
              {searchTerm || filterColor !== 'all' 
                ? 'No companies match your filters' 
                : 'No companies found'}
            </div>
          )}
        </div>

        {selectedCompany && (
          <div className="company-details-panel">
            <h3>Contacts for {selectedCompany.company_name}</h3>
            
            <div className="contacts-grid">
              {contacts.map(contact => (
                <div key={contact.contact_id} className="contact-card">
                  <div className="contact-header">
                    <div className="contact-name">
                      {contact.first_name} {contact.last_name}
                    </div>
                    <div className="contact-status">
                      <span className="dot-icon">{getDotColorIcon(contact.dot_color)}</span>
                      <span className="status-label">{getStatusBadge(contact.dot_color)}</span>
                    </div>
                  </div>
                  
                  <div className="contact-info">
                    {contact.email && (
                      <div className="contact-field">
                        <strong>Email:</strong> {contact.email}
                      </div>
                    )}
                    {contact.phone && (
                      <div className="contact-field">
                        <strong>Phone:</strong> {contact.phone}
                      </div>
                    )}
                    {contact.title && (
                      <div className="contact-field">
                        <strong>Title:</strong> {contact.title}
                      </div>
                    )}
                    {contact.verification_status && (
                      <div className="contact-field">
                        <strong>Status:</strong> {contact.verification_status}
                      </div>
                    )}
                  </div>

                  {contact.updated_at && (
                    <div className="contact-updated">
                      Updated: {new Date(contact.updated_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {contacts.length === 0 && (
              <div className="empty-state">
                No contacts found for this company
              </div>
            )}
          </div>
        )}
      </div>

      <style jsx>{`
        .company-manager {
          padding: 24px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .manager-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
          flex-wrap: wrap;
          gap: 20px;
        }

        .manager-header h2 {
          margin: 0;
          color: #1e293b;
          font-size: 1.8em;
        }

        .controls {
          display: flex;
          gap: 16px;
          align-items: center;
        }

        .search-box input {
          padding: 12px 16px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          font-size: 0.9em;
          min-width: 250px;
        }

        .search-box input:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        select {
          padding: 12px 16px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          font-size: 0.9em;
          background: white;
          cursor: pointer;
        }

        .manager-content {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 30px;
        }

        .companies-list h3,
        .company-details-panel h3 {
          margin: 0 0 20px 0;
          color: #374151;
          font-size: 1.3em;
        }

        .loading {
          text-align: center;
          padding: 40px;
          color: #6b7280;
          font-style: italic;
        }

        .companies-grid,
        .contacts-grid {
          display: flex;
          flex-direction: column;
          gap: 16px;
          max-height: 600px;
          overflow-y: auto;
          padding-right: 8px;
        }

        .company-card,
        .contact-card {
          background: white;
          padding: 20px;
          border-radius: 12px;
          border: 2px solid #e5e7eb;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .company-card:hover,
        .contact-card:hover {
          border-color: #667eea;
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
        }

        .company-card.selected {
          border-color: #667eea;
          background: #f8faff;
        }

        .company-header,
        .contact-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
        }

        .company-name,
        .contact-name {
          font-weight: 600;
          color: #1e293b;
          font-size: 1.1em;
        }

        .company-status,
        .contact-status {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .dot-icon {
          font-size: 0.8em;
        }

        .status-label {
          font-size: 0.8em;
          font-weight: 500;
          color: #6b7280;
        }

        .company-details {
          color: #6b7280;
          font-size: 0.9em;
          line-height: 1.5;
          margin-bottom: 12px;
        }

        .slot-info {
          padding-top: 12px;
          border-top: 1px solid #e5e7eb;
          font-size: 0.9em;
        }

        .slot-info strong {
          color: #1e293b;
        }

        .slot-info small {
          color: #9ca3af;
        }

        .contact-info {
          margin-bottom: 12px;
        }

        .contact-field {
          margin-bottom: 6px;
          font-size: 0.9em;
        }

        .contact-field strong {
          color: #374151;
          margin-right: 8px;
        }

        .contact-updated {
          font-size: 0.8em;
          color: #9ca3af;
          border-top: 1px solid #e5e7eb;
          padding-top: 8px;
        }

        .empty-state {
          text-align: center;
          padding: 40px 20px;
          color: #9ca3af;
          font-style: italic;
        }

        @media (max-width: 1024px) {
          .manager-content {
            grid-template-columns: 1fr;
          }

          .manager-header {
            flex-direction: column;
            align-items: stretch;
          }

          .controls {
            flex-direction: column;
          }

          .search-box input {
            min-width: auto;
            width: 100%;
          }
        }

        @media (max-width: 768px) {
          .company-manager {
            padding: 16px;
          }

          .controls {
            gap: 12px;
          }

          .companies-grid,
          .contacts-grid {
            max-height: 400px;
          }
        }
      `}</style>
    </div>
  );
}