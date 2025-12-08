import { X, CheckCircle } from 'lucide-react';

export default function PainSolution() {
  const pains = [
    'Forget follow-ups',
    'Sound bored',
    'Quit',
    'Cost too much',
  ];

  const solutions = [
    'Faster',
    'Cheaper',
    'Perfectly consistent',
    'Scalable',
    'With analytics you can actually use',
  ];

  return (
    <section className="py-24 px-6 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 gap-16">
          <div>
            <h2 className="text-3xl font-bold text-slate-900 mb-6">
              The Pain
            </h2>
            <p className="text-lg text-slate-600 mb-8">
              Businesses waste money on telecallers who:
            </p>
            <div className="space-y-4">
              {pains.map((pain, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="bg-red-50 rounded-full p-1 mt-1">
                    <X className="w-4 h-4 text-red-600" />
                  </div>
                  <span className="text-slate-700 text-lg">{pain}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h2 className="text-3xl font-bold text-slate-900 mb-6">
              Your Solution
            </h2>
            <p className="text-lg text-slate-600 mb-8">
              RelayX does the same work:
            </p>
            <div className="space-y-4">
              {solutions.map((solution, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="bg-green-50 rounded-full p-1 mt-1">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  </div>
                  <span className="text-slate-700 text-lg">{solution}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
