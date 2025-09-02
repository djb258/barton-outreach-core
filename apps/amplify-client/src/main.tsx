import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Amplify } from 'aws-amplify'
import { Authenticator } from '@aws-amplify/ui-react'
import App from './App.tsx'
import './index.css'
import '@aws-amplify/ui-react/styles.css'

// Configure Amplify
const amplifyConfig = {
  Auth: {
    Cognito: {
      region: import.meta.env.VITE_AWS_REGION || 'us-east-1',
      userPoolId: import.meta.env.VITE_USER_POOL_ID,
      userPoolClientId: import.meta.env.VITE_USER_POOL_CLIENT_ID,
      identityPoolId: import.meta.env.VITE_IDENTITY_POOL_ID,
      allowGuestAccess: true
    }
  },
  API: {
    REST: {
      bartonApi: {
        endpoint: import.meta.env.VITE_API_ENDPOINT || 'http://localhost:3000',
        region: import.meta.env.VITE_AWS_REGION || 'us-east-1'
      }
    }
  }
}

Amplify.configure(amplifyConfig)

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Authenticator.Provider>
          <App />
        </Authenticator.Provider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)