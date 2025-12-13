const Papa = require('papaparse');
const XLSX = require('xlsx');

/**
 * HEIR-Compliant Intelligent CSV/Excel Parser
 * Implements Intelligence principle through smart data detection and processing
 */
class IntelligentParser {
  constructor() {
    // Learning patterns for data type detection
    this.patterns = {
      email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      phone: /^(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}$/,
      url: /^https?:\/\/.+/,
      linkedin: /linkedin\.com\/in\/|linkedin\.com\/company\//,
      company: /\b(inc|llc|corp|ltd|co\.|company|corporation)\b/i
    };
    
    // Field mapping intelligence
    this.fieldMappings = {
      // Company fields
      company: ['company_name', 'company', 'organization', 'business_name', 'org'],
      domain: ['domain', 'website', 'company_website', 'url', 'web'],
      industry: ['industry', 'sector', 'business_type', 'category'],
      location: ['location', 'address', 'city', 'state', 'country', 'region'],
      employees: ['employee_count', 'employees', 'staff_count', 'team_size'],
      
      // People fields  
      firstName: ['first_name', 'fname', 'given_name', 'firstname'],
      lastName: ['last_name', 'lname', 'surname', 'lastname', 'family_name'],
      email: ['email', 'email_address', 'contact_email', 'work_email'],
      title: ['title', 'job_title', 'position', 'role', 'designation'],
      linkedin: ['linkedin', 'linkedin_url', 'profile', 'social']
    };
  }

  /**
   * Parse file with intelligent detection (HEIR Intelligence)
   */
  async parseFile(file, options = {}) {
    try {
      console.log(`[Intelligent-Parser] Processing file: ${file.name || 'buffer'}`);
      
      const extension = this.detectFileType(file);
      let rawData;
      
      // Parse based on file type
      switch (extension) {
        case 'csv':
          rawData = await this.parseCsv(file, options);
          break;
        case 'xlsx':
        case 'xls':
          rawData = await this.parseExcel(file, options);
          break;
        case 'json':
          rawData = await this.parseJson(file);
          break;
        default:
          throw new Error(`Unsupported file type: ${extension}`);
      }
      
      // Apply intelligent processing
      const processedData = this.applyIntelligentProcessing(rawData);
      const dataType = this.detectDataType(processedData);
      const quality = this.assessDataQuality(processedData);
      
      return {
        success: true,
        data: processedData,
        metadata: {
          originalFileName: file.name || 'unknown',
          fileType: extension,
          recordCount: processedData.length,
          detectedDataType: dataType,
          qualityScore: quality.score,
          qualityIssues: quality.issues,
          fieldMappings: this.getAppliedMappings(processedData),
          processingTimestamp: new Date().toISOString()
        }
      };
      
    } catch (error) {
      console.error('[Intelligent-Parser] Error:', error);
      return {
        success: false,
        error: error.message,
        data: [],
        metadata: {
          originalFileName: file.name || 'unknown',
          error: error.message,
          timestamp: new Date().toISOString()
        }
      };
    }
  }

  /**
   * Detect file type intelligently
   */
  detectFileType(file) {
    if (file.name) {
      return file.name.split('.').pop()?.toLowerCase();
    }
    
    // For buffers, try to detect from content
    if (Buffer.isBuffer(file)) {
      // Excel files start with specific bytes
      if (file.length > 4) {
        const header = file.slice(0, 4);
        if (header.toString('hex') === 'd0cf11e0') return 'xls';
        if (header.slice(0, 2).toString() === 'PK') return 'xlsx';
      }
    }
    
    return 'csv'; // Default fallback
  }

  /**
   * Parse CSV with intelligence
   */
  async parseCsv(file, options = {}) {
    return new Promise((resolve, reject) => {
      const config = {
        header: true,
        skipEmptyLines: true,
        dynamicTyping: true, // Automatically convert types
        trimHeaders: true,
        transformHeader: (header) => this.normalizeFieldName(header),
        ...options
      };

      if (file.name || typeof file === 'string') {
        Papa.parse(file, {
          ...config,
          complete: (results) => {
            if (results.errors.length > 0) {
              console.warn('[Parser] CSV warnings:', results.errors);
            }
            resolve(results.data);
          },
          error: reject
        });
      } else {
        // Handle buffer/blob
        Papa.parse(file, {
          ...config,
          complete: (results) => resolve(results.data),
          error: reject
        });
      }
    });
  }

  /**
   * Parse Excel with intelligence  
   */
  async parseExcel(file, options = {}) {
    try {
      let data;
      
      if (Buffer.isBuffer(file)) {
        data = file;
      } else {
        // Convert file to buffer
        data = await this.fileToBuffer(file);
      }
      
      const workbook = XLSX.read(data, { type: 'buffer' });
      
      // Intelligently select the best sheet
      const sheetName = this.selectBestSheet(workbook);
      const worksheet = workbook.Sheets[sheetName];
      
      // Convert with smart options
      const jsonData = XLSX.utils.sheet_to_json(worksheet, {
        header: 1,
        defval: null,
        ...options
      });
      
      // Convert array format to object format with headers
      if (jsonData.length > 0) {
        const headers = jsonData[0].map(h => this.normalizeFieldName(h));
        return jsonData.slice(1).map(row => {
          const obj = {};
          headers.forEach((header, index) => {
            obj[header] = row[index] || null;
          });
          return obj;
        });
      }
      
      return [];
    } catch (error) {
      throw new Error(`Excel parsing failed: ${error.message}`);
    }
  }

  /**
   * Parse JSON intelligently
   */
  async parseJson(file) {
    try {
      const content = await this.fileToString(file);
      const parsed = JSON.parse(content);
      
      // Ensure array format
      return Array.isArray(parsed) ? parsed : [parsed];
    } catch (error) {
      throw new Error(`JSON parsing failed: ${error.message}`);
    }
  }

  /**
   * Apply intelligent processing to raw data
   */
  applyIntelligentProcessing(data) {
    return data.map((record, index) => {
      const processed = { ...record };
      
      // Apply field mappings
      Object.keys(processed).forEach(key => {
        const normalizedKey = this.mapFieldName(key);
        if (normalizedKey !== key) {
          processed[normalizedKey] = processed[key];
          delete processed[key];
        }
      });
      
      // Data enrichment and cleaning
      processed._originalIndex = index;
      processed._processedAt = new Date().toISOString();
      
      // Clean and validate data
      Object.keys(processed).forEach(key => {
        processed[key] = this.cleanFieldValue(key, processed[key]);
      });
      
      return processed;
    });
  }

  /**
   * Detect data type (companies vs people)
   */
  detectDataType(data) {
    if (data.length === 0) return 'unknown';
    
    const firstRecord = data[0];
    const fields = Object.keys(firstRecord);
    
    // Score for company vs people indicators
    let companyScore = 0;
    let peopleScore = 0;
    
    fields.forEach(field => {
      if (this.isCompanyField(field)) companyScore++;
      if (this.isPeopleField(field)) peopleScore++;
    });
    
    if (companyScore > peopleScore) return 'companies';
    if (peopleScore > companyScore) return 'people';
    return 'mixed';
  }

  /**
   * Assess data quality (HEIR Intelligence)
   */
  assessDataQuality(data) {
    if (data.length === 0) {
      return { score: 0, issues: ['No data to assess'] };
    }
    
    const issues = [];
    let score = 100;
    
    // Check for empty records
    const emptyRecords = data.filter(record => 
      Object.values(record).every(val => !val || val === '')
    ).length;
    
    if (emptyRecords > 0) {
      issues.push(`${emptyRecords} empty records found`);
      score -= (emptyRecords / data.length) * 20;
    }
    
    // Check for missing critical fields
    const criticalFields = ['email', 'company_name', 'first_name', 'last_name'];
    const sampleRecord = data[0];
    
    criticalFields.forEach(field => {
      if (!sampleRecord.hasOwnProperty(field)) {
        const hasVariant = Object.keys(sampleRecord).some(key => 
          this.fieldMappings[field.replace('_', '')]?.includes(key.toLowerCase())
        );
        if (!hasVariant) {
          issues.push(`Missing critical field: ${field}`);
          score -= 10;
        }
      }
    });
    
    // Check data consistency
    const fieldConsistency = this.checkFieldConsistency(data);
    if (fieldConsistency < 0.8) {
      issues.push('Low field consistency across records');
      score -= 15;
    }
    
    return {
      score: Math.max(0, Math.round(score)),
      issues,
      consistency: fieldConsistency,
      completeness: this.calculateCompleteness(data)
    };
  }

  // Helper methods
  normalizeFieldName(name) {
    return name.trim().toLowerCase().replace(/[^a-z0-9]/g, '_');
  }

  mapFieldName(originalName) {
    const normalized = originalName.toLowerCase();
    
    for (const [standardField, variants] of Object.entries(this.fieldMappings)) {
      if (variants.includes(normalized)) {
        return standardField;
      }
    }
    
    return originalName;
  }

  cleanFieldValue(fieldName, value) {
    if (value === null || value === undefined || value === '') return null;
    
    const strValue = String(value).trim();
    
    // Email cleaning
    if (fieldName === 'email' && this.patterns.email.test(strValue)) {
      return strValue.toLowerCase();
    }
    
    // URL cleaning
    if (fieldName === 'domain' || fieldName === 'website') {
      return strValue.replace(/^https?:\/\//, '').replace(/\/$/, '');
    }
    
    return strValue;
  }

  isCompanyField(field) {
    const companyFields = ['company', 'domain', 'industry', 'employees', 'revenue'];
    return companyFields.some(cf => field.toLowerCase().includes(cf));
  }

  isPeopleField(field) {
    const peopleFields = ['first_name', 'last_name', 'email', 'title', 'phone'];
    return peopleFields.some(pf => field.toLowerCase().includes(pf));
  }

  selectBestSheet(workbook) {
    // Select sheet with most data
    const sheets = workbook.SheetNames;
    let bestSheet = sheets[0];
    let maxCells = 0;
    
    sheets.forEach(name => {
      const sheet = workbook.Sheets[name];
      const range = XLSX.utils.decode_range(sheet['!ref'] || 'A1:A1');
      const cellCount = (range.e.r - range.s.r) * (range.e.c - range.s.c);
      
      if (cellCount > maxCells) {
        maxCells = cellCount;
        bestSheet = name;
      }
    });
    
    return bestSheet;
  }

  checkFieldConsistency(data) {
    const fieldCounts = {};
    const totalRecords = data.length;
    
    data.forEach(record => {
      Object.keys(record).forEach(field => {
        fieldCounts[field] = (fieldCounts[field] || 0) + 1;
      });
    });
    
    const consistencyScores = Object.values(fieldCounts).map(count => count / totalRecords);
    return consistencyScores.reduce((sum, score) => sum + score, 0) / consistencyScores.length;
  }

  calculateCompleteness(data) {
    const totalFields = data.length * Object.keys(data[0]).length;
    const filledFields = data.reduce((count, record) => {
      return count + Object.values(record).filter(val => val !== null && val !== '').length;
    }, 0);
    
    return filledFields / totalFields;
  }

  getAppliedMappings(data) {
    if (data.length === 0) return {};
    
    const mappings = {};
    Object.keys(data[0]).forEach(field => {
      const originalField = this.findOriginalField(field);
      if (originalField !== field) {
        mappings[originalField] = field;
      }
    });
    
    return mappings;
  }

  findOriginalField(mappedField) {
    for (const [standard, variants] of Object.entries(this.fieldMappings)) {
      if (standard === mappedField) {
        return variants[0]; // Return first variant as "original"
      }
    }
    return mappedField;
  }

  async fileToBuffer(file) {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(new Uint8Array(e.target.result));
      reader.readAsArrayBuffer(file);
    });
  }

  async fileToString(file) {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.readAsText(file);
    });
  }
}

module.exports = IntelligentParser;