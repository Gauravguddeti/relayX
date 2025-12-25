import { useState, useEffect } from 'react';
import { Phone, TrendingUp, Clock, CheckCircle, XCircle, PhoneCall, Plus, Users } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import StatCard from '../components/dashboard/StatCard';
import RecentCallsList from '../components/dashboard/RecentCallsList';
import UpcomingEvents from '../components/dashboard/UpcomingEvents';
import CalendarWidget from '../components/dashboard/CalendarWidget';
import NewCallModal from '../components/dashboard/NewCallModal';
import CampaignsList from '../components/dashboard/CampaignsList';
import CampaignCreateModal from '../components/CampaignCreateModal';
import { useAuth } from '../contexts/AuthContext';

interface DashboardStats {
  totalCalls: number;
  interestedCalls: number;
  notInterestedCalls: number;
  avgConfidence: number;
  todayCalls: number;
}

type TabType = 'calls' | 'campaigns';

export default function Dashboard() {
  const { userId } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('calls');
  const [stats, setStats] = useState<DashboardStats>({
    totalCalls: 0,
    interestedCalls: 0,
    notInterestedCalls: 0,
    avgConfidence: 0,
    todayCalls: 0,
  });
  const [loading, setLoading] = useState(true);
  const [showNewCallModal, setShowNewCallModal] = useState(false);
  const [showCampaignModal, setShowCampaignModal] = useState(false);

  useEffect(() => {
    if (userId) {
      fetchDashboardStats();
    }
  }, [userId]);

  useEffect(() => {
    const handleOpenModal = () => setShowCampaignModal(true);
    window.addEventListener('openCampaignModal', handleOpenModal);
    return () => window.removeEventListener('openCampaignModal', handleOpenModal);
  }, []);

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
            <h1 className="text-3xl font-bold text-text">Dashboard</h1>
            <p className="text-text-secondary mt-1">Welcome back! Here's how your assistant is performing.</p>
          </div>
          <button
            onClick={() => activeTab === 'calls' ? setShowNewCallModal(true) : setShowCampaignModal(true)}
            className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl font-medium"
          >
            <Plus className="w-5 h-5" />
            <span>{activeTab === 'calls' ? 'New Call' : 'New Campaign'}</span>
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 bg-white rounded-t-lg shadow-sm">
          <nav className="-mb-px flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('calls')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'calls'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Phone className="w-5 h-5" />
                <span>Recent Calls</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('campaigns')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'campaigns'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Users className="w-5 h-5" />
                <span>Campaigns</span>
              </div>
            </button>
          </nav>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Today's Calls"
            value={stats.todayCalls || 0}
            icon={<Phone className="w-6 h-6" />}
            color="blue"
            loading={loading}
          />
          <StatCard
            title="Total Calls"
            value={stats.totalCalls || 0}
            icon={<PhoneCall className="w-6 h-6" />}
            color="indigo"
            loading={loading}
          />
          <StatCard
            title="Interested"
            value={stats.interestedCalls || 0}
            icon={<CheckCircle className="w-6 h-6" />}
            color="green"
            loading={loading}
          />
          <StatCard
            title="Avg. Confidence"
            value={`${Math.round((stats.avgConfidence || 0) * 100)}%`}
            icon={<TrendingUp className="w-6 h-6" />}
            color="purple"
            loading={loading}
          />
        </div>

        {/* Content based on active tab */}
        {activeTab === 'calls' ? (
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
        ) : (
          <CampaignsList />
        )}
      </div>

      {/* New Call Modal */}
      <NewCallModal
        isOpen={showNewCallModal}
        onClose={() => setShowNewCallModal(false)}
        onSuccess={() => {
          fetchDashboardStats();
        }}
      />

      {/* New Campaign Modal */}
      <CampaignCreateModal
        isOpen={showCampaignModal}
        onClose={() => setShowCampaignModal(false)}
        onSuccess={() => {
          setActiveTab('campaigns');
        }}
      />
    </DashboardLayout>
  );
}
