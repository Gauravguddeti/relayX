import { useState, useEffect } from 'react';
import { Save, Plus, Edit, Trash2, Bot, MessageSquare, Building2, Sparkles, Check, ChevronRight } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import { useAuth } from '../contexts/AuthContext';

interface Agent {
  id: string;
  name: string;
  prompt_text: string;
  resolved_system_prompt: string;
  temperature: number;
  is_active: boolean;
  user_id?: string;
}

const BUSINESS_TYPES = [
  { value: 'clinic', label: 'Medical Clinic / Healthcare', icon: '🏥' },
  { value: 'school', label: 'School / Educational Institution', icon: '🎓' },
  { value: 'realestate', label: 'Real Estate', icon: '🏠' },
  { value: 'automotive', label: 'Automotive / Car Dealership', icon: '🚗' },
  { value: 'restaurant', label: 'Restaurant / Food Service', icon: '🍽️' },
  { value: 'retail', label: 'Retail Store', icon: '🛍️' },
  { value: 'services', label: 'Professional Services', icon: '💼' },
  { value: 'technology', label: 'Technology / Software', icon: '💻' },
  { value: 'finance', label: 'Finance / Banking', icon: '🏦' },
  { value: 'other', label: 'Other', icon: '📦' },
];

// Business type-specific system prompt templates
const SYSTEM_PROMPT_TEMPLATES: Record<string, string> = {
  clinic: `**HEALTHCARE-SPECIFIC GUIDELINES:**
- Always maintain HIPAA compliance - never discuss specific medical conditions over the phone
- Be empathetic and reassuring, especially with anxious patients
- If asked about medical advice: "I'm not a licensed medical professional, but I can connect you with our nursing staff or schedule an appointment with the doctor."`,

  school: `**EDUCATIONAL INSTITUTION GUIDELINES:**
- Maintain student privacy (FERPA compliance) - verify caller identity before discussing student information
- Be warm and welcoming, especially to prospective families
- Show enthusiasm about the school's achievements and programs`,

  realestate: `**REAL ESTATE GUIDELINES:**
- Be professional yet approachable - real estate is both a business and personal decision
- Handle objections calmly and be transparent about fees, commissions, and process`,

  automotive: `**AUTOMOTIVE/DEALERSHIP GUIDELINES:**
- Be enthusiastic about vehicles without being pushy
- Listen for buying signals: specific model interest, trade-in mentions, financing questions
- Create urgency (when genuine): limited inventory, special promotions, seasonal sales`,

  restaurant: `**RESTAURANT/FOOD SERVICE GUIDELINES:**
- Be warm, friendly, and create excitement about the dining experience
- Handle complaints graciously and document issues
- Promote specials, happy hour, or upcoming events`,

  retail: `**RETAIL STORE GUIDELINES:**
- Create a personalized shopping experience over the phone
- Upsell naturally and create urgency when appropriate
- Always mention online shopping option with in-store return convenience`,

  services: `**PROFESSIONAL SERVICES GUIDELINES:**
- Establish credibility and professionalism immediately
- Be consultative, not salesy
- Build trust and offer resources even if they're not ready to buy`,

  technology: `**TECHNOLOGY/SOFTWARE GUIDELINES:**
- Speak clearly and avoid excessive jargon
- Demonstrate value through ROI and efficiency gains
- Push for free trial or pilot program when appropriate`,

  finance: `**FINANCE/BANKING GUIDELINES:**
- Maintain the highest level of professionalism and security
- NEVER ask for or discuss sensitive information over the phone
- Be transparent about fees and requirements`,

  other: `**GENERAL BUSINESS GUIDELINES:**
- Be professional, courteous, and adaptable
- Focus on understanding customer needs before pitching solutions
- Always look for ways to add value to the conversation`,
};

export default function AgentSettings() {
  const { userId } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [view, setView] = useState<'list' | 'edit' | 'create'>('list');

  // Editable fields
  const [agentName, setAgentName] = useState('');
  const [businessType, setBusinessType] = useState('services');
  const [greeting, setGreeting] = useState('Hi! Thanks for calling. How can I help you today?');
  const [businessDescription, setBusinessDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');

  useEffect(() => {
    if (userId) {
      fetchAgents();
    }
  }, [userId]);

  // Auto-populate system prompt when business type changes (only for new agents, not when editing)
  useEffect(() => {
    if (view === 'create' && businessType && SYSTEM_PROMPT_TEMPLATES[businessType]) {
      setSystemPrompt(SYSTEM_PROMPT_TEMPLATES[businessType]);
    }
  }, [businessType, view]);

  async function fetchAgents() {
    try {
      const response = await fetch(`/agents?user_id=${userId}`);
      if (!response.ok) {
        console.error('Failed to fetch agents:', response.status);
        setLoading(false);
        return;
      }
      const data = await response.json();
      const agentList = Array.isArray(data) ? data : [];
      const userAgents = agentList.filter((a: Agent) => a.user_id === userId);
      setAgents(userAgents);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      setAgents([]);
      setLoading(false);
    }
  }

  function handleEditAgent(agent: Agent) {
    setSelectedAgent(agent);
    setAgentName(agent.name);
    parsePromptFields(agent.prompt_text || agent.resolved_system_prompt || '');
    setView('edit');
    setMessage(null);
  }

  function handleNewAgent() {
    setSelectedAgent(null);
    setAgentName('');
    setBusinessType('services');
    setGreeting('Hi! Thanks for calling. How can I help you today?');
    setBusinessDescription('');
    setSystemPrompt(SYSTEM_PROMPT_TEMPLATES['services']);
    setView('create');
    setMessage(null);
  }

  function parsePromptFields(prompt: string) {
    const lines = prompt.split('\n');
    let foundGreeting = '';
    let foundDescription = '';
    let foundSystemPrompt = '';
    let foundBusinessType = 'services';

    // Extract greeting
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('GREETING & INTRODUCTION:')) {
        foundGreeting = lines[i + 1]?.trim() || '';
        break;
      }
    }

    // Extract business description
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('What we do:')) {
        foundDescription = lines[i + 1]?.trim() || '';
        break;
      }
    }

    // Extract business type from Industry line
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('Industry:')) {
        const industry = lines[i].split(':')[1]?.trim().toLowerCase();
        const matched = BUSINESS_TYPES.find(t =>
          t.label.toLowerCase().includes(industry) || industry.includes(t.value)
        );
        if (matched) foundBusinessType = matched.value;
        break;
      }
    }

    // Extract system prompt (everything after BUSINESS CONTEXT section until Remember:)
    const businessContextIndex = lines.findIndex(line => line.includes('BUSINESS CONTEXT:'));
    if (businessContextIndex !== -1) {
      // Find the end of business context (skip 3 lines: BUSINESS CONTEXT, Industry, What we do)
      const systemPromptStart = businessContextIndex + 4;
      const rememberIndex = lines.findIndex(line => line.includes('Remember: Your goal'));
      if (systemPromptStart < lines.length) {
        const endIndex = rememberIndex !== -1 ? rememberIndex : lines.length;
        foundSystemPrompt = lines.slice(systemPromptStart, endIndex).join('\n').trim();
      }
    }

    if (foundGreeting) setGreeting(foundGreeting);
    if (foundDescription) setBusinessDescription(foundDescription);
    if (foundSystemPrompt) setSystemPrompt(foundSystemPrompt);
    setBusinessType(foundBusinessType);
  }

  async function handleSaveAgent() {
    if (!userId) {
      setMessage({ type: 'error', text: 'User not authenticated. Please log in again.' });
      return;
    }

    setSaving(true);
    setMessage(null);

    try {
      const prompt = buildSystemPrompt();

      if (view === 'create') {
        // Create new agent
        const response = await fetch('/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: agentName,
            prompt_text: prompt,
            is_active: true,
            user_id: userId,
          }),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to create agent');
        }

        setMessage({ type: 'success', text: 'Agent created successfully!' });
      } else {
        // Update existing agent
        const response = await fetch(`/agents/${selectedAgent?.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: agentName,
            prompt_text: prompt,
            user_id: userId,
          }),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to update agent');
        }

        setMessage({ type: 'success', text: 'Agent saved successfully!' });
      }

      // Refresh agents list and return to list view
      await fetchAgents();
      setTimeout(() => {
        setView('list');
        setMessage(null);
      }, 1500);
    } catch (error: any) {
      console.error('Save error:', error);
      setMessage({ type: 'error', text: error.message || 'Failed to save agent. Please try again.' });
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteAgent(agentId: string) {
    if (!confirm('Are you sure you want to delete this agent?')) return;

    try {
      const response = await fetch(`/agents/${agentId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete agent');
      }

      setMessage({ type: 'success', text: 'Agent deleted successfully!' });
      await fetchAgents();
      setTimeout(() => setMessage(null), 3000);
    } catch (error: any) {
      console.error('Delete error:', error);
      setMessage({ type: 'error', text: error.message || 'Failed to delete agent.' });
    }
  }

  function buildSystemPrompt(): string {
    const companyName = businessDescription.split('.')[0] || 'our company';
    const businessLabel = BUSINESS_TYPES.find(t => t.value === businessType)?.label || 'Professional Services';

    let prompt = `You are ${agentName}, an AI-powered voice assistant representing ${companyName}.

IDENTITY & ROLE:
- Your name is ${agentName}
- You are a professional, knowledgeable representative
- You speak naturally and conversationally, like a real person

GREETING & INTRODUCTION:
${greeting}

Then introduce yourself: "My name is ${agentName}, and I'm reaching out from ${companyName}."

BUSINESS CONTEXT:
Industry: ${businessLabel}
What we do: ${businessDescription}

${systemPrompt}

Remember: Your goal is to help customers and represent ${companyName} professionally. You are ${agentName}, and you always introduce yourself by name.`;

    return prompt;
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  // Agent List View
  if (view === 'list') {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">My Agents</h1>
              <p className="text-gray-600 mt-1">Manage your AI voice assistants</p>
            </div>
            <button
              onClick={handleNewAgent}
              className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-5 h-5" />
              <span>New Agent</span>
            </button>
          </div>

          {message && (
            <div className={`rounded-lg p-4 ${message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
              {message.text}
            </div>
          )}

          {agents.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <Bot className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No agents yet</h3>
              <p className="text-gray-600 mb-6">Create your first AI voice assistant to start making calls</p>
              <button
                onClick={handleNewAgent}
                className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-5 h-5" />
                <span>Create Your First Agent</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-2 border-gray-200 hover:border-blue-500"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <Bot className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                        <span className={`text-xs px-2 py-1 rounded-full ${agent.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                          {agent.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2 mb-4">
                    <p className="text-sm text-gray-600 line-clamp-3">
                      {agent.prompt_text?.substring(0, 150) || 'No description'}...
                    </p>
                  </div>

                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleEditAgent(agent)}
                      className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      <Edit className="w-4 h-4" />
                      <span>Edit</span>
                    </button>
                    <button
                      onClick={() => handleDeleteAgent(agent.id)}
                      className="px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </DashboardLayout>
    );
  }

  // Edit/Create View
  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {view === 'create' ? 'Create New Agent' : 'Edit Agent'}
            </h1>
            <p className="text-gray-600 mt-1">Configure your AI voice assistant</p>
          </div>
          <button
            onClick={() => setView('list')}
            className="px-4 py-2 text-gray-600 hover:text-gray-900"
          >
            ← Back to Agents
          </button>
        </div>

        {message && (
          <div className={`rounded-lg p-4 ${message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
            {message.text}
          </div>
        )}

        <div className="bg-white rounded-lg shadow p-6 space-y-6">
          {/* Agent Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Agent Name
            </label>
            <input
              type="text"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-black"
              placeholder="e.g., Sarah, John, RelayX Assistant"
            />
            <p className="text-sm text-gray-500 mt-1">
              This is how your agent will introduce itself to customers
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
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-black"
            >
              <option value="">Select your business type...</option>
              {BUSINESS_TYPES.map(type => (
                <option key={type.value} value={type.value}>{type.icon} {type.label}</option>
              ))}
            </select>
            <p className="text-sm text-gray-500 mt-1">
              Helps the AI understand your industry context
            </p>
          </div>

          {/* Greeting */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              How should your agent greet callers?
            </label>
            <textarea
              value={greeting}
              onChange={(e) => setGreeting(e.target.value)}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-black"
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
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-black"
              placeholder="Describe your business, services, and what makes you unique..."
            />
            <p className="text-sm text-gray-500 mt-1">
              The agent uses this to answer questions about your business
            </p>
          </div>

          {/* System Prompt */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              System Prompt (Auto-populated based on business type)
            </label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={12}
              className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm bg-white text-black"
              placeholder="Select a business type to auto-load industry-specific guidelines..."
            />
            <p className="text-sm text-gray-500 mt-1">
              This prompt is automatically filled when you select a business type above. You can edit it to customize your agent's behavior.
            </p>
          </div>

          {/* Save Button */}
          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={handleSaveAgent}
              disabled={saving || !agentName.trim()}
              className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-5 h-5" />
              <span>{saving ? 'Saving...' : view === 'create' ? 'Create Agent' : 'Save Agent'}</span>
            </button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
