import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Lock, Mail, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const success = await login(email, password);
    if (success) {
      navigate('/dashboard');
    } else {
      setError('Invalid credentials. Please check your email and password.');
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4 font-body">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center space-x-2 mb-4">
            <div className="w-12 h-12 bg-primary rounded-xl"></div>
            <span className="text-4xl font-title font-bold text-primary">
              RelayX
            </span>
          </div>
          <h1 className="text-3xl font-title font-bold text-text">Welcome back</h1>
          <p className="text-text mt-2">Sign in to manage your AI assistant</p>
        </div>

        {/* Login Form */}
        <div className="bg-accent rounded-2xl shadow-xl p-8 border-2 border-primary">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-bold text-secondary mb-2">
                Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-secondary" />
                </div>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border-2 border-bg-lighter rounded-lg focus:ring-2 focus:ring-primary focus:border-primary bg-accent text-secondary"
                  placeholder="you@company.com"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-bold text-secondary mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-secondary" />
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border-2 border-bg-lighter rounded-lg focus:ring-2 focus:ring-primary focus:border-primary bg-accent text-secondary"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4 flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-800 font-bold">{error}</p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              className="w-full bg-primary text-secondary py-3 rounded-lg font-bold hover:opacity-80 transition-all text-lg"
            >
              Sign In
            </button>
          </form>

          {/* Test Credentials */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm font-medium text-blue-900 mb-2">Test Credentials:</p>
              <p className="text-xs text-blue-800 font-mono">Email: test@relayx.ai</p>
              <p className="text-xs text-blue-800 font-mono">Password: test123</p>
            </div>
          </div>
        </div>

        {/* Back to home */}
        <div className="text-center mt-6">
          <a href="/" className="text-gray-600 hover:text-blue-600 text-sm font-medium">
            ← Back to home
          </a>
        </div>
      </div>
    </div>
  );
}
