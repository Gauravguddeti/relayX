import { useState, useEffect } from 'react';
import { Save, AlertCircle } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';

interface Agent {
  id: string;
  name: string;
  prompt_text: string;
  resolved_system_prompt: string;
  temperature: number;
  is_active: boolean;
}

const BUSINESS_TYPES = [
  { value: 'clinic', label: 'Medical Clinic / Healthcare' },
  { value: 'school', label: 'School / Educational Institution' },
  { value: 'realestate', label: 'Real Estate' },
  { value: 'automotive', label: 'Automotive / Car Dealership' },
  { value: 'restaurant', label: 'Restaurant / Food Service' },
  { value: 'retail', label: 'Retail Store' },
  { value: 'services', label: 'Professional Services' },
  { value: 'other', label: 'Other' },
];

export default function BotSettings() {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Editable fields
  const [botName, setBotName] = useState('');
  const [businessType, setBusinessType] = useState('');
  const [greeting, setGreeting] = useState('');
  const [businessDescription, setBusinessDescription] = useState('');

  useEffect(() => {
    fetchAgent();
  }, []);

  async function fetchAgent() {
    try {
      const response = await fetch('/api/agents');
      const agents = await response.json();
      
      if (agents.length > 0) {
        const userAgent = agents[0]; // Get first agent (one bot per user)
        setAgent(userAgent);
        setBotName(userAgent.name);
        
        // Try to parse existing prompt to extract editable parts
        const promptText = userAgent.prompt_text || userAgent.resolved_system_prompt || '';
        parsePromptFields(promptText);
      }
    } catch (error) {
      console.error('Failed to fetch agent:', error);
    } finally {
      setLoading(false);
    }
  }

  function parsePromptFields(prompt: string) {
    // Try to extract greeting and business description from existing prompt
    // This is a simple parser - adjust based on your actual prompt format
    const lines = prompt.split('\n');
    let foundGreeting = '';
    let foundDescription = '';

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.includes('greeting') || line.includes('introduce')) {
        foundGreeting = lines[i + 1]?.trim() || '';
      }
      if (line.includes('business') || line.includes('company')) {
        foundDescription = lines[i + 1]?.trim() || '';
      }
    }

    setGreeting(foundGreeting || "Hi! Thanks for calling. How can I help you today?");
    setBusinessDescription(foundDescription || "We help businesses grow with AI-powered calling solutions.");
  }

  async function handleSave() {
    if (!agent) return;
    
    setSaving(true);
    setMessage(null);

    try {
      // Build updated prompt
      const updatedPrompt = buildSystemPrompt();

      const response = await fetch(`/api/agents/${agent.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: botName,
          prompt_text: updatedPrompt,
        }),
      });

      if (!response.ok) throw new Error('Failed to update bot');

      setMessage({ type: 'success', text: 'Bot settings saved successfully!' });
      
      // Refresh agent data
      await fetchAgent();
    } catch (error) {
      console.error('Save error:', error);
      setMessage({ type: 'error', text: 'Failed to save settings. Please try again.' });
    } finally {
      setSaving(false);
    }
  }

  function buildSystemPrompt(): string {
    // Build a clean system prompt from the user's inputs
    return `You are ${botName}, an AI assistant helping customers.

GREETING:
${greeting}

ABOUT THE BUSINESS:
${businessDescription}

CONVERSATION GUIDELINES:
- Be friendly, professional, and helpful
- Listen carefully to what the customer needs
- Ask clarifying questions when needed
- Keep responses concise and clear
- Always aim to provide value and build trust

BUSINESS TYPE: ${businessType || 'General'}

Remember: Your goal is to help customers and represent the business professionally.`;
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-96 bg-gray-200 rounded"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Bot Settings</h1>
          <p className="text-gray-600 mt-1">
            Customize how your AI assistant talks to customers
          </p>
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-900">
            <p className="font-medium">Keep it simple!</p>
            <p className="mt-1">
              These settings control how your assistant introduces itself and describes your business.
              The AI handles the conversation flow automatically.
            </p>
          </div>
        </div>

        {message && (
          <div className={`rounded-lg p-4 ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {message.text}
          </div>
        )}

        {/* Settings Form */}
        <div className="bg-white rounded-lg shadow p-6 space-y-6">
          {/* Bot Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assistant Name
            </label>
            <input
              type="text"
              value={botName}
              onChange={(e) => setBotName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Sarah, John, RelayX Assistant"
            />
            <p className="text-sm text-gray-500 mt-1">
              This is how your assistant will introduce itself to customers
            </p>
          </div>

          {/* Business Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Business Type
            </label>
            <select
              value={businessType}
              onChange={(e) => setBusinessType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select your business type...</option>
              {BUSINESS_TYPES.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
            <p className="text-sm text-gray-500 mt-1">
              Helps the AI understand your industry context
            </p>
          </div>

          {/* Greeting */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              How should your assistant greet callers?
            </label>
            <textarea
              value={greeting}
              onChange={(e) => setGreeting(e.target.value)}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Hi! Thanks for calling. How can I help you today?"
            />
            <p className="text-sm text-gray-500 mt-1">
              Keep it friendly and professional (1-2 sentences)
            </p>
          </div>

          {/* Business Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              What does your business do?
            </label>
            <textarea
              value={businessDescription}
              onChange={(e) => setBusinessDescription(e.target.value)}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Describe your business, services, and what makes you unique..."
            />
            <p className="text-sm text-gray-500 mt-1">
              The assistant uses this to answer questions about your business
            </p>
          </div>

          {/* Save Button */}
          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-5 h-5" />
              <span>{saving ? 'Saving...' : 'Save Changes'}</span>
            </button>
          </div>
        </div>

        {/* Preview */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="font-medium text-gray-900 mb-3">Preview</h3>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <p className="text-sm text-gray-600 mb-2">When a customer calls, your assistant will say:</p>
            <p className="text-gray-900 italic">"{greeting}"</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
