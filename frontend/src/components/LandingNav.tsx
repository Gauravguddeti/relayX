import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Sparkles } from 'lucide-react';

export default function LandingNav() {
  const { isAuthenticated } = useAuth();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/60 backdrop-blur-xl border-b border-white/20 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 group">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-700 via-cyan-600 to-teal-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-2xl font-black bg-gradient-to-r from-blue-700 via-cyan-600 to-teal-600 bg-clip-text text-transparent">
              RelayX
            </span>
          </Link>

          {/* Nav Items */}
          <div className="flex items-center space-x-8">
            <a 
              href="#features" 
              className="text-slate-700 hover:text-cyan-600 font-semibold transition-colors relative group"
              onClick={(e) => {
                e.preventDefault();
                document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              Features
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-cyan-600 to-blue-700 group-hover:w-full transition-all duration-300"></span>
            </a>
            <a 
              href="#pricing" 
              className="text-slate-700 hover:text-cyan-600 font-semibold transition-colors relative group"
              onClick={(e) => {
                e.preventDefault();
                document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              Pricing
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-cyan-600 to-blue-700 group-hover:w-full transition-all duration-300"></span>
            </a>
            
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl hover:from-blue-700 hover:to-cyan-700 font-bold shadow-lg hover:shadow-xl hover:scale-105 transition-all"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-slate-700 hover:text-cyan-600 font-semibold transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/login"
                  className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl hover:from-blue-700 hover:to-cyan-700 font-bold shadow-lg hover:shadow-xl hover:scale-105 transition-all"
                >
                  Start Free Trial
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
