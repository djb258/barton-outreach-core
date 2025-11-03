import React, { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { builder } from '@builder.io/react';
import BuilderPage from './pages/BuilderPage';
import AppDefault from './AppDefault';
import './App.css';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    console.error('Error caught by boundary:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ minHeight: '100vh', backgroundColor: '#fee2e2', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div style={{ backgroundColor: 'white', padding: '40px', borderRadius: '8px', maxWidth: '600px', border: '2px solid #dc2626' }}>
            <h1 style={{ color: '#dc2626', marginTop: 0 }}>Render Error</h1>
            <pre style={{ backgroundColor: '#f3f4f6', padding: '15px', borderRadius: '4px', overflow: 'auto', fontSize: '12px' }}>
              {this.state.error?.message}
            </pre>
            <div style={{ marginTop: '20px' }}>
              <button
                onClick={() => window.location.reload()}
                style={{ backgroundColor: '#dc2626', color: 'white', padding: '10px 20px', borderRadius: '6px', border: 'none', cursor: 'pointer' }}
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

function App() {
  const [useBuilder, setUseBuilder] = useState(false);
  const [checkingBuilder, setCheckingBuilder] = useState(true);

  useEffect(() => {
    checkForBuilderContent();
  }, []);

  const checkForBuilderContent = async () => {
    try {
      const urlPath = window.location.pathname;
      const forceBuilder = new URLSearchParams(window.location.search).get('builder') === 'true';

      if (forceBuilder) {
        console.log('[Builder.io] Forced Builder mode via query param');
        setUseBuilder(true);
        setCheckingBuilder(false);
        return;
      }

      if (urlPath === '/') {
        setUseBuilder(false);
        setCheckingBuilder(false);
        return;
      }

      const content = await builder
        .get('page', {
          userAttributes: {
            urlPath,
          },
        })
        .toPromise();

      if (content) {
        console.log('[Builder.io] Found content for path:', urlPath);
        setUseBuilder(true);
      } else {
        console.log('[Builder.io] No content found, using default dashboard');
        setUseBuilder(false);
      }
    } catch (error) {
      console.log('[Builder.io] Error checking content:', error);
      setUseBuilder(false);
    } finally {
      setCheckingBuilder(false);
    }
  };

  if (checkingBuilder) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: '50px', height: '50px', border: '4px solid #4f46e5', borderRightColor: 'transparent', borderRadius: '50%', margin: '0 auto 20px', animation: 'spin 1s linear infinite' }}></div>
          <p style={{ color: '#666', fontSize: '18px' }}>Loading...</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      {useBuilder ? <BuilderPage /> : <AppDefault />}
    </ErrorBoundary>
  );
}

export default App;
