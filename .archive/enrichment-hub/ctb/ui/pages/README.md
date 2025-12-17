# UI Pages

This directory contains page-level component blueprints and routing documentation.

## Page Structure

Pages are complete views that combine multiple components to create full user experiences.

## Routing

- **Library**: React Router
- **Lazy Loading**: Enabled for performance
- **Routes**: Defined in `src/App.tsx` or routing configuration

## Page Categories

### Public Pages
- Landing page
- Authentication (login, signup, forgot password)
- Public documentation
- Error pages (404, 500)

### Protected Pages
- Dashboard
- User profile
- Settings
- Feature-specific pages

### Admin Pages
- Admin dashboard
- User management
- System configuration
- Analytics

## Page Template

```tsx
import React from 'react';
import { Helmet } from 'react-helmet-async';

export const PageName: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>Page Title | App Name</title>
        <meta name="description" content="Page description" />
      </Helmet>

      <div className="container mx-auto px-4 py-8">
        {/* Page content */}
      </div>
    </>
  );
};
```

## Data Fetching

- Use React Query for server state
- Implement loading and error states
- Handle authentication requirements
- Optimize for performance

## SEO Considerations

- Use react-helmet-async for meta tags
- Implement proper heading hierarchy
- Add structured data when applicable
- Ensure proper alt text for images

## Best Practices

1. Keep pages focused on orchestration, not logic
2. Extract complex logic to custom hooks
3. Implement proper loading states
4. Handle errors gracefully
5. Optimize bundle size with code splitting
6. Test user flows end-to-end
