import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
  userId: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in (from localStorage)
    const savedUser = localStorage.getItem('relayx_user');
    const token = localStorage.getItem('relayx_token');
    
    if (savedUser && token) {
      try {
        // Verify token is still valid
        verifyToken(token).then(valid => {
          if (valid) {
            setUser(JSON.parse(savedUser));
          } else {
            localStorage.removeItem('relayx_user');
            localStorage.removeItem('relayx_token');
          }
          setLoading(false);
        });
      } catch (error) {
        console.error('Failed to parse saved user:', error);
        localStorage.removeItem('relayx_user');
        localStorage.removeItem('relayx_token');
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  async function verifyToken(token: string): Promise<boolean> {
    try {
      const response = await fetch('/auth/verify-token', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      
      if (data.access_token && data.user) {
        const userData = {
          id: data.user.id,
          email: data.user.email,
          name: data.user.name || email.split('@')[0]
        };
        
        setUser(userData);
        localStorage.setItem('relayx_user', JSON.stringify(userData));
        localStorage.setItem('relayx_token', data.access_token);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('relayx_user');
    localStorage.removeItem('relayx_token');
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      login, 
      logout, 
      isAuthenticated: !!user, 
      loading,
      userId: user?.id || null
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
