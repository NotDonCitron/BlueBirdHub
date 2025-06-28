import React, { createContext, useContext, useState, ReactNode } from 'react';

type ApiStatus = 'connected' | 'disconnected' | 'checking';

interface ApiContextType {
  apiStatus: ApiStatus;
  setApiStatus: (status: ApiStatus) => void;
  retryConnection: () => void;
  makeApiRequest: (endpoint: string, method?: string, data?: any) => Promise<any>;
}

export const ApiContext = createContext<ApiContextType | undefined>(undefined);

interface ApiProviderProps {
  children: ReactNode;
  apiStatus: ApiStatus;
  onRetryConnection: () => void;
}

export const ApiProvider: React.FC<ApiProviderProps> = ({ 
  children, 
  apiStatus: initialStatus, 
  onRetryConnection 
}) => {
  const [apiStatus, setApiStatus] = useState<ApiStatus>(initialStatus);

  const retryConnection = () => {
    setApiStatus('checking');
    onRetryConnection();
  };

  const makeApiRequest = async (endpoint: string, method = 'GET', data?: any): Promise<any> => {
    try {
      if (window.electronAPI) {
        // Use Electron API
        return await window.electronAPI.apiRequest(endpoint, method, data);
      } else {
        // Use localhost instead of 127.0.0.1 for Docker compatibility
        const url = `http://localhost:8000${endpoint}`;
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
        };

        // Add authentication token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        const options: RequestInit = {
          method,
          headers,
        };
        
        if (data && method !== 'GET') {
          options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        if (!response.ok) {
          // If 401 Unauthorized, try to continue without auth for some endpoints
          if (response.status === 401) {
            console.warn(`Authentication required for ${endpoint}`);
            // For development, create a mock token to test functionality
            const mockToken = 'dev-token-' + Date.now();
            localStorage.setItem('auth_token', mockToken);
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
      }
    } catch (error) {
      console.error('API request failed:', error);
      setApiStatus('disconnected');
      throw error;
    }
  };

  const value: ApiContextType = {
    apiStatus,
    setApiStatus,
    retryConnection,
    makeApiRequest,
  };

  return (
    <ApiContext.Provider value={value}>
      {children}
    </ApiContext.Provider>
  );
};

export const useApi = (): ApiContextType => {
  const context = useContext(ApiContext);
  if (context === undefined) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};