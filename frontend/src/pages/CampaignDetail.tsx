import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Pause, Download, Phone, CheckCircle, XCircle, Clock, User, Globe, Calendar, Edit2, Check, X, Trash2, Upload, UserPlus } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import { useAuth } from '../contexts/AuthContext';

interface Campaign {
  id: string;
  name: string;
  state: string;
  agent_id: string;
  timezone: string;
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
  settings_snapshot: any;
}

interface Contact {
  id: string;
  phone: string;
  name: string | null;
  metadata: any;
  state: string;
  outcome: string | null;
  retry_count: number;
  last_attempted_at: string | null;
  call_id: string | null;
}

const stateColors = {
  pending: 'bg-gray-100 text-gray-800',
  calling: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const outcomeLabels: any = {
  'completed': 'Completed',
  'no-answer': 'No Answer',
  'busy': 'Busy',
  'failed': 'Failed',
  'voicemail': 'Voicemail',
};

export default function CampaignDetail() {
  const { campaignId } = useParams();
  const navigate = useNavigate();
  const { userId } = useAuth();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [filterState, setFilterState] = useState<string>('all');
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [showAddContactsModal, setShowAddContactsModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [addContactsLoading, setAddContactsLoading] = useState(false);
  const [addContactsError, setAddContactsError] = useState('');
  const [addContactsSuccess, setAddContactsSuccess] = useState('');

  useEffect(() => {
    fetchCampaignData();
    const interval = setInterval(fetchCampaignData, 5000);
    return () => clearInterval(interval);
  }, [campaignId]);

  async function fetchCampaignData() {
    try {
      const [campaignRes, contactsRes] = await Promise.all([
        fetch(`/campaigns/${campaignId}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('relayx_token')}` }
        }),
        fetch(`/campaigns/${campaignId}/contacts`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('relayx_token')}` }
        })
      ]);

      // Handle 401 - redirect to login
      if (campaignRes.status === 401 || contactsRes.status === 401) {
        navigate('/login');
        return;
      }

      if (campaignRes.ok) {
        const campaignData = await campaignRes.json();
        setCampaign(campaignData);
      }

      if (contactsRes.ok) {
        const contactsData = await contactsRes.json();
        setContacts(contactsData.contacts || []);
      }
    } catch (error) {
      console.error('Failed to fetch campaign data:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleAction(action: 'start' | 'pause') {
    setActionLoading(true);
    try {
      const response = await fetch(`/campaigns/${campaignId}/${action}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('relayx_token')}` }
      });

      if (response.ok) {
        await fetchCampaignData();
      }
    } catch (error) {
      console.error(`Failed to ${action} campaign:`, error);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleRename() {
    if (!editedName.trim() || editedName === campaign?.name) {
      setIsEditingName(false);
      return;
    }

    try {
      const response = await fetch(`/campaigns/${campaignId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: editedName.trim() })
      });

      if (response.ok) {
        await fetchCampaignData();
        setIsEditingName(false);
      }
    } catch (error) {
      console.error('Failed to rename campaign:', error);
    }
  }

  async function handleDeleteCampaign() {
    if (!confirm('Are you sure you want to permanently delete this campaign? This action cannot be undone and will delete all campaign data and contacts.')) {
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
        navigate('/dashboard/contacts');
      }
    } catch (error) {
      console.error('Failed to delete campaign:', error);
    }
  }

  async function handleAddContacts() {
    if (!uploadFile) return;

    setAddContactsLoading(true);
    setAddContactsError('');
    setAddContactsSuccess('');

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);

      const response = await fetch(`/campaigns/${campaignId}/add-contacts`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        },
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to add contacts');
      }

      setAddContactsSuccess(`Added ${data.added_count} new contacts. ${data.skipped_duplicates > 0 ? `Skipped ${data.skipped_duplicates} duplicates.` : ''}`);
      setUploadFile(null);
      await fetchCampaignData();
      
      // Close modal after 2 seconds
      setTimeout(() => {
        setShowAddContactsModal(false);
        setAddContactsSuccess('');
      }, 2000);
    } catch (err: any) {
      setAddContactsError(err.message);
    } finally {
      setAddContactsLoading(false);
    }
  }

  function exportToCSV() {
    if (!contacts.length) return;

    const headers = ['Phone', 'Name', 'State', 'Outcome', 'Retry Count', 'Last Attempted'];
    const rows = filteredContacts.map(c => [
      c.phone,
      c.name || '',
      c.state,
      c.outcome || '',
      c.retry_count,
      c.last_attempted_at ? new Date(c.last_attempted_at).toLocaleString() : ''
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `campaign-${campaign?.name}-${new Date().toISOString()}.csv`;
    a.click();
  }

  if (loading || !campaign) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  const filteredContacts = filterState === 'all'
    ? contacts
    : contacts.filter(c => c.state === filterState);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-6 h-6 text-gray-600" />
            </button>
            <div>
              {isEditingName ? (
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={editedName}
                    onChange={(e) => setEditedName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleRename();
                      if (e.key === 'Escape') setIsEditingName(false);
                    }}
                    className="text-3xl font-bold text-gray-900 border-b-2 border-blue-500 focus:outline-none px-2 bg-transparent"
                    autoFocus
                  />
                  <button
                    onClick={handleRename}
                    className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                  >
                    <Check className="w-6 h-6" />
                  </button>
                  <button
                    onClick={() => setIsEditingName(false)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-2 group">
                  <h1 className="text-3xl font-bold text-gray-900">{campaign.name}</h1>
                  <button
                    onClick={() => {
                      setEditedName(campaign.name);
                      setIsEditingName(true);
                    }}
                    className="p-2 opacity-0 group-hover:opacity-100 text-gray-600 hover:bg-gray-100 rounded-lg transition-all"
                    title="Rename campaign"
                  >
                    <Edit2 className="w-5 h-5" />
                  </button>
                </div>
              )}
              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <Globe className="w-4 h-4" />
                  <span>{campaign.timezone}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Calendar className="w-4 h-4" />
                  <span>Created {new Date(campaign.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowAddContactsModal(true)}
              className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              <UserPlus className="w-5 h-5" />
              <span>Add Contacts</span>
            </button>

            {campaign.state === 'running' && (
              <button
                onClick={() => handleAction('pause')}
                disabled={actionLoading}
                className="flex items-center space-x-2 px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 font-medium"
              >
                <Pause className="w-5 h-5" />
                <span>Pause</span>
              </button>
            )}

            {(campaign.state === 'draft' || campaign.state === 'paused') && (
              <button
                onClick={() => handleAction('start')}
                disabled={actionLoading}
                className="flex items-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 font-medium"
              >
                <Play className="w-5 h-5" />
                <span>Start</span>
              </button>
            )}

            <button
              onClick={exportToCSV}
              className="flex items-center space-x-2 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              <Download className="w-5 h-5" />
              <span>Export CSV</span>
            </button>

            <button
              onClick={handleDeleteCampaign}
              className="flex items-center space-x-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
              title="Delete campaign permanently"
            >
              <Trash2 className="w-5 h-5" />
              <span>Delete</span>
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Total Contacts</span>
              <User className="w-5 h-5 text-gray-400" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{campaign.stats.total}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Pending</span>
              <Clock className="w-5 h-5 text-gray-400" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{campaign.stats.pending}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Completed</span>
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
            <p className="text-3xl font-bold text-green-600">{campaign.stats.completed}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Success Rate</span>
              <Phone className="w-5 h-5 text-blue-500" />
            </div>
            <p className="text-3xl font-bold text-blue-600">
              {campaign.stats.success_rate ? Math.round(campaign.stats.success_rate * 100) : 0}%
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900">Campaign Progress</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              campaign.state === 'running' ? 'bg-blue-100 text-blue-800' :
              campaign.state === 'paused' ? 'bg-orange-100 text-orange-800' :
              campaign.state === 'completed' ? 'bg-green-100 text-green-800' :
              campaign.state === 'failed' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {campaign.state.charAt(0).toUpperCase() + campaign.state.slice(1)}
            </span>
          </div>
          
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className={`h-4 rounded-full transition-all ${
                campaign.state === 'running' ? 'bg-blue-600' :
                campaign.state === 'completed' ? 'bg-green-600' :
                'bg-gray-400'
              }`}
              style={{
                width: `${((campaign.stats.completed + campaign.stats.failed) / campaign.stats.total) * 100}%`
              }}
            />
          </div>

          <div className="flex items-center justify-between text-sm text-gray-600 mt-2">
            <span>{campaign.stats.completed + campaign.stats.failed} / {campaign.stats.total} calls attempted</span>
            <span>{campaign.stats.pending} remaining</span>
          </div>
        </div>

        {/* Contacts Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Contacts</h2>
              
              {/* Filter Buttons */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setFilterState('all')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filterState === 'all'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All ({contacts.length})
                </button>
                <button
                  onClick={() => setFilterState('pending')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filterState === 'pending'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Pending ({contacts.filter(c => c.state === 'pending').length})
                </button>
                <button
                  onClick={() => setFilterState('completed')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filterState === 'completed'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Completed ({contacts.filter(c => c.state === 'completed').length})
                </button>
                <button
                  onClick={() => setFilterState('failed')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filterState === 'failed'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Failed ({contacts.filter(c => c.state === 'failed').length})
                </button>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Phone
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    State
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Outcome
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Retries
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Attempted
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredContacts.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                      No contacts found
                    </td>
                  </tr>
                ) : (
                  filteredContacts.map((contact) => (
                    <tr
                      key={contact.id}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => {
                        if (contact.call_id) {
                          navigate(`/dashboard/calls/${contact.call_id}`);
                        }
                      }}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {contact.name || 'Unknown'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{contact.phone}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          stateColors[contact.state as keyof typeof stateColors] || 'bg-gray-100 text-gray-800'
                        }`}>
                          {contact.state}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {contact.outcome ? outcomeLabels[contact.outcome] || contact.outcome : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{contact.retry_count}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          {contact.last_attempted_at
                            ? new Date(contact.last_attempted_at).toLocaleString()
                            : '-'}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Add Contacts Modal */}
      {showAddContactsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">Add Contacts</h3>
              <button
                onClick={() => {
                  setShowAddContactsModal(false);
                  setUploadFile(null);
                  setAddContactsError('');
                  setAddContactsSuccess('');
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <p className="text-sm text-gray-600 mb-4">
              Upload a CSV file to add more contacts to this campaign. Duplicate phone numbers will be skipped automatically.
            </p>

            {addContactsError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">{addContactsError}</p>
              </div>
            )}

            {addContactsSuccess && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">{addContactsSuccess}</p>
              </div>
            )}

            <div className="mb-4">
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none p-2"
              />
              {uploadFile && (
                <p className="mt-2 text-sm text-gray-600">
                  Selected: {uploadFile.name} ({(uploadFile.size / 1024).toFixed(2)} KB)
                </p>
              )}
            </div>

            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => {
                  setShowAddContactsModal(false);
                  setUploadFile(null);
                  setAddContactsError('');
                  setAddContactsSuccess('');
                }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddContacts}
                disabled={!uploadFile || addContactsLoading}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Upload className="w-5 h-5" />
                <span>{addContactsLoading ? 'Adding...' : 'Add Contacts'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
