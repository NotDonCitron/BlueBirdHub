import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: number;
  username: string;
  last_login: string | null;
  created_at: string;
}

interface AuthContextType {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored token on mount  
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      setToken(storedToken);
      fetchUserInfo(storedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchUserInfo = async (authToken: string) => {
    try {
      const headers = {
        'Authorization': `Bearer ${authToken}`
      };

      let response;
      if ((window as any).electronAPI) {
        response = await (window as any).electronAPI.apiRequest('/auth/me', 'GET', null, headers);
      } else {
        const res = await fetch('http://127.0.0.1:8000/auth/me', {
          headers
        });
        if (!res.ok) {
          throw new Error('Failed to fetch user info');
        }
        response = await res.json();
      }

      setUser(response.user);
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      // If fetching user info fails, clear the token
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (authToken: string) => {
    setToken(authToken);
    localStorage.setItem('auth_token', authToken);
    await fetchUserInfo(authToken);
  };

  const logout = async () => {
    // Inform backend about logout
    if (token) {
      try {
        const headers = {
          'Authorization': `Bearer ${token}`
        };

        if ((window as any).electronAPI) {
          await (window as any).electronAPI.apiRequest('/auth/logout', 'POST', null, headers);
        } else {
          await fetch('http://127.0.0.1:8000/auth/logout', {
            method: 'POST',
            headers
          });
        }
      } catch (error) {
        console.error('Failed to logout on backend:', error);
        // Continue with frontend logout even if backend fails
      }
    }

    // Clear frontend state
    setToken(null);
    setUser(null);
    localStorage.removeItem('auth_token');
  };

  const value = {
    token,
    user,
    isAuthenticated: !!token && !!user,
    isLoading,
    login,
    logout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};