import { useState, useEffect } from 'react';
import { Phone, TrendingUp, Clock, CheckCircle, XCircle, PhoneCall } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import StatCard from '../components/dashboard/StatCard';
import RecentCallsList from '../components/dashboard/RecentCallsList';

interface DashboardStats {
  totalCalls: number;
  interestedCalls: number;
  notInterestedCalls: number;
  avgConfidence: number;
  todayCalls: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalCalls: 0,
    interestedCalls: 0,
    notInterestedCalls: 0,
    avgConfidence: 0,
    todayCalls: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  async function fetchDashboardStats() {
    try {
      // Fetch recent calls (last 24h)
      const response = await fetch('/api/calls?limit=100');
      if (!response.ok) {
        console.error('Failed to fetch calls:', response.status);
        return;
      }
      const data = await response.json();
      const calls = Array.isArray(data) ? data : [];

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const todayCalls = calls.filter((call: any) => {
        const callDate = new Date(call.created_at);
        return callDate >= today;
      });

      const completed = calls.filter((c: any) => c.status === 'completed');
      
      // Calculate stats from call analysis
      let interestedCount = 0;
      let notInterestedCount = 0;
      let confidenceSum = 0;
      let confidenceCount = 0;

      for (const call of completed) {
        try {
          const analysisRes = await fetch(`/api/calls/${call.id}/analysis`);
          if (analysisRes.ok) {
            const analysis = await analysisRes.json();
            if (analysis.outcome?.toLowerCase().includes('interested')) interestedCount++;
            if (analysis.outcome?.toLowerCase().includes('not interested')) notInterestedCount++;
            if (analysis.confidence_score) {
              confidenceSum += analysis.confidence_score;
              confidenceCount++;
            }
          }
        } catch (e) {
          // Skip if analysis not available
        }
      }

      setStats({
        totalCalls: calls.length,
        interestedCalls: interestedCount,
        notInterestedCalls: notInterestedCount,
        avgConfidence: confidenceCount > 0 ? confidenceSum / confidenceCount : 0,
        todayCalls: todayCalls.length,
      });
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back! Here's how your assistant is performing.</p>
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

        {/* Recent Calls */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Recent Calls</h2>
            <p className="text-sm text-gray-600 mt-1">View and analyze your recent conversations</p>
          </div>
          <RecentCallsList />
        </div>
      </div>
    </DashboardLayout>
  );
}
