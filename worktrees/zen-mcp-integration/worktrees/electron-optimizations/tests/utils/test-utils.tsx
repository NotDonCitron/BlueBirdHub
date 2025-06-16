import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Create a simple mock provider instead of importing real contexts
const MockApiProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Mock the API context value
  const mockApiContext = {
    apiStatus: 'connected' as const,
    setApiStatus: jest.fn(),
    retryConnection: jest.fn(),
    makeApiRequest: jest.fn().mockResolvedValue({ success: true })
  };

  return (
    <div data-testid="mock-api-provider">
      {children}
    </div>
  );
};

const MockThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div data-testid="mock-theme-provider">
      {children}
    </div>
  );
};

interface AllTheProvidersProps {
  children: React.ReactNode;
}

// All providers wrapper
const AllTheProviders: React.FC<AllTheProvidersProps> = ({ children }) => {
  return (
    <BrowserRouter>
      <MockThemeProvider>
        <MockApiProvider>
          {children}
        </MockApiProvider>
      </MockThemeProvider>
    </BrowserRouter>
  );
};

// Custom render function
const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';

// Override render method
export { customRender as render };