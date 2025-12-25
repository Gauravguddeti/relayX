import { useState, useEffect } from 'react';
import { Calendar, Play, Pause, Eye, Trash2, Users, Phone, TrendingUp, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Campaign {
  id: string;
  name: string;
  state: 'draft' | 'pending' | 'running' | 'paused' | 'completed' | 'failed';
  stats: {
    total: number;
    pending: number;
    calling: number;
    completed: number;
    failed: number;
    success_rate?: number;
  };
  scheduled_start_time: string | null;
  created_at: string;
  agent_name?: string;
}

const stateConfig = {
  draft: { label: 'Draft', color: 'gray', bgColor: 'bg-gray-100', textColor: 'text-gray-800' },
  pending: { label: 'Scheduled', color: 'yellow', bgColor: 'bg-yellow-100', textColor: 'text-yellow-800' },
  running: { label: 'Running', color: 'blue', bgColor: 'bg-blue-100', textColor: 'text-blue-800' },
  paused: { label: 'Paused', color: 'orange', bgColor: 'bg-orange-100', textColor: 'text-orange-800' },
  completed: { label: 'Completed', color: 'green', bgColor: 'bg-green-100', textColor: 'text-green-800' },
  failed: { label: 'Failed', color: 'red', bgColor: 'bg-red-100', textColor: 'text-red-800' },
};

export default function CampaignsList() {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    fetchCampaigns();
    const interval = setInterval(fetchCampaigns, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  async function fetchCampaigns() {
    try {
      const response = await fetch('/campaigns', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCampaigns(data.campaigns || []);
      }
    } catch (error) {
      console.error('Failed to fetch campaigns:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleAction(campaignId: string, action: 'start' | 'pause' | 'delete') {
    setActionLoading(campaignId);
    try {
      const endpoint = action === 'delete' ? `/campaigns/${campaignId}` : `/campaigns/${campaignId}/${action}`;
      const response = await fetch(endpoint, {
        method: action === 'delete' ? 'DELETE' : 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        }
      });

      if (response.ok) {
        await fetchCampaigns();
      }
    } catch (error) {
      console.error(`Failed to ${action} campaign:`, error);
    } finally {
      setActionLoading(null);
    }
  }

  function getProgressPercentage(stats: Campaign['stats']) {
    if (stats.total === 0) return 0;
    return ((stats.completed + stats.failed) / stats.total) * 100;
  }

  function groupCampaignsByDate(campaigns: Campaign[]) {
    const groups: { [key: string]: Campaign[] } = {};
    
    campaigns.forEach(campaign => {
      const date = new Date(campaign.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
      
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(campaign);
    });

    return groups;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (campaigns.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No campaigns yet</h3>
        <p className="text-gray-600 mb-6">Create your first bulk calling campaign to get started</p>
        <button
          onClick={() => window.dispatchEvent(new CustomEvent('openCampaignModal'))}
          className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl font-medium"
        >
          <Users className="w-5 h-5 mr-2" />
          Click here to start your first campaign
        </button>
      </div>
    );
  }

  const groupedCampaigns = groupCampaignsByDate(campaigns);

  return (
    <div className="space-y-8">
      {Object.entries(groupedCampaigns).map(([date, dateCampaigns]) => (
        <div key={date}>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            <span>{date}</span>
          </h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {dateCampaigns.map((campaign) => {
              const config = stateConfig[campaign.state];
              const progress = getProgressPercentage(campaign.stats);

              return (
                <div
                  key={campaign.id}
                  className="bg-white rounded-lg shadow-md hover:shadow-xl transition-all border border-gray-200 hover:border-blue-300"
                >
                  {/* Header */}
                  <div className="p-6 border-b border-gray-200">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h4 className="text-lg font-semibold text-gray-900 mb-1">
                          {campaign.name}
                        </h4>
                        {campaign.agent_name && (
                          <p className="text-sm text-gray-600">Agent: {campaign.agent_name}</p>
                        )}
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor}`}>
                        {config.label}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-3">
                      <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                        <span>Progress</span>
                        <span>{Math.round(progress)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            campaign.state === 'running' ? 'bg-blue-600' :
                            campaign.state === 'completed' ? 'bg-green-600' :
                            campaign.state === 'failed' ? 'bg-red-600' :
                            'bg-gray-400'
                          }`}
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                    </div>

                    {/* Scheduled Time */}
                    {campaign.scheduled_start_time && campaign.state === 'pending' && (
                      <div className="flex items-center space-x-2 text-sm text-gray-600 mt-2">
                        <Clock className="w-4 h-4" />
                        <span>
                          Starts: {new Date(campaign.scheduled_start_time).toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Stats */}
                  <div className="p-6 bg-gray-50 grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="flex items-center justify-center space-x-1 text-gray-600 mb-1">
                        <Users className="w-4 h-4" />
                        <span className="text-xs">Total</span>
                      </div>
                      <p className="text-2xl font-bold text-gray-900">{campaign.stats.total}</p>
                    </div>

                    <div className="text-center">
                      <div className="flex items-center justify-center space-x-1 text-blue-600 mb-1">
                        <Phone className="w-4 h-4" />
                        <span className="text-xs">Completed</span>
                      </div>
                      <p className="text-2xl font-bold text-blue-600">{campaign.stats.completed}</p>
                    </div>

                    {campaign.stats.success_rate !== undefined && (
                      <div className="text-center col-span-2">
                        <div className="flex items-center justify-center space-x-1 text-green-600 mb-1">
                          <TrendingUp className="w-4 h-4" />
                          <span className="text-xs">Success Rate</span>
                        </div>
                        <p className="text-2xl font-bold text-green-600">
                          {Math.round(campaign.stats.success_rate * 100)}%
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="p-4 border-t border-gray-200 flex items-center justify-end space-x-2">
                    {/* View Details */}
                    <button
                      onClick={() => navigate(`/campaigns/${campaign.id}`)}
                      className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="View Details"
                    >
                      <Eye className="w-5 h-5" />
                    </button>

                    {/* Start/Pause */}
                    {(campaign.state === 'draft' || campaign.state === 'paused') && (
                      <button
                        onClick={() => handleAction(campaign.id, 'start')}
                        disabled={actionLoading === campaign.id}
                        className="p-2 text-green-600 hover:text-green-700 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Start Campaign"
                      >
                        {actionLoading === campaign.id ? (
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-green-600" />
                        ) : (
                          <Play className="w-5 h-5" />
                        )}
                      </button>
                    )}

                    {campaign.state === 'running' && (
                      <button
                        onClick={() => handleAction(campaign.id, 'pause')}
                        disabled={actionLoading === campaign.id}
                        className="p-2 text-orange-600 hover:text-orange-700 hover:bg-orange-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Pause Campaign"
                      >
                        {actionLoading === campaign.id ? (
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-orange-600" />
                        ) : (
                          <Pause className="w-5 h-5" />
                        )}
                      </button>
                    )}

                    {/* Delete */}
                    {(campaign.state === 'draft' || campaign.state === 'paused' || campaign.state === 'completed' || campaign.state === 'failed') && (
                      <button
                        onClick={() => {
                          if (window.confirm(`Are you sure you want to delete "${campaign.name}"?`)) {
                            handleAction(campaign.id, 'delete');
                          }
                        }}
                        disabled={actionLoading === campaign.id}
                        className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Delete Campaign"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
