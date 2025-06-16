import React, { ReactNode } from 'react';
type ApiStatus = 'connected' | 'disconnected' | 'checking';
interface ApiContextType {
    apiStatus: ApiStatus;
    setApiStatus: (status: ApiStatus) => void;
    retryConnection: () => void;
    makeApiRequest: (endpoint: string, method?: string, data?: any) => Promise<any>;
}
export declare const ApiContext: React.Context<ApiContextType | undefined>;
interface ApiProviderProps {
    children: ReactNode;
    apiStatus: ApiStatus;
    onRetryConnection: () => void;
}
export declare const ApiProvider: React.FC<ApiProviderProps>;
export declare const useApi: () => ApiContextType;
export {};
