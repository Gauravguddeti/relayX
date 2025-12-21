import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Phone, Clock, CheckCircle, XCircle, PhoneMissed, PhoneIncoming } from 'lucide-react';

interface Call {
  id: string;
  to_number: string;
  status: string;
  duration: number;
  created_at: string;
  direction: string;
}

export default function RecentCallsList() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCalls();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchCalls, 30000);
    return () => clearInterval(interval);
  }, []);

  async function fetchCalls() {
    try {
      const response = await fetch('/calls?limit=10');
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

    const badge = badges[status as keyof typeof badges] || badges.completed;
    const Icon = badge.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {badge.text}
      </span>
    );
  }

  function formatDuration(seconds: number) {
    if (!seconds) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function formatDate(dateString: string) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  }

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="animate-pulse flex space-x-4">
            <div className="h-12 w-12 bg-gray-200 rounded-full"></div>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (calls.length === 0) {
    return (
      <div className="p-12 text-center">
        <Phone className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-600 font-medium">No calls yet</p>
        <p className="text-sm text-gray-500 mt-1">
          Your call history will appear here once you start making calls
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Contact
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Duration
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Time
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Action
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {calls.map((call) => (
            <tr key={call.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div className={`p-2 rounded-full ${call.direction === 'inbound' ? 'bg-blue-100' : 'bg-purple-100'}`}>
                    {call.direction === 'inbound' ? (
                      <PhoneIncoming className="w-4 h-4 text-blue-600" />
                    ) : (
                      <Phone className="w-4 h-4 text-purple-600" />
                    )}
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">{call.to_number}</p>
                    <p className="text-xs text-gray-500 capitalize">{call.direction}</p>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {getStatusBadge(call.status)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                <div className="flex items-center">
                  <Clock className="w-4 h-4 text-gray-400 mr-1" />
                  {formatDuration(call.duration)}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(call.created_at)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <button
                  onClick={() => navigate(`/dashboard/calls/${call.id}`)}
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  View Details
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
