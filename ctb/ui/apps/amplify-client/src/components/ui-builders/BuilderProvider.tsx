import React from 'react';
import { builder } from '@builder.io/react';

// Initialize Builder.io
builder.init(process.env.REACT_APP_BUILDER_IO_KEY || process.env.VITE_BUILDER_IO_KEY || '');

interface BuilderProviderProps {
  children: React.ReactNode;
}

export const BuilderProvider: React.FC<BuilderProviderProps> = ({ children }) => {
  React.useEffect(() => {
    // Register custom components with Builder.io
    builder.registerComponent(() => import('../contact-vault/ContactList'), {
      name: 'ContactList',
      inputs: [
        { name: 'limit', type: 'number', defaultValue: 50 },
        { name: 'showFilters', type: 'boolean', defaultValue: true }
      ]
    });

    builder.registerComponent(() => import('../data-ingestion/DataIngestionForm'), {
      name: 'DataIngestionForm',
      inputs: [
        { name: 'source', type: 'string', defaultValue: 'manual' },
        { name: 'autoPromote', type: 'boolean', defaultValue: false }
      ]
    });

    builder.registerComponent(() => import('../analytics/MetricsDashboard'), {
      name: 'MetricsDashboard',
      inputs: [
        { name: 'timeRange', type: 'string', defaultValue: '30d' },
        { name: 'showExport', type: 'boolean', defaultValue: true }
      ]
    });
  }, []);

  return <>{children}</>;
};

// Builder.io page wrapper component
export const BuilderPage: React.FC<{ model: string; content?: any }> = ({ 
  model, 
  content 
}) => {
  const [builderContent, setBuilderContent] = React.useState(content);

  React.useEffect(() => {
    if (!content) {
      builder.get(model, {
        url: window.location.pathname
      }).then(setBuilderContent);
    }
  }, [model, content]);

  if (!builderContent) {
    return <div className="p-8 text-center">Loading...</div>;
  }

  return (
    <div className="builder-page">
      {builder.BuilderComponent({ model, content: builderContent })}
    </div>
  );
};