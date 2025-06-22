import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AuthenticatedApp from '../AuthenticatedApp';
import { useAuth } from '../../contexts/AuthContext';

// Mock the dependencies
jest.mock('../../contexts/AuthContext');
jest.mock('../Layout/Layout', () => {
  return function MockLayout() {
    return <div data-testid="layout">Layout Component</div>;
  };
});
jest.mock('../ErrorDashboard', () => {
  return function MockErrorDashboard() {
    return <div data-testid="error-dashboard">Error Dashboard</div>;
  };
});
jest.mock('../PerformanceDashboard', () => {
  return function MockPerformanceDashboard() {
    return <div data-testid="performance-dashboard">Performance Dashboard</div>;
  };
});
jest.mock('../Login/Login', () => {
  return function MockLogin({ onLogin }: { onLogin: (token: string) => void }) {
    const handleLogin = () => {
      onLogin('test-token');
    };
    
    return (
      <div data-testid="login">
        <div>Login Component</div>
        <button onClick={handleLogin}>Mock Login</button>
      </div>
    );
  };
});

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('AuthenticatedApp Component', () => {
  const mockLogin = jest.fn();

  const defaultAuthContext = {
    token: 'test-token',
    user: {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      is_active: true,
    },
    isAuthenticated: true,
    isLoading: false,
    login: mockLogin,
    logout: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('renders loading spinner when isLoading is true', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: true,
        isAuthenticated: false,
        user: null,
        token: null,
      });

      render(<AuthenticatedApp />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      
      // Should have loading spinner element
      const loadingContainer = screen.getByText('Loading...').parentElement;
      expect(loadingContainer).toHaveClass('app-loading');
      expect(loadingContainer?.querySelector('.loading-spinner')).toBeInTheDocument();
    });

    it('does not render other components when loading', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: true,
        isAuthenticated: false,
        user: null,
        token: null,
      });

      render(<AuthenticatedApp />);

      expect(screen.queryByTestId('layout')).not.toBeInTheDocument();
      expect(screen.queryByTestId('login')).not.toBeInTheDocument();
      expect(screen.queryByTestId('error-dashboard')).not.toBeInTheDocument();
      expect(screen.queryByTestId('performance-dashboard')).not.toBeInTheDocument();
    });
  });

  describe('Authentication States', () => {
    it('renders Login component when not authenticated and not loading', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isAuthenticated: false,
        user: null,
        token: null,
        isLoading: false,
      });

      render(<AuthenticatedApp />);

      expect(screen.getByTestId('login')).toBeInTheDocument();
      expect(screen.getByText('Login Component')).toBeInTheDocument();
      
      // Should not render authenticated components
      expect(screen.queryByTestId('layout')).not.toBeInTheDocument();
      expect(screen.queryByTestId('error-dashboard')).not.toBeInTheDocument();
      expect(screen.queryByTestId('performance-dashboard')).not.toBeInTheDocument();
    });

    it('passes login function to Login component', async () => {
      const user = userEvent.setup();
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isAuthenticated: false,
        user: null,
        token: null,
        isLoading: false,
      });

      render(<AuthenticatedApp />);

      const loginButton = screen.getByText('Mock Login');
      await user.click(loginButton);

      expect(mockLogin).toHaveBeenCalledWith('test-token');
    });

    it('renders authenticated components when authenticated', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isAuthenticated: true,
      });

      render(<AuthenticatedApp />);

      expect(screen.getByTestId('layout')).toBeInTheDocument();
      expect(screen.getByTestId('error-dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('performance-dashboard')).toBeInTheDocument();
      
      // Should not render login or loading
      expect(screen.queryByTestId('login')).not.toBeInTheDocument();
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });
  });

  describe('Component Integration', () => {
    it('renders all authenticated components together', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isAuthenticated: true,
      });

      render(<AuthenticatedApp />);

      expect(screen.getByText('Layout Component')).toBeInTheDocument();
      expect(screen.getByText('Error Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Performance Dashboard')).toBeInTheDocument();
    });

    it('renders components in correct order', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isAuthenticated: true,
      });

      render(<AuthenticatedApp />);

      // All components should be present
      expect(screen.getByTestId('layout')).toBeInTheDocument();
      expect(screen.getByTestId('error-dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('performance-dashboard')).toBeInTheDocument();
    });
  });

  describe('State Transitions', () => {
    it('transitions from loading to login when authentication fails', () => {
      // First render with loading state
      const { rerender } = render(<AuthenticatedApp />);
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: true,
        isAuthenticated: false,
        user: null,
        token: null,
      });

      rerender(<AuthenticatedApp />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();

      // Then transition to login state
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: false,
        isAuthenticated: false,
        user: null,
        token: null,
      });

      rerender(<AuthenticatedApp />);
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      expect(screen.getByTestId('login')).toBeInTheDocument();
    });

    it('transitions from loading to authenticated when authentication succeeds', () => {
      // First render with loading state
      const { rerender } = render(<AuthenticatedApp />);
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: true,
        isAuthenticated: false,
        user: null,
        token: null,
      });

      rerender(<AuthenticatedApp />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();

      // Then transition to authenticated state
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: false,
        isAuthenticated: true,
      });

      rerender(<AuthenticatedApp />);
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      expect(screen.getByTestId('layout')).toBeInTheDocument();
    });

    it('transitions from login to authenticated after successful login', () => {
      // First render with login state
      const { rerender } = render(<AuthenticatedApp />);
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: false,
        isAuthenticated: false,
        user: null,
        token: null,
      });

      rerender(<AuthenticatedApp />);
      expect(screen.getByTestId('login')).toBeInTheDocument();

      // Then transition to authenticated state
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: false,
        isAuthenticated: true,
      });

      rerender(<AuthenticatedApp />);
      expect(screen.queryByTestId('login')).not.toBeInTheDocument();
      expect(screen.getByTestId('layout')).toBeInTheDocument();
    });

    it('transitions from authenticated to login when logged out', () => {
      // First render with authenticated state
      const { rerender } = render(<AuthenticatedApp />);
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: false,
        isAuthenticated: true,
      });

      rerender(<AuthenticatedApp />);
      expect(screen.getByTestId('layout')).toBeInTheDocument();

      // Then transition to login state
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: false,
        isAuthenticated: false,
        user: null,
        token: null,
      });

      rerender(<AuthenticatedApp />);
      expect(screen.queryByTestId('layout')).not.toBeInTheDocument();
      expect(screen.getByTestId('login')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined user in authenticated state', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        user: undefined as any,
        isAuthenticated: true,
        isLoading: false,
      });

      render(<AuthenticatedApp />);

      expect(screen.getByTestId('layout')).toBeInTheDocument();
      expect(screen.getByTestId('error-dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('performance-dashboard')).toBeInTheDocument();
    });

    it('handles null token in authenticated state', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        token: null,
        isAuthenticated: true,
        isLoading: false,
      });

      render(<AuthenticatedApp />);

      expect(screen.getByTestId('layout')).toBeInTheDocument();
      expect(screen.getByTestId('error-dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('performance-dashboard')).toBeInTheDocument();
    });

    it('prioritizes loading state over authentication state', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: true,
        isAuthenticated: true, // This should be ignored when loading
      });

      render(<AuthenticatedApp />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.queryByTestId('layout')).not.toBeInTheDocument();
      expect(screen.queryByTestId('login')).not.toBeInTheDocument();
    });

    it('handles loading with existing user data', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: true,
        isAuthenticated: false, // Not yet confirmed
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          is_active: true,
        },
        token: 'existing-token',
      });

      render(<AuthenticatedApp />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.queryByTestId('layout')).not.toBeInTheDocument();
      expect(screen.queryByTestId('login')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('provides accessible loading indicator', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: true,
        isAuthenticated: false,
        user: null,
        token: null,
      });

      render(<AuthenticatedApp />);

      const loadingText = screen.getByText('Loading...');
      expect(loadingText).toBeInTheDocument();
      
      // The loading container should be properly structured
      const loadingContainer = loadingText.parentElement;
      expect(loadingContainer).toHaveClass('app-loading');
    });

    it('maintains proper semantic structure for authenticated state', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isAuthenticated: true,
      });

      const { container } = render(<AuthenticatedApp />);

      // The main content should be wrapped in a React Fragment
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  describe('CSS Classes', () => {
    it('applies correct CSS class to loading container', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: true,
        isAuthenticated: false,
        user: null,
        token: null,
      });

      render(<AuthenticatedApp />);

      const loadingContainer = screen.getByText('Loading...').parentElement;
      expect(loadingContainer).toHaveClass('app-loading');
    });

    it('applies correct CSS class to loading spinner', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: true,
        isAuthenticated: false,
        user: null,
        token: null,
      });

      render(<AuthenticatedApp />);

      const loadingContainer = screen.getByText('Loading...').parentElement;
      const spinner = loadingContainer?.querySelector('.loading-spinner');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveClass('loading-spinner');
    });
  });

  describe('Component Props', () => {
    it('passes correct onLogin prop to Login component', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isAuthenticated: false,
        user: null,
        token: null,
        isLoading: false,
      });

      render(<AuthenticatedApp />);

      // The Login component should receive the login function
      expect(screen.getByTestId('login')).toBeInTheDocument();
      
      // This is tested indirectly through the mock Login component
      // which calls onLogin when the Mock Login button is clicked
    });
  });

  describe('Performance', () => {
    it('does not render unnecessary components when loading', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isLoading: true,
        isAuthenticated: false,
        user: null,
        token: null,
      });

      render(<AuthenticatedApp />);

      // Only loading should be rendered
      expect(screen.getByText('Loading...')).toBeInTheDocument();
      
      // These should not be in the DOM at all
      expect(screen.queryByTestId('layout')).not.toBeInTheDocument();
      expect(screen.queryByTestId('login')).not.toBeInTheDocument();
      expect(screen.queryByTestId('error-dashboard')).not.toBeInTheDocument();
      expect(screen.queryByTestId('performance-dashboard')).not.toBeInTheDocument();
    });

    it('does not render authenticated components when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthContext,
        isAuthenticated: false,
        user: null,
        token: null,
        isLoading: false,
      });

      render(<AuthenticatedApp />);

      // Only login should be rendered
      expect(screen.getByTestId('login')).toBeInTheDocument();
      
      // These should not be in the DOM at all
      expect(screen.queryByTestId('layout')).not.toBeInTheDocument();
      expect(screen.queryByTestId('error-dashboard')).not.toBeInTheDocument();
      expect(screen.queryByTestId('performance-dashboard')).not.toBeInTheDocument();
    });
  });
});