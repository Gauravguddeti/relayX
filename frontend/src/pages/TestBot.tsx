import { useState, useEffect } from 'react';
import { Phone, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';

export default function TestBot() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [agentId, setAgentId] = useState<string>('');

  useEffect(() => {
    fetchAgent();
  }, []);

  async function fetchAgent() {
    try {
      const response = await fetch('/api/agents');
      const agents = await response.json();
      if (agents.length > 0) {
        setAgentId(agents[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch agent:', error);
    }
  }

  function formatPhoneNumber(value: string) {
    // Remove all non-digits
    const digits = value.replace(/\D/g, '');
    
    // Format as (XXX) XXX-XXXX
    if (digits.length <= 3) {
      return digits;
    } else if (digits.length <= 6) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
    } else {
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`;
    }
  }

  function handlePhoneChange(e: React.ChangeEvent<HTMLInputElement>) {
    const formatted = formatPhoneNumber(e.target.value);
    setPhoneNumber(formatted);
  }

  function getDigitsOnly(phone: string) {
    return phone.replace(/\D/g, '');
  }

  async function handleTestCall() {
    if (!phoneNumber || !agentId) return;

    const digits = getDigitsOnly(phoneNumber);
    if (digits.length !== 10) {
      setResult({ type: 'error', message: 'Please enter a valid 10-digit phone number' });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('/api/calls/outbound', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agentId,
          to_number: `+1${digits}`,
          metadata: {
            test: true,
            source: 'test_bot_ui',
          },
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to initiate call');
      }

      const data = await response.json();
      
      setResult({
        type: 'success',
        message: `Test call initiated! Your phone will ring shortly. Call ID: ${data.call_id}`,
      });
      
      // Reset form after 3 seconds
      setTimeout(() => {
        setPhoneNumber('');
        setResult(null);
      }, 5000);
    } catch (error) {
      console.error('Test call error:', error);
      setResult({
        type: 'error',
        message: error instanceof Error ? error.message : 'Failed to start test call. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-2xl space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Test Your Bot</h1>
          <p className="text-gray-600 mt-1">
            Call yourself to see how your assistant performs
          </p>
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-900">
            <p className="font-medium">Safe Testing Environment</p>
            <ul className="mt-2 space-y-1 list-disc list-inside">
              <li>Test calls are clearly marked in your call history</li>
              <li>Use this to practice and improve your bot's responses</li>
              <li>Test as many times as you need - no limits!</li>
            </ul>
          </div>
        </div>

        {/* Test Form */}
        <div className="bg-white rounded-lg shadow p-8">
          <div className="space-y-6">
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                Your Phone Number
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Phone className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="phone"
                  type="tel"
                  value={phoneNumber}
                  onChange={handlePhoneChange}
                  placeholder="(555) 123-4567"
                  maxLength={14}
                  className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg text-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <p className="text-sm text-gray-500 mt-2">
                Enter the phone number where you want to receive the test call
              </p>
            </div>

            {result && (
              <div className={`rounded-lg p-4 flex items-start space-x-3 ${
                result.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
              }`}>
                {result.type === 'success' ? (
                  <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                )}
                <p className="text-sm">{result.message}</p>
              </div>
            )}

            <button
              onClick={handleTestCall}
              disabled={loading || !phoneNumber || getDigitsOnly(phoneNumber).length !== 10}
              className="w-full flex items-center justify-center space-x-2 px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-lg"
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  <span>Initiating Call...</span>
                </>
              ) : (
                <>
                  <Phone className="w-5 h-5" />
                  <span>Start Test Call</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* What to Expect */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">What to Expect</h2>
          <ol className="space-y-3 text-sm text-gray-700">
            <li className="flex items-start">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-medium flex items-center justify-center mr-3">
                1
              </span>
              <span>
                Click "Start Test Call" - your phone will ring within a few seconds
              </span>
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-medium flex items-center justify-center mr-3">
                2
              </span>
              <span>
                Answer the call and have a natural conversation with your AI assistant
              </span>
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-medium flex items-center justify-center mr-3">
                3
              </span>
              <span>
                After the call, check the Dashboard to see the conversation summary and transcript
              </span>
            </li>
            <li className="flex items-start">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-medium flex items-center justify-center mr-3">
                4
              </span>
              <span>
                Use what you learn to improve your bot's settings and knowledge base
              </span>
            </li>
          </ol>
        </div>

        {/* Tips */}
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h3 className="font-medium text-purple-900 mb-2">Pro Tips</h3>
          <ul className="text-sm text-purple-800 space-y-1 list-disc list-inside">
            <li>Try different scenarios: interested customer, busy person, someone with questions</li>
            <li>Test how your bot handles objections and concerns</li>
            <li>Make sure your bot knows key information about your business</li>
            <li>Listen for natural conversation flow - does it feel human?</li>
          </ul>
        </div>
      </div>
    </DashboardLayout>
  );
}
