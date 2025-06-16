import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TaskManager from '../../src/frontend/react/components/TaskManager/TaskManager';
import { ApiContext } from '../../src/frontend/react/contexts/ApiContext';

// Mock API context
const mockMakeApiRequest = jest.fn();
const mockApiContext = {
  apiStatus: 'connected' as const,
  setApiStatus: jest.fn(),
  retryConnection: jest.fn(),
  makeApiRequest: mockMakeApiRequest
};

describe('TaskManager Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderWithContext = (component: React.ReactElement) => {
    return render(
      <ApiContext.Provider value={mockApiContext}>
        {component}
      </ApiContext.Provider>
    );
  };

  test('renders task manager interface', () => {
    renderWithContext(<TaskManager />);
    
    expect(screen.getByText(/ai-powered task management/i)).toBeInTheDocument();
    expect(screen.getByText(/overview/i)).toBeInTheDocument();
    expect(screen.getByText(/all tasks/i)).toBeInTheDocument();
    expect(screen.getByText(/add task/i)).toBeInTheDocument();
    expect(screen.getByText(/analyze task complexity/i)).toBeInTheDocument();
  });

  test('displays tasks when loaded', async () => {
    const mockTasks = {
      tasks: [
        {
          id: 1,
          title: 'Complete project',
          description: 'Finish the main project',
          status: 'pending',
          priority: 'high',
          due_date: '2024-12-31'
        },
        {
          id: 2,
          title: 'Review code',
          description: 'Review pull requests',
          status: 'in_progress',
          priority: 'medium'
        }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockTasks });

    renderWithContext(<TaskManager />);

    await waitFor(() => {
      expect(screen.getByText('Complete project')).toBeInTheDocument();
      expect(screen.getByText('Review code')).toBeInTheDocument();
    });
  });

  test('creates new task', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        id: 3,
        title: 'New Task',
        description: 'Task description',
        status: 'pending',
        priority: 'medium'
      }
    });

    renderWithContext(<TaskManager />);

    const addButton = screen.getByRole('button', { name: /add task/i });
    fireEvent.click(addButton);

    // Fill in task form
    const titleInput = await screen.findByPlaceholderText(/task title/i);
    const descriptionInput = screen.getByPlaceholderText(/task description/i);
    const prioritySelect = screen.getByLabelText(/priority/i);

    fireEvent.change(titleInput, { target: { value: 'New Task' } });
    fireEvent.change(descriptionInput, { target: { value: 'Task description' } });
    fireEvent.change(prioritySelect, { target: { value: 'medium' } });

    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/tasks',
        expect.objectContaining({
          title: 'New Task',
          description: 'Task description',
          priority: 'medium'
        })
      );
    });
  });

  test('updates task status', async () => {
    const mockTasks = {
      tasks: [{
        id: 1,
        title: 'Test Task',
        status: 'pending',
        priority: 'high'
      }]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockTasks });
    mockApiContext.put.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<TaskManager />);

    await waitFor(() => {
      expect(screen.getByText('Test Task')).toBeInTheDocument();
    });

    const statusSelect = screen.getByTestId('task-status-1');
    fireEvent.change(statusSelect, { target: { value: 'completed' } });

    await waitFor(() => {
      expect(mockApiContext.put).toHaveBeenCalledWith(
        '/api/tasks/1',
        expect.objectContaining({ status: 'completed' })
      );
    });
  });

  test('deletes task with confirmation', async () => {
    const mockTasks = {
      tasks: [{
        id: 1,
        title: 'Task to Delete',
        status: 'pending',
        priority: 'low'
      }]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockTasks });
    mockApiContext.delete.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<TaskManager />);

    await waitFor(() => {
      expect(screen.getByText('Task to Delete')).toBeInTheDocument();
    });

    const deleteButton = screen.getByTestId('delete-task-1');
    fireEvent.click(deleteButton);

    const confirmButton = await screen.findByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockApiContext.delete).toHaveBeenCalledWith('/api/tasks/1');
    });
  });

  test('filters tasks by status', async () => {
    const mockTasks = {
      tasks: [
        { id: 1, title: 'Pending Task', status: 'pending', priority: 'high' },
        { id: 2, title: 'Completed Task', status: 'completed', priority: 'medium' }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockTasks });

    renderWithContext(<TaskManager />);

    await waitFor(() => {
      expect(screen.getByText('Pending Task')).toBeInTheDocument();
      expect(screen.getByText('Completed Task')).toBeInTheDocument();
    });

    const filterSelect = screen.getByLabelText(/filter by status/i);
    fireEvent.change(filterSelect, { target: { value: 'pending' } });

    expect(screen.getByText('Pending Task')).toBeInTheDocument();
    expect(screen.queryByText('Completed Task')).not.toBeInTheDocument();
  });

  test('sorts tasks by different criteria', async () => {
    const mockTasks = {
      tasks: [
        { id: 1, title: 'A Task', priority: 'low', due_date: '2024-12-01' },
        { id: 2, title: 'B Task', priority: 'high', due_date: '2024-11-01' }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockTasks });

    renderWithContext(<TaskManager />);

    await waitFor(() => {
      expect(screen.getByText('A Task')).toBeInTheDocument();
      expect(screen.getByText('B Task')).toBeInTheDocument();
    });

    const sortSelect = screen.getByLabelText(/sort by/i);
    fireEvent.change(sortSelect, { target: { value: 'priority' } });

    const tasks = screen.getAllByTestId(/^task-item-/);
    expect(tasks[0]).toHaveTextContent('B Task'); // High priority first
  });

  test('displays AI task suggestions', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        suggestions: [
          {
            title: 'AI Suggested Task',
            description: 'This task was suggested by AI',
            priority: 'medium',
            estimated_time: 30
          }
        ]
      }
    });

    renderWithContext(<TaskManager />);

    const suggestButton = screen.getByRole('button', { name: /get ai suggestions/i });
    fireEvent.click(suggestButton);

    await waitFor(() => {
      expect(screen.getByText('AI Suggested Task')).toBeInTheDocument();
      expect(screen.getByText(/30 minutes/i)).toBeInTheDocument();
    });
  });

  test('handles task search', async () => {
    const mockTasks = {
      tasks: [
        { id: 1, title: 'Search me', status: 'pending', priority: 'high' },
        { id: 2, title: 'Other task', status: 'pending', priority: 'medium' }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockTasks });

    renderWithContext(<TaskManager />);

    await waitFor(() => {
      expect(screen.getByText('Search me')).toBeInTheDocument();
      expect(screen.getByText('Other task')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search tasks/i);
    fireEvent.change(searchInput, { target: { value: 'search' } });

    expect(screen.getByText('Search me')).toBeInTheDocument();
    expect(screen.queryByText('Other task')).not.toBeInTheDocument();
  });

  test('displays task due date warnings', async () => {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const mockTasks = {
      tasks: [{
        id: 1,
        title: 'Urgent Task',
        status: 'pending',
        priority: 'high',
        due_date: tomorrow.toISOString()
      }]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockTasks });

    renderWithContext(<TaskManager />);

    await waitFor(() => {
      expect(screen.getByText('Urgent Task')).toBeInTheDocument();
      expect(screen.getByText(/due tomorrow/i)).toBeInTheDocument();
      expect(screen.getByTestId('task-item-1')).toHaveClass('urgent');
    });
  });

  describe('Create New Workspace Functionality', () => {
    beforeEach(() => {
      // Mock window.alert
      window.alert = jest.fn();
      
      // Mock workspaces response
      mockMakeApiRequest.mockResolvedValueOnce([
        { id: 1, name: 'Personal Organization', color: '#3b82f6' },
        { id: 2, name: 'Work Projects', color: '#059669' }
      ]);
    });

    test('displays create new workspace option in dropdown', async () => {
      renderWithContext(<TaskManager />);
      
      // Click on Add Task tab
      fireEvent.click(screen.getByText('Add Task'));
      
      await waitFor(() => {
        const workspaceSelect = screen.getByLabelText(/workspace/i);
        expect(workspaceSelect).toBeInTheDocument();
      });

      const workspaceSelect = screen.getByLabelText(/workspace/i);
      const options = workspaceSelect.querySelectorAll('option');
      
      // Check that Create New Workspace option exists
      const createOption = Array.from(options).find(
        option => option.textContent === '➕ Create New Workspace'
      );
      expect(createOption).toBeInTheDocument();
      expect(createOption?.value).toBe('create_new');
    });

    test('shows alert when create new workspace is selected', async () => {
      renderWithContext(<TaskManager />);
      
      // Click on Add Task tab
      fireEvent.click(screen.getByText('Add Task'));
      
      await waitFor(() => {
        const workspaceSelect = screen.getByLabelText(/workspace/i);
        expect(workspaceSelect).toBeInTheDocument();
      });

      const workspaceSelect = screen.getByLabelText(/workspace/i);
      
      // Select Create New Workspace option
      fireEvent.change(workspaceSelect, { target: { value: 'create_new' } });
      
      // Check that alert was called
      expect(window.alert).toHaveBeenCalledWith(
        'Create new workspace functionality will be implemented'
      );
      
      // Check that the select value remains empty (not selected)
      expect(workspaceSelect.value).toBe('');
    });

    test('workspace dropdown includes all options in correct order', async () => {
      renderWithContext(<TaskManager />);
      
      // Click on Add Task tab
      fireEvent.click(screen.getByText('Add Task'));
      
      await waitFor(() => {
        const workspaceSelect = screen.getByLabelText(/workspace/i);
        expect(workspaceSelect).toBeInTheDocument();
      });

      const workspaceSelect = screen.getByLabelText(/workspace/i);
      const options = Array.from(workspaceSelect.querySelectorAll('option'));
      
      // Verify order and content
      expect(options[0].textContent).toBe('🤖 Let AI suggest (recommended)');
      expect(options[0].value).toBe('');
      
      expect(options[1].textContent).toBe('➕ Create New Workspace');
      expect(options[1].value).toBe('create_new');
      
      expect(options[2].textContent).toBe('🗂️ Personal Organization');
      expect(options[2].value).toBe('1');
      
      expect(options[3].textContent).toBe('🗂️ Work Projects');
      expect(options[3].value).toBe('2');
    });

    test('can still select existing workspace after create new alert', async () => {
      renderWithContext(<TaskManager />);
      
      // Click on Add Task tab
      fireEvent.click(screen.getByText('Add Task'));
      
      await waitFor(() => {
        const workspaceSelect = screen.getByLabelText(/workspace/i);
        expect(workspaceSelect).toBeInTheDocument();
      });

      const workspaceSelect = screen.getByLabelText(/workspace/i);
      
      // First select Create New Workspace
      fireEvent.change(workspaceSelect, { target: { value: 'create_new' } });
      
      // Then select an existing workspace
      fireEvent.change(workspaceSelect, { target: { value: '1' } });
      
      // Verify the workspace is selected
      expect(workspaceSelect.value).toBe('1');
    });

    test('workspace selection persists when filling form', async () => {
      renderWithContext(<TaskManager />);
      
      // Click on Add Task tab
      fireEvent.click(screen.getByText('Add Task'));
      
      await waitFor(() => {
        const workspaceSelect = screen.getByLabelText(/workspace/i);
        expect(workspaceSelect).toBeInTheDocument();
      });

      // Fill in task details
      const titleInput = screen.getByPlaceholderText(/enter task title/i);
      const descriptionInput = screen.getByPlaceholderText(/describe the task/i);
      const workspaceSelect = screen.getByLabelText(/workspace/i);
      
      fireEvent.change(titleInput, { target: { value: 'Test Task' } });
      fireEvent.change(descriptionInput, { target: { value: 'Test Description' } });
      fireEvent.change(workspaceSelect, { target: { value: '2' } });
      
      // Verify all values persist
      expect(titleInput.value).toBe('Test Task');
      expect(descriptionInput.value).toBe('Test Description');
      expect(workspaceSelect.value).toBe('2');
    });
  });
});