import { ArrowRight } from 'lucide-react';

export default function Pricing() {
  const plans = [
    { name: 'Starter', price: '₹999', period: '/mo' },
    { name: 'Growth', price: '₹3999', period: '/mo' },
    { name: 'Pro', price: '₹9999', period: '/mo' },
  ];

  return (
    <section className="py-24 px-6 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            Simple Pricing
          </h2>
          <p className="text-lg text-slate-600">
            Pay only for minutes you use.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`rounded-2xl p-8 border-2 transition-all hover:shadow-lg ${
                index === 1
                  ? 'border-blue-600 shadow-md bg-blue-50'
                  : 'border-slate-200 bg-white'
              }`}
            >
              <h3 className="text-xl font-bold text-slate-900 mb-2">
                {plan.name}
              </h3>
              <div className="mb-6">
                <span className="text-4xl font-bold text-slate-900">
                  {plan.price}
                </span>
                <span className="text-slate-600">{plan.period}</span>
              </div>
              <button
                className={`w-full py-3 rounded-lg font-semibold transition-all ${
                  index === 1
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-900'
                }`}
              >
                Get Started
              </button>
            </div>
          ))}
        </div>

        <div className="text-center">
          <button className="text-blue-600 hover:text-blue-700 font-semibold inline-flex items-center gap-2">
            See full pricing
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </section>
  );
}
