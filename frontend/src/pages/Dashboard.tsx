import { useState, useEffect } from 'react';
import { Phone, TrendingUp, Clock, CheckCircle, XCircle, PhoneCall, Plus } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import StatCard from '../components/dashboard/StatCard';
import RecentCallsList from '../components/dashboard/RecentCallsList';
import UpcomingEvents from '../components/dashboard/UpcomingEvents';
import CalendarWidget from '../components/dashboard/CalendarWidget';
import NewCallModal from '../components/dashboard/NewCallModal';
import { useAuth } from '../contexts/AuthContext';

interface DashboardStats {
  totalCalls: number;
  interestedCalls: number;
  notInterestedCalls: number;
  avgConfidence: number;
  todayCalls: number;
}

export default function Dashboard() {
  const { userId } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalCalls: 0,
    interestedCalls: 0,
    notInterestedCalls: 0,
    avgConfidence: 0,
    todayCalls: 0,
  });
  const [loading, setLoading] = useState(true);
  const [showNewCallModal, setShowNewCallModal] = useState(false);

  useEffect(() => {
    if (userId) {
      fetchDashboardStats();
    }
  }, [userId]);

  async function fetchDashboardStats() {
    if (!userId) return;

    try {
      setLoading(true);
      // Use the optimized dashboard stats endpoint
      const response = await fetch('/dashboard/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        }
      });
      
      if (!response.ok) {
        console.error('Failed to fetch dashboard stats:', response.status);
        setLoading(false);
        return;
      }
      
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  }
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
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-1">Welcome back! Here's how your assistant is performing.</p>
          </div>
          <button
            onClick={() => setShowNewCallModal(true)}
            className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl font-medium"
          >
            <Plus className="w-5 h-5" />
            <span>New Call</span>
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Today's Calls"
            value={stats.todayCalls}
            icon={<Phone className="w-6 h-6" />}
            color="blue"
            loading={loading}
          />
          <StatCard
            title="Total Calls"
            value={stats.totalCalls}
            icon={<PhoneCall className="w-6 h-6" />}
            color="indigo"
            loading={loading}
          />
          <StatCard
            title="Interested"
            value={stats.interestedCalls}
            icon={<CheckCircle className="w-6 h-6" />}
            color="green"
            loading={loading}
          />
          <StatCard
            title="Avg. Confidence"
            value={`${Math.round(stats.avgConfidence * 100)}%`}
            icon={<TrendingUp className="w-6 h-6" />}
            color="purple"
            loading={loading}
          />
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Calls - Takes 2 columns */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Recent Calls</h2>
                <p className="text-sm text-gray-600 mt-1">View and analyze your recent conversations</p>
              </div>
              <RecentCallsList />
            </div>
          </div>

          {/* Sidebar - Takes 1 column */}
          <div className="lg:col-span-1 space-y-6">
            {/* Upcoming Events */}
            <UpcomingEvents />
            
            {/* Cal.com Calendar Widget */}
            <CalendarWidget />
          </div>
        </div>
      </div>

      {/* New Call Modal */}
      <NewCallModal
        isOpen={showNewCallModal}
        onClose={() => setShowNewCallModal(false)}
        onSuccess={() => {
          fetchDashboardStats();
        }}
      />
    </DashboardLayout>
  );
}
