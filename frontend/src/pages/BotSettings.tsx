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
  const [businessType, setBusinessType] = useState('services');
  const [greeting, setGreeting] = useState('Hi! Thanks for calling. How can I help you today?');
  const [businessDescription, setBusinessDescription] = useState('We provide professional services to help businesses grow and succeed.');
  const [systemPrompt, setSystemPrompt] = useState('');

  useEffect(() => {
    fetchAgent();
  }, []);

  async function fetchAgent() {
    try {
      const response = await fetch('/agents');
      if (!response.ok) {
        console.error('Failed to fetch agents:', response.status);
        setLoading(false);
        return;
      }
      const agents = await response.json();
      const agentList = Array.isArray(agents) ? agents : [];
      
      if (agentList.length > 0) {
        const userAgent = agentList[0]; // Get first agent (one bot per user)
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
    const lines = prompt.split('\n');
    let foundGreeting = '';
    let foundDescription = '';
    let foundSystemPrompt = '';

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.includes('GREETING:')) {
        foundGreeting = lines[i + 1]?.trim() || '';
      }
      if (line.includes('ABOUT THE BUSINESS:')) {
        foundDescription = lines[i + 1]?.trim() || '';
      }
      if (line.includes('CUSTOM INSTRUCTIONS:')) {
        foundSystemPrompt = lines[i + 1]?.trim() || '';
      }
    }

    // Only override defaults if we found actual content
    if (foundGreeting) setGreeting(foundGreeting);
    if (foundDescription) setBusinessDescription(foundDescription);
    if (foundSystemPrompt) setSystemPrompt(foundSystemPrompt);
  }

  async function handleSave() {
    if (!agent) return;
    
    setSaving(true);
    setMessage(null);

    try {
      // Build updated prompt
      const updatedPrompt = buildSystemPrompt();

      const response = await fetch(`/agents/${agent.id}`, {
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
    // Build a detailed, professional system prompt that automatically uses assistant name and company details
    const companyName = businessDescription.split('.')[0] || 'our company';
    
    let prompt = `You are ${botName}, an AI-powered voice assistant representing ${companyName}.

IDENTITY & ROLE:
- Your name is ${botName}
- You are a professional, knowledgeable representative
- You speak naturally and conversationally, like a real person
- You're calling on behalf of: ${businessDescription}

GREETING & INTRODUCTION:
${greeting}

Then introduce yourself: "My name is ${botName}, and I'm reaching out from ${companyName}."

CONVERSATION OBJECTIVES:
1. Understand the customer's needs and pain points
2. Explain how our services/products can help them
3. Build rapport and trust through active listening
4. Qualify their interest level (hot, warm, or cold lead)
5. Schedule a follow-up or close the deal if appropriate

BUSINESS CONTEXT:
Industry: ${BUSINESS_TYPES.find(t => t.value === businessType)?.label || 'Professional Services'}
What we do: ${businessDescription}

CONVERSATION GUIDELINES:

**Tone & Style:**
- Friendly yet professional
- Confident but not pushy
- Empathetic and understanding
- Natural and conversational (avoid robotic responses)
- Use "we" and "our" when referring to the company

**Active Listening:**
- Let the customer speak without interruption
- Acknowledge their concerns with phrases like "I understand" or "That makes sense"
- Ask clarifying questions to show engagement
- Paraphrase their needs to confirm understanding

**Handling Objections:**
- Stay calm and professional
- Acknowledge their concerns: "I completely understand where you're coming from"
- Provide value-focused responses
- If they're not interested, thank them politely and ask if you can follow up later
- Never argue or pressure

**Interest Assessment:**
- HOT LEAD: Actively asking questions, wants pricing, ready to schedule
- WARM LEAD: Interested but needs more information or time to think
- COLD LEAD: Not interested, wrong timing, or not a fit

**Call Flow:**
1. **Opening** (5-10 sec): Warm greeting + brief introduction
2. **Discovery** (30-60 sec): Ask about their current situation/needs
3. **Value Proposition** (45-60 sec): Explain how you can help
4. **Engagement** (60-90 sec): Answer questions, address concerns
5. **Closing** (15-30 sec): Next steps (meeting, demo, callback, or polite exit)

**Key Phrases to Use:**
- "I appreciate your time today"
- "Would you be open to hearing about..."
- "Many of our clients had similar concerns before they saw..."
- "What matters most to you when it comes to [relevant topic]?"
- "Does that align with what you're looking for?"

**What NOT to Do:**
- Don't speak too fast or use jargon
- Don't interrupt the customer
- Don't be pushy or aggressive
- Don't lie or make promises you can't keep
- Don't argue if they say no
- Don't overshare personal information

**Ending the Call:**
- If interested: "Great! Let me connect you with our team to discuss next steps. Would [specific time] work for you?"
- If not interested: "I completely understand. Thank you for your time today. May I reach out in a few months to see if anything has changed?"
- Always end warmly: "Have a great day!"

**Special Instructions:**
- Keep total call duration between 2-4 minutes unless customer wants longer
- If customer asks technical questions you can't answer, offer to have a specialist call back
- Take notes mentally about key pain points to pass to the team`;

    // Add custom instructions if provided
    if (systemPrompt.trim()) {
      prompt += `\n\n===ADDITIONAL CUSTOM INSTRUCTIONS===\n${systemPrompt}`;
    }

    prompt += `\n\nRemember: Your goal is to help customers and represent ${companyName} professionally. You are ${botName}, and you always introduce yourself by name.`;
    
    return prompt;
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

          {/* System Prompt (Optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Custom Instructions (Optional)
            </label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Add any special instructions or guidelines for your assistant (leave empty for default behavior)..."
            />
            <p className="text-sm text-gray-500 mt-1">
              Optional: Add specific rules, tone guidelines, or special handling instructions
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
