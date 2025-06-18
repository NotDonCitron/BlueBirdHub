import { test, expect } from '@playwright/test';
import { WorkspaceAPIClient } from '../helpers/api-client';
import { testWorkspaces } from '../helpers/test-data';

test.describe('Workspace CRUD Operations', () => {
  let apiClient: WorkspaceAPIClient;
  let createdWorkspaceIds: number[] = [];

  test.beforeEach(async ({ request }) => {
    apiClient = new WorkspaceAPIClient(request);
  });

  test.afterEach(async () => {
    // Cleanup created workspaces
    for (const id of createdWorkspaceIds) {
      try {
        await apiClient.deleteWorkspace(id);
      } catch (error) {
        console.error(`Failed to delete workspace ${id}:`, error);
      }
    }
    createdWorkspaceIds = [];
  });

  test('should list all workspaces', async () => {
    const workspaces = await apiClient.getWorkspaces();
    
    expect(Array.isArray(workspaces)).toBeTruthy();
    expect(workspaces.length).toBeGreaterThan(0);
    
    // Verify workspace structure
    if (workspaces.length > 0) {
      const workspace = workspaces[0];
      expect(workspace).toHaveProperty('id');
      expect(workspace).toHaveProperty('name');
      expect(workspace).toHaveProperty('theme');
      expect(workspace).toHaveProperty('color');
      expect(workspace).toHaveProperty('user_id');
      expect(workspace).toHaveProperty('created_at');
    }
  });

  test('should create a new workspace', async () => {
    const newWorkspace = await apiClient.createWorkspace(testWorkspaces.basic);
    createdWorkspaceIds.push(newWorkspace.id);
    
    expect(newWorkspace).toMatchObject({
      name: testWorkspaces.basic.name,
      description: testWorkspaces.basic.description,
      theme: testWorkspaces.basic.theme,
      color: testWorkspaces.basic.color,
      user_id: testWorkspaces.basic.user_id
    });
    expect(newWorkspace.id).toBeDefined();
    expect(newWorkspace.created_at).toBeDefined();
  });

  test('should create workspace with AI suggestions', async () => {
    const workspaceData = {
      ...testWorkspaces.basic,
      name: 'AI Enhanced Workspace',
      description: 'A workspace for managing financial documents and reports'
    };
    
    const newWorkspace = await apiClient.createWorkspace(workspaceData);
    createdWorkspaceIds.push(newWorkspace.id);
    
    expect(newWorkspace).toBeDefined();
    expect(newWorkspace.name).toBe('AI Enhanced Workspace');
    // AI might suggest a different theme based on description
    expect(['professional', 'dark']).toContain(newWorkspace.theme);
  });

  test('should get a specific workspace by ID', async () => {
    // First create a workspace
    const created = await apiClient.createWorkspace(testWorkspaces.minimal);
    createdWorkspaceIds.push(created.id);
    
    // Then fetch it by ID
    const fetched = await apiClient.getWorkspace(created.id);
    
    expect(fetched).toMatchObject({
      id: created.id,
      name: created.name,
      description: created.description,
      theme: created.theme,
      color: created.color
    });
  });

  test('should update an existing workspace', async () => {
    // Create a workspace
    const created = await apiClient.createWorkspace(testWorkspaces.basic);
    createdWorkspaceIds.push(created.id);
    
    // Update it
    const updates = {
      name: 'Updated Workspace Name',
      description: 'Updated description',
      theme: 'dark',
      color: '#10b981'
    };
    
    const updated = await apiClient.updateWorkspace(created.id, updates);
    
    expect(updated).toMatchObject(updates);
    expect(updated.id).toBe(created.id);
  });

  test('should partially update a workspace', async () => {
    // Create a workspace
    const created = await apiClient.createWorkspace(testWorkspaces.creative);
    createdWorkspaceIds.push(created.id);
    
    // Update only the name
    const updated = await apiClient.updateWorkspace(created.id, {
      name: 'Renamed Creative Studio'
    });
    
    expect(updated.name).toBe('Renamed Creative Studio');
    // Other fields should remain unchanged
    expect(updated.theme).toBe(testWorkspaces.creative.theme);
    expect(updated.color).toBe(testWorkspaces.creative.color);
  });

  test('should delete a workspace', async () => {
    // Create a workspace
    const created = await apiClient.createWorkspace(testWorkspaces.minimal);
    
    // Delete it
    const deleteResponse = await apiClient.deleteWorkspace(created.id);
    expect(deleteResponse).toHaveProperty('message');
    expect(deleteResponse.message).toContain('deleted successfully');
    
    // Verify it's deleted by trying to fetch it
    try {
      await apiClient.getWorkspace(created.id);
      // If we reach here, the test should fail
      expect(true).toBe(false);
    } catch (error: any) {
      // Expected to fail with 404
      expect(error.response?.status).toBe(404);
    }
  });

  test('should handle non-existent workspace gracefully', async () => {
    const nonExistentId = 99999;
    
    try {
      await apiClient.getWorkspace(nonExistentId);
      expect(true).toBe(false); // Should not reach here
    } catch (error: any) {
      expect(error.response?.status).toBe(404);
    }
  });

  test('should validate required fields when creating workspace', async () => {
    try {
      // Try to create workspace without required fields
      await apiClient.createWorkspace({
        description: 'Missing name field'
      });
      expect(true).toBe(false); // Should not reach here
    } catch (error: any) {
      expect(error.response?.status).toBe(422); // Validation error
    }
  });

  test('should create workspace with layout configuration', async () => {
    const workspace = await apiClient.createWorkspace(testWorkspaces.withState);
    createdWorkspaceIds.push(workspace.id);
    
    expect(workspace.layout_config).toBeDefined();
    expect(workspace.layout_config.widgets).toEqual(['calendar', 'tasks', 'notes']);
    expect(workspace.layout_config.positions).toBeDefined();
  });
});