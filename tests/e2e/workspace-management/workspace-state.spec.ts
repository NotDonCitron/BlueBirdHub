import { test, expect } from '@playwright/test';
import { WorkspaceAPIClient } from '../helpers/api-client';
import { testWorkspaces, testStates } from '../helpers/test-data';

test.describe('Workspace State Management', () => {
  let apiClient: WorkspaceAPIClient;
  let testWorkspaceId: number;

  test.beforeAll(async ({ request }) => {
    apiClient = new WorkspaceAPIClient(request);
    // Create a test workspace for state tests
    const workspace = await apiClient.createWorkspace(testWorkspaces.basic);
    testWorkspaceId = workspace.id;
  });

  test.afterAll(async () => {
    // Cleanup
    if (testWorkspaceId) {
      try {
        await apiClient.deleteWorkspace(testWorkspaceId);
      } catch (error) {
        console.error('Failed to cleanup test workspace:', error);
      }
    }
  });

  test('should switch to a workspace', async () => {
    const switchResponse = await apiClient.switchWorkspace(testWorkspaceId);
    
    expect(switchResponse).toHaveProperty('workspace');
    expect(switchResponse).toHaveProperty('state');
    expect(switchResponse).toHaveProperty('message');
    expect(switchResponse.workspace.id).toBe(testWorkspaceId);
    expect(switchResponse.message).toContain('Switched to workspace');
  });

  test('should update workspace state', async () => {
    const newState = testStates.basic;
    
    const response = await apiClient.updateWorkspaceState(testWorkspaceId, newState);
    
    expect(response).toHaveProperty('workspace_id');
    expect(response).toHaveProperty('state');
    expect(response).toHaveProperty('message');
    expect(response.workspace_id).toBe(testWorkspaceId);
    expect(response.state).toMatchObject(newState);
    expect(response.message).toContain('updated successfully');
  });

  test('should get workspace state', async () => {
    // First set a state
    await apiClient.updateWorkspaceState(testWorkspaceId, testStates.complex);
    
    // Then retrieve it
    const stateResponse = await apiClient.getWorkspaceState(testWorkspaceId);
    
    expect(stateResponse).toHaveProperty('workspace_id');
    expect(stateResponse).toHaveProperty('state');
    expect(stateResponse).toHaveProperty('last_accessed_at');
    expect(stateResponse.workspace_id).toBe(testWorkspaceId);
    expect(stateResponse.state).toMatchObject(testStates.complex);
  });

  test('should preserve complex state structures', async () => {
    const complexState = {
      activeView: 'kanban',
      filters: {
        status: ['active', 'pending'],
        priority: 'high',
        dateRange: {
          start: '2024-01-01',
          end: '2024-12-31'
        }
      },
      ui: {
        sidebarWidth: 250,
        theme: 'dark',
        collapsed: {
          navigation: false,
          widgets: ['weather', 'news']
        }
      },
      userData: {
        preferences: {
          notifications: true,
          autoSave: false,
          saveInterval: 300
        },
        recentFiles: [
          '/docs/report1.pdf',
          '/images/chart.png'
        ]
      }
    };
    
    await apiClient.updateWorkspaceState(testWorkspaceId, complexState);
    const retrieved = await apiClient.getWorkspaceState(testWorkspaceId);
    
    expect(retrieved.state).toEqual(complexState);
  });

  test('should handle empty state', async () => {
    const emptyState = {};
    
    const response = await apiClient.updateWorkspaceState(testWorkspaceId, emptyState);
    expect(response.state).toEqual(emptyState);
    
    const retrieved = await apiClient.getWorkspaceState(testWorkspaceId);
    expect(retrieved.state).toEqual(emptyState);
  });

  test('should update last_accessed_at when switching workspace', async () => {
    // Get initial state
    const initialState = await apiClient.getWorkspaceState(testWorkspaceId);
    const initialAccessTime = initialState.last_accessed_at;
    
    // Wait a bit to ensure time difference
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Switch workspace
    await apiClient.switchWorkspace(testWorkspaceId);
    
    // Get updated state
    const updatedState = await apiClient.getWorkspaceState(testWorkspaceId);
    const updatedAccessTime = updatedState.last_accessed_at;
    
    // Verify last_accessed_at was updated
    if (initialAccessTime && updatedAccessTime) {
      expect(new Date(updatedAccessTime).getTime()).toBeGreaterThan(
        new Date(initialAccessTime).getTime()
      );
    }
  });

  test('should maintain state across workspace switches', async () => {
    // Create another workspace
    const secondWorkspace = await apiClient.createWorkspace({
      ...testWorkspaces.minimal,
      name: 'Second Test Workspace'
    });
    
    try {
      // Set different states for each workspace
      await apiClient.updateWorkspaceState(testWorkspaceId, testStates.basic);
      await apiClient.updateWorkspaceState(secondWorkspace.id, testStates.complex);
      
      // Switch between workspaces and verify states are preserved
      const firstSwitch = await apiClient.switchWorkspace(testWorkspaceId);
      expect(firstSwitch.state).toMatchObject(testStates.basic);
      
      const secondSwitch = await apiClient.switchWorkspace(secondWorkspace.id);
      expect(secondSwitch.state).toMatchObject(testStates.complex);
      
      // Switch back and verify state is still preserved
      const backToFirst = await apiClient.switchWorkspace(testWorkspaceId);
      expect(backToFirst.state).toMatchObject(testStates.basic);
    } finally {
      // Cleanup second workspace
      await apiClient.deleteWorkspace(secondWorkspace.id);
    }
  });

  test('should handle state updates for non-existent workspace', async () => {
    const nonExistentId = 99999;
    
    try {
      await apiClient.updateWorkspaceState(nonExistentId, testStates.basic);
      expect(true).toBe(false); // Should not reach here
    } catch (error: any) {
      expect(error.response?.status).toBe(404);
    }
  });
});