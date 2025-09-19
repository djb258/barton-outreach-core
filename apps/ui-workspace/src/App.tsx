import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { OutreachManagement } from './pages/OutreachManagement'
import { CompanyDatabase } from './pages/CompanyDatabase'
import { PeopleDatabase } from './pages/PeopleDatabase'
import { CampaignExecution } from './pages/CampaignExecution'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/outreach" element={<OutreachManagement />} />
        <Route path="/companies" element={<CompanyDatabase />} />
        <Route path="/people" element={<PeopleDatabase />} />
        <Route path="/campaigns" element={<CampaignExecution />} />
      </Routes>
    </Layout>
  )
}

export default App