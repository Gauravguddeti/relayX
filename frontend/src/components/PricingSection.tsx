import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Check } from "lucide-react"

export default function PricingSection() {
  const plans = [
    {
      name: "Starter",
      price: "₹499",
      period: "/month",
      description: "Perfect for trying out AI voice calling",
      features: [
        "50 minutes included",
        "1 AI agent",
        "Email support",
        "Basic analytics",
        "Standard voice quality"
      ],
      cta: "Get Started",
      popular: false
    },
    {
      name: "Pay As You Go",
      price: "₹8",
      period: "/completed call",
      description: "Only pay for successful conversations",
      features: [
        "No monthly commitment",
        "Unlimited agents",
        "Priority support",
        "Advanced analytics",
        "Premium voice quality",
        "Pay only for usage"
      ],
      cta: "Start Calling",
      popular: true
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "",
      description: "Tailored solutions for your business",
      features: [
        "Unlimited everything",
        "Dedicated support team",
        "White label solution",
        "Custom integrations",
        "SLA guarantee",
        "Priority onboarding"
      ],
      cta: "Contact Sales",
      popular: false
    }
  ]

  return (
    <section id="pricing" className="py-24 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Choose the plan that fits your needs. Start free, scale as you grow.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <Card 
              key={plan.name}
              className={`relative ${
                plan.popular 
                  ? 'border-2 border-blue-600 shadow-xl' 
                  : 'border border-slate-200'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <Badge className="bg-blue-600 text-white px-4 py-1">
                    Most Popular
                  </Badge>
                </div>
              )}
              
              <CardHeader>
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <CardDescription>{plan.description}</CardDescription>
                <div className="mt-4">
                  <span className="text-4xl font-bold text-slate-900">
                    {plan.price}
                  </span>
                  {plan.period && (
                    <span className="text-slate-600 text-lg ml-1">
                      {plan.period}
                    </span>
                  )}
                </div>
              </CardHeader>

              <CardContent>
                <ul className="space-y-3">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <span className="text-slate-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>

              <CardFooter>
                <Button 
                  className="w-full"
                  variant={plan.popular ? "default" : "outline"}
                  size="lg"
                >
                  {plan.cta}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
