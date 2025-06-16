import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import TaskManager from '../../src/frontend/react/components/TaskManager/TaskManager';
import { ApiProvider } from '../../src/frontend/react/contexts/ApiContext';
import { ThemeProvider } from '../../src/frontend/react/contexts/ThemeContext';

// Mock API responses
const mockTasksResponse = {
  tasks: [
    {
      id: "T001",
      title: "Setup Core Application Framework",
      description: "Create the foundational structure for OrdnungsHub",
      status: "done",
      priority: "high",
      workspace_id: 1,
      dependencies: []
    },
    {
      id: "T002",
      title: "Implement Database Layer",
      description: "Setup SQLite with SQLAlchemy ORM",
      status: "done",
      priority: "high",
      workspace_id: 1,
      dependencies: ["T001"]
    },
    {
      id: "T005",
      title: "Deploy to Cloud Platform",
      description: "Make OrdnungsHub accessible online for demonstration",
      status: "in-progress",
      priority: "medium",
      workspace_id: 1,
      dependencies: ["T004"]
    },
    {
      id: "T006",
      title: "Add Real-time Collaboration",
      description: "Enable multiple users to collaborate on workspaces",
      status: "pending",
      priority: "low",
      workspace_id: 2,
      dependencies: ["T005"]
    }
  ],
  total: 4,
  source: "taskmaster"
};

const mockProgressResponse = {
  total_tasks: 4,
  completed_tasks: 2,
  pending_tasks: 1,
  in_progress_tasks: 1,
  completion_percentage: 50.0
};

const mockNextTaskResponse = {
  task: {
    id: "T005",
    title: "Deploy to Cloud Platform",
    description: "Make OrdnungsHub accessible online for demonstration",
    status: "in-progress",
    priority: "medium",
    workspace_id: 1
  }
};

const mockWorkspacesResponse = [
  {
    id: 1,
    name: "Development",
    color: "#3b82f6",
    description: "Software development and coding projects"
  },
  {
    id: 2,
    name: "Design", 
    color: "#10b981",
    description: "UI/UX design and creative projects"
  }
];

const mockWorkspaceOverviewResponse = {
  success: true,
  overview: {
    "1": {
      workspace_name: "Development",
      workspace_color: "#3b82f6",
      statistics: {
        total_tasks: 3,
        completed_tasks: 2,
        in_progress_tasks: 1,
        pending_tasks: 0,
        completion_rate: 66.7
      },
      recent_tasks: [
        {
          id: "T001",
          title: "Setup Core Application Framework",
          status: "done",
          priority: "high"
        },
        {
          id: "T005",
          title: "Deploy to Cloud Platform", 
          status: "in-progress",
          priority: "medium"
        }
      ],
      tasks: [
        {
          id: "T001",
          title: "Setup Core Application Framework",
          description: "Create the foundational structure for OrdnungsHub",
          status: "done",
          priority: "high",
          workspace_id: 1
        },
        {
          id: "T002",
          title: "Implement Database Layer",
          description: "Setup SQLite with SQLAlchemy ORM", 
          status: "done",
          priority: "high",
          workspace_id: 1
        },
        {
          id: "T005",
          title: "Deploy to Cloud Platform",
          description: "Make OrdnungsHub accessible online for demonstration",
          status: "in-progress",
          priority: "medium",
          workspace_id: 1
        }
      ]
    },
    "2": {
      workspace_name: "Design",
      workspace_color: "#10b981",
      statistics: {
        total_tasks: 1,
        completed_tasks: 0,
        in_progress_tasks: 0,
        pending_tasks: 1,
        completion_rate: 0.0
      },
      recent_tasks: [
        {
          id: "T006",
          title: "Add Real-time Collaboration",
          status: "pending",
          priority: "low"
        }
      ],
      tasks: [
        {
          id: "T006",
          title: "Add Real-time Collaboration",
          description: "Enable multiple users to collaborate on workspaces",
          status: "pending",
          priority: "low",
          workspace_id: 2
        }
      ]
    }
  }
};

const mockWorkspaceSuggestionsResponse = {
  success: true,
  suggestions: [
    {
      workspace_id: 1,
      workspace_name: "Development",
      confidence: 0.85,
      reason: "Task appears to be development-related based on keywords"
    },
    {
      workspace_id: 2,
      workspace_name: "Design",
      confidence: 0.45,
      reason: "Some design elements mentioned"
    }
  ],
  auto_suggestion: {
    workspace_id: 1,
    workspace_name: "Development",
    confidence: 0.85,
    reason: "Task appears to be development-related based on keywords"
  }
};

// Mock fetch globally
global.fetch = jest.fn();

const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

// Setup default API responses
const setupMockResponses = () => {
  mockFetch.mockImplementation((url: string | URL | Request, options?: RequestInit) => {
    const urlString = url.toString();
    
    if (urlString.includes('/tasks/taskmaster/all')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockTasksResponse),
      } as Response);
    }
    
    if (urlString.includes('/tasks/taskmaster/progress')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockProgressResponse),
      } as Response);
    }
    
    if (urlString.includes('/tasks/taskmaster/next')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockNextTaskResponse),
      } as Response);
    }
    
    if (urlString.includes('/workspaces/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockWorkspacesResponse),
      } as Response);
    }
    
    if (urlString.includes('/tasks/taskmaster/workspace-overview')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockWorkspaceOverviewResponse),
      } as Response);
    }
    
    if (urlString.includes('/tasks/taskmaster/suggest-workspace')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockWorkspaceSuggestionsResponse),
      } as Response);
    }
    
    if (urlString.includes('/tasks/taskmaster/add')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          task: {
            id: "T008",
            title: "New Test Task",
            description: "Test task description",
            status: "pending",
            priority: "medium",
            workspace_id: 1
          },
          message: "Task created successfully"
        }),
      } as Response);
    }
    
    if (urlString.includes('/tasks/taskmaster/') && urlString.includes('/status')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          message: "Status updated"
        }),
      } as Response);
    }
    
    return Promise.resolve({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ error: 'Not found' }),
    } as Response);
  });
};

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    <ApiProvider apiUrl="http://localhost:8000">
      {children}
    </ApiProvider>
  </ThemeProvider>
);

describe('TaskManager Comprehensive Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setupMockResponses();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Overview Tab', () => {
    test('renders overview tab with progress statistics', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('50%')).toBeInTheDocument();
      });

      // Check progress statistics
      expect(screen.getByText('Complete')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument(); // Completed tasks
      expect(screen.getByText('Done')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument(); // In progress tasks
      expect(screen.getByText('In Progress')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
    });

    test('displays next recommended task', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('🎯 Recommended Next Task')).toBeInTheDocument();
      });

      expect(screen.getByText('Deploy to Cloud Platform')).toBeInTheDocument();
      expect(screen.getByText('in-progress')).toBeInTheDocument();
    });

    test('AI actions section is functional', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('AI Tools')).toBeInTheDocument();
      });

      expect(screen.getByText('Analyze Task Complexity')).toBeInTheDocument();
      expect(screen.getByText('Refresh Data')).toBeInTheDocument();
    });
  });

  describe('All Tasks Tab', () => {
    test('displays all tasks with correct information', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      // Switch to All Tasks tab
      fireEvent.click(screen.getByText('All Tasks'));

      await waitFor(() => {
        expect(screen.getByText('All Tasks (4)')).toBeInTheDocument();
      });

      // Check individual tasks
      expect(screen.getByText('Setup Core Application Framework')).toBeInTheDocument();
      expect(screen.getByText('Implement Database Layer')).toBeInTheDocument();
      expect(screen.getByText('Deploy to Cloud Platform')).toBeInTheDocument();
      expect(screen.getByText('Add Real-time Collaboration')).toBeInTheDocument();
    });

    test('displays workspace badges for tasks', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('All Tasks'));

      await waitFor(() => {
        expect(screen.getByText('All Tasks (4)')).toBeInTheDocument();
      });

      // Check for workspace badges
      const workspaceBadges = screen.getAllByText(/🗂️/);
      expect(workspaceBadges.length).toBeGreaterThan(0);
    });

    test('can select and view task details', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('All Tasks'));

      await waitFor(() => {
        expect(screen.getByText('Setup Core Application Framework')).toBeInTheDocument();
      });

      // Click on a task to select it
      fireEvent.click(screen.getByText('Setup Core Application Framework'));

      // Task details should appear
      expect(screen.getByText('Status: done')).toBeInTheDocument();
      expect(screen.getByText('Priority: high')).toBeInTheDocument();
    });

    test('can update task status', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('All Tasks'));

      await waitFor(() => {
        expect(screen.getByText('Add Real-time Collaboration')).toBeInTheDocument();
      });

      // Find the pending task and start it
      const pendingTask = screen.getByText('Add Real-time Collaboration').closest('.task-card');
      expect(pendingTask).toBeInTheDocument();
      
      const startButton = within(pendingTask!).getByText('Start');
      fireEvent.click(startButton);

      // Should call the API to update status
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/tasks/taskmaster/T006/status'),
          expect.objectContaining({
            method: 'PUT',
            headers: expect.objectContaining({
              'Content-Type': 'application/json'
            }),
            body: JSON.stringify({ status: 'in-progress' })
          })
        );
      });
    });
  });

  describe('Add Task Tab', () => {
    test('renders add task form', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Add Task'));

      await waitFor(() => {
        expect(screen.getByText('Add New Task')).toBeInTheDocument();
      });

      expect(screen.getByPlaceholderText('Enter task title...')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Describe the task...')).toBeInTheDocument();
      expect(screen.getByDisplayValue('medium')).toBeInTheDocument(); // Priority select
    });

    test('shows workspace suggestions when typing', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Add Task'));

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Enter task title...')).toBeInTheDocument();
      });

      const titleInput = screen.getByPlaceholderText('Enter task title...');
      fireEvent.change(titleInput, { target: { value: 'Create new component' } });

      await waitFor(() => {
        expect(screen.getByText('🤖 AI Workspace Vorschläge:')).toBeInTheDocument();
      });

      expect(screen.getByText('🗂️ Development')).toBeInTheDocument();
      expect(screen.getByText('85% sicher')).toBeInTheDocument();
    });

    test('can create new task', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Add Task'));

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Enter task title...')).toBeInTheDocument();
      });

      // Fill form
      const titleInput = screen.getByPlaceholderText('Enter task title...');
      const descriptionInput = screen.getByPlaceholderText('Describe the task...');
      
      fireEvent.change(titleInput, { target: { value: 'Test New Task' } });
      fireEvent.change(descriptionInput, { target: { value: 'This is a test task' } });

      // Submit form
      const addButton = screen.getByText('Add Task with AI');
      fireEvent.click(addButton);

      // Should call the API
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/tasks/taskmaster/add'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json'
            }),
            body: expect.stringContaining('Test New Task')
          })
        );
      });
    });

    test('workspace selection works', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Add Task'));

      await waitFor(() => {
        expect(screen.getByDisplayValue('🤖 Let AI suggest (recommended)')).toBeInTheDocument();
      });

      const workspaceSelect = screen.getByDisplayValue('🤖 Let AI suggest (recommended)');
      
      // Should have workspace options
      expect(screen.getByText('🗂️ Development')).toBeInTheDocument();
      expect(screen.getByText('🗂️ Design')).toBeInTheDocument();
    });
  });

  describe('Workspaces Tab', () => {
    test('displays workspace overview', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('🗂️ Workspaces'));

      await waitFor(() => {
        expect(screen.getByText('🗂️ Tasks by Workspace')).toBeInTheDocument();
      });

      // Check workspace cards
      expect(screen.getByText('🗂️ Development')).toBeInTheDocument();
      expect(screen.getByText('🗂️ Design')).toBeInTheDocument();
      
      // Check statistics
      expect(screen.getByText('66.7% complete')).toBeInTheDocument();
      expect(screen.getByText('0.0% complete')).toBeInTheDocument();
      expect(screen.getByText('3 tasks')).toBeInTheDocument();
      expect(screen.getByText('1 tasks')).toBeInTheDocument();
    });

    test('shows task breakdown by workspace', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('🗂️ Workspaces'));

      await waitFor(() => {
        expect(screen.getByText('🗂️ Development')).toBeInTheDocument();
      });

      // Development workspace stats
      const devWorkspace = screen.getByText('🗂️ Development').closest('.workspace-overview-card');
      expect(devWorkspace).toBeInTheDocument();
      
      within(devWorkspace!).getByText('2'); // Completed tasks
      within(devWorkspace!).getByText('1'); // In progress tasks
      within(devWorkspace!).getByText('0'); // Pending tasks
    });

    test('can expand workspace to view all tasks', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('🗂️ Workspaces'));

      await waitFor(() => {
        expect(screen.getByText('View All Tasks')).toBeInTheDocument();
      });

      const viewAllButton = screen.getAllByText('View All Tasks')[0];
      fireEvent.click(viewAllButton);

      // Should show detailed task view
      await waitFor(() => {
        expect(screen.getByText('All Tasks in Development')).toBeInTheDocument();
      });
    });
  });

  describe('Navigation and Tab Switching', () => {
    test('can switch between all tabs', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      // Default is Overview
      expect(screen.getByText('Project Progress')).toBeInTheDocument();

      // Switch to All Tasks
      fireEvent.click(screen.getByText('All Tasks'));
      await waitFor(() => {
        expect(screen.getByText('All Tasks (4)')).toBeInTheDocument();
      });

      // Switch to Dependencies
      fireEvent.click(screen.getByText('Dependencies'));
      // Dependencies tab should be visible

      // Switch to Add Task
      fireEvent.click(screen.getByText('Add Task'));
      await waitFor(() => {
        expect(screen.getByText('Add New Task')).toBeInTheDocument();
      });

      // Switch to Workspaces
      fireEvent.click(screen.getByText('🗂️ Workspaces'));
      await waitFor(() => {
        expect(screen.getByText('🗂️ Tasks by Workspace')).toBeInTheDocument();
      });

      // Switch back to Overview
      fireEvent.click(screen.getByText('Overview'));
      await waitFor(() => {
        expect(screen.getByText('Project Progress')).toBeInTheDocument();
      });
    });

    test('active tab styling is applied', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      const overviewTab = screen.getByText('Overview');
      const allTasksTab = screen.getByText('All Tasks');

      // Overview should be active by default
      expect(overviewTab.closest('.tab')).toHaveClass('active');
      expect(allTasksTab.closest('.tab')).not.toHaveClass('active');

      // Switch tabs
      fireEvent.click(allTasksTab);

      await waitFor(() => {
        expect(allTasksTab.closest('.tab')).toHaveClass('active');
        expect(overviewTab.closest('.tab')).not.toHaveClass('active');
      });
    });
  });

  describe('Error Handling', () => {
    test('handles API errors gracefully', async () => {
      // Mock failed API call
      mockFetch.mockRejectedValueOnce(new Error('API Error'));

      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      // Component should still render without crashing
      expect(screen.getByText('AI-Powered Task Management')).toBeInTheDocument();
    });

    test('handles empty task list', async () => {
      mockFetch.mockImplementation((url: string | URL | Request) => {
        const urlString = url.toString();
        
        if (urlString.includes('/tasks/taskmaster/all')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ tasks: [], total: 0, source: "taskmaster" }),
          } as Response);
        }
        
        return Promise.resolve({
          ok: false,
          status: 404,
          json: () => Promise.resolve({ error: 'Not found' }),
        } as Response);
      });

      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('All Tasks'));

      await waitFor(() => {
        expect(screen.getByText('All Tasks (0)')).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    test('shows loading state during data fetch', async () => {
      // Mock slow API response
      mockFetch.mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve(mockTasksResponse),
          } as Response), 100)
        )
      );

      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      // Should show loading or initial state
      expect(screen.getByText('AI-Powered Task Management')).toBeInTheDocument();
    });
  });

  describe('Task Actions', () => {
    test('expand task functionality', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('All Tasks'));

      await waitFor(() => {
        expect(screen.getByText('Add Real-time Collaboration')).toBeInTheDocument();
      });

      // Find pending task and expand it
      const pendingTask = screen.getByText('Add Real-time Collaboration').closest('.task-card');
      const expandButton = within(pendingTask!).getByText('Expand');
      
      fireEvent.click(expandButton);

      // Should call expand API
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/tasks/taskmaster/T006/expand'),
          expect.objectContaining({
            method: 'POST'
          })
        );
      });
    });
  });

  describe('Complexity Analysis', () => {
    test('can trigger complexity analysis', async () => {
      render(
        <TestWrapper>
          <TaskManager />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Analyze Task Complexity')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Analyze Task Complexity'));

      // Should call complexity analysis API
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/tasks/taskmaster/analyze-complexity'),
          expect.objectContaining({
            method: 'POST'
          })
        );
      });
    });
  });
});