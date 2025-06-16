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
      if ((window as any).electronAPI) {
        // Use Electron API
        return await (window as any).electronAPI.apiRequest(endpoint, method, data);
      } else {
        // Fallback for development in browser
        const url = `http://127.0.0.1:8001${endpoint}`;
        const options: RequestInit = {
          method,
          headers: {
            'Content-Type': 'application/json',
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