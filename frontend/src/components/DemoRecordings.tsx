import { Play } from 'lucide-react';

export default function DemoRecordings() {
  const recordings = [
    {
      title: 'Clinic Reminder',
      duration: '0:43',
      description: 'Confirming dental appointment',
    },
    {
      title: 'Real Estate Inquiry',
      duration: '1:12',
      description: 'Qualifying property buyer',
    },
    {
      title: 'Lead Qualification',
      duration: '0:58',
      description: 'B2B software demo request',
    },
  ];

  return (
    <section className="py-24 px-6 bg-slate-50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            Hear It Handle Real Phone Calls
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {recordings.map((recording, index) => (
            <div
              key={index}
              className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow border border-slate-200"
            >
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">
                    {recording.title}
                  </h3>
                  <p className="text-sm text-slate-500">{recording.description}</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <button className="bg-blue-600 hover:bg-blue-700 w-12 h-12 rounded-full flex items-center justify-center transition-colors shadow-md">
                  <Play className="w-5 h-5 text-white ml-0.5" fill="currentColor" />
                </button>
                <div className="flex-1">
                  <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-600 w-0 rounded-full"></div>
                  </div>
                  <div className="text-xs text-slate-500 mt-2">{recording.duration}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
