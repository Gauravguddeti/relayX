import { Link } from 'react-router-dom';
import { Phone } from 'lucide-react';
import { Button } from './ui/button';

export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-lg border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <Phone className="w-5 h-5 text-white" />
            </div>
            <span className="text-2xl font-black text-white">
              RelayX
            </span>
          </Link>

          {/* Nav Items */}
          <div className="flex items-center space-x-4">
            <Link to="/login">
              <Button 
                variant="ghost" 
                className="text-gray-300 hover:text-white hover:bg-gray-800"
              >
                Sign In
              </Button>
            </Link>
            <Link to="/signup">
              <Button 
                className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold"
              >
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}
