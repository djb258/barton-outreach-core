import { Routes, Route, Navigate } from 'react-router-dom'
import { Authenticator } from '@aws-amplify/ui-react'
import { BartonLayout } from './components/layout/BartonLayout'
import { Dashboard } from './pages/Dashboard'
import { DataIngestion } from './pages/DataIngestion'
import { ContactVault } from './pages/ContactVault'
import { Analytics } from './pages/Analytics'
import { Settings } from './pages/Settings'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Authenticator>
        {({ signOut, user }) => (
          <BartonLayout user={user} signOut={signOut}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/ingestion" element={<DataIngestion />} />
              <Route path="/contacts" element={<ContactVault />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </BartonLayout>
        )}
      </Authenticator>
    </div>
  )
}

export default App