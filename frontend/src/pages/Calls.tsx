import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Phone, Clock, CheckCircle, XCircle, PhoneMissed, Search, Filter, Plus } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import NewCallModal from '../components/dashboard/NewCallModal';
import { useAuth } from '../contexts/AuthContext';

interface Call {
  id: string;
  to_number: string;
  status: string;
  duration: number;
  created_at: string;
  direction: string;
}

export default function Calls() {
  const { userId } = useAuth();
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showNewCallModal, setShowNewCallModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (userId) {
      fetchCalls();
    }
  }, [userId]);

  async function fetchCalls() {
    if (!userId) return;

    try {
      setLoading(true);
      // Fetch only current user's calls
      const response = await fetch(`/calls?user_id=${userId}&limit=100`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        }
      });
      if (!response.ok) {
        console.error('Failed to fetch calls:', response.status);
        setCalls([]);
        setLoading(false);
        return;
      }
      const data = await response.json();
      const callsList = Array.isArray(data) ? data : [];
      setCalls(callsList);
    } catch (error) {
      console.error('Failed to fetch calls:', error);
      setCalls([]);
    } finally {
      setLoading(false);
    }
  }

  function getStatusBadge(status: string) {
    const badges = {
      completed: { icon: CheckCircle, text: 'Completed', color: 'bg-green-100 text-green-800' },
      'in-progress': { icon: Phone, text: 'In Progress', color: 'bg-blue-100 text-blue-800' },
      failed: { icon: XCircle, text: 'Failed', color: 'bg-red-100 text-red-800' },
      'no-answer': { icon: PhoneMissed, text: 'No Answer', color: 'bg-yellow-100 text-yellow-800' },
      busy: { icon: PhoneMissed, text: 'Busy', color: 'bg-orange-100 text-orange-800' },
    };
    const badge = badges[status as keyof typeof badges] || badges.failed;
    const Icon = badge.icon;
    return (
      <span className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        <Icon className="w-3 h-3" />
        <span>{badge.text}</span>
      </span>
    );
  }

  function formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString();
  }

  const filteredCalls = calls
    .filter((call) => filter === 'all' || call.status === filter)
    .filter((call) => 
      searchTerm === '' || 
      call.to_number.includes(searchTerm) || 
      call.id.toLowerCase().includes(searchTerm.toLowerCase())
    );

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-text">Call History</h1>
            <p className="text-gray-600 mt-1">View and manage all your calls</p>
          </div>
          <button
            onClick={() => setShowNewCallModal(true)}
            className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl font-medium"
          >
            <Plus className="w-5 h-5" />
            <span>New Call</span>
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-4 items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by phone number or call ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Calls</option>
              <option value="completed">Completed</option>
              <option value="in-progress">In Progress</option>
              <option value="failed">Failed</option>
              <option value="no-answer">No Answer</option>
              <option value="busy">Busy</option>
            </select>
          </div>
        </div>

        {/* Calls Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Phone Number
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Direction
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredCalls.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                      {searchTerm || filter !== 'all' ? 'No calls match your filters' : 'No calls yet'}
                    </td>
                  </tr>
                ) : (
                  filteredCalls.map((call) => (
                    <tr
                      key={call.id}
                      onClick={() => navigate(`/dashboard/calls/${call.id}`)}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Phone className="w-4 h-4 text-gray-400 mr-2" />
                          <span className="text-sm font-medium text-gray-900">{call.to_number}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(call.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-500">
                          <Clock className="w-4 h-4 mr-1" />
                          {formatDuration(call.duration)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(call.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm ${call.direction === 'outbound' ? 'text-blue-600' : 'text-green-600'}`}>
                          {call.direction === 'outbound' ? 'Outbound' : 'Inbound'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* New Call Modal */}
      <NewCallModal
        isOpen={showNewCallModal}
        onClose={() => setShowNewCallModal(false)}
        onSuccess={() => {
          fetchCalls();
        }}
      />
    </DashboardLayout>
  );
}
