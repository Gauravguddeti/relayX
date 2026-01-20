import { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Phone, Settings, BookOpen, TestTube, Users, LogOut, Calendar, BarChart3, CreditCard } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: Home },
    { name: 'Analytics', path: '/dashboard/analytics', icon: BarChart3 },
    { name: 'Calls', path: '/dashboard/calls', icon: Phone },
    { name: 'Campaigns', path: '/dashboard/campaigns', icon: Users },
    { name: 'Contacts', path: '/dashboard/contacts', icon: Users },
    { name: 'My Agents', path: '/dashboard/bot', icon: Settings },
    { name: 'Knowledge Base', path: '/dashboard/knowledge', icon: BookOpen },
    { name: 'Test Agent', path: '/dashboard/test', icon: TestTube },
    { name: 'Cal.com', path: '/dashboard/cal', icon: Calendar },
    { name: 'Billing', path: '/dashboard/billing', icon: CreditCard },
  ];

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-background font-body">
      {/* Top Navigation */}
      <nav className="bg-secondary border-b-2 border-primary">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/dashboard" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary rounded-lg"></div>
                <span className="text-3xl font-title font-bold text-primary">
                  RelayX
                </span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-text">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 text-text hover:text-primary px-3 py-2 rounded-lg hover:bg-bg-lighter font-bold transition"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-bg-lighter border-r-2 border-bg-lighter min-h-[calc(100vh-4rem)]">
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors font-bold ${isActive
                    ? 'bg-primary text-secondary'
                    : 'text-text hover:bg-bg-darker hover:text-primary'
                    }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
