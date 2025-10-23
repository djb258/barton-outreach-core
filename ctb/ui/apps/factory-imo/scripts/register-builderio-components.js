/**
 * Builder.io Component Registration via Composio MCP
 * Registers Doctrine Tracker components for visual editing
 */
import fetch from 'node-fetch';
import dotenv from 'dotenv';

dotenv.config();

const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';
const MCP_SERVER_URL = 'http://localhost:3001';

/**
 * Register a component with Builder.io via MCP
 */
async function registerBuilderIOComponent(componentConfig) {
  try {
    const mcpPayload = {
      tool: 'builderio.register_component',
      params: componentConfig,
      metadata: {
        unique_id: `BUILDERIO-REG-${Date.now()}`,
        process_id: 'doctrine-tracker-registration',
        orbt_layer: 10000,
        timestamp: new Date().toISOString()
      }
    };

    console.log(`🔧 Registering ${componentConfig.name} with Builder.io...`);

    const response = await fetch(`${MCP_SERVER_URL}/tool`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Composio-Api-Key': COMPOSIO_API_KEY
      },
      body: JSON.stringify(mcpPayload)
    });

    if (!response.ok) {
      throw new Error(`Builder.io registration failed: ${response.statusText}`);
    }

    const result = await response.json();
    console.log(`✅ Successfully registered ${componentConfig.name}`);
    return result;

  } catch (error) {
    console.error(`❌ Failed to register ${componentConfig.name}:`, error.message);
    return null;
  }
}

/**
 * Component configurations for Builder.io
 */
const componentConfigs = [
  {
    name: 'PhaseGroup',
    friendlyName: 'Doctrine Phase Group',
    description: 'Groups process steps by Barton Doctrine altitude levels (Vision/Category/Execution)',
    component: {
      name: 'PhaseGroup',
      inputs: [
        {
          name: 'altitude',
          type: 'number',
          required: true,
          enum: [30000, 20000, 10000],
          defaultValue: 10000,
          helperText: 'Barton Doctrine altitude: 30000=Vision, 20000=Category, 10000=Execution'
        },
        {
          name: 'title',
          type: 'string',
          required: true,
          defaultValue: 'Process Phase',
          helperText: 'Display title for this phase group'
        },
        {
          name: 'steps',
          type: 'array',
          required: true,
          subFields: [
            {
              name: 'unique_id',
              type: 'string',
              required: true,
              helperText: 'Barton ID in format XX.XX.XX.XX.ALTITUDE.SEQUENCE'
            },
            {
              name: 'process_id',
              type: 'string',
              required: true,
              helperText: 'Human-readable process description'
            },
            {
              name: 'altitude',
              type: 'number',
              required: true
            },
            {
              name: 'tool_id',
              type: 'string',
              required: false,
              helperText: 'MCP tool identifier'
            },
            {
              name: 'table_reference',
              type: 'string',
              required: false,
              helperText: 'Database table reference'
            }
          ],
          defaultValue: [],
          helperText: 'Array of process steps for this phase'
        }
      ],
      outputs: [
        {
          name: 'rendered',
          type: 'element',
          description: 'Rendered phase group with step cards'
        }
      ]
    },
    image: 'https://cdn.builder.io/api/v1/image/assets%2F%40builderio%2Fgeneric-component',
    category: 'Process Management'
  },
  {
    name: 'StepCard',
    friendlyName: 'Doctrine Step Card',
    description: 'Individual process step card with Barton ID compliance and click-to-detail functionality',
    component: {
      name: 'StepCard',
      inputs: [
        {
          name: 'process_id',
          type: 'string',
          required: true,
          defaultValue: 'Sample Process',
          helperText: 'Human-readable process description'
        },
        {
          name: 'unique_id',
          type: 'string',
          required: true,
          defaultValue: '02.03.07.04.10000.001',
          helperText: 'Barton ID in format XX.XX.XX.XX.ALTITUDE.SEQUENCE'
        },
        {
          name: 'tool_id',
          type: 'string',
          required: false,
          helperText: 'MCP tool identifier (optional)'
        },
        {
          name: 'table_reference',
          type: 'string',
          required: false,
          helperText: 'Database table reference (optional)'
        }
      ],
      outputs: [
        {
          name: 'rendered',
          type: 'element',
          description: 'Rendered step card with modal trigger'
        }
      ]
    },
    image: 'https://cdn.builder.io/api/v1/image/assets%2F%40builderio%2Fcard-component',
    category: 'Process Management'
  },
  {
    name: 'ProcessDetailView',
    friendlyName: 'Doctrine Process View',
    description: 'Complete process detail view with altitude-based organization and Barton Doctrine compliance. Supports both live MCP data and demo data.',
    component: {
      name: 'ProcessDetailView',
      inputs: [
        {
          name: 'microprocess_id',
          type: 'string',
          required: false,
          helperText: 'Filter processes by microprocess ID (fetches from MCP server)'
        },
        {
          name: 'blueprint_id',
          type: 'string',
          required: false,
          helperText: 'Filter processes by blueprint ID (fetches from MCP server)'
        },
        {
          name: 'useDemoData',
          type: 'boolean',
          required: false,
          defaultValue: false,
          helperText: 'Use demo data instead of fetching from MCP server'
        }
      ],
      outputs: [
        {
          name: 'rendered',
          type: 'element',
          description: 'Complete process detail view with grouped phases, loading states, and error handling'
        }
      ]
    },
    image: 'https://cdn.builder.io/api/v1/image/assets%2F%40builderio%2Fdashboard-component',
    category: 'Process Management'
  }
];

/**
 * Main registration function
 */
async function main() {
  console.log('🚀 Starting Builder.io component registration via Composio MCP...');
  console.log(`📡 MCP Server: ${MCP_SERVER_URL}`);
  console.log(`🔑 Using Composio API Key: ${COMPOSIO_API_KEY.substring(0, 10)}...`);

  // Test MCP connection first
  try {
    const healthResponse = await fetch(`${MCP_SERVER_URL}/health`);
    if (!healthResponse.ok) {
      throw new Error('MCP server health check failed');
    }
    console.log('✅ MCP server is healthy');
  } catch (error) {
    console.error('❌ MCP server is not accessible:', error.message);
    console.log('Please ensure the Composio MCP server is running on localhost:3001');
    process.exit(1);
  }

  // Register each component
  const results = [];
  for (const config of componentConfigs) {
    const result = await registerBuilderIOComponent(config);
    results.push({ component: config.name, success: !!result });

    // Small delay between registrations
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  // Summary
  console.log('\n📊 Registration Summary:');
  results.forEach(({ component, success }) => {
    console.log(`${success ? '✅' : '❌'} ${component}`);
  });

  const successCount = results.filter(r => r.success).length;
  console.log(`\n🎉 Successfully registered ${successCount}/${results.length} components with Builder.io`);

  if (successCount > 0) {
    console.log('\n🔗 Next Steps:');
    console.log('1. Open Builder.io visual editor');
    console.log('2. Look for "Process Management" category in component library');
    console.log('3. Drag and drop Doctrine Tracker components');
    console.log('4. Configure component properties in the editor');
  }
}

// Run the registration
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export { registerBuilderIOComponent, componentConfigs };