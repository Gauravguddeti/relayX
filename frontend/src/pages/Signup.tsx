import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Phone, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name }),
      });

      if (response.ok) {
        const data = await response.json();
        login(data.user_id);
        navigate('/dashboard');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create account');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { number: 1, title: 'Sign up your account', active: step >= 1 },
    { number: 2, title: 'Set up your workspace', active: step >= 2 },
    { number: 3, title: 'Set up your profile', active: step >= 3 },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center">
              <Phone className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-black text-white">RelayX</h1>
          </div>
        </div>

        {/* Card */}
        <Card className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 border-slate-700 backdrop-blur-xl">
          <CardHeader className="text-center pb-8">
            <CardTitle className="text-3xl font-bold text-white mb-2">
              Get Started with Us
            </CardTitle>
            <CardDescription className="text-slate-400 text-base">
              Complete these easy steps to register your account.
            </CardDescription>
          </CardHeader>

          <CardContent>
            {/* Steps */}
            <div className="space-y-3 mb-8">
              {steps.map((stepItem) => (
                <div
                  key={stepItem.number}
                  className={`flex items-center gap-4 p-4 rounded-xl transition-all ${
                    stepItem.active
                      ? 'bg-blue-500/20 border border-blue-500/30'
                      : 'bg-slate-800/30 border border-slate-700/30'
                  }`}
                >
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                      stepItem.active
                        ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white'
                        : 'bg-slate-700/50 text-slate-500'
                    }`}
                  >
                    {stepItem.number}
                  </div>
                  <span
                    className={`text-base ${
                      stepItem.active ? 'text-white font-medium' : 'text-slate-500'
                    }`}
                  >
                    {stepItem.title}
                  </span>
                  {stepItem.active && step > stepItem.number && (
                    <CheckCircle2 className="w-5 h-5 text-green-400 ml-auto" />
                  )}
                </div>
              ))}
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Input
                  type="text"
                  placeholder="Full Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="h-12 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div className="space-y-2">
                <Input
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="h-12 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div className="space-y-2">
                <Input
                  type="password"
                  placeholder="Password (min 6 characters)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="h-12 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div className="space-y-2">
                <Input
                  type="password"
                  placeholder="Confirm Password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="h-12 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              {error && (
                <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                disabled={loading}
                className="w-full h-12 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-bold text-base"
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </Button>
            </form>

            {/* Sign in link */}
            <div className="mt-6 text-center">
              <p className="text-slate-400">
                Already have an account?{' '}
                <Link to="/login" className="text-blue-400 hover:text-blue-300 font-semibold">
                  Sign in
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Back to home */}
        <Link
          to="/"
          className="flex items-center justify-center gap-2 mt-6 text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to home
        </Link>
      </div>
    </div>
  );
}
