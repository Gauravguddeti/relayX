import { useState, useEffect } from 'react';
import { Save, AlertCircle, Plus, ChevronRight, Check, Bot, MessageSquare, Building2, Sparkles } from 'lucide-react';
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

type SetupStep = 'name' | 'business' | 'greeting' | 'description' | 'review';

export default function BotSettings() {
  const { userId } = useAuth();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showSetupWizard, setShowSetupWizard] = useState(false);
  const [currentStep, setCurrentStep] = useState<SetupStep>('name');

  // Editable fields
  const [botName, setBotName] = useState('');
  const [businessType, setBusinessType] = useState('services');
  const [greeting, setGreeting] = useState('Hi! Thanks for calling. How can I help you today?');
  const [businessDescription, setBusinessDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');

  useEffect(() => {
    if (userId) {
      fetchAgent();
    }
  }, [userId]);

  async function fetchAgent() {
    if (!userId) {
      setShowSetupWizard(true);
      setLoading(false);
      return;
    }

    try {
      // Fetch agents filtered by current user
      const response = await fetch(`/agents?user_id=${userId}`);
      if (!response.ok) {
        console.error('Failed to fetch agents:', response.status);
        setLoading(false);
        setShowSetupWizard(true);
        return;
      }
      const agents = await response.json();
      const agentList = Array.isArray(agents) ? agents : [];
      
      // Filter to only show current user's agents
      const userAgents = agentList.filter((a: Agent) => a.user_id === userId);
      
      if (userAgents.length > 0) {
        const userAgent = userAgents[0];
        setAgent(userAgent);
        setBotName(userAgent.name);
        
        const promptText = userAgent.prompt_text || userAgent.resolved_system_prompt || '';
        parsePromptFields(promptText);
        setShowSetupWizard(false);
      } else {
        setShowSetupWizard(true);
      }
    } catch (error) {
      console.error('Failed to fetch agent:', error);
      setShowSetupWizard(true);
    } finally {
      setLoading(false);
    }
  }

  function parsePromptFields(prompt: string) {
    const lines = prompt.split('\n');
    let foundGreeting = '';
    let foundDescription = '';
    let foundSystemPrompt = '';
    let foundBusinessType = 'services';

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.includes('GREETING:') || line.includes('GREETING & INTRODUCTION:')) {
        foundGreeting = lines[i + 1]?.trim() || '';
      }
      if (line.includes('ABOUT THE BUSINESS:') || line.includes('What we do:')) {
        foundDescription = lines[i + 1]?.trim() || '';
      }
      if (line.includes('CUSTOM INSTRUCTIONS:') || line.includes('ADDITIONAL CUSTOM INSTRUCTIONS')) {
        foundSystemPrompt = lines[i + 1]?.trim() || '';
      }
      if (line.includes('Industry:')) {
        const industry = line.split(':')[1]?.trim().toLowerCase();
        const matched = BUSINESS_TYPES.find(t => 
          t.label.toLowerCase().includes(industry) || industry.includes(t.value)
        );
        if (matched) foundBusinessType = matched.value;
      }
    }

    if (foundGreeting) setGreeting(foundGreeting);
    if (foundDescription) setBusinessDescription(foundDescription);
    if (foundSystemPrompt) setSystemPrompt(foundSystemPrompt);
    setBusinessType(foundBusinessType);
  }

  async function handleCreateBot() {
    if (!userId) {
      setMessage({ type: 'error', text: 'User not authenticated. Please log in again.' });
      return;
    }

    setSaving(true);
    setMessage(null);

    try {
      const prompt = buildSystemPrompt();

      const response = await fetch('/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: botName,
          prompt_text: prompt,
          is_active: true,
          user_id: userId, // Associate bot with current user
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create bot');
      }

      setMessage({ type: 'success', text: 'Bot created successfully! You can now make calls.' });
      setShowSetupWizard(false);
      await fetchAgent();
    } catch (error: any) {
      console.error('Create error:', error);
      setMessage({ type: 'error', text: error.message || 'Failed to create bot. Please try again.' });
    } finally {
      setSaving(false);
    }
  }

  async function handleSave() {
    if (!agent || !userId) return;
    
    setSaving(true);
    setMessage(null);

    try {
      const updatedPrompt = buildSystemPrompt();

      const response = await fetch(`/agents/${agent.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: botName,
          prompt_text: updatedPrompt,
          user_id: userId, // Include user_id for authorization
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update bot');
      }

      setMessage({ type: 'success', text: 'Bot settings saved successfully!' });
      await fetchAgent();
    } catch (error: any) {
      console.error('Save error:', error);
      setMessage({ type: 'error', text: error.message || 'Failed to save settings. Please try again.' });
    } finally {
      setSaving(false);
    }
  }

  function buildSystemPrompt(): string {
    const companyName = businessDescription.split('.')[0] || 'our company';
    const businessLabel = BUSINESS_TYPES.find(t => t.value === businessType)?.label || 'Professional Services';
    
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
Industry: ${businessLabel}
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

    if (systemPrompt.trim()) {
      prompt += `\n\n===ADDITIONAL CUSTOM INSTRUCTIONS===\n${systemPrompt}`;
    }

    prompt += `\n\nRemember: Your goal is to help customers and represent ${companyName} professionally. You are ${botName}, and you always introduce yourself by name.`;
    
    return prompt;
  }

  const setupSteps: { key: SetupStep; title: string; icon: any }[] = [
    { key: 'name', title: 'Name Your Bot', icon: Bot },
    { key: 'business', title: 'Business Type', icon: Building2 },
    { key: 'greeting', title: 'Greeting', icon: MessageSquare },
    { key: 'description', title: 'About Your Business', icon: Sparkles },
    { key: 'review', title: 'Review & Create', icon: Check },
  ];

  const currentStepIndex = setupSteps.findIndex(s => s.key === currentStep);

  function nextStep() {
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < setupSteps.length) {
      setCurrentStep(setupSteps[nextIndex].key);
    }
  }

  function prevStep() {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(setupSteps[prevIndex].key);
    }
  }

  function canProceed(): boolean {
    switch (currentStep) {
      case 'name': return botName.trim().length > 0;
      case 'business': return businessType.length > 0;
      case 'greeting': return greeting.trim().length > 0;
      case 'description': return businessDescription.trim().length > 0;
      case 'review': return true;
      default: return false;
    }
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

  // Setup Wizard for new users
  if (showSetupWizard) {
    return (
      <DashboardLayout>
        <div className="max-w-3xl mx-auto py-8">
          {/* Progress Steps */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              {setupSteps.map((step, index) => {
                const StepIcon = step.icon;
                const isActive = index === currentStepIndex;
                const isCompleted = index < currentStepIndex;
                
                return (
                  <div key={step.key} className="flex items-center">
                    <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all ${
                      isCompleted ? 'bg-green-500 border-green-500 text-white' :
                      isActive ? 'bg-blue-600 border-blue-600 text-white' :
                      'bg-white border-gray-300 text-gray-400'
                    }`}>
                      {isCompleted ? <Check className="w-5 h-5" /> : <StepIcon className="w-5 h-5" />}
                    </div>
                    {index < setupSteps.length - 1 && (
                      <div className={`w-12 md:w-24 h-1 mx-2 ${
                        isCompleted ? 'bg-green-500' : 'bg-gray-200'
                      }`} />
                    )}
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between mt-2">
              {setupSteps.map((step, index) => (
                <span key={step.key} className={`text-xs md:text-sm ${
                  index === currentStepIndex ? 'text-blue-600 font-medium' : 'text-gray-500'
                }`}>
                  {step.title}
                </span>
              ))}
            </div>
          </div>

          {message && (
            <div className={`mb-6 rounded-lg p-4 ${
              message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
            }`}>
              {message.text}
            </div>
          )}

          {/* Step Content */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            {currentStep === 'name' && (
              <div className="space-y-6">
                <div className="text-center mb-8">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Bot className="w-8 h-8 text-blue-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">Let's create your AI assistant</h2>
                  <p className="text-gray-600 mt-2">What would you like to name your bot?</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Assistant Name</label>
                  <input
                    type="text"
                    value={botName}
                    onChange={(e) => setBotName(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                    placeholder="e.g., Sarah, Alex, RelayX Assistant"
                    autoFocus
                  />
                  <p className="text-sm text-gray-500 mt-2">This is how your bot will introduce itself to customers</p>
                </div>
              </div>
            )}

            {currentStep === 'business' && (
              <div className="space-y-6">
                <div className="text-center mb-8">
                  <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Building2 className="w-8 h-8 text-purple-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">What type of business do you have?</h2>
                  <p className="text-gray-600 mt-2">This helps {botName} understand your industry context</p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {BUSINESS_TYPES.map((type) => (
                    <button
                      key={type.value}
                      onClick={() => setBusinessType(type.value)}
                      className={`p-4 rounded-lg border-2 text-left transition-all ${
                        businessType === type.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <span className="text-2xl mr-2">{type.icon}</span>
                      <span className="font-medium">{type.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {currentStep === 'greeting' && (
              <div className="space-y-6">
                <div className="text-center mb-8">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <MessageSquare className="w-8 h-8 text-green-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">How should {botName} greet callers?</h2>
                  <p className="text-gray-600 mt-2">This is the first thing customers will hear</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Greeting Message</label>
                  <textarea
                    value={greeting}
                    onChange={(e) => setGreeting(e.target.value)}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Hi! Thanks for calling. How can I help you today?"
                  />
                  <p className="text-sm text-gray-500 mt-2">Keep it friendly and concise (1-2 sentences)</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-2">Preview:</p>
                  <p className="text-gray-900 italic">"{greeting}"</p>
                </div>
              </div>
            )}

            {currentStep === 'description' && (
              <div className="space-y-6">
                <div className="text-center mb-8">
                  <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Sparkles className="w-8 h-8 text-orange-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">Tell us about your business</h2>
                  <p className="text-gray-600 mt-2">{botName} will use this to answer questions</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Business Description</label>
                  <textarea
                    value={businessDescription}
                    onChange={(e) => setBusinessDescription(e.target.value)}
                    rows={5}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="We are a [type of business] that helps [target customers] with [main service/product]. Our specialty is [unique value proposition]..."
                  />
                  <p className="text-sm text-gray-500 mt-2">Include what you do, who you serve, and what makes you unique</p>
                </div>
              </div>
            )}

            {currentStep === 'review' && (
              <div className="space-y-6">
                <div className="text-center mb-8">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Check className="w-8 h-8 text-blue-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">Review Your Bot Settings</h2>
                  <p className="text-gray-600 mt-2">Make sure everything looks good before creating</p>
                </div>
                
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-700">Bot Name</p>
                    <p className="text-lg text-gray-900">{botName}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-700">Business Type</p>
                    <p className="text-lg text-gray-900">
                      {BUSINESS_TYPES.find(t => t.value === businessType)?.icon}{' '}
                      {BUSINESS_TYPES.find(t => t.value === businessType)?.label}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-700">Greeting</p>
                    <p className="text-gray-900 italic">"{greeting}"</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-700">Business Description</p>
                    <p className="text-gray-900">{businessDescription}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between mt-8 pt-6 border-t">
              <button
                onClick={prevStep}
                disabled={currentStepIndex === 0}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Back
              </button>
              
              {currentStep === 'review' ? (
                <button
                  onClick={handleCreateBot}
                  disabled={saving}
                  className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 flex items-center space-x-2"
                >
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      <span>Creating...</span>
                    </>
                  ) : (
                    <>
                      <Plus className="w-5 h-5" />
                      <span>Create Bot</span>
                    </>
                  )}
                </button>
              ) : (
                <button
                  onClick={nextStep}
                  disabled={!canProceed()}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  <span>Continue</span>
                  <ChevronRight className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // Edit Mode (when bot exists)
  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Edit Bot Settings</h1>
            <p className="text-gray-600 mt-1">
              Customize how your AI assistant talks to customers
            </p>
          </div>
          <div className="flex items-center space-x-2 px-4 py-2 bg-green-100 text-green-800 rounded-lg">
            <Check className="w-5 h-5" />
            <span className="font-medium">Bot Active</span>
          </div>
        </div>

        {message && (
          <div className={`rounded-lg p-4 ${
            message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
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
              disabled={saving || !botName.trim()}
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
            <p className="text-gray-700 mt-2 italic">"My name is {botName}, and I'm reaching out from {businessDescription.split('.')[0] || 'your company'}."</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
