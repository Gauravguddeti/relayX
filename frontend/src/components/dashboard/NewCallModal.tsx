import { useState, useEffect } from 'react';
import { X, Phone, Calendar, User, FileText, Clock, Save, Check } from 'lucide-react';

interface NewCallModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

interface Agent {
  id: string;
  name: string;
  is_active: boolean;
}

const COUNTRY_CODES = [
  { code: '+1', country: 'US', flag: '🇺🇸' },
  { code: '+91', country: 'India', flag: '🇮🇳' },
  { code: '+44', country: 'UK', flag: '🇬🇧' },
  { code: '+61', country: 'Australia', flag: '🇦🇺' },
  { code: '+971', country: 'UAE', flag: '🇦🇪' },
  { code: '+81', country: 'Japan', flag: '🇯🇵' },
  { code: '+86', country: 'China', flag: '🇨🇳' },
  { code: '+49', country: 'Germany', flag: '🇩🇪' },
  { code: '+33', country: 'France', flag: '🇫🇷' },
  { code: '+39', country: 'Italy', flag: '🇮🇹' },
];

export default function NewCallModal({ isOpen, onClose, onSuccess }: NewCallModalProps) {
  const [countryCode, setCountryCode] = useState('+1');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('');
  const [contactName, setContactName] = useState('');
  const [notes, setNotes] = useState('');
  const [callType, setCallType] = useState<'immediate' | 'scheduled'>('immediate');
  const [scheduledTime, setScheduledTime] = useState('');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [callSuccess, setCallSuccess] = useState(false);
  const [lastCalledNumber, setLastCalledNumber] = useState('');
  const [showSaveContact, setShowSaveContact] = useState(false);
  const [saveContactName, setSaveContactName] = useState('');
  const [contactSaved, setContactSaved] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchAgents();
    }
  }, [isOpen]);

  async function fetchAgents() {
    try {
      const response = await fetch('/agents');
      if (response.ok) {
        const data = await response.json();
        const agentList = Array.isArray(data) ? data : [];
        setAgents(agentList);
        if (agentList.length > 0) {
          setSelectedAgent(agentList[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    setCallSuccess(false);
    setShowSaveContact(false);

    // Validate phone number (basic validation)
    const cleanPhone = phoneNumber.replace(/\D/g, '');
    if (cleanPhone.length < 7) {
      setError('Please enter a valid phone number');
      setLoading(false);
      return;
    }

    // Format phone number with country code
    const formattedPhone = `${countryCode}${cleanPhone}`;
    setLastCalledNumber(formattedPhone);

    try {
      const payload: any = {
        to_number: formattedPhone,
        agent_id: selectedAgent,
      };

      if (contactName) payload.contact_name = contactName;
      if (notes) payload.notes = notes;
      if (callType === 'scheduled' && scheduledTime) {
        payload.scheduled_at = new Date(scheduledTime).toISOString();
      }

      const response = await fetch('/calls/outbound', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to initiate call');
      }

      // Success!
      setCallSuccess(true);
      setShowSaveContact(true);
      setSaveContactName(contactName || '');
      setPhoneNumber('');
      setContactName('');
      setNotes('');
      setScheduledTime('');
      if (onSuccess) onSuccess();
      
      // Auto-close after 3 seconds if user doesn't want to save contact
      setTimeout(() => {
        if (!contactSaved) {
          onClose();
        }
      }, 5000);
    } catch (error: any) {
      setError(error.message || 'Failed to initiate call');
    } finally {
      setLoading(false);
    }
  }

  function saveContact() {
    if (!saveContactName.trim()) {
      setError('Please enter a name for the contact');
      return;
    }

    const contacts = JSON.parse(localStorage.getItem('contacts') || '[]');
    contacts.push({
      name: saveContactName,
      phone: lastCalledNumber,
      savedAt: new Date().toISOString(),
    });
    localStorage.setItem('contacts', JSON.stringify(contacts));
    setContactSaved(true);
    
    setTimeout(() => {
      onClose();
      // Reset states
      setCallSuccess(false);
      setShowSaveContact(false);
      setContactSaved(false);
      setSaveContactName('');
      setLastCalledNumber('');
    }, 1500);
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Phone className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Make a Call</h2>
              <p className="text-sm text-gray-600">Initiate an AI-powered call</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {/* Phone Number with Country Code */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Phone className="w-4 h-4 inline mr-2" />
              Phone Number *
            </label>
            <div className="flex space-x-2">
              <select
                value={countryCode}
                onChange={(e) => setCountryCode(e.target.value)}
                className="px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
              >
                {COUNTRY_CODES.map((country) => (
                  <option key={country.code} value={country.code}>
                    {country.flag} {country.code}
                  </option>
                ))}
              </select>
              <input
                type="tel"
                required
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value.replace(/[^0-9]/g, ''))}
                placeholder="5551234567"
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Enter phone number without country code</p>
          </div>

          {/* Contact Name (Optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="w-4 h-4 inline mr-2" />
              Contact Name (Optional)
            </label>
            <input
              type="text"
              value={contactName}
              onChange={(e) => setContactName(e.target.value)}
              placeholder="John Doe"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Agent Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Bot *
            </label>
            <select
              required
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name} {!agent.is_active && '(Inactive)'}
                </option>
              ))}
            </select>
          </div>

          {/* Call Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              <Clock className="w-4 h-4 inline mr-2" />
              When to call?
            </label>
            <div className="flex space-x-4">
              <button
                type="button"
                onClick={() => setCallType('immediate')}
                className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
                  callType === 'immediate'
                    ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium'
                    : 'border-gray-300 text-gray-700 hover:border-gray-400'
                }`}
              >
                <Phone className="w-5 h-5 inline mr-2" />
                Call Now
              </button>
              <button
                type="button"
                onClick={() => setCallType('scheduled')}
                className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
                  callType === 'scheduled'
                    ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium'
                    : 'border-gray-300 text-gray-700 hover:border-gray-400'
                }`}
              >
                <Calendar className="w-5 h-5 inline mr-2" />
                Schedule
              </button>
            </div>
          </div>

          {/* Scheduled Time (if scheduled) */}
          {callType === 'scheduled' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-2" />
                Schedule Date & Time *
              </label>
              <input
                type="datetime-local"
                required={callType === 'scheduled'}
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                min={new Date().toISOString().slice(0, 16)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <FileText className="w-4 h-4 inline mr-2" />
              Notes (Optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any context or special instructions for this call..."
              rows={3}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>

          {/* Save Contact Section (shown after successful call) */}
          {callSuccess && showSaveContact && (
            <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span className="text-green-800 font-semibold">Call initiated successfully!</span>
                </div>
              </div>
              
              {!contactSaved ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Save this contact for future calls?
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={saveContactName}
                      onChange={(e) => setSaveContactName(e.target.value)}
                      placeholder="Enter contact name"
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      onKeyPress={(e) => e.key === 'Enter' && saveContact()}
                    />
                    <button
                      type="button"
                      onClick={saveContact}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      Save
                    </button>
                  </div>
                  <p className="text-xs text-gray-600 mt-2">Phone: {lastCalledNumber}</p>
                </div>
              ) : (
                <div className="flex items-center space-x-2 text-green-700">
                  <Check className="w-5 h-5" />
                  <span>Contact saved! Closing...</span>
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          {!callSuccess && (
            <div className="flex space-x-4 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Processing...
                  </span>
                ) : (
                  <span className="flex items-center justify-center">
                    <Phone className="w-5 h-5 mr-2" />
                    {callType === 'immediate' ? 'Call Now' : 'Schedule Call'}
                  </span>
                )}
              </button>
            </div>
          )}
          
          {callSuccess && (
            <div className="flex justify-end pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
              >
                Close
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
