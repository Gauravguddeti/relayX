import { Calendar, Target, Headphones, Phone } from 'lucide-react';
import GlassCard from './ui/glass-card';

export default function Features() {
  const features = [
    {
      icon: Calendar,
      title: 'Appointment Reminders',
      description: 'Your AI calls clients to confirm tomorrow\'s appointments.',
      gradient: 'from-blue-600 to-cyan-600'
    },
    {
      icon: Target,
      title: 'Lead Qualification',
      description: 'It asks the right questions and tags hot leads automatically.',
      gradient: 'from-teal-600 to-emerald-600'
    },
    {
      icon: Headphones,
      title: 'Customer Support',
      description: 'Answers FAQs. Creates tickets. Doesn\'t sound like a robot.',
      gradient: 'from-cyan-600 to-blue-600'
    },
    {
      icon: Phone,
      title: 'Sales Outreach',
      description: 'Follows up instantly, not "whenever the intern remembers."',
      gradient: 'from-blue-700 to-cyan-600'
    },
  ];

  return (
    <section id="features" className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <GlassCard key={index} className="p-8 group cursor-pointer">
              <div className={`bg-gradient-to-br ${feature.gradient} w-16 h-16 rounded-2xl flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                <feature.icon className="w-8 h-8 text-white" strokeWidth={2.5} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-cyan-600 group-hover:to-blue-700 group-hover:bg-clip-text transition-all">
                {feature.title}
              </h3>
              <p className="text-slate-600 leading-relaxed font-medium">
                {feature.description}
              </p>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  );
}
