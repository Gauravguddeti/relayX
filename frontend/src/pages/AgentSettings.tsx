import { useState, useEffect } from 'react';
import { Save, Plus, Edit, Trash2, Bot, MessageSquare, Building2, Sparkles, Check, ChevronRight, LayoutGrid, List as ListIcon } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import { useAuth } from '../contexts/AuthContext';
import { AgentKanbanBoard, type AgentColumn } from '../components/ui/AgentKanbanBoard';

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
  clinic: `**CONVERSATION GUIDELINES:**
**Tone & Style:**
- Friendly yet professional
- Confident but not pushy
- Empathetic and understanding (avoid robotic responses)
- Natural and conversational (avoid "I understand" or "That makes sense")

**Active Listening:**
- Let the customer speak without interruption
- Acknowledge their concerns with phrases like "I understand" or "That makes sense"
- Ask clarifying questions to show you're engaged
- Don't start pitching until you've understood their needs

**HEALTHCARE-SPECIFIC GUIDELINES:**
- Always maintain HIPAA compliance - never discuss specific medical conditions over the phone
- Be empathetic and reassuring, especially with anxious patients
- If asked about medical advice: "I'm not a licensed medical professional, but I can connect you with our nursing staff or schedule an appointment with the doctor."
- Handle emergencies: "If this is a medical emergency, please hang up and call 911 immediately. For urgent but non-emergency issues, I can connect you with our on-call nurse."
- Scheduling: Offer next available appointment, explain what to bring (insurance card, ID, previous records)
- Insurance: "We accept most major insurance plans. Our billing team can verify your coverage before your visit."

**Remember: Your goal is to make patients feel cared for and ensure they get the medical attention they need.**`,

  school: `**CONVERSATION GUIDELINES:**
**Tone & Style:**
- Friendly yet professional
- Confident but not pushy
- Empathetic and understanding (avoid robotic responses)
- Natural and conversational (avoid "I understand" or "That makes sense")

**Active Listening:**
- Let the customer speak without interruption
- Acknowledge their concerns with phrases like "I understand" or "That makes sense"
- Ask clarifying questions to show you're engaged
- Don't start pitching until you've understood their needs

**EDUCATIONAL INSTITUTION GUIDELINES:**
- Maintain student privacy (FERPA compliance) - verify caller identity before discussing student information
- Be warm and welcoming, especially to prospective families
- Show enthusiasm about the school's achievements and programs
- For enrollment inquiries: Discuss curriculum, extracurriculars, teacher-student ratio, campus tours
- For current parents: Handle attendance, grades, behavior reports professionally and privately
- Tours & Open Houses: "We'd love to show you our campus! Our next open house is [date], or we can schedule a private tour."
- Financial Aid: "We offer various financial aid options and scholarships. I can connect you with our financial aid office for details."

**Remember: You're representing the school's values and creating first impressions for prospective families.**`,

  realestate: `**CONVERSATION GUIDELINES:**
**Tone & Style:**
- Friendly yet professional
- Confident but not pushy
- Empathetic and understanding (avoid robotic responses)
- Natural and conversational (avoid "I understand" or "That makes sense")

**Active Listening:**
- Let the customer speak without interruption
- Acknowledge their concerns with phrases like "I understand" or "That makes sense"
- Ask clarifying questions to show you're engaged
- Don't start pitching until you've understood their needs

**REAL ESTATE GUIDELINES:**
- Be professional yet approachable - real estate is both a business and personal decision
- Handle objections calmly and be transparent about fees, commissions, and process
- Qualify leads: Budget, timeline, must-haves, deal-breakers, pre-approval status
- Buying: Discuss neighborhoods, schools, commute, property types, market conditions
- Selling: Discuss home value estimates, staging, photography, marketing strategy, timeline
- Create urgency (when genuine): "This is a hot market - homes in this area are selling within days"
- Never pressure: "There's no obligation. Let's find what works best for your family."
- Viewing scheduling: "I can schedule a showing as soon as today. What times work for you?"

**Remember: You're helping people with one of the biggest financial decisions of their lives - build trust.**`,

  automotive: `**CONVERSATION GUIDELINES:**
**Tone & Style:**
- Friendly yet professional
- Confident but not pushy
- Empathetic and understanding (avoid robotic responses)
- Natural and conversational (avoid "I understand" or "That makes sense")

**Active Listening:**
- Let the customer speak without interruption
- Acknowledge their concerns with phrases like "I understand" or "That makes sense"
- Ask clarifying questions to show you're engaged
- Don't start pitching until you've understood their needs

**AUTOMOTIVE/DEALERSHIP GUIDELINES:**
- Be enthusiastic about vehicles without being pushy
- Listen for buying signals: specific model interest, trade-in mentions, financing questions
- Create urgency (when genuine): limited inventory, special promotions, seasonal sales
- Qualify interest: New or used? Budget range? Trade-in? Financing or cash?
- Test drives: "Would you like to schedule a test drive? We can have it ready when you arrive."
- Trade-ins: "We offer competitive trade-in values. I can get you an estimate over the phone with your VIN."
- Financing: "We work with multiple lenders to find the best rates. Our finance team can get you pre-approved today."
- Service Department: For service calls, be efficient - ask about symptoms, mileage, service history

**Remember: Buying a car is exciting - match their enthusiasm while being informative.**`,

  restaurant: `**CONVERSATION GUIDELINES:**
**Tone & Style:**
- Friendly yet professional
- Confident but not pushy
- Empathetic and understanding (avoid robotic responses)
- Natural and conversational (avoid "I understand" or "That makes sense")

**Active Listening:**
- Let the customer speak without interruption
- Acknowledge their concerns with phrases like "I understand" or "That makes sense"
- Ask clarifying questions to show you're engaged
- Don't start pitching until you've understood their needs

**RESTAURANT/FOOD SERVICE GUIDELINES:**
- Be warm, friendly, and create excitement about the dining experience
- Handle complaints graciously and document issues
- Promote specials, happy hour, or upcoming events
- Reservations: Ask party size, date/time, special occasions (birthdays, anniversaries), dietary restrictions
- Menu questions: Describe dishes vividly, mention popular items, dietary options (vegan, gluten-free)
- Takeout/Delivery: Confirm order details, address, payment method, estimated time
- Wait times: Be honest - "We're busy tonight, but I can call you when your table is ready so you can explore the area."
- Complaints: "I'm so sorry to hear that. Let me make this right..." - offer refund, discount, or free item

**Remember: People eat with their emotions - create a memorable experience from the first call.**`,

  retail: `**CONVERSATION GUIDELINES:**
**Tone & Style:**
- Friendly yet professional
- Confident but not pushy
- Empathetic and understanding (avoid robotic responses)
- Natural and conversational (avoid "I understand" or "That makes sense")

**Active Listening:**
- Let the customer speak without interruption
- Acknowledge their concerns with phrases like "I understand" or "That makes sense"
- Ask clarifying questions to show you're engaged
- Don't start pitching until you've understood their needs

**RETAIL STORE GUIDELINES:**
- Create a personalized shopping experience over the phone
- Upsell naturally and create urgency when appropriate
- Always mention online shopping option with in-store return convenience
- Product inquiries: Ask about intended use, size/fit, budget, style preferences
- Inventory: "Let me check if we have that in stock... Yes! Would you like me to hold it for you?"
- Returns/Exchanges: Be accommodating - "Our return policy is [X days]. Do you have your receipt?"
- Sales & Promotions: "We're actually running a sale right now - [discount]. Would you like to hear about our loyalty program?"
- Gift shopping: Help with gift ideas, mention gift wrapping, gift cards

**Remember: Every call is a chance to turn a shopper into a loyal customer - be helpful and genuine.**`,

  services: `**CONVERSATION GUIDELINES:**
**Tone & Style:**
- Friendly yet professional
- Confident but not pushy
- Empathetic and understanding (avoid robotic responses)
- Natural and conversational (avoid "I understand" or "That makes sense")

**Active Listening:**
- Let the customer speak without interruption
- Acknowledge their concerns with phrases like "I understand" or "That makes sense"
- Ask clarifying questions to show you're engaged
- Don't start pitching until you've understood their needs

**PROFESSIONAL SERVICES GUIDELINES:**
- Establish credibility and professionalism immediately
- Be consultative, not salesy
- Build trust and offer resources even if they're not ready to buy
- Understand their problem: "Tell me more about what you're trying to accomplish..."
- Qualify: Budget, timeline, previous solutions tried, decision makers involved
- Consultations: "I'd love to offer you a free consultation to discuss your specific needs. Does [day/time] work?"
- Pricing: Be transparent about pricing structure (hourly, project-based, retainer)
- References: "I can send you testimonials from similar clients we've helped."
- Process: Explain your approach, timeline, deliverables clearly

**Remember: You're a trusted advisor, not a salesperson - focus on solving their problem.**`,

  technology: `**CONVERSATION GUIDELINES:**
**Tone & Style:**
- Friendly yet professional
- Confident but not pushy
- Empathetic and understanding (avoid robotic responses)
- Natural and conversational (avoid "I understand" or "That makes sense")

**Active Listening:**
- Let the customer speak without interruption
- Acknowledge their concerns with phrases like "I understand" or "That makes sense"
- Ask clarifying questions to show you're engaged
- Don't start pitching until you've understood their needs

**TECHNOLOGY/SOFTWARE GUIDELINES:**
- Speak clearly and avoid excessive jargon
- Demonstrate value through ROI and efficiency gains
- Push for free trial or pilot program when appropriate
- Understand pain points: Current solution, frustrations, team size, integration needs
- Technical support: Be patient, ask diagnostic questions, provide step-by-step guidance
- Product demos: "I can schedule a personalized demo to show you exactly how this solves [their problem]"
- Implementation: Address concerns about onboarding, training, migration from old system
- Pricing: Explain pricing tiers, what's included, compare to competitors if asked
- Security/Compliance: Highlight security features, certifications (SOC 2, GDPR, HIPAA)

**Remember: Technology can be intimidating - be the guide that makes it simple and valuable.**`,

  finance: `**CONVERSATION GUIDELINES:**
**Tone & Style:**
- Friendly yet professional
- Confident but not pushy
- Empathetic and understanding (avoid robotic responses)
- Natural and conversational (avoid "I understand" or "That makes sense")

**Active Listening:**
- Let the customer speak without interruption
- Acknowledge their concerns with phrases like "I understand" or "That makes sense"
- Ask clarifying questions to show you're engaged
- Don't start pitching until you've understood their needs

**FINANCE/BANKING GUIDELINES:**
- Maintain the highest level of professionalism and security
- NEVER ask for or discuss sensitive information over the phone
- Be transparent about fees and requirements
- Verify identity: "For security purposes, can you verify your account number and last four digits of your SSN?"
- Products: Savings accounts, checking, loans, mortgages, credit cards, investment accounts
- Fraud concerns: Take seriously - "I'm escalating this to our fraud department immediately"
- Account issues: Balance inquiries, transaction disputes, fees, overdrafts
- Applications: Explain requirements (credit score, income verification, documentation)
- Rates: Be clear about APR, APY, variable vs fixed rates, terms and conditions

**Remember: People trust you with their money - security, accuracy, and transparency are paramount.**`,

  other: `**CONVERSATION GUIDELINES:**
**Tone & Style:**
- Friendly yet professional
- Confident but not pushy
- Empathetic and understanding (avoid robotic responses)
- Natural and conversational (avoid "I understand" or "That makes sense")

**Active Listening:**
- Let the customer speak without interruption
- Acknowledge their concerns with phrases like "I understand" or "That makes sense"
- Ask clarifying questions to show you're engaged
- Don't start pitching until you've understood their needs

**GENERAL BUSINESS GUIDELINES:**
- Be professional, courteous, and adaptable
- Focus on understanding customer needs before pitching solutions
- Always look for ways to add value to the conversation
- Ask open-ended questions: "What brings you to us today?" or "What are you hoping to accomplish?"
- Qualify leads: Budget, timeline, decision-making process, urgency
- Handle objections: Listen fully, acknowledge their concern, address it directly
- Next steps: Always end with clear next steps - appointment, follow-up call, email with info
- Gratitude: Thank them for their time and interest

**Remember: Every interaction is an opportunity to build a relationship - be genuine, helpful, and professional.**`,
};

export default function AgentSettings() {
  const { userId } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [view, setView] = useState<'list' | 'edit' | 'create'>('list');
  const [listView, setListView] = useState<'grid' | 'kanban'>('kanban');

  // Editable fields
  const [agentName, setAgentName] = useState('');
  const [businessType, setBusinessType] = useState('services');
  const [greeting, setGreeting] = useState('Hi! Thanks for calling. How can I help you today?');
  const [businessDescription, setBusinessDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');

  // Helper to extract clean description from full prompt
  const getAgentDescription = (prompt: string | undefined): string => {
    if (!prompt) return "No description available";
    
    // Extract the first line which usually has "You are [name], an AI-powered..."
    const lines = prompt.split('\n');
    const firstLine = lines[0]?.trim();
    
    if (firstLine && firstLine.startsWith('You are')) {
      return firstLine;
    }
    
    // Fallback: try to find business description
    const businessDescIndex = lines.findIndex(line => line.includes('What we do:'));
    if (businessDescIndex !== -1 && lines[businessDescIndex + 1]) {
      return lines[businessDescIndex + 1].trim();
    }
    
    // Last resort: return first meaningful line
    return lines.find(line => line.trim().length > 20)?.trim() || "Professional AI voice assistant";
  }

  useEffect(() => {
    if (userId) {
      fetchAgents();
    }
  }, [userId]);

  // Auto-populate system prompt when business type changes
  useEffect(() => {
    if (businessType && SYSTEM_PROMPT_TEMPLATES[businessType]) {
      console.log('Setting system prompt for business type:', businessType);
      setSystemPrompt(SYSTEM_PROMPT_TEMPLATES[businessType]);
    }
  }, [businessType]);

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
    setGreeting('Hi! Thanks for calling. How can I help you today?');
    setBusinessDescription('');
    setBusinessType('services'); // This will trigger useEffect to set system prompt
    setView('create');
    setMessage(null);
  }

  function parsePromptFields(prompt: string) {
    const lines = prompt.split('\n');
    let foundGreeting = '';
    let foundDescription = '';
    let foundBusinessType = 'services';

    // Extract greeting - look for the line after GREETING & INTRODUCTION
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('GREETING & INTRODUCTION:')) {
        // Get the next non-empty line
        let j = i + 1;
        while (j < lines.length && !lines[j].trim()) j++;
        if (j < lines.length) {
          foundGreeting = lines[j].trim();
          // Remove the "Then introduce yourself" part if present
          if (foundGreeting.includes('Then introduce yourself')) {
            foundGreeting = foundGreeting.split('Then introduce yourself')[0].trim();
          }
        }
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

    // Set values
    if (foundGreeting) setGreeting(foundGreeting);
    if (foundDescription) setBusinessDescription(foundDescription);
    
    // Set business type - this will trigger useEffect to auto-populate system prompt template
    // The useEffect will load the correct template for this business type
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

  async function handleAgentMove(agentId: string, fromColumnId: string, toColumnId: string) {
    const newIsActive = toColumnId === 'active';
    
    try {
      const response = await fetch(`/agents/${agentId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('relayx_token')}`
        },
        body: JSON.stringify({ is_active: newIsActive })
      });

      if (!response.ok) {
        throw new Error('Failed to update agent status');
      }

      // Update local state
      setAgents(agents.map(agent => 
        agent.id === agentId ? { ...agent, is_active: newIsActive } : agent
      ));

      setMessage({
        type: 'success',
        text: `Agent ${newIsActive ? 'activated' : 'deactivated'} successfully`
      });
      
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      console.error('Error updating agent status:', error);
      setMessage({
        type: 'error',
        text: 'Failed to update agent status'
      });
      // Refresh to get correct state
      fetchAgents();
    }
  }

  function getKanbanColumns(): AgentColumn[] {
    return [
      {
        id: 'active',
        title: 'Active',
        subtitle: 'Drag here to activate agents',
        agents: agents.filter(a => a.is_active).map(a => ({
          id: a.id,
          name: a.name,
          prompt_text: a.prompt_text,
          user_id: a.user_id,
          created_at: a.created_at
        }))
      },
      {
        id: 'deactivated',
        title: 'Deactivated',
        subtitle: 'Drag here to deactivate agents',
        agents: agents.filter(a => !a.is_active).map(a => ({
          id: a.id,
          name: a.name,
          prompt_text: a.prompt_text,
          user_id: a.user_id,
          created_at: a.created_at
        }))
      }
    ];
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
              <h1 className="text-3xl font-bold text-text">My Agents</h1>
              <p className="text-text-secondary mt-1">Manage your AI voice assistants</p>
            </div>
            <div className="flex items-center gap-3">
              {/* View Toggle */}
              <div className="flex items-center gap-1 bg-lighter rounded-lg p-1">
                <button
                  onClick={() => setListView('kanban')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${
                    listView === 'kanban' 
                      ? 'bg-primary text-darker font-medium' 
                      : 'text-text-secondary hover:text-text'
                  }`}
                >
                  <LayoutGrid className="w-4 h-4" />
                  <span className="text-sm">Kanban</span>
                </button>
                <button
                  onClick={() => setListView('grid')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${
                    listView === 'grid' 
                      ? 'bg-primary text-darker font-medium' 
                      : 'text-text-secondary hover:text-text'
                  }`}
                >
                  <ListIcon className="w-4 h-4" />
                  <span className="text-sm">Grid</span>
                </button>
              </div>
              
              <button
                onClick={handleNewAgent}
                className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-5 h-5" />
                <span>New Agent</span>
              </button>
            </div>
          </div>

          {message && (
            <div className={`rounded-lg p-4 ${message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
              {message.text}
            </div>
          )}

          {agents.length === 0 ? (
            <div className="bg-lighter rounded-lg shadow p-12 text-center border border-border">
              <Bot className="w-16 h-16 text-text-secondary mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-text mb-2">No agents yet</h3>
              <p className="text-text-secondary mb-6">Create your first AI voice assistant to start making calls</p>
              <button
                onClick={handleNewAgent}
                className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-5 h-5" />
                <span>Create Your First Agent</span>
              </button>
            </div>
          ) : listView === 'kanban' ? (
            /* Kanban Board View */
            <div>
              <div className="mb-6 p-5 bg-gradient-to-r from-primary/5 to-primary/10 rounded-xl border border-primary/20 backdrop-blur-sm">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center border border-primary/30">
                    <span className="text-xl">💡</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-text mb-1">How to manage agents</h3>
                    <p className="text-sm text-text-secondary/90 leading-relaxed">
                      Drag agents between columns to activate or deactivate them. 
                      <span className="font-medium text-text"> Active agents</span> can receive calls and appear in your dashboard, 
                      while <span className="font-medium text-text-secondary">deactivated agents</span> are hidden but retained for future use.
                    </p>
                  </div>
                </div>
              </div>
              <AgentKanbanBoard
                columns={getKanbanColumns()}
                onAgentMove={handleAgentMove}
                onAgentEdit={(agentId) => {
                  const agent = agents.find(a => a.id === agentId);
                  if (agent) handleEditAgent(agent);
                }}
                onAgentDelete={handleDeleteAgent}
              />
            </div>
          ) : (
            /* Grid View */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className="bg-lighter rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-2 border-border hover:border-primary"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center">
                        <Bot className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-text">{agent.name}</h3>
                        <span className={`text-xs px-2 py-1 rounded-full ${agent.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                          {agent.is_active ? 'Active' : 'Deactivated'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2 mb-4">
                    <p className="text-sm text-text-secondary line-clamp-3">
                      {getAgentDescription(agent.prompt_text)}
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
                      className="px-4 py-2 bg-red-600/10 text-red-400 rounded-lg hover:bg-red-600/20"
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
            <h1 className="text-3xl font-bold text-text">
              {view === 'create' ? 'Create New Agent' : 'Edit Agent'}
            </h1>
            <p className="text-text-secondary mt-1">Configure your AI voice assistant</p>
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
              onChange={(e) => {
                const newBusinessType = e.target.value;
                setBusinessType(newBusinessType);
                // Immediately update system prompt when business type changes
                if (newBusinessType && SYSTEM_PROMPT_TEMPLATES[newBusinessType]) {
                  setSystemPrompt(SYSTEM_PROMPT_TEMPLATES[newBusinessType]);
                }
              }}
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
