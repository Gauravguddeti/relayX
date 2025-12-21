import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Calendar, Send, Link as LinkIcon } from 'lucide-react';

interface CalendlyStatus {
  configured: boolean;
  user?: {
    name: string;
    email: string;
    slug: string;
  };
  event_type_url?: string;
  message?: string;
}

interface SchedulingLinkRequest {
  name: string;
  email: string;
  phone?: string;
  notes?: string;
}

export default function CalendlyIntegration() {
  const [status, setStatus] = useState<CalendlyStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState<SchedulingLinkRequest>({
    name: '',
    email: '',
    phone: '',
    notes: ''
  });
  const [generatedLink, setGeneratedLink] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await fetch('/calendly/status');
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      console.error('Error checking Calendly status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLink = async () => {
    setError('');
    setSuccess('');
    setGeneratedLink('');

    if (!formData.name || !formData.email) {
      setError('Name and email are required');
      return;
    }

    try {
      const response = await fetch('/calendly/create-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to create link');
      }

      const data = await response.json();
      setGeneratedLink(data.scheduling_url);
      setSuccess('Scheduling link created successfully!');
    } catch (err) {
      setError('Failed to create scheduling link');
      console.error(err);
    }
  };

  const handleSendSMS = async () => {
    setError('');
    setSuccess('');

    if (!formData.name || !formData.email || !formData.phone) {
      setError('Name, email, and phone are required to send SMS');
      return;
    }

    try {
      const response = await fetch('/calendly/send-link-sms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          phone: formData.phone
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send SMS');
      }

      setSuccess('Scheduling link sent via SMS!');
      setFormData({ name: '', email: '', phone: '', notes: '' });
    } catch (err) {
      setError('Failed to send SMS');
      console.error(err);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedLink);
    setSuccess('Link copied to clipboard!');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Status Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Calendar className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Calendly Integration</h1>
                <p className="text-gray-600">Book appointments directly from your calls</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {status?.configured ? (
                <>
                  <CheckCircle className="w-6 h-6 text-green-500" />
                  <span className="text-green-600 font-medium">Connected</span>
                </>
              ) : (
                <>
                  <XCircle className="w-6 h-6 text-red-500" />
                  <span className="text-red-600 font-medium">Not Configured</span>
                </>
              )}
            </div>
          </div>

          {status?.user && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>Connected as:</strong> {status.user.name} ({status.user.email})
              </p>
              {status.event_type_url && (
                <p className="text-sm text-gray-700 mt-1">
                  <strong>Event URL:</strong>{' '}
                  <a
                    href={status.event_type_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {status.event_type_url}
                  </a>
                </p>
              )}
            </div>
          )}

          {!status?.configured && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                Calendly is not configured. Please add CALENDLY_API_TOKEN and CALENDLY_EVENT_TYPE_URL
                to your .env file and restart the backend.
              </p>
            </div>
          )}
        </div>

        {/* Create Scheduling Link */}
        {status?.configured && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create Scheduling Link</h2>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            {success && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                {success}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email *
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="john@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone (optional)
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="+1234567890"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notes (optional)
                </label>
                <input
                  type="text"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Demo request"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleCreateLink}
                className="flex-1 flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                <LinkIcon className="w-5 h-5" />
                Generate Link
              </button>

              <button
                onClick={handleSendSMS}
                disabled={!formData.phone}
                className="flex-1 flex items-center justify-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-5 h-5" />
                Send via SMS
              </button>
            </div>

            {/* Generated Link Display */}
            {generatedLink && (
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-700 mb-2">Generated Link:</p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={generatedLink}
                    readOnly
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-white text-sm"
                  />
                  <button
                    onClick={copyToClipboard}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Copy
                  </button>
                </div>
              </div>
            )}

            {/* How to Use */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-2">How to Use:</h3>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• <strong>Generate Link:</strong> Creates a pre-filled Calendly link you can share</li>
                <li>• <strong>Send via SMS:</strong> Instantly sends the booking link to the prospect's phone</li>
                <li>• Use during calls to schedule follow-ups or demos</li>
                <li>• Links pre-fill prospect information for faster booking</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
