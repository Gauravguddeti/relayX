import { useState } from 'react';
import { X, Phone } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

interface TestCallModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const COUNTRY_CODES = [
  { code: '+1', country: 'US/Canada', flag: '🇺🇸' },
  { code: '+91', country: 'India', flag: '🇮🇳' },
  { code: '+44', country: 'UK', flag: '🇬🇧' },
];

export default function TestCallModal({ isOpen, onClose }: TestCallModalProps) {
  const [countryCode, setCountryCode] = useState('+91');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  if (!isOpen) return null;

  const handleTestCall = async () => {
    if (!phoneNumber || phoneNumber.length < 10) {
      setResult({ type: 'error', message: 'Please enter a valid phone number' });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('/api/agent/test-call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_number: `${countryCode}${phoneNumber}`,
        }),
      });

      if (response.ok) {
        setResult({ 
          type: 'success', 
          message: 'Test call initiated! You should receive a call shortly.' 
        });
        setPhoneNumber('');
      } else {
        const error = await response.json();
        setResult({ type: 'error', message: error.detail || 'Failed to initiate call' });
      }
    } catch (error) {
      setResult({ type: 'error', message: 'Network error. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <Card className="w-full max-w-md bg-gray-900 border-gray-800 text-white">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl text-white">Test AI Call</CardTitle>
              <CardDescription className="text-gray-400">
                Enter your phone number to receive a test call from our AI
              </CardDescription>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Phone Number</label>
            <div className="flex gap-2">
              <select
                value={countryCode}
                onChange={(e) => setCountryCode(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white w-32"
              >
                {COUNTRY_CODES.map((country) => (
                  <option key={country.code} value={country.code}>
                    {country.flag} {country.code}
                  </option>
                ))}
              </select>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value.replace(/\D/g, ''))}
                placeholder="9876543210"
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>

          {result && (
            <div
              className={`p-4 rounded-lg ${
                result.type === 'success'
                  ? 'bg-green-500/20 border border-green-500/50 text-green-400'
                  : 'bg-red-500/20 border border-red-500/50 text-red-400'
              }`}
            >
              {result.message}
            </div>
          )}

          <Button
            onClick={handleTestCall}
            disabled={loading}
            className="w-full bg-cyan-500 hover:bg-cyan-600 text-black font-bold"
          >
            {loading ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Calling...
              </>
            ) : (
              <>
                <Phone className="w-4 h-4 mr-2" />
                Start Test Call
              </>
            )}
          </Button>

          <p className="text-xs text-gray-500 text-center">
            You'll receive a call from our AI in a few seconds. Press 1 if asked to accept.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
