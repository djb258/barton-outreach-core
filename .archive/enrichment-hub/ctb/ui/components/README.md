# UI Components

This directory contains reusable UI component blueprints and documentation.

## Component Structure

Components follow Atomic Design principles:

### Atoms
- Basic building blocks (buttons, inputs, icons)
- No dependencies on other components
- Highly reusable

### Molecules
- Simple combinations of atoms
- Single responsibility
- Examples: search bar, card header

### Organisms
- Complex components with multiple molecules/atoms
- Examples: navigation bar, data table, form sections

### Templates
- Page-level layouts
- Define content structure without data
- Examples: dashboard layout, auth layout

### Pages
- Complete page implementations
- Combine templates with actual content
- Connected to routing

## Implementation

CTB components serve as blueprints. Actual implementations go in `src/components/`.

## Styling

- **Framework**: Tailwind CSS
- **Custom Components**: shadcn/ui components in `src/components/ui/`
- **Theme**: Configured in `tailwind.config.ts`

## Best Practices

1. Use TypeScript for type safety
2. Follow naming conventions: PascalCase for components
3. Include PropTypes or TypeScript interfaces
4. Document component props and usage
5. Write unit tests for complex logic
6. Keep components small and focused

## Component Template

```tsx
import React from 'react';

interface ComponentNameProps {
  // Define props here
}

export const ComponentName: React.FC<ComponentNameProps> = ({ ...props }) => {
  return (
    <div className="...">
      {/* Component implementation */}
    </div>
  );
};
```
