import { useQuery } from '@tanstack/react-query'
import { BarChart3, Users, Upload, TrendingUp } from 'lucide-react'
import { checkHealth, getContacts } from '@barton/data-router'

export function Dashboard() {
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: () => checkHealth({ apiBase: import.meta.env.VITE_API_ENDPOINT }),
    refetchInterval: 30000, // Check health every 30 seconds
  })

  const { data: contactsData } = useQuery({
    queryKey: ['contacts', { limit: 5 }],
    queryFn: () => getContacts({ limit: 5 }, { apiBase: import.meta.env.VITE_API_ENDPOINT }),
  })

  const stats = [
    {
      name: 'Total Contacts',
      value: contactsData?.total || 0,
      icon: Users,
      change: '+12%',
      changeType: 'increase' as const,
    },
    {
      name: 'Data Ingested Today',
      value: '1,234',
      icon: Upload,
      change: '+8%',
      changeType: 'increase' as const,
    },
    {
      name: 'Conversion Rate',
      value: '3.2%',
      icon: TrendingUp,
      change: '+0.5%',
      changeType: 'increase' as const,
    },
    {
      name: 'API Health',
      value: healthData?.status || 'Unknown',
      icon: BarChart3,
      change: healthData?.status === 'healthy' ? 'Online' : 'Offline',
      changeType: healthData?.status === 'healthy' ? 'increase' : 'decrease' as const,
    },
  ]

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Welcome to your Barton Outreach Core dashboard</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-full ${
                stat.changeType === 'increase' ? 'bg-green-100' : 'bg-red-100'
              }`}>
                <stat.icon className={`h-6 w-6 ${
                  stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                }`} />
              </div>
            </div>
            <div className="mt-4">
              <span className={`inline-flex items-center text-sm font-medium ${
                stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
              }`}>
                {stat.change}
              </span>
              <span className="text-sm text-gray-500 ml-2">from last month</span>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Contacts */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Contacts</h2>
          <div className="space-y-4">
            {contactsData?.contacts?.slice(0, 5).map((contact, index) => (
              <div key={contact.id || index} className="flex items-center justify-between py-2">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-blue-600">
                      {contact.name?.charAt(0) || contact.email?.charAt(0) || '?'}
                    </span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">{contact.name || 'Unknown'}</p>
                    <p className="text-sm text-gray-500">{contact.email}</p>
                  </div>
                </div>
                <div className="text-sm text-gray-400">
                  {contact.source && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {contact.source}
                    </span>
                  )}
                </div>
              </div>
            )) || (
              <p className="text-gray-500 text-center py-4">No contacts found</p>
            )}
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">API Server</span>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                healthData?.status === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {healthData?.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Database</span>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                healthData ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
              }`}>
                {healthData ? 'Connected' : 'Checking...'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Last Updated</span>
              <span className="text-sm text-gray-500">
                {healthData?.timestamp ? new Date(healthData.timestamp).toLocaleTimeString() : 'Unknown'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}