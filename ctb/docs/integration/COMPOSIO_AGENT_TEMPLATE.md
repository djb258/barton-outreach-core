# Composio Expert Agent - Template & Implementation Guide
**Created:** 2025-10-24
**Status:** Ready to Build
**Estimated Build Time:** 1-2 hours for MVP

---

## 🎯 Purpose

A reusable CLI agent that handles all Composio integrations:
- Automatic authentication
- Service discovery
- Connection management
- Testing & validation
- Error handling

---

## 📦 Project Structure

```
composio-agent/
├── package.json
├── index.js                    # CLI entry point
├── lib/
│   ├── core/
│   │   ├── auth.js            # Authentication manager
│   │   ├── api.js             # Generic API wrapper
│   │   └── config.js          # Config management
│   ├── services/
│   │   ├── neon.js            # Neon-specific functions
│   │   ├── github.js          # GitHub functions
│   │   ├── gmail.js           # Gmail functions
│   │   └── template.js        # Template for new services
│   └── utils/
│       ├── logger.js          # Logging
│       └── formatter.js       # Output formatting
├── commands/
│   ├── connect.js             # Connect command
│   ├── test.js                # Test command
│   ├── list.js                # List command
│   └── get.js                 # Get command
└── README.md
```

---

## 🚀 Quick Start Template

### package.json

```json
{
  "name": "composio-agent",
  "version": "1.0.0",
  "description": "Expert agent for all Composio integrations",
  "main": "index.js",
  "bin": {
    "composio-agent": "./index.js"
  },
  "scripts": {
    "start": "node index.js",
    "test": "node test/test.js"
  },
  "dependencies": {
    "commander": "^11.1.0",
    "chalk": "^4.1.2",
    "ora": "^5.4.1",
    "dotenv": "^16.0.3",
    "@composio/core": "^0.1.52"
  },
  "devDependencies": {
    "eslint": "^8.0.0"
  }
}
```

### index.js (CLI Entry Point)

```javascript
#!/usr/bin/env node

const { program } = require('commander');
const chalk = require('chalk');
const connectCommand = require('./commands/connect');
const testCommand = require('./commands/test');
const listCommand = require('./commands/list');
const getCommand = require('./commands/get');

program
  .name('composio-agent')
  .description('Expert agent for Composio integrations')
  .version('1.0.0');

// Connect command
program
  .command('connect <service> <api-key>')
  .description('Connect to a service (neon, github, gmail, etc.)')
  .option('-t, --test', 'Test connection after setup')
  .action(connectCommand);

// Test command
program
  .command('test <service>')
  .description('Test connection to a service')
  .action(testCommand);

// List command
program
  .command('list <service> <resource>')
  .description('List resources (e.g., list neon projects)')
  .option('-l, --limit <number>', 'Limit results', '10')
  .action(listCommand);

// Get command
program
  .command('get <service> <resource> <id>')
  .description('Get specific resource details')
  .option('-f, --format <type>', 'Output format (json, table)', 'table')
  .action(getCommand);

program.parse(process.argv);
```

---

## 💻 Core Implementation

### lib/core/api.js (Generic API Wrapper)

```javascript
const https = require('https');

class ComposioAPI {
  constructor(apiKey, service) {
    this.apiKey = apiKey;
    this.service = service;
    this.baseUrls = {
      neon: 'console.neon.tech',
      composio: 'backend.composio.dev',
      github: 'api.github.com'
    };
  }

  async request(path, options = {}) {
    return new Promise((resolve, reject) => {
      const requestOptions = {
        hostname: this.baseUrls[this.service] || 'api.composio.dev',
        path: path,
        method: options.method || 'GET',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          ...options.headers
        }
      };

      const req = https.request(requestOptions, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(parsed);
            } else {
              reject(new Error(`API Error: ${parsed.message || data}`));
            }
          } catch (e) {
            reject(new Error(`Parse Error: ${e.message}`));
          }
        });
      });

      req.on('error', (e) => {
        reject(new Error(`Request Error: ${e.message}`));
      });

      if (options.body) {
        req.write(JSON.stringify(options.body));
      }

      req.end();
    });
  }

  async get(path) {
    return this.request(path, { method: 'GET' });
  }

  async post(path, body) {
    return this.request(path, { method: 'POST', body });
  }

  async put(path, body) {
    return this.request(path, { method: 'PUT', body });
  }

  async delete(path) {
    return this.request(path, { method: 'DELETE' });
  }
}

module.exports = ComposioAPI;
```

### lib/services/neon.js (Neon Service - WORKING CODE)

```javascript
const ComposioAPI = require('../core/api');

class NeonService {
  constructor(apiKey) {
    this.api = new ComposioAPI(apiKey, 'neon');
  }

  // List all projects
  async listProjects() {
    const data = await this.api.get('/api/v2/projects');
    return data.projects;
  }

  // Get specific project
  async getProject(projectId) {
    const data = await this.api.get(`/api/v2/projects/${projectId}`);
    return data.project;
  }

  // Get project branches
  async getBranches(projectId) {
    const data = await this.api.get(`/api/v2/projects/${projectId}/branches`);
    return data.branches;
  }

  // Get databases for a branch
  async getDatabases(projectId, branchId) {
    const data = await this.api.get(
      `/api/v2/projects/${projectId}/branches/${branchId}/databases`
    );
    return data.databases;
  }

  // Get connection string
  async getConnectionString(projectId, branchId, databaseName, roleName) {
    const path = `/api/v2/projects/${projectId}/connection_uri` +
                 `?branch_id=${branchId}` +
                 `&database_name=${encodeURIComponent(databaseName)}` +
                 `&role_name=${encodeURIComponent(roleName)}`;
    const data = await this.api.get(path);
    return data.uri;
  }

  // Create new branch
  async createBranch(projectId, branchName, parentBranchId) {
    const body = {
      endpoints: [{ type: 'read_write' }],
      name: branchName,
      parent_id: parentBranchId
    };
    const data = await this.api.post(`/api/v2/projects/${projectId}/branches`, body);
    return data.branch;
  }

  // Test connection
  async testConnection() {
    try {
      const projects = await this.listProjects();
      return {
        success: true,
        message: `Connected! Found ${projects.length} projects.`,
        projects: projects.map(p => ({ id: p.id, name: p.name, region: p.region_id }))
      };
    } catch (error) {
      return {
        success: false,
        message: `Connection failed: ${error.message}`
      };
    }
  }
}

module.exports = NeonService;
```

### commands/connect.js (Connect Command)

```javascript
const chalk = require('chalk');
const ora = require('ora');
const fs = require('fs');
const path = require('path');

async function connect(service, apiKey, options) {
  const spinner = ora(`Connecting to ${service}...`).start();

  try {
    // Load service module
    const ServiceClass = require(`../lib/services/${service}`);
    const serviceInstance = new ServiceClass(apiKey);

    // Test connection
    const result = await serviceInstance.testConnection();

    if (result.success) {
      spinner.succeed(chalk.green(result.message));

      // Save to config
      const configPath = path.join(process.cwd(), '.composio-agent.json');
      let config = {};
      if (fs.existsSync(configPath)) {
        config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      }
      config[service] = { apiKey, connectedAt: new Date().toISOString() };
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

      console.log(chalk.blue('\nConnection details saved to .composio-agent.json'));

      // Display results
      if (result.projects) {
        console.log(chalk.yellow('\nProjects found:'));
        result.projects.forEach(p => {
          console.log(`  • ${p.name} (${p.id}) - ${p.region}`);
        });
      }

      // Run test if requested
      if (options.test) {
        console.log(chalk.blue('\nRunning connection test...'));
        require('./test')(service);
      }
    } else {
      spinner.fail(chalk.red(result.message));
      process.exit(1);
    }
  } catch (error) {
    spinner.fail(chalk.red(`Failed: ${error.message}`));
    process.exit(1);
  }
}

module.exports = connect;
```

### commands/test.js (Test Command)

```javascript
const chalk = require('chalk');
const ora = require('ora');
const fs = require('fs');
const path = require('path');

async function test(service) {
  const spinner = ora(`Testing ${service} connection...`).start();

  try {
    // Load config
    const configPath = path.join(process.cwd(), '.composio-agent.json');
    if (!fs.existsSync(configPath)) {
      spinner.fail(chalk.red('No configuration found. Run connect first.'));
      process.exit(1);
    }

    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    if (!config[service]) {
      spinner.fail(chalk.red(`${service} not configured. Run connect first.`));
      process.exit(1);
    }

    // Load service
    const ServiceClass = require(`../lib/services/${service}`);
    const serviceInstance = new ServiceClass(config[service].apiKey);

    // Run test
    const result = await serviceInstance.testConnection();

    if (result.success) {
      spinner.succeed(chalk.green('✓ Connection working!'));
      console.log(chalk.gray(`Connected at: ${config[service].connectedAt}`));
      if (result.message) {
        console.log(chalk.blue(result.message));
      }
    } else {
      spinner.fail(chalk.red('✗ Connection failed'));
      console.log(chalk.red(result.message));
      process.exit(1);
    }
  } catch (error) {
    spinner.fail(chalk.red(`Error: ${error.message}`));
    process.exit(1);
  }
}

module.exports = test;
```

---

## 🔧 Usage Examples

Once built, here's how you'd use it:

```bash
# Install globally
npm install -g .

# Connect to Neon
composio-agent connect neon napi_xjl7fz34lkcw5j00o1iu8p07mvu4im2uynkk9kiigqp7g9c3aunc57fcc7nbdqu1

# Test connection
composio-agent test neon

# List projects
composio-agent list neon projects

# Get connection string
composio-agent get neon connection white-union-26418370

# Create a branch
composio-agent create neon branch my-new-branch --project white-union-26418370
```

---

## 📋 Adding New Services (Template)

### lib/services/template.js

```javascript
const ComposioAPI = require('../core/api');

class [ServiceName]Service {
  constructor(apiKey) {
    this.api = new ComposioAPI(apiKey, '[service-name]');
  }

  // List main resources
  async list[Resources]() {
    const data = await this.api.get('/api/v2/[resources]');
    return data.[resources];
  }

  // Get specific resource
  async get[Resource](id) {
    const data = await this.api.get(`/api/v2/[resources]/${id}`);
    return data.[resource];
  }

  // Test connection
  async testConnection() {
    try {
      const resources = await this.list[Resources]();
      return {
        success: true,
        message: `Connected! Found ${resources.length} [resources].`,
        [resources]: resources
      };
    } catch (error) {
      return {
        success: false,
        message: `Connection failed: ${error.message}`
      };
    }
  }
}

module.exports = [ServiceName]Service;
```

### Steps to Add a Service:

1. Copy `lib/services/template.js` to `lib/services/[service].js`
2. Replace placeholders with service-specific values
3. Add service base URL to `lib/core/api.js`
4. Test with `composio-agent connect [service] [api-key]`

---

## 🎨 Advanced Features (Optional)

### Config Management

```javascript
// lib/core/config.js
const os = require('os');
const path = require('path');
const fs = require('fs');

class Config {
  constructor() {
    this.configDir = path.join(os.homedir(), '.composio-agent');
    this.configFile = path.join(this.configDir, 'config.json');
    this.ensureConfigDir();
  }

  ensureConfigDir() {
    if (!fs.existsSync(this.configDir)) {
      fs.mkdirSync(this.configDir, { recursive: true });
    }
  }

  get(service) {
    if (!fs.existsSync(this.configFile)) {
      return null;
    }
    const config = JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
    return config[service] || null;
  }

  set(service, data) {
    let config = {};
    if (fs.existsSync(this.configFile)) {
      config = JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
    }
    config[service] = data;
    fs.writeFileSync(this.configFile, JSON.stringify(config, null, 2));
  }

  delete(service) {
    if (!fs.existsSync(this.configFile)) {
      return;
    }
    const config = JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
    delete config[service];
    fs.writeFileSync(this.configFile, JSON.stringify(config, null, 2));
  }
}

module.exports = new Config();
```

### Pretty Output Formatting

```javascript
// lib/utils/formatter.js
const chalk = require('chalk');

class Formatter {
  static table(data, columns) {
    if (!data || data.length === 0) {
      console.log(chalk.gray('No data to display'));
      return;
    }

    // Calculate column widths
    const widths = columns.map(col => {
      const maxLength = Math.max(
        col.label.length,
        ...data.map(row => String(row[col.key] || '').length)
      );
      return Math.min(maxLength + 2, 50); // Max 50 chars per column
    });

    // Header
    console.log(
      columns.map((col, i) =>
        chalk.bold(col.label.padEnd(widths[i]))
      ).join(' ')
    );

    console.log(
      widths.map(w => '-'.repeat(w)).join(' ')
    );

    // Rows
    data.forEach(row => {
      console.log(
        columns.map((col, i) => {
          let value = String(row[col.key] || '');
          if (value.length > widths[i] - 2) {
            value = value.substring(0, widths[i] - 5) + '...';
          }
          return value.padEnd(widths[i]);
        }).join(' ')
      );
    });
  }

  static json(data) {
    console.log(JSON.stringify(data, null, 2));
  }

  static success(message) {
    console.log(chalk.green('✓ ' + message));
  }

  static error(message) {
    console.log(chalk.red('✗ ' + message));
  }

  static info(message) {
    console.log(chalk.blue('ℹ ' + message));
  }

  static warn(message) {
    console.log(chalk.yellow('⚠ ' + message));
  }
}

module.exports = Formatter;
```

---

## 🚀 Build Steps

When you're ready to build:

1. **Create project directory**
   ```bash
   mkdir composio-agent
   cd composio-agent
   ```

2. **Copy files from this template**
   - Create structure from "Project Structure" section
   - Copy code from each section into respective files

3. **Install dependencies**
   ```bash
   npm install
   ```

4. **Test with Neon**
   ```bash
   node index.js connect neon napi_xjl7fz34lkcw5j00o1iu8p07mvu4im2uynkk9kiigqp7g9c3aunc57fcc7nbdqu1
   node index.js test neon
   ```

5. **Install globally** (optional)
   ```bash
   npm link
   ```

---

## 📚 Resources

- **Neon API Docs:** https://api-docs.neon.tech/reference/getting-started-with-neon-api
- **Composio Docs:** https://docs.composio.dev
- **Commander.js:** https://github.com/tj/commander.js
- **Chalk:** https://github.com/chalk/chalk
- **Ora:** https://github.com/sindresorhus/ora

---

## ✨ Future Enhancements

- OAuth flow handling
- Interactive prompts
- Auto-discovery of service capabilities
- Batch operations
- Connection health monitoring
- Multi-service orchestration
- Web UI dashboard
- Plugin system for custom services

---

**Status:** Template ready. Copy/paste to build when you have time!
