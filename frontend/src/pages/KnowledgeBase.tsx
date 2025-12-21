import { useState, useEffect } from 'react';
import { Upload, Link as LinkIcon, Trash2, FileText, ExternalLink, Plus } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';

interface KnowledgeItem {
  id: string;
  agent_id: string;
  source_type: string;
  source_url?: string;
  content: string;
  created_at: string;
}

export default function KnowledgeBase() {
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [agentId, setAgentId] = useState<string>('');
  
  // URL input state
  const [showUrlForm, setShowUrlForm] = useState(false);
  const [url, setUrl] = useState('');
  const [urlLoading, setUrlLoading] = useState(false);

  // File upload state
  const [uploadLoading, setUploadLoading] = useState(false);

  useEffect(() => {
    fetchAgent();
  }, []);

  async function fetchAgent() {
    try {
      const response = await fetch('/api/agents');
      const agents = await response.json();
      if (agents.length > 0) {
        setAgentId(agents[0].id);
        fetchKnowledge(agents[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch agent:', error);
      setLoading(false);
    }
  }

  async function fetchKnowledge(id: string) {
    try {
      const response = await fetch(`/api/agents/${id}/knowledge`);
      const data = await response.json();
      setKnowledge(data);
    } catch (error) {
      console.error('Failed to fetch knowledge:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddUrl() {
    if (!url || !agentId) return;

    setUrlLoading(true);
    try {
      const response = await fetch('/api/knowledge/from-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agentId,
          url: url,
        }),
      });

      if (!response.ok) throw new Error('Failed to add URL');

      // Refresh knowledge list
      await fetchKnowledge(agentId);
      setUrl('');
      setShowUrlForm(false);
    } catch (error) {
      console.error('Failed to add URL:', error);
      alert('Failed to add URL. Please check the URL and try again.');
    } finally {
      setUrlLoading(false);
    }
  }

  async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const files = event.target.files;
    if (!files || files.length === 0 || !agentId) return;

    setUploadLoading(true);
    const formData = new FormData();
    formData.append('agent_id', agentId);
    formData.append('file', files[0]);

    try {
      const response = await fetch('/api/knowledge/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      // Refresh knowledge list
      await fetchKnowledge(agentId);
      
      // Reset file input
      event.target.value = '';
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload file. Please try again.');
    } finally {
      setUploadLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Are you sure you want to delete this knowledge item?')) return;

    try {
      const response = await fetch(`/api/knowledge/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Delete failed');

      // Refresh list
      await fetchKnowledge(agentId);
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete. Please try again.');
    }
  }

  function formatDate(dateString: string) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-gray-600 mt-1">
            Add information for your assistant to reference during calls
          </p>
        </div>

        {/* Add Knowledge Buttons */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Add Knowledge</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Add URL */}
            <button
              onClick={() => setShowUrlForm(!showUrlForm)}
              className="flex items-center justify-center space-x-3 px-6 py-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
            >
              <LinkIcon className="w-6 h-6 text-gray-400" />
              <span className="font-medium text-gray-700">Add from Website</span>
            </button>

            {/* Upload File */}
            <label className="flex items-center justify-center space-x-3 px-6 py-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors cursor-pointer">
              <Upload className="w-6 h-6 text-gray-400" />
              <span className="font-medium text-gray-700">
                {uploadLoading ? 'Uploading...' : 'Upload Document'}
              </span>
              <input
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleFileUpload}
                disabled={uploadLoading}
                className="hidden"
              />
            </label>
          </div>

          {/* URL Form */}
          {showUrlForm && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Website URL
              </label>
              <div className="flex space-x-2">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/about-us"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={handleAddUrl}
                  disabled={urlLoading || !url}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {urlLoading ? 'Adding...' : 'Add'}
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                We'll extract relevant information from this page
              </p>
            </div>
          )}
        </div>

        {/* Knowledge List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Your Knowledge</h2>
            <p className="text-sm text-gray-600 mt-1">
              {knowledge.length} {knowledge.length === 1 ? 'item' : 'items'}
            </p>
          </div>

          {knowledge.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 font-medium">No knowledge added yet</p>
              <p className="text-sm text-gray-500 mt-1">
                Add information about your business, services, or FAQs
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {knowledge.map((item) => (
                <div key={item.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <FileText className="w-5 h-5 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900 capitalize">
                          {item.source_type}
                        </span>
                        {item.source_url && (
                          <a
                            href={item.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {item.content.substring(0, 200)}...
                      </p>
                      <p className="text-xs text-gray-500 mt-2">
                        Added {formatDate(item.created_at)}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="ml-4 p-2 text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-medium text-blue-900 mb-1">How it works</h3>
          <p className="text-sm text-blue-800">
            Your assistant automatically uses this knowledge during calls to answer customer questions
            accurately. The more information you add, the better it can help your customers.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
