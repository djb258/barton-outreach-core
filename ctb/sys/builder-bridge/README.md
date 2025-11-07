# Builder Bridge - Design-to-Code Integration

**Doctrine ID**: 04.04.06
**Altitude**: 40k ft (System Infrastructure)

## Purpose

Builder Bridge provides seamless integration between design tools (Builder.io, Figma) and the codebase. It enables design-driven development workflows and automated component generation.

## Features

- **Builder.io Integration** - Visual page builder
- **Figma Plugin** - Design-to-code conversion
- **Component Sync** - Automated component generation
- **Style System** - Design token management
- **Preview Mode** - Live design preview

## Architecture

### Integration Flow

```
Figma Design → Figma Plugin → Builder Bridge → React Components → Production
     ↓                                                ↓
  Design Tokens                              Component Library
```

## Setup

### Builder.io Configuration

1. Create Builder.io account
2. Add API key to MCP vault:
   ```bash
   BUILDER_API_KEY=your-api-key
   BUILDER_SPACE_ID=your-space-id
   ```

3. Install Builder.io SDK:
   ```bash
   npm install @builder.io/react
   ```

### Figma Plugin Setup

1. Install Figma plugin: "Builder Bridge Connector"
2. Configure plugin with API credentials
3. Set export settings in plugin preferences

## Directory Structure

```
builder-bridge/
├── templates/        # Builder.io page templates
├── components/       # Generated React components
├── figma/           # Figma design exports
├── styles/          # Design tokens and CSS
└── config/          # Integration configuration
```

## Usage

### Builder.io Pages

```jsx
import { BuilderComponent } from '@builder.io/react';

function DynamicPage({ page }) {
  return <BuilderComponent model="page" content={page} />;
}
```

### Figma Export

1. Open design in Figma
2. Select component/frame
3. Run Builder Bridge plugin
4. Choose export options:
   - React component
   - Vue component
   - HTML/CSS
5. Generated code appears in `components/`

### Design Tokens

Design tokens are automatically synced:

```css
/* Auto-generated from Figma */
:root {
  --color-primary: #1a73e8;
  --color-secondary: #34a853;
  --spacing-unit: 8px;
  --font-family-base: 'Inter', sans-serif;
}
```

## Builder.io Features

### Visual Page Builder

Create pages visually in Builder.io:
- Drag-and-drop components
- Real-time preview
- A/B testing support
- Personalization rules
- SEO optimization

### Custom Components

Register custom components:

```javascript
import { Builder } from '@builder.io/react';
import MyCustomComponent from './components/MyCustomComponent';

Builder.registerComponent(MyCustomComponent, {
  name: 'MyCustomComponent',
  inputs: [
    { name: 'title', type: 'string' },
    { name: 'description', type: 'richText' }
  ]
});
```

## Figma Integration

### Plugin Features

- **Component Detection** - Auto-detect components
- **Variant Support** - Handle component variants
- **Auto-layout** - Convert to Flexbox/Grid
- **Typography** - Extract text styles
- **Icons** - Export as SVG components
- **Images** - Optimize and export

### Export Options

```json
{
  "componentFormat": "react",
  "styleFormat": "css-modules",
  "typeScriptSupport": true,
  "includeTests": true,
  "preserveStructure": true
}
```

## Workflows

### Design → Development

1. Designer creates UI in Figma
2. Developer reviews and approves
3. Run Figma plugin to export
4. Components auto-generated in `components/`
5. Import and use in application
6. Push to production

### Marketing Pages

1. Marketing team builds page in Builder.io
2. Preview and test
3. Publish to production
4. Analytics and optimization

## Integration with CTB

Builder Bridge connects to:
- **ctb/ui/** - Generated UI components
- **ctb/docs/** - Component documentation
- **ctb/sys/firebase-workbench** - Asset storage
- **ctb/meta/** - Design system configuration

## Status

**Status**: Configured (awaiting integration)
**Builder.io**: Not yet connected
**Figma Plugin**: Not yet installed
**Components Generated**: 0

---

For more information, see [CTB_DOCTRINE.md](../../meta/global-config/CTB_DOCTRINE.md)
