import { Badge } from "@/components/ui/badge"

export const sections = [
  { 
    id: 'hero', 
    subtitle: <Badge variant="outline" className="text-white border-white">AI Voice Calling</Badge>,
    title: "Ready to Automate?",
    content: 'Join thousands of businesses using AI to handle their phone calls. Setup in 5 minutes.',
    showButton: true,
    buttonText: 'Get Started Free'
  },
  { 
    id: 'about', 
    title: 'Why RelayX?', 
    content: 'Automate your calls with human-like AI agents. Available 24/7, never misses a beat.' 
  },
  { 
    id: 'features', 
    title: 'What We Offer', 
    content: 'Appointment reminders, lead qualification, customer support, and sales outreach - all automated.',
    showButton: true,
    buttonText: 'View Pricing'
  },
  { 
    id: 'pricing', 
    title: 'Try It Now', 
    content: 'Test our AI voice agent with a free call. Start from ₹499/month or pay ₹8 per call.',
    showButton: true,
    buttonText: 'Test Call Now'
  },
  { 
    id: 'join', 
    title: 'Ready to Scale?', 
    content: 'Get started today with full access. Enterprise solutions available for growing teams.',
    showButton: true,
    buttonText: 'Sign Up'
  },
]
