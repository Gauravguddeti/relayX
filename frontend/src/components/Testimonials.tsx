import { Star } from 'lucide-react';

export default function Testimonials() {
  const testimonials = [
    {
      quote: 'Saved us 40 hours a week on follow-ups.',
      author: 'Sarah Mitchell',
      role: 'Operations Manager',
    },
    {
      quote: 'Booked 37% more appointments.',
      author: 'James Chen',
      role: 'Clinic Director',
    },
    {
      quote: 'Our sales team hates how good this is.',
      author: 'Michael Roberts',
      role: 'Sales VP',
    },
  ];

  return (
    <section className="py-24 px-6 bg-slate-50">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200"
            >
              <div className="flex gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 text-yellow-400" fill="currentColor" />
                ))}
              </div>
              <p className="text-lg text-slate-900 mb-6 font-medium">
                "{testimonial.quote}"
              </p>
              <div>
                <div className="font-semibold text-slate-900">{testimonial.author}</div>
                <div className="text-sm text-slate-500">{testimonial.role}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
