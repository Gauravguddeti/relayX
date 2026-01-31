import { useState, useEffect } from 'react';
import { Save, Plus, Edit, Trash2, Bot, LayoutGrid, List as ListIcon } from 'lucide-react';
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
  voice_settings?: {
    vad_mode?: number;
    silence_threshold_ms?: number;
    min_audio_duration_ms?: number;
    min_speech_energy?: number;
    echo_ignore_ms?: number;
    speech_start_ms?: number;
    speech_end_ms?: number;
    tts_voice?: string;
    preset?: string;
  };
  user_id?: string;
  created_at?: string;
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

// Voice settings presets for different call scenarios
const VOICE_PRESETS = {
  balanced: {
    label: 'Balanced (Recommended)',
    description: 'Best for most scenarios with good call quality',
    icon: '⚖️',
    settings: {
      vad_mode: 2,
      silence_threshold_ms: 600,
      min_audio_duration_ms: 400,
      min_speech_energy: 30,
      echo_ignore_ms: 400,
      speech_start_ms: 200,
      speech_end_ms: 240,
    }
  },
  fast: {
    label: 'Fast & Responsive',
    description: 'Quick responses, ideal for clean connections',
    icon: '⚡',
    settings: {
      vad_mode: 1,
      silence_threshold_ms: 500,
      min_audio_duration_ms: 300,
      min_speech_energy: 25,
      echo_ignore_ms: 300,
      speech_start_ms: 150,
      speech_end_ms: 200,
    }
  },
  conservative: {
    label: 'Conservative',
    description: 'Fewer interruptions, better for noisy environments',
    icon: '🛡️',
    settings: {
      vad_mode: 3,
      silence_threshold_ms: 800,
      min_audio_duration_ms: 500,
      min_speech_energy: 40,
      echo_ignore_ms: 500,
      speech_start_ms: 250,
      speech_end_ms: 300,
    }
  },
  mobile: {
    label: 'Mobile Optimized',
    description: 'Tuned for cellular connections with variable quality',
    icon: '📱',
    settings: {
      vad_mode: 2,
      silence_threshold_ms: 700,
      min_audio_duration_ms: 450,
      min_speech_energy: 35,
      echo_ignore_ms: 450,
      speech_start_ms: 220,
      speech_end_ms: 260,
    }
  },
  custom: {
    label: 'Custom',
    description: 'Manually configure all voice settings',
    icon: '🎛️',
    settings: {
      vad_mode: 2,
      silence_threshold_ms: 600,
      min_audio_duration_ms: 400,
      min_speech_energy: 30,
      echo_ignore_ms: 400,
      speech_start_ms: 200,
      speech_end_ms: 240,
    }
  }
};

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

  // Voice settings state
  const [showVoiceSettings, setShowVoiceSettings] = useState(false);
  const [voiceSettingsPreset, setVoiceSettingsPreset] = useState('balanced');
  const [vadMode, setVadMode] = useState(2);
  const [silenceThreshold, setSilenceThreshold] = useState(600);
  const [minAudioDuration, setMinAudioDuration] = useState(400);
  const [minSpeechEnergy, setMinSpeechEnergy] = useState(30);
  const [echoIgnore, setEchoIgnore] = useState(400);
  const [speechStartMs, setSpeechStartMs] = useState(200);
  const [speechEndMs, setSpeechEndMs] = useState(240);

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

  // Auto-populate system prompt when business type changes (only for new agents, not when editing)
  useEffect(() => {
    // Only auto-populate if:
    // 1. We're in create mode
    // 2. System prompt is empty or matches the default template
    // 3. Business type changed
    if (view === 'create' && businessType && SYSTEM_PROMPT_TEMPLATES[businessType]) {
      const isEmptyOrDefault = !systemPrompt || systemPrompt.length < 100 || 
                               Object.values(SYSTEM_PROMPT_TEMPLATES).includes(systemPrompt);
      if (isEmptyOrDefault) {
        setSystemPrompt(SYSTEM_PROMPT_TEMPLATES[businessType]);
      }
    }
  }, [businessType, view]);

  async function fetchAgents() {
    try {
      const response = await fetch(`/agents?user_id=${userId}`);
      if (!response.ok) {
        setLoading(false);
        return;
      }
      const data = await response.json();
      const agentList = Array.isArray(data) ? data : [];
      const userAgents = agentList.filter((a: Agent) => a.user_id === userId);
      setAgents(userAgents);
      setLoading(false);
    } catch (error) {
      setAgents([]);
      setLoading(false);
    }
  }

  function handleEditAgent(agent: Agent) {
    setSelectedAgent(agent);
    setAgentName(agent.name);
    setView('edit'); // Set view FIRST before parsing
    parsePromptFields(agent.prompt_text || agent.resolved_system_prompt || '');
    
    // Load voice settings if they exist
    if (agent.voice_settings && Object.keys(agent.voice_settings).length > 0) {
      const vs = agent.voice_settings;
      setVadMode(vs.vad_mode ?? 2);
      setSilenceThreshold(vs.silence_threshold_ms ?? 600);
      setMinAudioDuration(vs.min_audio_duration_ms ?? 400);
      setMinSpeechEnergy(vs.min_speech_energy ?? 30);
      setEchoIgnore(vs.echo_ignore_ms ?? 400);
      setSpeechStartMs(vs.speech_start_ms ?? 200);
      setSpeechEndMs(vs.speech_end_ms ?? 240);
      setVoiceSettingsPreset(vs.preset ?? 'balanced');
    } else {
      // Use default balanced preset
      applyVoicePreset('balanced');
    }
    
    setMessage(null);
    // Scroll to top when switching views
    window.scrollTo(0, 0);
  }

  function handleNewAgent() {
    setSelectedAgent(null);
    setAgentName('');
    setGreeting('Hi! Thanks for calling. How can I help you today?');
    setBusinessDescription('');
    setBusinessType('services'); // This will trigger useEffect to set system prompt
    applyVoicePreset('balanced'); // Set default voice settings
    setView('create');
    setMessage(null);
    // Scroll to top when switching views
    window.scrollTo(0, 0);
  }

  function parsePromptFields(prompt: string) {
    // For editing: Always show the FULL prompt in the System Prompt field
    // Don't try to parse it - let user see exactly what's in the database
    setSystemPrompt(prompt);
    
    // Still try to extract other fields for convenience
    const lines = prompt.split('\n');
    let foundGreeting = '';
    let foundDescription = '';
    let foundBusinessType: string = 'other';

    // Extract greeting if it exists
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('GREETING & INTRODUCTION:')) {
        let j = i + 1;
        while (j < lines.length && !lines[j].trim()) j++;
        if (j < lines.length) {
          foundGreeting = lines[j].trim();
          if (foundGreeting.includes('Then introduce yourself')) {
            foundGreeting = foundGreeting.split('Then introduce yourself')[0].trim();
          }
        }
        break;
      }
    }

    // Extract business description if it exists
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('What we do:')) {
        const sameLine = lines[i].split('What we do:')[1]?.trim();
        if (sameLine) {
          foundDescription = sameLine;
        } else {
          foundDescription = lines[i + 1]?.trim() || '';
        }
        break;
      }
    }

    // Extract business type if it exists
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('Industry:')) {
        const industry = lines[i].split(':')[1]?.trim().toLowerCase();
        const matched = BUSINESS_TYPES.find(t =>
          t.label.toLowerCase().includes(industry) || industry.includes(t.value)
        );
        if (matched) {
          foundBusinessType = matched.value;
          setBusinessType(matched.value); // Apply the found business type
        }
        break;
      }
    }

    // Apply parsed values if found
    if (foundGreeting) setGreeting(foundGreeting);
    if (foundDescription) setBusinessDescription(foundDescription);

    console.log('Parsed values:');
    console.log('- greeting:', foundGreeting);
    console.log('- description:', foundDescription);
    console.log('- business type:', foundBusinessType);
  }

  // Helper function to apply voice preset
  function applyVoicePreset(presetName: string) {
    const preset = VOICE_PRESETS[presetName as keyof typeof VOICE_PRESETS];
    if (preset) {
      setVadMode(preset.settings.vad_mode);
      setSilenceThreshold(preset.settings.silence_threshold_ms);
      setMinAudioDuration(preset.settings.min_audio_duration_ms);
      setMinSpeechEnergy(preset.settings.min_speech_energy);
      setEchoIgnore(preset.settings.echo_ignore_ms);
      setSpeechStartMs(preset.settings.speech_start_ms);
      setSpeechEndMs(preset.settings.speech_end_ms);
      setVoiceSettingsPreset(presetName);
    }
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
      
      // Build voice settings object
      const voice_settings = {
        vad_mode: vadMode,
        silence_threshold_ms: silenceThreshold,
        min_audio_duration_ms: minAudioDuration,
        min_speech_energy: minSpeechEnergy,
        echo_ignore_ms: echoIgnore,
        speech_start_ms: speechStartMs,
        speech_end_ms: speechEndMs,
        preset: voiceSettingsPreset,
      };

      if (view === 'create') {
        // Create new agent
        const response = await fetch('/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: agentName,
            prompt_text: prompt,
            voice_settings,
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
            voice_settings,
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

  async function handleAgentMove(agentId: string, _fromColumnId: string, toColumnId: string) {
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
          user_id: a.user_id || '',
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
          user_id: a.user_id || '',
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
            onClick={() => {
              setView('list');
              window.scrollTo(0, 0);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg border border-gray-300 transition-colors font-medium"
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

          {/* Voice Settings Section */}
          <div className="border-t pt-6">
            <button
              type="button"
              onClick={() => setShowVoiceSettings(!showVoiceSettings)}
              className="flex items-center justify-between w-full mb-4"
            >
              <div>
                <h3 className="text-lg font-semibold text-gray-900">🎙️ Voice & Audio Settings</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Configure voice detection, silence thresholds, and audio processing
                </p>
              </div>
              <span className="text-2xl text-gray-400">
                {showVoiceSettings ? '▼' : '▶'}
              </span>
            </button>

            {showVoiceSettings && (
              <div className="space-y-6 bg-gray-50 p-6 rounded-lg">
                {/* Preset Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Voice Settings Preset
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(VOICE_PRESETS).map(([key, preset]) => (
                      <button
                        key={key}
                        type="button"
                        onClick={() => applyVoicePreset(key)}
                        className={`p-4 rounded-lg border-2 text-left transition-all ${
                          voiceSettingsPreset === key
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-300 bg-white hover:border-gray-400'
                        }`}
                      >
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-2xl">{preset.icon}</span>
                          <span className="font-semibold text-gray-900">{preset.label}</span>
                        </div>
                        <p className="text-xs text-gray-600">{preset.description}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Advanced Settings (only show for custom preset) */}
                {voiceSettingsPreset === 'custom' && (
                  <div className="space-y-4 pt-4 border-t border-gray-300">
                    <h4 className="font-medium text-gray-900">Advanced Configuration</h4>
                    
                    {/* VAD Mode */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        VAD Mode (Voice Activity Detection): {vadMode}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="3"
                        step="1"
                        value={vadMode}
                        onChange={(e) => setVadMode(Number(e.target.value))}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>0 - Least Aggressive</span>
                        <span>3 - Most Aggressive</span>
                      </div>
                      <p className="text-xs text-gray-600 mt-1">
                        Higher values filter more noise but may cut off speech
                      </p>
                    </div>

                    {/* Silence Threshold */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Silence Threshold: {silenceThreshold}ms
                      </label>
                      <input
                        type="range"
                        min="300"
                        max="1200"
                        step="50"
                        value={silenceThreshold}
                        onChange={(e) => setSilenceThreshold(Number(e.target.value))}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-600 mt-1">
                        How long to wait after user stops speaking before processing
                      </p>
                    </div>

                    {/* Min Audio Duration */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Minimum Audio Duration: {minAudioDuration}ms
                      </label>
                      <input
                        type="range"
                        min="200"
                        max="800"
                        step="50"
                        value={minAudioDuration}
                        onChange={(e) => setMinAudioDuration(Number(e.target.value))}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-600 mt-1">
                        Minimum speech duration to process (filters out noise)
                      </p>
                    </div>

                    {/* Min Speech Energy */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Minimum Speech Energy: {minSpeechEnergy}
                      </label>
                      <input
                        type="range"
                        min="10"
                        max="80"
                        step="5"
                        value={minSpeechEnergy}
                        onChange={(e) => setMinSpeechEnergy(Number(e.target.value))}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-600 mt-1">
                        Energy threshold to distinguish speech from silence
                      </p>
                    </div>

                    {/* Echo Ignore Window */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Echo Ignore Window: {echoIgnore}ms
                      </label>
                      <input
                        type="range"
                        min="200"
                        max="800"
                        step="50"
                        value={echoIgnore}
                        onChange={(e) => setEchoIgnore(Number(e.target.value))}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-600 mt-1">
                        Ignore incoming audio for this duration after AI finishes speaking
                      </p>
                    </div>

                    {/* Speech Start Threshold */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Speech Start Threshold: {speechStartMs}ms
                      </label>
                      <input
                        type="range"
                        min="100"
                        max="500"
                        step="50"
                        value={speechStartMs}
                        onChange={(e) => setSpeechStartMs(Number(e.target.value))}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-600 mt-1">
                        Duration of continuous speech needed to trigger detection
                      </p>
                    </div>

                    {/* Speech End Threshold */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Speech End Threshold: {speechEndMs}ms
                      </label>
                      <input
                        type="range"
                        min="100"
                        max="500"
                        step="20"
                        value={speechEndMs}
                        onChange={(e) => setSpeechEndMs(Number(e.target.value))}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-600 mt-1">
                        Duration of silence needed to mark speech as ended
                      </p>
                    </div>
                  </div>
                )}

                {/* Current Settings Summary (for non-custom presets) */}
                {voiceSettingsPreset !== 'custom' && (
                  <div className="bg-white p-4 rounded border border-gray-200">
                    <h4 className="font-medium text-gray-900 mb-3">Current Settings</h4>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <span className="text-gray-600">VAD Mode:</span>
                        <span className="ml-2 font-medium">{vadMode}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Silence Threshold:</span>
                        <span className="ml-2 font-medium">{silenceThreshold}ms</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Min Audio Duration:</span>
                        <span className="ml-2 font-medium">{minAudioDuration}ms</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Min Speech Energy:</span>
                        <span className="ml-2 font-medium">{minSpeechEnergy}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Echo Ignore:</span>
                        <span className="ml-2 font-medium">{echoIgnore}ms</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Speech Start:</span>
                        <span className="ml-2 font-medium">{speechStartMs}ms</span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => applyVoicePreset('custom')}
                      className="mt-3 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg border border-blue-200 transition-colors font-medium text-sm"
                    >
                      Customize these settings →
                    </button>
                  </div>
                )}
              </div>
            )}
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
