import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Dashboard from '../../src/frontend/react/components/Dashboard/Dashboard';
import { ApiProvider } from '../../src/frontend/react/contexts/ApiContext';

const MockedDashboard = () => (
  <ApiProvider apiStatus="connected" onRetryConnection={() => {}}>
    <Dashboard />
  </ApiProvider>
);

describe('Dashboard Component', () => {
  test('renders dashboard header', () => {
    render(<MockedDashboard />);
    expect(screen.getByText('Welcome to OrdnungsHub')).toBeInTheDocument();
  });

  test('displays stats cards', () => {
    render(<MockedDashboard />);
    expect(screen.getByText('Total Tasks')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Workspaces')).toBeInTheDocument();
    expect(screen.getByText('Files Indexed')).toBeInTheDocument();
  });

  test('shows quick actions', () => {
    render(<MockedDashboard />);
    expect(screen.getByText('New Task')).toBeInTheDocument();
    expect(screen.getByText('New Workspace')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    expect(screen.getByText('AI Assistant')).toBeInTheDocument();
  });

  test('displays recent activity section', () => {
    render(<MockedDashboard />);
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
  });
});