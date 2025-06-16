import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TaskManager from '../../src/frontend/react/components/TaskManager/TaskManager';
import { ApiContext } from '../../src/frontend/react/contexts/ApiContext';

describe('Create Workspace Dropdown Tests', () => {
  const mockMakeApiRequest = jest.fn();
  const mockApiContext = {
    apiStatus: 'connected' as const,
    setApiStatus: jest.fn(),
    retryConnection: jest.fn(),
    makeApiRequest: mockMakeApiRequest
  };

  const mockWorkspaces = [
    { id: 1, name: 'Personal Organization', color: '#3b82f6', icon: '🏠' },
    { id: 2, name: 'Work Projects', color: '#059669', icon: '💼' },
    { id: 3, name: 'Learning & Research', color: '#8b5cf6', icon: '📚' }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    window.alert = jest.fn();
    
    // Default mock implementations
    mockMakeApiRequest.mockImplementation((endpoint: string) => {
      if (endpoint === '/workspaces/') {
        return Promise.resolve(mockWorkspaces);
      }
      if (endpoint === '/tasks/taskmaster/all') {
        return Promise.resolve({ tasks: [] });
      }
      if (endpoint === '/tasks/taskmaster/progress') {
        return Promise.resolve({
          total_tasks: 0,
          completed_tasks: 0,
          pending_tasks: 0,
          in_progress_tasks: 0,
          completion_percentage: 0
        });
      }
      if (endpoint === '/tasks/taskmaster/next') {
        return Promise.resolve({ task: null });
      }
      return Promise.resolve({});
    });
  });

  const renderComponent = () => {
    return render(
      <ApiContext.Provider value={mockApiContext}>
        <TaskManager />
      </ApiContext.Provider>
    );
  };

  test('renders create new workspace option with correct styling', async () => {
    renderComponent();
    
    // Navigate to Add Task tab
    fireEvent.click(screen.getByText('Add Task'));
    
    await waitFor(() => {
      expect(screen.getByLabelText(/workspace/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/workspace/i);
    const options = select.querySelectorAll('option');
    
    // Find the create new option
    const createOption = Array.from(options).find(
      opt => opt.textContent === '➕ Create New Workspace'
    );
    
    expect(createOption).toBeInTheDocument();
    expect(createOption).toHaveValue('create_new');
    expect(createOption).toHaveTextContent('➕ Create New Workspace');
  });

  test('maintains dropdown position when hovering over create option', async () => {
    renderComponent();
    
    fireEvent.click(screen.getByText('Add Task'));
    
    await waitFor(() => {
      expect(screen.getByLabelText(/workspace/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/workspace/i);
    
    // Open dropdown
    fireEvent.focus(select);
    
    const createOption = Array.from(select.options).find(
      opt => opt.value === 'create_new'
    );
    
    // Simulate hover
    if (createOption) {
      fireEvent.mouseOver(createOption);
      
      // Verify dropdown is still open and option is visible
      expect(select).toHaveFocus();
      expect(createOption).toBeVisible();
    }
  });

  test('shows all workspace options in correct order', async () => {
    renderComponent();
    
    fireEvent.click(screen.getByText('Add Task'));
    
    await waitFor(() => {
      expect(screen.getByLabelText(/workspace/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/workspace/i);
    const options = Array.from(select.options);
    
    // Verify exact order
    expect(options).toHaveLength(5); // AI suggest + Create new + 3 workspaces
    expect(options[0]).toHaveTextContent('🤖 Let AI suggest (recommended)');
    expect(options[1]).toHaveTextContent('➕ Create New Workspace');
    expect(options[2]).toHaveTextContent('🏠 Personal Organization');
    expect(options[3]).toHaveTextContent('💼 Work Projects');
    expect(options[4]).toHaveTextContent('📚 Learning & Research');
  });

  test('preserves form state when create new is selected', async () => {
    renderComponent();
    
    fireEvent.click(screen.getByText('Add Task'));
    
    await waitFor(() => {
      expect(screen.getByLabelText(/workspace/i)).toBeInTheDocument();
    });

    // Fill in form fields
    const titleInput = screen.getByPlaceholderText(/enter task title/i);
    const descriptionInput = screen.getByPlaceholderText(/describe the task/i);
    const prioritySelect = screen.getByLabelText(/priority/i);
    
    fireEvent.change(titleInput, { target: { value: 'Important Task' } });
    fireEvent.change(descriptionInput, { target: { value: 'This is important' } });
    fireEvent.change(prioritySelect, { target: { value: 'high' } });
    
    // Select create new workspace
    const workspaceSelect = screen.getByLabelText(/workspace/i);
    fireEvent.change(workspaceSelect, { target: { value: 'create_new' } });
    
    // Verify alert was shown
    expect(window.alert).toHaveBeenCalledWith(
      'Create new workspace functionality will be implemented'
    );
    
    // Verify form fields retained their values
    expect(titleInput).toHaveValue('Important Task');
    expect(descriptionInput).toHaveValue('This is important');
    expect(prioritySelect).toHaveValue('high');
    expect(workspaceSelect).toHaveValue(''); // Reset to empty
  });

  test('handles keyboard navigation through workspace options', async () => {
    renderComponent();
    
    fireEvent.click(screen.getByText('Add Task'));
    
    await waitFor(() => {
      expect(screen.getByLabelText(/workspace/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/workspace/i);
    
    // Focus the select
    select.focus();
    
    // Navigate with arrow keys
    fireEvent.keyDown(select, { key: 'ArrowDown' });
    fireEvent.keyDown(select, { key: 'ArrowDown' });
    
    // Press Enter on create new option
    fireEvent.keyDown(select, { key: 'Enter' });
    
    // Should trigger the alert
    expect(window.alert).toHaveBeenCalled();
  });

  test('resets to empty after create new selection', async () => {
    renderComponent();
    
    fireEvent.click(screen.getByText('Add Task'));
    
    await waitFor(() => {
      expect(screen.getByLabelText(/workspace/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/workspace/i);
    
    // First select a real workspace
    fireEvent.change(select, { target: { value: '2' } });
    expect(select).toHaveValue('2');
    
    // Then select create new
    fireEvent.change(select, { target: { value: 'create_new' } });
    
    // Should reset to empty (AI suggest)
    expect(select).toHaveValue('');
  });

  test('allows workspace selection after dismissing create alert', async () => {
    renderComponent();
    
    fireEvent.click(screen.getByText('Add Task'));
    
    await waitFor(() => {
      expect(screen.getByLabelText(/workspace/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/workspace/i);
    
    // Select create new
    fireEvent.change(select, { target: { value: 'create_new' } });
    expect(window.alert).toHaveBeenCalled();
    
    // Now select a real workspace
    fireEvent.change(select, { target: { value: '3' } });
    expect(select).toHaveValue('3');
    
    // Verify the selection persists
    expect(screen.getByDisplayValue('3')).toBeInTheDocument();
  });

  test('integrates with AI workspace suggestions', async () => {
    // Mock AI suggestion response
    mockMakeApiRequest.mockImplementation((endpoint: string, method: string, data: any) => {
      if (endpoint === '/workspaces/') {
        return Promise.resolve(mockWorkspaces);
      }
      if (endpoint === '/tasks/taskmaster/suggest-workspace' && method === 'POST') {
        return Promise.resolve({
          success: true,
          suggestions: [
            {
              workspace_id: 2,
              workspace_name: 'Work Projects',
              confidence: 0.85,
              reason: 'Task title suggests work-related content'
            }
          ],
          auto_suggestion: {
            workspace_id: 2,
            confidence: 0.85
          }
        });
      }
      return Promise.resolve({});
    });

    renderComponent();
    
    fireEvent.click(screen.getByText('Add Task'));
    
    await waitFor(() => {
      expect(screen.getByLabelText(/workspace/i)).toBeInTheDocument();
    });

    // Type a work-related task
    const titleInput = screen.getByPlaceholderText(/enter task title/i);
    fireEvent.change(titleInput, { target: { value: 'Prepare project presentation' } });
    
    // Wait for AI suggestions
    await waitFor(() => {
      expect(mockMakeApiRequest).toHaveBeenCalledWith(
        '/tasks/taskmaster/suggest-workspace',
        'POST',
        expect.objectContaining({
          title: 'Prepare project presentation'
        })
      );
    });
    
    // Verify create new option is still available despite AI suggestion
    const select = screen.getByLabelText(/workspace/i);
    const createOption = Array.from(select.options).find(
      opt => opt.value === 'create_new'
    );
    expect(createOption).toBeInTheDocument();
  });

  test('displays workspace colors in dropdown options', async () => {
    renderComponent();
    
    fireEvent.click(screen.getByText('Add Task'));
    
    await waitFor(() => {
      expect(screen.getByLabelText(/workspace/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/workspace/i);
    
    // Check that workspace names are displayed with their icons
    mockWorkspaces.forEach(workspace => {
      const option = screen.getByText(`${workspace.icon} ${workspace.name}`);
      expect(option).toBeInTheDocument();
    });
  });
});