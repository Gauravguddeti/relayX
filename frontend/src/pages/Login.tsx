import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Phone, ArrowLeft } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        login(data.user_id);
        navigate('/dashboard');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Invalid credentials');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

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
              Welcome Back
            </CardTitle>
            <CardDescription className="text-slate-400 text-base">
              Sign in to access your AI calling dashboard
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
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
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
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
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>

            {/* Test Credentials */}
            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <p className="text-sm font-semibold text-blue-400 mb-2">Test Credentials:</p>
              <p className="text-xs text-slate-400">
                <span className="font-mono">Email: test@relayx.ai</span>
                <br />
                <span className="font-mono">Password: test123</span>
              </p>
            </div>

            {/* Sign up link */}
            <div className="mt-6 text-center">
              <p className="text-slate-400">
                Don't have an account?{' '}
                <Link to="/signup" className="text-blue-400 hover:text-blue-300 font-semibold">
                  Sign up
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
