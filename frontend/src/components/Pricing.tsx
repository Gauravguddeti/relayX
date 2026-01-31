import { ArrowRight, Sparkles, Check } from 'lucide-react';
import GlassCard from './ui/glass-card';

export default function Pricing() {
  const plans = [
    { 
      name: 'Starter', 
      price: '₹499', 
      period: '/mo',
      features: ['50 minutes included', '1 AI agent', 'Email support', 'Basic analytics'],
      gradient: 'from-blue-600 to-cyan-600'
    },
    { 
      name: 'Pay As You Go', 
      price: '₹2/min', 
      period: '',
      features: ['No monthly fee', 'Unlimited agents', 'Priority support', 'Advanced analytics', 'Pay only for usage'],
      gradient: 'from-teal-600 to-emerald-600',
      popular: true
    },
    { 
      name: 'Enterprise', 
      price: 'Custom', 
      period: '',
      features: ['Unlimited everything', 'Dedicated support', 'White label', 'Custom integrations', 'SLA guarantee'],
      gradient: 'from-cyan-600 to-blue-700'
    },
  ];

  return (
    <section id="pricing" className="py-32 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <h2 className="text-5xl md:text-6xl font-black mb-6">
            <span className="bg-gradient-to-r from-blue-700 to-cyan-600 bg-clip-text text-transparent">
              Simple Pricing
            </span>
          </h2>
          <p className="text-xl text-slate-600 font-medium">
            Pay only for minutes you use. No hidden fees. Cancel anytime.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {plans.map((plan, index) => (
            <div key={index} className="relative">
              {plan.popular && (
                <div className="absolute -top-5 left-1/2 -translate-x-1/2 z-20">
                  <div className="bg-gradient-to-r from-teal-600 to-emerald-600 text-white px-4 py-1.5 rounded-full text-sm font-bold shadow-lg flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5" />
                    Most Popular
                  </div>
                </div>
              )}
              <GlassCard
                className={`p-8 h-full ${
                  plan.popular ? 'ring-2 ring-teal-400/50 shadow-2xl shadow-teal-500/20' : ''
                }`}
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${plan.gradient} flex items-center justify-center mb-6 shadow-lg`}>
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                
                <h3 className="text-2xl font-bold text-slate-900 mb-2">
                  {plan.name}
                </h3>
                <div className="mb-8">
                  <span className="text-5xl font-black bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
                    {plan.price}
                  </span>
                  <span className="text-slate-600 text-lg font-semibold">{plan.period}</span>
                </div>

                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <div className={`w-5 h-5 rounded-full bg-gradient-to-br ${plan.gradient} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                        <Check className="w-3 h-3 text-white" strokeWidth={3} />
                      </div>
                      <span className="text-slate-700 font-medium">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  className={`w-full py-4 rounded-xl font-bold transition-all group flex items-center justify-center gap-2 ${
                    plan.popular
                      ? 'bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white shadow-xl hover:shadow-2xl hover:scale-105'
                      : 'bg-white/80 backdrop-blur-md hover:bg-white text-slate-900 border-2 border-cyan-200/50 hover:border-cyan-400 shadow-lg hover:shadow-xl hover:scale-105'
                  }`}
                >
                  Get Started
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>
              </GlassCard>
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
