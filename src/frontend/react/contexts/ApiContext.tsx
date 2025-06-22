import React, { createContext, useContext, useState, ReactNode } from 'react';
import { API_CONFIG, getApiUrl } from '../config/api';

type ApiStatus = 'connected' | 'disconnected' | 'checking';

interface ApiContextType {
  apiStatus: ApiStatus;
  setApiStatus: (status: ApiStatus) => void;
  retryConnection: () => void;
  makeApiRequest: (endpoint: string, method?: string, data?: any, headers?: Record<string, string>) => Promise<any>;
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

  const makeApiRequest = async (endpoint: string, method = 'GET', data?: any, headers?: Record<string, string>): Promise<any> => {
    try {
      // Get auth token from localStorage
      const authToken = localStorage.getItem('auth_token');
      const authHeaders = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      
      if ((window as any).electronAPI) {
        // Use Electron API
        return await (window as any).electronAPI.apiRequest(endpoint, method, data, { ...authHeaders, ...headers });
      } else {
        // Use configured API URL (works in both dev and production)
        const url = getApiUrl(endpoint);
        const options: RequestInit = {
          method,
          headers: {
            'Content-Type': 'application/json',
            ...authHeaders,
            ...headers
          },
        };
        
        if (data && method !== 'GET') {
          options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        if (!response.ok) {
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