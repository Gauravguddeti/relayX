import { CheckCircle } from 'lucide-react';

export default function FeatureGrid() {
  const features = [
    'Natural AI conversations',
    'Outbound calling via Twilio',
    'Knowledge base support (RAG integrated)',
    'Call recordings & transcripts',
    'Sentiment analysis',
    'Appointment booking flows',
    'Lead qualification templates',
    'Real-time dashboard',
  ];

  return (
    <section className="py-24 px-6 bg-slate-50">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-3xl p-12 shadow-sm border border-slate-200">
          <h2 className="text-3xl font-bold text-slate-900 mb-12 text-center">
            Everything You Need
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <div key={index} className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <span className="text-slate-700">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
