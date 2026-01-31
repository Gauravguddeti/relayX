import { Link } from 'react-router-dom';
import { ArrowLeft, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function Pricing() {
  const plans = [
    {
      name: 'Starter',
      price: '₹499',
      period: '/month',
      description: 'Perfect for small businesses getting started',
      features: [
        '100 minutes included',
        'Basic AI voice agent',
        'Email support',
        'Analytics dashboard',
        'Single phone number',
      ],
      cta: 'Get Started',
      highlighted: false,
    },
    {
      name: 'Pay As You Go',
      price: '₹8',
      period: '/call',
      description: 'Flexible pricing for growing businesses',
      features: [
        'No monthly commitment',
        'Advanced AI capabilities',
        'Priority support',
        'Full analytics suite',
        'Multiple phone numbers',
        'Custom voice training',
      ],
      cta: 'Start Now',
      highlighted: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'For large teams with custom needs',
      features: [
        'Unlimited calls',
        'Dedicated account manager',
        '24/7 premium support',
        'Custom integrations',
        'SLA guarantee',
        'Advanced security',
      ],
      cta: 'Contact Sales',
      highlighted: false,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <div className="border-b border-slate-700/50 backdrop-blur-xl bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to home
          </Link>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-20">
        {/* Title */}
        <div className="text-center mb-16">
          <Badge variant="outline" className="text-cyan-400 border-cyan-400 mb-4">
            Pricing
          </Badge>
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Choose the plan that fits your business. No hidden fees, cancel anytime.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={`relative flex flex-col ${
                plan.highlighted
                  ? 'bg-gradient-to-br from-blue-50 to-cyan-50 border-cyan-300'
                  : 'bg-white/95 border-slate-200'
              } backdrop-blur-xl shadow-2xl`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <Badge className="bg-gradient-to-r from-cyan-500 to-blue-500 text-black font-bold px-4 py-1">
                    Most Popular
                  </Badge>
                </div>
              )}

              <CardHeader className="text-center pb-8 pt-8">
                <CardTitle className={`text-2xl font-bold mb-2 ${
                  plan.highlighted ? 'text-slate-800' : 'text-slate-900'
                }`}>
                  {plan.name}
                </CardTitle>
                <CardDescription className={`${
                  plan.highlighted ? 'text-slate-600' : 'text-slate-500'
                }`}>
                  {plan.description}
                </CardDescription>
                <div className="mt-6">
                  <span className={`text-5xl font-bold ${
                    plan.highlighted ? 'text-slate-800' : 'text-slate-900'
                  }`}>
                    {plan.price}
                  </span>
                  {plan.period && (
                    <span className={`text-lg ${
                      plan.highlighted ? 'text-slate-600' : 'text-slate-500'
                    }`}>{plan.period}</span>
                  )}
                </div>
              </CardHeader>

              <CardContent className="flex-1 flex flex-col">
                <ul className="space-y-4 mb-8 flex-1">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-cyan-500 flex-shrink-0 mt-0.5" />
                      <span className={`${
                        plan.highlighted ? 'text-slate-700' : 'text-slate-600'
                      }`}>{feature}</span>
                    </li>
                  ))}
                </ul>

                <Link to="/signup" className="block mt-auto">
                  <Button
                    className={`w-full h-12 text-base font-bold ${
                      plan.highlighted
                        ? 'bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-black'
                        : 'bg-slate-800 hover:bg-slate-900 text-white'
                    }`}
                  >
                    {plan.cta}
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* FAQ or Additional Info */}
        <div className="mt-20 text-center">
          <p className="text-slate-400 text-lg">
            Need a custom solution?{' '}
            <Link to="/signup" className="text-cyan-400 hover:text-cyan-300 font-semibold">
              Contact our sales team
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
