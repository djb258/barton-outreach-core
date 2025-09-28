/**
 * Barton Doctrine Validator
 * Validates Barton ID format and doctrine compliance in the codebase
 */

const fs = require('fs');
const path = require('path');

class BartonDoctrineValidator {
  constructor() {
    this.bartonIdRegex = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d{3}$/;
    this.errors = [];
    this.warnings = [];
  }

  // Validate Barton ID format
  validateBartonId(id, context) {
    if (!this.bartonIdRegex.test(id)) {
      this.errors.push({
        type: 'invalid_barton_id',
        message: `Invalid Barton ID format: ${id}`,
        context,
        expected: 'NN.NN.NN.NN.NNNNN.NNN'
      });
      return false;
    }
    return true;
  }

  // Check if file has doctrine header
  validateDoctrineHeader(filePath, content) {
    const doctrineHeaderRegex = /\/\*\*[\s\S]*?Doctrine Spec:[\s\S]*?Barton ID:[\s\S]*?\*\//;

    if (!doctrineHeaderRegex.test(content)) {
      this.warnings.push({
        type: 'missing_doctrine_header',
        message: `Missing Doctrine header in ${filePath}`,
        recommendation: 'Add Doctrine spec header with Barton ID'
      });
      return false;
    }

    // Extract Barton ID from header
    const bartonIdMatch = content.match(/Barton ID:\s*([0-9.]+)/);
    if (bartonIdMatch) {
      const bartonId = bartonIdMatch[1];
      if (!this.validateBartonId(bartonId, `File: ${filePath}`)) {
        return false;
      }
    }

    return true;
  }

  // Check for direct database connections (non-MCP)
  validateMcpCompliance(filePath, content) {
    const directDbPatterns = [
      /import.*neon.*from.*@neondatabase/,
      /import.*firebase/,
      /import.*pg.*from.*pg/,
      /new Pool\(/,
      /client\.query\(/,
      /pool\.query\(/
    ];

    const mcpPatterns = [
      /ComposioNeonBridge/,
      /ComposioMCPClient/,
      /executeNeonOperation/
    ];

    const hasDirectDb = directDbPatterns.some(pattern => pattern.test(content));
    const hasMcp = mcpPatterns.some(pattern => pattern.test(content));

    if (hasDirectDb && !hasMcp) {
      this.errors.push({
        type: 'mcp_violation',
        message: `Direct database connection detected in ${filePath}`,
        recommendation: 'Use ComposioNeonBridge for MCP compliance'
      });
      return false;
    }

    return true;
  }

  // Validate API file compliance
  validateApiFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');

    let isCompliant = true;

    // Check doctrine header
    if (!this.validateDoctrineHeader(filePath, content)) {
      isCompliant = false;
    }

    // Check MCP compliance
    if (!this.validateMcpCompliance(filePath, content)) {
      isCompliant = false;
    }

    return isCompliant;
  }

  // Validate migration file compliance
  validateMigrationFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');

    let isCompliant = true;

    // Check for Barton ID columns
    if (!content.includes('barton_id') && !content.includes('unique_id')) {
      this.warnings.push({
        type: 'missing_barton_id_column',
        message: `Migration ${filePath} may be missing Barton ID column`,
        recommendation: 'Ensure tables have barton_id or unique_id column'
      });
    }

    // Check for audit columns
    const requiredColumns = ['created_at', 'updated_at'];
    requiredColumns.forEach(col => {
      if (!content.includes(col)) {
        this.warnings.push({
          type: 'missing_audit_column',
          message: `Migration ${filePath} missing ${col} column`,
          recommendation: `Add ${col} TIMESTAMP column for audit compliance`
        });
      }
    });

    return isCompliant;
  }

  // Scan directory for violations
  scanDirectory(dirPath, extensions = ['.ts', '.js', '.sql']) {
    if (!fs.existsSync(dirPath)) {
      return;
    }

    const files = fs.readdirSync(dirPath);

    files.forEach(file => {
      const filePath = path.join(dirPath, file);
      const stat = fs.statSync(filePath);

      if (stat.isDirectory()) {
        // Skip node_modules and .git
        if (!['node_modules', '.git', '.github'].includes(file)) {
          this.scanDirectory(filePath, extensions);
        }
      } else {
        const ext = path.extname(file);
        if (extensions.includes(ext)) {
          if (filePath.includes('/api/') && (ext === '.ts' || ext === '.js')) {
            this.validateApiFile(filePath);
          }
          if (filePath.includes('/migration') && ext === '.sql') {
            this.validateMigrationFile(filePath);
          }
        }
      }
    });
  }

  // Generate compliance report
  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      compliance_status: this.errors.length === 0 ? 'PASS' : 'FAIL',
      summary: {
        total_errors: this.errors.length,
        total_warnings: this.warnings.length,
        critical_issues: this.errors.filter(e => e.type === 'mcp_violation' || e.type === 'invalid_barton_id').length
      },
      errors: this.errors,
      warnings: this.warnings,
      recommendations: [
        'All API files should have Doctrine headers with valid Barton IDs',
        'Use ComposioNeonBridge for all database operations',
        'Ensure migrations include audit columns (created_at, updated_at)',
        'Validate Barton ID format: NN.NN.NN.NN.NNNNN.NNN'
      ]
    };

    return report;
  }

  // Main validation function
  validate(projectPath) {
    console.log('🔍 Starting Barton Doctrine validation...');

    // Scan API files
    this.scanDirectory(path.join(projectPath, 'apps/outreach-process-manager/api'), ['.ts', '.js']);
    this.scanDirectory(path.join(projectPath, 'api'), ['.ts', '.js']);

    // Scan migration files
    this.scanDirectory(path.join(projectPath, 'migrations'), ['.sql']);
    this.scanDirectory(path.join(projectPath, 'apps/outreach-process-manager/migrations'), ['.sql']);

    const report = this.generateReport();

    console.log('\n📋 Barton Doctrine Validation Report:');
    console.log(`Status: ${report.compliance_status}`);
    console.log(`Errors: ${report.summary.total_errors}`);
    console.log(`Warnings: ${report.summary.total_warnings}`);
    console.log(`Critical Issues: ${report.summary.critical_issues}`);

    if (report.errors.length > 0) {
      console.log('\n❌ Errors:');
      report.errors.forEach(error => {
        console.log(`  - ${error.message}`);
        if (error.recommendation) {
          console.log(`    Recommendation: ${error.recommendation}`);
        }
      });
    }

    if (report.warnings.length > 0) {
      console.log('\n⚠️  Warnings:');
      report.warnings.forEach(warning => {
        console.log(`  - ${warning.message}`);
        if (warning.recommendation) {
          console.log(`    Recommendation: ${warning.recommendation}`);
        }
      });
    }

    // Write report file
    fs.writeFileSync(
      path.join(projectPath, 'barton-doctrine-report.json'),
      JSON.stringify(report, null, 2)
    );

    console.log('\n📄 Report saved to: barton-doctrine-report.json');

    return report.compliance_status === 'PASS';
  }
}

// CLI usage
if (require.main === module) {
  const projectPath = process.argv[2] || '.';
  const validator = new BartonDoctrineValidator();
  const isCompliant = validator.validate(projectPath);

  if (!isCompliant) {
    console.log('\n💥 Barton Doctrine validation FAILED!');
    process.exit(1);
  } else {
    console.log('\n✅ Barton Doctrine validation PASSED!');
    process.exit(0);
  }
}

module.exports = BartonDoctrineValidator;