import { useState, useEffect } from 'react';
import { Plus, Play, Pause, Calendar, Settings as SettingsIcon, Trash2, Clock, Users as UsersIcon, CheckCircle, AlertCircle, RefreshCw, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import CampaignCreateModal from '../components/CampaignCreateModal';

interface Campaign {
  id: string;
  name: string;
  state: string;
  agent_id: string;
  timezone: string;
  scheduled_start_time: string | null;
  stats: {
    total: number;
    completed: number;
    failed: number;
    pending: number;
    calling: number;
    success_rate: number;
  };
  created_at: string;
  updated_at: string;
}

export default function Campaigns() {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCampaignModal, setShowCampaignModal] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    loadCampaigns();
  }, []);

  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  async function loadCampaigns() {
    try {
      setLoading(true);
      const response = await fetch('/campaigns', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        }
      });

      if (!response.ok) {
        console.error('Failed to load campaigns:', response.status);
        return;
      }

      const data = await response.json();
      setCampaigns(data.campaigns || []);
    } catch (error) {
      console.error('Failed to load campaigns:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleStartCampaign(campaignId: string) {
    try {
      const response = await fetch(`/campaigns/${campaignId}/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        }
      });

      if (response.ok) {
        setSuccessMessage('Campaign started successfully');
        loadCampaigns();
      }
    } catch (error) {
      console.error('Failed to start campaign:', error);
    }
  }

  async function handlePauseCampaign(campaignId: string) {
    try {
      const response = await fetch(`/campaigns/${campaignId}/pause`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        }
      });

      if (response.ok) {
        setSuccessMessage('Campaign paused');
        loadCampaigns();
      }
    } catch (error) {
      console.error('Failed to pause campaign:', error);
    }
  }

  async function handleDeleteCampaign(campaignId: string) {
    if (!confirm('Are you sure you want to delete this campaign? This cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/campaigns/${campaignId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        }
      });

      if (response.ok) {
        setSuccessMessage('Campaign deleted');
        loadCampaigns();
      }
    } catch (error) {
      console.error('Failed to delete campaign:', error);
    }
  }

  function getStateColor(state: string) {
    switch (state) {
      case 'draft': return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
      case 'pending': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'scheduled': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'running': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'paused': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'completed': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  }

  function getStateLabel(state: string) {
    return state.charAt(0).toUpperCase() + state.slice(1);
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
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
            <h1 className="text-3xl font-bold text-text">Campaigns</h1>
            <p className="text-text-secondary mt-1">Manage your bulk calling campaigns and scheduled jobs</p>
          </div>
          <button
            onClick={() => setShowCampaignModal(true)}
            className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>New Campaign</span>
          </button>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="text-green-800">{successMessage}</span>
            </div>
            <button
              onClick={() => setSuccessMessage('')}
              className="text-green-600 hover:text-green-800"
            >
              ×
            </button>
          </div>
        )}

        {/* Empty State */}
        {campaigns.length === 0 ? (
          <div className="bg-lighter rounded-lg shadow p-12 text-center border border-border">
            <UsersIcon className="w-16 h-16 text-text-secondary mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-text mb-2">No campaigns yet</h3>
            <p className="text-text-secondary mb-6">Create your first bulk calling campaign to get started</p>
            <button
              onClick={() => setShowCampaignModal(true)}
              className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-5 h-5" />
              <span>Create Your First Campaign</span>
            </button>
          </div>
        ) : (
          /* Campaign Cards */
          <div className="space-y-4">
            {campaigns.map((campaign) => (
              <div
                key={campaign.id}
                className="bg-lighter rounded-lg border border-border p-6 hover:shadow-lg transition-all"
              >
                <div className="flex items-start justify-between">
                  {/* Left: Campaign Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-text">{campaign.name}</h3>
                      <span className={`text-xs font-bold uppercase px-3 py-1 rounded-full border ${getStateColor(campaign.state)}`}>
                        {getStateLabel(campaign.state)}
                      </span>
                    </div>

                    {/* Stats Row */}
                    <div className="flex items-center gap-6 text-sm text-text-secondary mt-3">
                      <div className="flex items-center gap-2">
                        <UsersIcon className="w-4 h-4" />
                        <span>{campaign.stats.total} contacts</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span>{campaign.stats.completed} completed</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-yellow-400" />
                        <span>{campaign.stats.pending} pending</span>
                      </div>
                      {campaign.stats.failed > 0 && (
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-red-400" />
                          <span>{campaign.stats.failed} failed</span>
                        </div>
                      )}
                    </div>

                    {/* Progress Bar */}
                    {campaign.stats.total > 0 && (
                      <div className="mt-4">
                        <div className="flex items-center justify-between text-xs text-text-secondary mb-1">
                          <span>Progress</span>
                          <span>{Math.round((campaign.stats.completed / campaign.stats.total) * 100)}%</span>
                        </div>
                        <div className="w-full bg-darker rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full transition-all"
                            style={{ width: `${(campaign.stats.completed / campaign.stats.total) * 100}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Scheduled Time */}
                    {campaign.scheduled_start_time && (
                      <div className="mt-3 flex items-center gap-2 text-sm text-text-secondary">
                        <Calendar className="w-4 h-4" />
                        <span>Scheduled: {new Date(campaign.scheduled_start_time).toLocaleString()}</span>
                      </div>
                    )}
                  </div>

                  {/* Right: Actions */}
                  <div className="flex flex-col gap-2 ml-6">
                    {/* Primary Action */}
                    {campaign.state === 'draft' || campaign.state === 'pending' ? (
                      <button
                        onClick={() => handleStartCampaign(campaign.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        <Play className="w-4 h-4" />
                        <span>Start</span>
                      </button>
                    ) : campaign.state === 'running' ? (
                      <button
                        onClick={() => handlePauseCampaign(campaign.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
                      >
                        <Pause className="w-4 h-4" />
                        <span>Pause</span>
                      </button>
                    ) : campaign.state === 'paused' ? (
                      <button
                        onClick={() => handleStartCampaign(campaign.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        <Play className="w-4 h-4" />
                        <span>Resume</span>
                      </button>
                    ) : null}

                    {/* View Details */}
                    <button
                      onClick={() => navigate(`/campaigns/${campaign.id}`)}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <ArrowRight className="w-4 h-4" />
                      <span>View</span>
                    </button>

                    {/* Delete */}
                    <button
                      onClick={() => handleDeleteCampaign(campaign.id)}
                      className="flex items-center gap-2 px-4 py-2 bg-red-600/10 text-red-400 rounded-lg hover:bg-red-600/20 border border-red-600/20 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span>Delete</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Campaign Create Modal */}
      <CampaignCreateModal
        isOpen={showCampaignModal}
        onClose={() => setShowCampaignModal(false)}
        onSuccess={() => {
          setSuccessMessage('Campaign created successfully');
          setShowCampaignModal(false);
          loadCampaigns();
        }}
      />
    </DashboardLayout>
  );
}
