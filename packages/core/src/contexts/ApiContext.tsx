import React, { createContext, useContext, useState, ReactNode, useRef, useEffect } from 'react';
import { ApiClient, ApiRequestError, RequestOptions } from '../api/index';

type ApiStatus = 'connected' | 'disconnected' | 'checking';

interface ApiContextType {
  apiStatus: ApiStatus;
  setApiStatus: (status: ApiStatus) => void;
  retryConnection: () => void;
  makeApiRequest: (endpoint: string, method?: string, data?: any, options?: RequestOptions) => Promise<any>;
  cancelAllRequests: () => void;
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
  const apiClientRef = useRef<ApiClient>();
  const activeRequestsRef = useRef<AbortController[]>([]);

  useEffect(() => {
    apiClientRef.current = new ApiClient({
      baseUrl: 'http://127.0.0.1:8000',
      timeout: 15000,
      retries: 2
    });

    return () => {
      activeRequestsRef.current.forEach(controller => controller.abort());
    };
  }, []);

  const retryConnection = () => {
    setApiStatus('checking');
    onRetryConnection();
  };

  const cancelAllRequests = () => {
    activeRequestsRef.current.forEach(controller => controller.abort());
    activeRequestsRef.current = [];
  };

  const makeApiRequest = async (endpoint: string, method = 'GET', data?: any, options: RequestOptions = {}): Promise<any> => {
    const controller = new AbortController();
    activeRequestsRef.current.push(controller);

    try {
      if (window.electronAPI) {
        return await window.electronAPI.apiRequest(endpoint, method, data);
      } else {
        if (!apiClientRef.current) {
          throw new ApiRequestError('API client not initialized');
        }

        const requestOptions: RequestOptions = {
          ...options,
          signal: controller.signal
        };

        let result;
        switch (method.toUpperCase()) {
          case 'GET':
            result = await apiClientRef.current.get(endpoint, requestOptions);
            break;
          case 'POST':
            result = await apiClientRef.current.post(endpoint, data, requestOptions);
            break;
          case 'PUT':
            result = await apiClientRef.current.put(endpoint, data, requestOptions);
            break;
          case 'DELETE':
            result = await apiClientRef.current.delete(endpoint, requestOptions);
            break;
          default:
            throw new ApiRequestError(`Unsupported HTTP method: ${method}`);
        }

        setApiStatus('connected');
        return result;
      }
    } catch (error) {
      if (error instanceof ApiRequestError) {
        if (error.code === 'CANCELLED') {
          console.log('Request was cancelled');
          return null;
        } else if (error.code === 'TIMEOUT') {
          console.error('Request timeout:', error.message);
          setApiStatus('disconnected');
        } else {
          console.error('API request failed:', error.message);
          setApiStatus('disconnected');
        }
        throw error;
      } else {
        console.error('Unexpected error:', error);
        setApiStatus('disconnected');
        throw new ApiRequestError(`Unexpected error: ${error}`);
      }
    } finally {
      const index = activeRequestsRef.current.indexOf(controller);
      if (index > -1) {
        activeRequestsRef.current.splice(index, 1);
      }
    }
  };

  const value: ApiContextType = {
    apiStatus,
    setApiStatus,
    retryConnection,
    makeApiRequest,
    cancelAllRequests,
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