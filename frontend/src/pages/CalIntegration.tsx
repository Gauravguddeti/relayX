import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Calendar, Send, Link as LinkIcon, Loader2 } from 'lucide-react';

interface CalStatus {
  configured: boolean;
  user?: {
    name: string;
    email: string;
    username: string;
  };
  event_types?: Array<{
    id: number;
    title: string;
    slug: string;
    length: number;
  }>;
  message?: string;
}

interface BookingForm {
  name: string;
  email: string;
  phone: string;
  notes: string;
  eventTypeId: number;
  eventTypeSlug: string;
  username: string;
}

export default function CalIntegration() {
  const [status, setStatus] = useState<CalStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState<BookingForm>({
    name: '',
    email: '',
    phone: '',
    notes: '',
    eventTypeId: 0,
    eventTypeSlug: '',
    username: ''
  });
  const [generatedLink, setGeneratedLink] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await fetch('/cal/status');
      const data = await response.json();
      setStatus(data);

      // Auto-select first event type
      if (data.event_types && data.event_types.length > 0) {
        const firstEvent = data.event_types[0];
        setFormData(prev => ({
          ...prev,
          eventTypeId: firstEvent.id,
          eventTypeSlug: firstEvent.slug,
          username: data.user?.username || ''
        }));
      }
    } catch (err) {
      console.error('Error checking Cal.com status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLink = async () => {
    setError('');
    setSuccess('');
    setGeneratedLink('');
    setActionLoading(true);

    if (!formData.name || !formData.email) {
      setError('Name and email are required');
      setActionLoading(false);
      return;
    }

    try {
      const response = await fetch('/cal/create-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type_slug: formData.eventTypeSlug,
          username: formData.username,
          name: formData.name,
          email: formData.email
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create link');
      }

      const data = await response.json();
      setGeneratedLink(data.booking_url);
      setSuccess('Booking link created successfully!');
    } catch (err) {
      setError('Failed to create booking link');
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSendSMS = async () => {
    setError('');
    setSuccess('');
    setActionLoading(true);

    if (!formData.name || !formData.email || !formData.phone) {
      setError('Name, email, and phone are required to send SMS');
      setActionLoading(false);
      return;
    }

    // Generate link first
    const linkResponse = await fetch('/cal/create-link', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type_slug: formData.eventTypeSlug,
        username: formData.username,
        name: formData.name,
        email: formData.email
      })
    });

    if (!linkResponse.ok) {
      setError('Failed to generate link');
      setActionLoading(false);
      return;
    }

    const linkData = await linkResponse.json();

    try {
      // Ensure phone number has country code
      let phoneNumber = formData.phone;
      if (!phoneNumber.startsWith('+')) {
        phoneNumber = '+' + phoneNumber;
      }

      const response = await fetch('/cal/send-link-sms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          phone: phoneNumber,
          booking_url: linkData.booking_url
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send SMS');
      }

      setSuccess('Booking link sent via SMS!');
      setFormData({
        name: '',
        email: '',
        phone: '',
        notes: '',
        eventTypeId: formData.eventTypeId,
        eventTypeSlug: formData.eventTypeSlug,
        username: formData.username
      });
    } catch (err) {
      setError('Failed to send SMS');
      console.error(err);
    } finally {
      setActionLoading(false);
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
                <h1 className="text-2xl font-bold text-gray-900">Cal.com Integration</h1>
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
              <p className="text-sm text-gray-700 mt-1">
                <strong>Username:</strong> {status.user.username}
              </p>
            </div>
          )}

          {status?.event_types && status.event_types.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Available Event Types:</p>
              <div className="space-y-2">
                {status.event_types.map((et) => (
                  <div key={et.id} className="p-3 bg-gray-50 rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{et.title}</p>
                      <p className="text-sm text-gray-600">{et.length} minutes</p>
                    </div>
                    <span className="text-xs text-gray-500">/{et.slug}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!status?.configured && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                Cal.com is not configured. Please add CAL_API_KEY to your .env file and restart the backend.
              </p>
            </div>
          )}
        </div>

        {/* Create Booking Link */}
        {status?.configured && status.event_types && status.event_types.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create Booking Link</h2>

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

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Event Type *
              </label>
              <select
                value={formData.eventTypeId}
                onChange={(e) => {
                  const selectedId = parseInt(e.target.value);
                  const selectedEvent = status.event_types?.find(et => et.id === selectedId);
                  if (selectedEvent) {
                    setFormData({
                      ...formData,
                      eventTypeId: selectedId,
                      eventTypeSlug: selectedEvent.slug
                    });
                  }
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
              >
                {status.event_types.map((et) => (
                  <option key={et.id} value={et.id}>
                    {et.title} ({et.length} min)
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
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
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
                  placeholder="john@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone (for SMS)
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
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
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
                  placeholder="Demo request"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleCreateLink}
                disabled={actionLoading}
                className="flex-1 flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <LinkIcon className="w-5 h-5" />
                )}
                Generate Link
              </button>

              <button
                onClick={handleSendSMS}
                disabled={!formData.phone || actionLoading}
                className="flex-1 flex items-center justify-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
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
                <li>• <strong>Generate Link:</strong> Creates a pre-filled Cal.com link you can share</li>
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
