import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function LandingNav() {
  const { isAuthenticated } = useAuth();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg"></div>
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              RelayX
            </span>
          </Link>

          {/* Nav Items */}
          <div className="flex items-center space-x-6">
            <a href="#features" className="text-gray-700 hover:text-blue-600 font-medium">
              Features
            </a>
            <a href="#pricing" className="text-gray-700 hover:text-blue-600 font-medium">
              Pricing
            </a>
            
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-gray-700 hover:text-blue-600 font-medium"
                >
                  Sign In
                </Link>
                <Link
                  to="/login"
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
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
