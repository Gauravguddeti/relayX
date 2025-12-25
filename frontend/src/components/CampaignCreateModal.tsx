import { useState, useEffect } from 'react';
import { X, Upload, FileText, AlertCircle, Check } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
}

interface CampaignCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function CampaignCreateModal({ isOpen, onClose, onSuccess }: CampaignCreateModalProps) {
  const [step, setStep] = useState<'upload' | 'settings'>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parseResult, setParseResult] = useState<any>(null);
  
  const [formData, setFormData] = useState({
    name: '',
    agentId: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    scheduledStartTime: '',
    enableBusinessHours: false,
    businessHoursStart: '09:00',
    businessHoursEnd: '17:00',
    businessDays: [1, 2, 3, 4, 5], // Mon-Fri
    pacingSeconds: 30,
    maxRetries: 2,
  });

  useEffect(() => {
    if (isOpen) {
      fetchAgents();
      // Set default campaign name with timestamp
      setFormData(prev => ({
        ...prev,
        name: `Campaign ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`,
      }));
    }
  }, [isOpen]);

  async function fetchAgents() {
    try {
      const response = await fetch('/agents', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAgents(data.agents || []);
        if (data.agents?.length > 0) {
          setFormData(prev => ({ ...prev, agentId: data.agents[0].id }));
        }
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    }
  }

  function handleDrag(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  }

  function handleFile(file: File) {
    const validTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/plain',
      'application/pdf'
    ];

    if (!validTypes.includes(file.type) && !file.name.match(/\.(csv|xlsx?|txt|pdf)$/i)) {
      setError('Please upload a CSV, Excel, TXT, or PDF file');
      return;
    }

    setFile(file);
    setError(null);
  }

  async function handleUploadAndParse() {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const formDataObj = new FormData();
      formDataObj.append('file', file);

      const response = await fetch('/campaigns/parse-preview', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        },
        body: formDataObj
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to parse file');
      }

      setParseResult(data);
      setStep('settings');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateCampaign() {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const formDataObj = new FormData();
      formDataObj.append('file', file);
      formDataObj.append('name', formData.name);
      formDataObj.append('agent_id', formData.agentId);
      formDataObj.append('timezone', formData.timezone);
      
      if (formData.scheduledStartTime) {
        formDataObj.append('scheduled_start_time', new Date(formData.scheduledStartTime).toISOString());
      }

      // Business hours settings
      const settings: any = {
        pacing_seconds: formData.pacingSeconds,
        max_retries: formData.maxRetries,
      };

      if (formData.enableBusinessHours) {
        settings.business_hours = {
          start: formData.businessHoursStart,
          end: formData.businessHoursEnd,
          days: formData.businessDays,
        };
      }

      formDataObj.append('settings', JSON.stringify(settings));

      const response = await fetch('/campaigns/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        },
        body: formDataObj
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create campaign');
      }

      onSuccess();
      handleClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleClose() {
    setStep('upload');
    setFile(null);
    setError(null);
    setParseResult(null);
    setFormData({
      name: '',
      agentId: '',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      scheduledStartTime: '',
      enableBusinessHours: false,
      businessHoursStart: '09:00',
      businessHoursEnd: '17:00',
      businessDays: [1, 2, 3, 4, 5],
      pacingSeconds: 30,
      maxRetries: 2,
    });
    onClose();
  }

  if (!isOpen) return null;

  const timezones = Intl.supportedValuesOf('timeZone');
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Create Campaign</h2>
            <p className="text-sm text-gray-600 mt-1">
              {step === 'upload' ? 'Upload your contact list' : 'Configure campaign settings'}
            </p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          )}

          {step === 'upload' ? (
            <div className="space-y-6">
              {/* File Upload */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                {file ? (
                  <div className="space-y-4">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full">
                      <Check className="w-8 h-8 text-green-600" />
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-gray-900">{file.name}</p>
                      <p className="text-sm text-gray-600">
                        {(file.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                    <button
                      onClick={() => setFile(null)}
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Choose different file
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full">
                      <Upload className="w-8 h-8 text-gray-600" />
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-gray-900 mb-2">
                        Drop your file here
                      </p>
                      <p className="text-sm text-gray-600 mb-4">
                        or click to browse
                      </p>
                      <input
                        type="file"
                        accept=".csv,.xlsx,.xls,.txt,.pdf"
                        onChange={handleFileInput}
                        className="hidden"
                        id="file-upload"
                      />
                      <label
                        htmlFor="file-upload"
                        className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer font-medium"
                      >
                        Select File
                      </label>
                    </div>
                    <p className="text-xs text-gray-500">
                      Supported formats: CSV, Excel (.xlsx, .xls), TXT, PDF
                    </p>
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <FileText className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 text-sm text-blue-800">
                    <p className="font-medium mb-2">File Format Tips:</p>
                    <ul className="list-disc list-inside space-y-1 text-blue-700">
                      <li>Include a column with phone numbers (we'll auto-detect it)</li>
                      <li>Optionally include name, email, or any custom fields</li>
                      <li>Phone numbers can be in any format (we'll normalize them)</li>
                      <li>All extra columns will be available during calls</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-3">
                <button
                  onClick={handleClose}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUploadAndParse}
                  disabled={!file || loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {loading ? 'Parsing...' : 'Next'}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Parse Results */}
              {parseResult && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-green-800 mb-2">
                        File parsed successfully!
                      </p>
                      <div className="text-sm text-green-700 space-y-1">
                        <p>✓ {parseResult.total_contacts} contacts found</p>
                        <p>✓ {parseResult.valid_contacts} valid phone numbers</p>
                        {parseResult.invalid_contacts > 0 && (
                          <p className="text-orange-700">
                            ⚠ {parseResult.invalid_contacts} contacts skipped (invalid phone)
                          </p>
                        )}
                        {parseResult.metadata_fields?.length > 0 && (
                          <p>
                            ✓ Extra fields: {parseResult.metadata_fields.join(', ')}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Campaign Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Campaign Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  placeholder="Enter campaign name"
                />
              </div>

              {/* Agent Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AI Agent
                </label>
                <select
                  value={formData.agentId}
                  onChange={(e) => setFormData({ ...formData, agentId: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                >
                  {agents.map((agent) => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Timezone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Timezone
                </label>
                <select
                  value={formData.timezone}
                  onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                >
                  {timezones.map((tz) => (
                    <option key={tz} value={tz}>
                      {tz}
                    </option>
                  ))}
                </select>
              </div>

              {/* Scheduled Start Time */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Scheduled Start Time (Optional)
                </label>
                <input
                  type="datetime-local"
                  value={formData.scheduledStartTime}
                  onChange={(e) => setFormData({ ...formData, scheduledStartTime: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Leave empty to start immediately
                </p>
              </div>

              {/* Business Hours */}
              <div className="border border-gray-300 rounded-lg p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Business Hours Only
                    </label>
                    <p className="text-xs text-gray-500 mt-1">
                      Only make calls during specified hours
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.enableBusinessHours}
                    onChange={(e) => setFormData({ ...formData, enableBusinessHours: e.target.checked })}
                    className="h-5 w-5 text-blue-600 rounded focus:ring-blue-500"
                  />
                </div>

                {formData.enableBusinessHours && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Start Time
                        </label>
                        <input
                          type="time"
                          value={formData.businessHoursStart}
                          onChange={(e) => setFormData({ ...formData, businessHoursStart: e.target.value })}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          End Time
                        </label>
                        <input
                          type="time"
                          value={formData.businessHoursEnd}
                          onChange={(e) => setFormData({ ...formData, businessHoursEnd: e.target.value })}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-2">
                        Days
                      </label>
                      <div className="flex items-center space-x-2">
                        {dayNames.map((day, index) => (
                          <button
                            key={index}
                            onClick={() => {
                              const days = formData.businessDays.includes(index)
                                ? formData.businessDays.filter(d => d !== index)
                                : [...formData.businessDays, index].sort();
                              setFormData({ ...formData, businessDays: days });
                            }}
                            className={`flex-1 py-2 text-xs font-medium rounded-lg transition-colors ${
                              formData.businessDays.includes(index)
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            {day}
                          </button>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Pacing */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Pacing: {formData.pacingSeconds} seconds between calls
                </label>
                <input
                  type="range"
                  min="5"
                  max="60"
                  step="5"
                  value={formData.pacingSeconds}
                  onChange={(e) => setFormData({ ...formData, pacingSeconds: parseInt(e.target.value) })}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>5s (Faster)</span>
                  <span>60s (Slower)</span>
                </div>
              </div>

              {/* Max Retries */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Retries for Failed Calls
                </label>
                <select
                  value={formData.maxRetries}
                  onChange={(e) => setFormData({ ...formData, maxRetries: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                >
                  <option value="0">No retries</option>
                  <option value="1">1 retry</option>
                  <option value="2">2 retries</option>
                  <option value="3">3 retries</option>
                </select>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-3 pt-4">
                <button
                  onClick={() => setStep('upload')}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  Back
                </button>
                <button
                  onClick={handleCreateCampaign}
                  disabled={loading || !formData.name || !formData.agentId}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {loading ? 'Creating...' : 'Create Campaign'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
