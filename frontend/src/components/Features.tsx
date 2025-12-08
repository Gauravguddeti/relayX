import { Calendar, Target, Headphones, Phone } from 'lucide-react';

export default function Features() {
  const features = [
    {
      icon: Calendar,
      title: 'Appointment Reminders',
      description: 'Your AI calls clients to confirm tomorrow\'s appointments.',
    },
    {
      icon: Target,
      title: 'Lead Qualification',
      description: 'It asks the right questions and tags hot leads automatically.',
    },
    {
      icon: Headphones,
      title: 'Customer Support',
      description: 'Answers FAQs. Creates tickets. Doesn\'t sound like a robot.',
    },
    {
      icon: Phone,
      title: 'Sales Outreach',
      description: 'Follows up instantly, not "whenever the intern remembers."',
    },
  ];

  return (
    <section className="py-24 px-6 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="group">
              <div className="bg-blue-50 w-14 h-14 rounded-xl flex items-center justify-center mb-5 group-hover:bg-blue-100 transition-colors">
                <feature.icon className="w-7 h-7 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-slate-600 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
