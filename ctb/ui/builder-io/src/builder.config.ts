/**
 * Builder.io Configuration
 * Centralized setup for Builder.io visual editor integration
 */

import { Builder } from '@builder.io/react';

// Import all components to register
import AccordionItem from './components/AccordionItem';
import PhaseCard from './components/PhaseCard';
import PhaseDetail from './components/PhaseDetail';
import ErrorConsole from './components/ErrorConsole';

/**
 * Builder.io API Key
 * Get your public API key from: https://builder.io/account/organization
 * Add to .env as VITE_BUILDER_PUBLIC_KEY
 */
export const BUILDER_API_KEY = import.meta.env.VITE_BUILDER_PUBLIC_KEY || 'YOUR_BUILDER_PUBLIC_KEY_HERE';

/**
 * Initialize Builder.io SDK
 */
export function initializeBuilder() {
  // Set the public API key
  Builder.set({ apiKey: BUILDER_API_KEY });

  // Register components for visual editing
  registerComponents();

  console.log('[Builder.io] SDK initialized with API key:', BUILDER_API_KEY);
}

/**
 * Register all custom components with Builder.io
 * This makes them available in the Builder.io visual editor
 */
function registerComponents() {
  // Register AccordionItem component
  Builder.registerComponent(AccordionItem, {
    name: 'AccordionItem',
    description: 'Expandable accordion section with toggle functionality',
    inputs: [
      {
        name: 'title',
        type: 'string',
        defaultValue: 'Section Title',
        required: true,
      },
      {
        name: 'defaultOpen',
        type: 'boolean',
        defaultValue: false,
        helperText: 'Whether the accordion should be open by default',
      },
      {
        name: 'badge',
        type: 'string',
        helperText: 'Optional badge text or number to display',
      },
      {
        name: 'children',
        type: 'blocks',
        hideFromUI: false,
        helperText: 'Content to display inside the accordion',
        defaultValue: [
          {
            '@type': '@builder.io/sdk:Element',
            component: { name: 'Text', options: { text: 'Add your content here' } },
          },
        ],
      },
    ],
  });

  // Register PhaseCard component
  Builder.registerComponent(PhaseCard, {
    name: 'PhaseCard',
    description: 'Display summary metrics for a pipeline phase',
    inputs: [
      {
        name: 'phase',
        type: 'string',
        required: true,
        defaultValue: 'Phase Name',
      },
      {
        name: 'stats',
        type: 'list',
        subFields: [
          {
            name: 'status',
            type: 'string',
            enum: ['completed', 'processing', 'pending', 'failed'],
          },
          {
            name: 'count',
            type: 'number',
            defaultValue: 0,
          },
          {
            name: 'last_updated',
            type: 'string',
          },
        ],
        defaultValue: [
          { status: 'completed', count: 10, last_updated: new Date().toISOString() },
          { status: 'pending', count: 5, last_updated: new Date().toISOString() },
        ],
      },
    ],
  });

  // Register PhaseDetail component
  Builder.registerComponent(PhaseDetail, {
    name: 'PhaseDetail',
    description: 'Detailed view of a pipeline phase with Apify integration',
    inputs: [
      {
        name: 'phase',
        type: 'string',
        required: true,
        defaultValue: 'Phase Name',
      },
      {
        name: 'stats',
        type: 'list',
        subFields: [
          {
            name: 'status',
            type: 'string',
          },
          {
            name: 'count',
            type: 'number',
          },
          {
            name: 'last_updated',
            type: 'string',
          },
        ],
        defaultValue: [
          { status: 'completed', count: 10, last_updated: new Date().toISOString() },
        ],
      },
      {
        name: 'apifyActorId',
        type: 'string',
        helperText: 'Apify actor ID to run for this phase',
      },
    ],
  });

  // Register ErrorConsole component
  Builder.registerComponent(ErrorConsole, {
    name: 'ErrorConsole',
    description: 'Display recent errors from Neon database and n8n workflows',
    inputs: [], // No inputs needed - fetches data automatically
  });

  console.log('[Builder.io] Registered components:', [
    'AccordionItem',
    'PhaseCard',
    'PhaseDetail',
    'ErrorConsole',
  ]);
}

/**
 * Custom field types for Builder.io
 */
export const customFieldTypes = {
  phaseStats: {
    name: 'Phase Statistics',
    type: 'list',
    subFields: [
      { name: 'phase', type: 'string' },
      { name: 'status', type: 'string' },
      { name: 'count', type: 'number' },
      { name: 'last_updated', type: 'string' },
    ],
  },
};

/**
 * Default Builder.io content options
 */
export const builderOptions = {
  includeRefs: true,
  // Enable preview mode for development
  preview: import.meta.env.DEV,
};
