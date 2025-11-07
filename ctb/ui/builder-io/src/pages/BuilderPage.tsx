/**
 * Builder.io Visual Editor Page
 * This component renders content from Builder.io's visual editor
 */

import { useEffect, useState } from 'react';
import { BuilderComponent, builder } from '@builder.io/react';
import { BUILDER_API_KEY } from '../builder.config';

interface BuilderPageProps {
  model?: string;
  content?: any;
}

export default function BuilderPage({ model = 'page', content }: BuilderPageProps) {
  const [pageContent, setPageContent] = useState(content);
  const [loading, setLoading] = useState(!content);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    // If content is provided as prop, use it
    if (content) {
      setPageContent(content);
      setLoading(false);
      return;
    }

    // Otherwise, fetch content from Builder.io based on current URL
    const fetchContent = async () => {
      try {
        const urlPath = window.location.pathname;

        const fetchedContent = await builder
          .get(model, {
            userAttributes: {
              urlPath,
            },
          })
          .toPromise();

        if (fetchedContent) {
          setPageContent(fetchedContent);
          setNotFound(false);
        } else {
          setNotFound(true);
        }
      } catch (error) {
        console.error('[Builder.io] Error fetching content:', error);
        setNotFound(true);
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [model, content]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading Builder.io content...</p>
        </div>
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            No Builder.io Content Found
          </h1>
          <p className="text-lg text-gray-600 mb-6">
            This page doesn't have any Builder.io content yet.
          </p>
          <div className="bg-white rounded-lg shadow-lg p-6 text-left">
            <h2 className="text-xl font-semibold mb-4">To create content:</h2>
            <ol className="list-decimal list-inside space-y-2 text-gray-700">
              <li>Go to <a href="https://builder.io" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">builder.io</a></li>
              <li>Create a new "Page" model content</li>
              <li>Set the URL to match this path: <code className="bg-gray-100 px-2 py-1 rounded">{window.location.pathname}</code></li>
              <li>Drag and drop your registered components</li>
              <li>Publish and refresh this page</li>
            </ol>
            <div className="mt-4 p-4 bg-blue-50 rounded border border-blue-200">
              <p className="text-sm text-blue-800">
                <strong>API Key:</strong> {BUILDER_API_KEY === 'YOUR_BUILDER_PUBLIC_KEY_HERE'
                  ? '⚠️ Not configured - Add to .env'
                  : '✓ Configured'}
              </p>
            </div>
          </div>
          <div className="mt-6">
            <a
              href="/"
              className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Go to Default Dashboard
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <BuilderComponent
        model={model}
        content={pageContent}
      />
    </div>
  );
}
