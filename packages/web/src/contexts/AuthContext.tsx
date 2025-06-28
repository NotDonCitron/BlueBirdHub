import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
}

interface AuthContextType {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  loginWithCredentials: (username: string, password: string) => Promise<boolean>;
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
        const res = await fetch('http://localhost:8000/auth/me', {
          headers
        });
        if (!res.ok) {
          throw new Error('Failed to fetch user info');
        }
        response = await res.json();
      }

      setUser(response);
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      // If fetching user info fails, clear the invalid token and logout
      setToken(null);
      setUser(null);
      localStorage.removeItem('auth_token');
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithCredentials = async (username: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      // Use default admin credentials if none provided
      const actualUsername = username.trim() || 'admin';
      const actualPassword = password.trim() || 'admin123';
      
      const response = await fetch('http://localhost:8000/auth/login-json', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          username: actualUsername, 
          password: actualPassword 
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.access_token) {
          await login(data.access_token);
          return true;
        } else {
          throw new Error('No access token received');
        }
      } else {
        const errorText = await response.text();
        console.error('Login failed:', errorText);
        throw new Error(`Authentication failed: ${response.status}`);
      }
    } catch (error) {
      console.error('Login failed:', error);
      // Clear any invalid state
      setToken(null);
      setUser(null);
      localStorage.removeItem('auth_token');
      throw error;
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
          await fetch('http://localhost:8000/auth/logout', {
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
    logout,
    loginWithCredentials
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