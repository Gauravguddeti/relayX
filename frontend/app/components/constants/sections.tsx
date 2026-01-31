import { Badge } from "../ui/badge"

export const sections = [
  { 
    id: 'hero', 
    subtitle: <Badge variant="outline" className="text-white border-white">S1: Feb 15</Badge>,
    title: "It's time to build.",
    showButton: true,
    buttonText: 'apply to s5'
  },
  { 
    id: 'about', 
    title: 'Why Us?', 
    content: 'We provide resources, mentorship, and a supportive network to help you grow your projects.' 
  },
  { 
    id: 'features', 
    title: 'What We Offer', 
    content: 'Access to expert advice, networking opportunities, and cutting-edge tools to accelerate your growth.' 
  },
  { 
    id: 'testimonials', 
    title: 'Success Stories', 
    content: 'Hear from solo builders who have transformed their side projects into thriving businesses.' 
  },
  { 
    id: 'join', 
    title: 'Get Started', 
    content: 'Ready to take your side project to the next level? Join our community today and start building your future.',
    showButton: true,
    buttonText: 'Join Now'
  },
]
