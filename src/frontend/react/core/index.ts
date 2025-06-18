/**
 * Core Integration - Initializes all preventive systems
 * Import this in your main App.tsx to enable all safety features
 */

import ApiManager from './ApiManager';
import RequestInterceptor from './RequestInterceptor';

// Environment validation
const validateEnvironment = (): void => {
  console.log('🔍 Validating environment configuration...');
  
  const requiredEnvVars = [
    'REACT_APP_API_URL',
    'REACT_APP_FALLBACK_API_URL'
  ];
  
  const missing = requiredEnvVars.filter(envVar => !process.env[envVar]);
  
  if (missing.length > 0) {
    console.warn(`⚠️ Missing environment variables: ${missing.join(', ')}`);
    console.warn('Using default values for development');
  }
  
  console.log('Environment:', {
    NODE_ENV: process.env.NODE_ENV,
    API_URL: process.env.REACT_APP_API_URL,
    FALLBACK_URL: process.env.REACT_APP_FALLBACK_API_URL,
    TIMEOUT: process.env.REACT_APP_API_TIMEOUT
  });
};

// Development warnings
const showDevelopmentWarnings = (): void => {
  if (process.env.NODE_ENV !== 'development') return;
  
  console.log(
    '%c🛡️ OrdnungsHub Development Mode Active',
    'color: blue; font-size: 14px; font-weight: bold;'
  );
  
  console.log('Available debugging tools:');
  console.log('- window.apiManager: API Manager instance');
  console.log('- window.debugApi: API debugging utilities');
  console.log('- window.requestInterceptor: Request monitoring');
  console.log('- window.debugRequests: Request debugging utilities');
  
  // Show preventive measures
  setTimeout(() => {
    console.log(
      '%c🔒 Frontend Self-Call Protection Active',
      'color: green; font-weight: bold;'
    );
    console.log('All API calls are being monitored for safety');
  }, 1000);
};

// Core initialization
export const initializeCore = async (): Promise<void> => {
  console.log('🚀 Initializing OrdnungsHub Core Systems...');
  
  try {
    // 1. Validate environment
    validateEnvironment();
    
    // 2. Initialize API Manager
    const apiManager = ApiManager.getInstance();
    await apiManager.initializeConnection();
    
    // 3. Initialize Request Interceptor (development only)
    if (process.env.NODE_ENV === 'development') {
      RequestInterceptor.getInstance();
      showDevelopmentWarnings();
    }
    
    console.log('✅ Core systems initialized successfully');
    
    // 4. Run connection test
    await runConnectionTest();
    
  } catch (error) {
    console.error('❌ Core initialization failed:', error);
    throw error;
  }
};

// Connection test
const runConnectionTest = async (): Promise<void> => {
  try {
    const apiManager = ApiManager.getInstance();
    const healthCheck = await apiManager.get('/health');
    
    console.log('🩺 Connection test passed:', healthCheck);
    
    // Show current backend
    const currentBackend = apiManager.getCurrentBackend();
    console.log(`🔗 Using backend: ${currentBackend}`);
    
  } catch (error) {
    console.warn('⚠️ Connection test failed:', error);
    console.warn('App will attempt to reconnect automatically');
  }
};

// Export utilities for components
export const getApiManager = (): ApiManager => ApiManager.getInstance();

export const safeApiCall = async <T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  data?: any
): Promise<T> => {
  const apiManager = getApiManager();
  
  switch (method) {
    case 'GET':
      return apiManager.get<T>(endpoint);
    case 'POST':
      return apiManager.post<T>(endpoint, data);
    case 'PUT':
      return apiManager.put<T>(endpoint, data);
    case 'DELETE':
      return apiManager.delete<T>(endpoint);
    default:
      throw new Error(`Unsupported method: ${method}`);
  }
};

// Hook for React components
export const useApiManager = () => {
  return {
    apiManager: getApiManager(),
    safeApiCall,
    getCurrentBackend: () => getApiManager().getCurrentBackend(),
    getHealthStatus: () => getApiManager().getHealthStatus()
  };
};

export default {
  initializeCore,
  getApiManager,
  safeApiCall,
  useApiManager
};
