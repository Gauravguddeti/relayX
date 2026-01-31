import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface Analytics {
  total_clients: number;
  active_clients: number;
  total_agents: number;
  total_calls: number;
  calls_today: number;
  success_rate: number;
  avg_call_duration: number;
  peak_hours: number[];
  top_clients: any[];
}

interface ClientCard {
  id: string;
  name: string;
  email: string;
  company?: string;
  phone?: string;
  agent_count: number;
  total_calls: number;
  active_calls: number;
  last_call?: string;
  created_at: string;
  is_active: boolean;
  subscription_tier: string;
}

interface Agent {
  id: string;
  name: string;
  user_id: string;
  is_active: boolean;
  created_at: string;
  user_name?: string;
  user_email?: string;
  user_company?: string;
}

interface Call {
  id: string;
  user_id: string;
  agent_id: string;
  to_number: string;
  status: string;
  duration?: number;
  created_at: string;
  user_name?: string;
  agent_name?: string;
}

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [clients, setClients] = useState<ClientCard[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);
  const [selectedClient, setSelectedClient] = useState<ClientCard | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const adminToken = localStorage.getItem('admin_token');
  const adminUsername = localStorage.getItem('admin_username') || 'Admin';

  const [activeLogTab, setActiveLogTab] = useState<'backend' | 'voice-gateway'>('backend');
  const [logLines, setLogLines] = useState<string[]>([]);

  useEffect(() => {
    if (!adminToken) {
      navigate('/admin/login');
      return;
    }
    loadData();
    fetchLogs('backend'); // Initial load
  }, [adminToken, navigate]);

  useEffect(() => {
    fetchLogs(activeLogTab);
    // Auto-refresh logs every 5 seconds
    const interval = setInterval(() => fetchLogs(activeLogTab), 5000);
    return () => clearInterval(interval);
  }, [activeLogTab]);

  const apiCall = async (endpoint: string) => {
    const response = await fetch(`http://localhost:8000${endpoint}`, {
      headers: {
        'Authorization': `Bearer ${adminToken}`,
      },
    });
    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('admin_token');
        navigate('/admin/login');
        throw new Error('Unauthorized');
      }
      throw new Error('API call failed');
    }
    return response.json();
  };

  const fetchLogs = async (service: string) => {
    try {
      const data = await apiCall(`/admin/system-logs/${service}?lines=500`);
      setLogLines(data.lines || []);
    } catch (error) {
      console.error(`Error fetching ${service} logs:`, error);
    }
  };

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [analyticsData, clientsData, agentsData, callsData] = await Promise.all([
        apiCall('/admin/analytics'),
        apiCall('/admin/clients'),
        apiCall('/admin/agents'),
        apiCall('/admin/calls?limit=20'),
      ]);

      setAnalytics(analyticsData);
      setClients(clientsData);
      setAgents(agentsData);
      setCalls(callsData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_username');
    navigate('/admin/login');
  };

  const filteredClients = clients.filter(
    (client) =>
      client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      client.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      client.company?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      completed: 'bg-green-500',
      failed: 'bg-red-500',
      'in-progress': 'bg-blue-500',
      initiated: 'bg-yellow-500',
      ringing: 'bg-purple-500',
    };
    return colors[status as keyof typeof colors] || 'bg-gray-500';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#161616] flex items-center justify-center">
        <div className="text-[#DAED6E] text-2xl">Loading admin dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#161616] text-[#FAFAFA]">
      {/* Header */}
      <nav className="bg-black border-b-2 border-[#DAED6E] shadow-lg">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-[#DAED6E]">RelayX</h1>
              <p className="text-sm text-[#FAFAFA]">
                Admin Dashboard • {adminUsername}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => { loadData(); fetchLogs(activeLogTab); }}
                className="px-4 py-2 bg-[#1E1E1E] hover:bg-[#DAED6E] hover:text-black rounded-lg transition font-bold"
              >
                🔄 Refresh
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-[#DAED6E] text-black hover:opacity-80 rounded-lg transition font-bold"
              >
                🚪 Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-6 py-8">
        {/* Analytics Overview */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-lg p-6 border-2 border-[#DAED6E]">
              <div className="text-sm text-gray-600">Total Clients</div>
              <div className="text-4xl font-bold text-black">
                {analytics.total_clients}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-lg p-6 border-2 border-[#DAED6E]">
              <div className="text-sm text-gray-600">Active Clients</div>
              <div className="text-4xl font-bold text-black">
                {analytics.active_clients}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-lg p-6 border-2 border-[#DAED6E]">
              <div className="text-sm text-gray-600">Calls Today</div>
              <div className="text-4xl font-bold text-black">
                {analytics.calls_today}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-lg p-6 border-2 border-[#DAED6E]">
              <div className="text-sm text-gray-600">Success Rate</div>
              <div className="text-4xl font-bold text-black">
                {analytics.success_rate.toFixed(1)}%
              </div>
            </div>
          </div>
        )}

        {/* Clients Section */}
        <div className="bg-[#1E1E1E] rounded-lg shadow-lg p-6 mb-8 border-2 border-[#1E1E1E]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-[#DAED6E]">👥 Clients</h2>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search clients..."
              className="px-4 py-2 bg-[#0A0A0A] border-2 border-[#0A0A0A] text-white rounded-lg focus:border-[#DAED6E] focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredClients.map((client) => (
              <div
                key={client.id}
                onClick={() => setSelectedClient(client)}
                className={`bg-[#1E1E1E] border-2 p-4 rounded-lg cursor-pointer transition hover:border-[#DAED6E] ${selectedClient?.id === client.id ? 'border-[#DAED6E]' : 'border-[#2A2A2A]'
                  }`}
              >
                <div className="font-bold text-white">{client.name}</div>
                <div className="text-sm text-gray-400">{client.email}</div>
                {client.company && (
                  <div className="text-xs text-gray-500">{client.company}</div>
                )}
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="text-[#DAED6E]">{client.agent_count} agents</span>
                  <span className="text-gray-400">{client.total_calls} calls</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Client Details */}
        {selectedClient && (
          <div className="bg-[#1E1E1E] rounded-lg shadow-lg p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">{selectedClient.name}</h2>
                <p className="text-gray-400">
                  {selectedClient.email} • {selectedClient.company}
                </p>
              </div>
              <button
                onClick={() => setSelectedClient(null)}
                className="px-4 py-2 bg-[#0A0A0A] hover:bg-[#DAED6E] hover:text-black rounded-lg transition font-bold"
              >
                ✕ Close
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-[#DAED6E] rounded-lg p-4">
                <div className="text-sm text-black font-bold">Agents</div>
                <div className="text-3xl font-bold text-black">
                  {selectedClient.agent_count}
                </div>
              </div>
              <div className="bg-[#DAED6E] rounded-lg p-4">
                <div className="text-sm text-black font-bold">Total Calls</div>
                <div className="text-3xl font-bold text-black">
                  {selectedClient.total_calls}
                </div>
              </div>
              <div className="bg-[#DAED6E] rounded-lg p-4">
                <div className="text-sm text-black font-bold">Active Calls</div>
                <div className="text-3xl font-bold text-black">
                  {selectedClient.active_calls}
                </div>
              </div>
              <div className="bg-[#DAED6E] rounded-lg p-4">
                <div className="text-sm text-black font-bold">Last Call</div>
                <div className="text-sm font-bold text-black">
                  {formatDate(selectedClient.last_call)}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* All Agents */}
        <div className="bg-[#1E1E1E] rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-4">
            🤖 All Agents ({agents.length})
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-[#0A0A0A]">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                    Client
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                    Email
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {agents.slice(0, 10).map((agent) => (
                  <tr key={agent.id}>
                    <td className="px-4 py-3 text-sm text-white">{agent.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {agent.user_name || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {agent.user_email || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span
                        className={`px-2 py-1 rounded-full text-xs ${agent.is_active
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-500 text-white'
                          }`}
                      >
                        {agent.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent System Calls */}
        <div className="bg-[#1E1E1E] rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-4">
            📞 Recent System Calls ({calls.length})
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-[#0A0A0A]">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                    Time
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                    Client
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                    Phone
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                    Agent
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                    Duration
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {calls.map((call) => (
                  <tr key={call.id}>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {formatDate(call.created_at)}
                    </td>
                    <td className="px-4 py-3 text-sm text-white">
                      {call.user_name || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {call.to_number}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {call.agent_name || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span
                        className={`px-2 py-1 rounded-full text-xs text-white ${getStatusBadge(
                          call.status
                        )}`}
                      >
                        {call.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {formatDuration(call.duration)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Service Logs */}
        <div className="bg-[#1E1E1E] rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">
              🖥️ Service Logs
            </h2>
            <div className="flex space-x-2">
              <button
                onClick={() => setActiveLogTab('backend')}
                className={`px-3 py-1 text-sm rounded-lg transition ${activeLogTab === 'backend'
                    ? 'bg-[#DAED6E] text-black font-bold'
                    : 'bg-[#2A2A2A] text-gray-400 hover:text-white'
                  }`}
              >
                Backend
              </button>
              <button
                onClick={() => setActiveLogTab('voice-gateway')}
                className={`px-3 py-1 text-sm rounded-lg transition ${activeLogTab === 'voice-gateway'
                    ? 'bg-[#DAED6E] text-black font-bold'
                    : 'bg-[#2A2A2A] text-gray-400 hover:text-white'
                  }`}
              >
                Voice Gateway
              </button>
            </div>
          </div>
          <div className="bg-black rounded-lg p-4 font-mono text-xs overflow-x-auto h-96 border border-gray-800">
            {logLines.length > 0 ? (
              logLines.map((line, i) => (
                <div key={i} className="whitespace-pre-wrap text-green-500 mb-1">
                  <span className="text-gray-600 select-none mr-2">{i + 1}</span>
                  {line}
                </div>
              ))
            ) : (
              <div className="text-gray-500 italic">No logs available or loading...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
