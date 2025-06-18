import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import ApiManager from '../core/ApiManager';
import RequestInterceptor from '../core/RequestInterceptor';

type ApiStatus = 'connected' | 'disconnected' | 'checking';

interface ApiContextType {
  apiStatus: ApiStatus;
  setApiStatus: (status: ApiStatus) => void;
  retryConnection: () => void;
  makeApiRequest: (endpoint: string, method?: string, data?: any) => Promise<any>;
  getCurrentBackend: () => string;
  getHealthStatus: () => Map<string, any>;
}

export const ApiContext = createContext<ApiContextType | undefined>(undefined);

interface ApiProviderProps {
  children: ReactNode;
}

export const ApiProvider: React.FC<ApiProviderProps> = ({ children }) => {
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking');
  const [apiManager] = useState(() => ApiManager.getInstance());

  useEffect(() => {
    // Initialize request interceptor in development
    if (process.env.NODE_ENV === 'development') {
      RequestInterceptor.getInstance();
    }

    // Initialize API connection
    initializeConnection();
  }, []);

  const initializeConnection = async () => {
    setApiStatus('checking');
    
    try {
      await apiManager.initializeConnection();
      setApiStatus('connected');
      console.log('✅ API connection established');
    } catch (error) {
      setApiStatus('disconnected');
      console.error('❌ API connection failed:', error);
    }
  };

  const retryConnection = async () => {
    await initializeConnection();
  };

  const makeApiRequest = async (endpoint: string, method = 'GET', data?: any): Promise<any> => {
    try {
      let response;
      
      switch (method.toUpperCase()) {
        case 'GET':
          response = await apiManager.get(endpoint);
          break;
        case 'POST':
          response = await apiManager.post(endpoint, data);
          break;
        case 'PUT':
          response = await apiManager.put(endpoint, data);
          break;
        case 'DELETE':
          response = await apiManager.delete(endpoint);
          break;
        default:
          throw new Error(`Unsupported HTTP method: ${method}`);
      }

      // Update status on successful request
      if (apiStatus !== 'connected') {
        setApiStatus('connected');
      }

      return response;
    } catch (error) {
      console.error('API request failed:', error);
      
      // Don't immediately set to disconnected for single request failures
      // Only disconnect if it's a connection-level error
      if (error instanceof Error && error.message.includes('fetch')) {
        setApiStatus('disconnected');
      }
      
      throw error;
    }
  };

  const getCurrentBackend = (): string => {
    return apiManager.getCurrentBackend();
  };

  const getHealthStatus = (): Map<string, any> => {
    return apiManager.getHealthStatus();
  };

  const value: ApiContextType = {
    apiStatus,
    setApiStatus,
    retryConnection,
    makeApiRequest,
    getCurrentBackend,
    getHealthStatus,
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
