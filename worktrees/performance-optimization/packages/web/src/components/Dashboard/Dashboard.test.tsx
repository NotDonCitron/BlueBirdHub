import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from './Dashboard';

// Create a simple mock context
const mockApiContext = {
  apiStatus: 'connected' as const,
  makeApiRequest: vi.fn(),
  apiRequest: vi.fn(),
  retryConnection: vi.fn(),
};

// Mock the useApi hook
vi.mock('../../contexts/ApiContext', () => ({
  useApi: () => mockApiContext,
}));

const renderDashboard = () => {
  return render(
    <BrowserRouter>
      <Dashboard />
    </BrowserRouter>
  );
};

describe('Dashboard Component - Simplified', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiContext.makeApiRequest.mockResolvedValue({
      success: false, // Force fallback to mock data
    });
  });

  it('should eventually render dashboard content', async () => {
    await act(async () => {
      renderDashboard();
    });

    // Wait for any async operations
    await waitFor(() => {
      expect(screen.getByText('Welcome to OrdnungsHub')).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('should display statistics when loaded', async () => {
    await act(async () => {
      renderDashboard();
    });

    await waitFor(() => {
      expect(screen.getByText('Total Tasks')).toBeInTheDocument();
    }, { timeout: 5000 });

    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Workspaces')).toBeInTheDocument();
    expect(screen.getByText('Files Indexed')).toBeInTheDocument();
  });

  it('should display quick actions', async () => {
    await act(async () => {
      renderDashboard();
    });

    await waitFor(() => {
      expect(screen.getByText('Quick Actions')).toBeInTheDocument();
    }, { timeout: 5000 });

    // Check for action buttons
    expect(screen.getByText('New Task')).toBeInTheDocument();
    expect(screen.getByText('New Workspace')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    expect(screen.getByText('AI Assistant')).toBeInTheDocument();
  });
});