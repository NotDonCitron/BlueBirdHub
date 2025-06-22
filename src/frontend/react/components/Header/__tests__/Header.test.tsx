import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Header from '../Header';
import { useAuth } from '../../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

// Mock dependencies
jest.mock('../../../contexts/AuthContext');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockNavigate = useNavigate as jest.MockedFunction<typeof useNavigate>;

// Wrapper component for Router context
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('Header Component', () => {
  const mockOnSidebarToggle = jest.fn();
  const mockLogout = jest.fn();
  const navigateMock = jest.fn();

  const defaultProps = {
    currentView: 'dashboard',
    apiStatus: 'connected' as const,
    onSidebarToggle: mockOnSidebarToggle,
  };

  const mockUser = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    is_active: true,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockReturnValue(navigateMock);
    mockUseAuth.mockReturnValue({
      user: mockUser,
      token: 'test-token',
      isAuthenticated: true,
      isLoading: false,
      login: jest.fn(),
      logout: mockLogout,
    });
  });

  describe('Rendering', () => {
    it('renders header with correct title for known view', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} currentView="tasks" />
        </TestWrapper>
      );

      expect(screen.getByText('Task Management')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '☰' })).toBeInTheDocument();
    });

    it('renders default title for unknown view', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} currentView="unknown" />
        </TestWrapper>
      );

      expect(screen.getByText('OrdnungsHub')).toBeInTheDocument();
    });

    it('renders search input and button', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByPlaceholderText('Search everything...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '🔍' })).toBeInTheDocument();
    });

    it('renders user information when authenticated', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('testuser')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '🚪' })).toBeInTheDocument();
    });

    it('does not render user info when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        login: jest.fn(),
        logout: mockLogout,
      });

      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.queryByText('testuser')).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: '🚪' })).not.toBeInTheDocument();
    });

    it('renders all header action buttons', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByRole('button', { name: '🔔' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '⚡' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '❓' })).toBeInTheDocument();
    });
  });

  describe('API Status Indicator', () => {
    it('displays connected status correctly', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} apiStatus="connected" />
        </TestWrapper>
      );

      const statusText = screen.getByText('Connected');
      const statusIndicator = screen.getByTitle('Backend status: Connected');
      
      expect(statusText).toBeInTheDocument();
      expect(statusIndicator).toBeInTheDocument();
      expect(statusIndicator).toHaveStyle({
        backgroundColor: 'var(--color-success)',
      });
    });

    it('displays disconnected status correctly', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} apiStatus="disconnected" />
        </TestWrapper>
      );

      const statusText = screen.getByText('Disconnected');
      const statusIndicator = screen.getByTitle('Backend status: Disconnected');
      
      expect(statusText).toBeInTheDocument();
      expect(statusIndicator).toBeInTheDocument();
      expect(statusIndicator).toHaveStyle({
        backgroundColor: 'var(--color-danger)',
      });
    });

    it('displays checking status correctly', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} apiStatus="checking" />
        </TestWrapper>
      );

      const statusText = screen.getByText('Connecting...');
      const statusIndicator = screen.getByTitle('Backend status: Connecting...');
      
      expect(statusText).toBeInTheDocument();
      expect(statusIndicator).toBeInTheDocument();
      expect(statusIndicator).toHaveStyle({
        backgroundColor: 'var(--color-warning)',
      });
    });
  });

  describe('User Interactions', () => {
    it('calls onSidebarToggle when sidebar toggle button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const toggleButton = screen.getByRole('button', { name: '☰' });
      await user.click(toggleButton);

      expect(mockOnSidebarToggle).toHaveBeenCalledTimes(1);
    });

    it('calls logout when logout button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const logoutButton = screen.getByRole('button', { name: '🚪' });
      await user.click(logoutButton);

      expect(mockLogout).toHaveBeenCalledTimes(1);
    });

    it('updates search input value on change', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Search everything...') as HTMLInputElement;
      await user.type(searchInput, 'test query');

      expect(searchInput.value).toBe('test query');
    });

    it('navigates to search with query when search button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Search everything...');
      const searchButton = screen.getByRole('button', { name: '🔍' });

      await user.type(searchInput, 'test query');
      await user.click(searchButton);

      expect(navigateMock).toHaveBeenCalledWith('/search?q=test%20query');
    });

    it('navigates to search without query when search input is empty', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const searchButton = screen.getByRole('button', { name: '🔍' });
      await user.click(searchButton);

      expect(navigateMock).toHaveBeenCalledWith('/search');
    });

    it('trims whitespace from search query', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Search everything...');
      const searchButton = screen.getByRole('button', { name: '🔍' });

      await user.type(searchInput, '  test query  ');
      await user.click(searchButton);

      expect(navigateMock).toHaveBeenCalledWith('/search?q=test%20query');
    });

    it('navigates to search when Enter key is pressed', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Search everything...');
      await user.type(searchInput, 'test query');
      await user.keyboard('{Enter}');

      expect(navigateMock).toHaveBeenCalledWith('/search?q=test%20query');
    });

    it('does not navigate when other keys are pressed', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Search everything...');
      await user.type(searchInput, 'test');
      await user.keyboard('{Escape}');

      expect(navigateMock).not.toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty search query gracefully', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Search everything...');
      const searchButton = screen.getByRole('button', { name: '🔍' });

      await user.type(searchInput, '   ');
      await user.click(searchButton);

      expect(navigateMock).toHaveBeenCalledWith('/search');
    });

    it('encodes special characters in search URL', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Search everything...');
      const searchButton = screen.getByRole('button', { name: '🔍' });

      await user.type(searchInput, 'test & query #special');
      await user.click(searchButton);

      expect(navigateMock).toHaveBeenCalledWith('/search?q=test%20%26%20query%20%23special');
    });

    it('renders correctly with undefined user', () => {
      mockUseAuth.mockReturnValue({
        user: undefined as any,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        login: jest.fn(),
        logout: mockLogout,
      });

      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.queryByText('testuser')).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: '🚪' })).not.toBeInTheDocument();
    });
  });

  describe('View Titles', () => {
    const viewTestCases = [
      { view: 'dashboard', title: 'Dashboard' },
      { view: 'tasks', title: 'Task Management' },
      { view: 'workspaces', title: 'Workspaces' },
      { view: 'files', title: 'File Manager' },
      { view: 'search', title: 'Smart Search' },
      { view: 'ai-assistant', title: 'AI Assistant' },
      { view: 'ai-content', title: 'AI Content' },
      { view: 'settings', title: 'Settings' },
    ];

    viewTestCases.forEach(({ view, title }) => {
      it(`displays correct title for ${view} view`, () => {
        render(
          <TestWrapper>
            <Header {...defaultProps} currentView={view} />
          </TestWrapper>
        );

        expect(screen.getByText(title)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and titles', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByRole('button', { name: '☰' })).toHaveAttribute('title', 'Toggle sidebar');
      expect(screen.getByRole('button', { name: '🔍' })).toHaveAttribute('title', 'Search');
      expect(screen.getByRole('button', { name: '🔔' })).toHaveAttribute('title', 'Notifications');
      expect(screen.getByRole('button', { name: '⚡' })).toHaveAttribute('title', 'Quick Actions');
      expect(screen.getByRole('button', { name: '❓' })).toHaveAttribute('title', 'Help');
      expect(screen.getByRole('button', { name: '🚪' })).toHaveAttribute('title', 'Logout');
    });

    it('has proper semantic structure', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const header = screen.getByRole('banner');
      expect(header).toBeInTheDocument();
      expect(header.tagName).toBe('HEADER');
    });

    it('search input has proper type and placeholder', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Search everything...');
      expect(searchInput).toHaveAttribute('type', 'text');
    });
  });

  describe('CSS Classes', () => {
    it('applies correct CSS classes', () => {
      render(
        <TestWrapper>
          <Header {...defaultProps} />
        </TestWrapper>
      );

      const header = screen.getByRole('banner');
      expect(header).toHaveClass('header');

      const searchInput = screen.getByPlaceholderText('Search everything...');
      expect(searchInput).toHaveClass('search-input');

      const searchButton = screen.getByRole('button', { name: '🔍' });
      expect(searchButton).toHaveClass('search-button');
    });
  });
});