import { test, expect } from '@playwright/test';
import { WorkspaceAPIClient } from '../helpers/api-client';
import { testWorkspaces, workspaceTemplates } from '../helpers/test-data';

test.describe('Workspace End-to-End Scenarios', () => {
  let apiClient: WorkspaceAPIClient;
  let createdWorkspaceIds: number[] = [];

  test.beforeEach(async ({ request }) => {
    apiClient = new WorkspaceAPIClient(request);
  });

  test.afterEach(async () => {
    // Cleanup all created workspaces
    for (const id of createdWorkspaceIds) {
      try {
        await apiClient.deleteWorkspace(id);
      } catch (error) {
        console.error(`Failed to delete workspace ${id}:`, error);
      }
    }
    createdWorkspaceIds = [];
  });

  test('complete workspace lifecycle', async () => {
    // 1. Create workspace from template
    const createResponse = await apiClient.createFromTemplate('work', 'Project Alpha', 1);
    const workspaceId = createResponse.workspace.id;
    createdWorkspaceIds.push(workspaceId);
    
    // 2. Switch to the workspace
    const switchResponse = await apiClient.switchWorkspace(workspaceId);
    expect(switchResponse.message).toContain('Switched to workspace');
    
    // 3. Update workspace state
    const initialState = {
      activeView: 'kanban',
      filters: { priority: 'high', status: 'active' },
      openTasks: [1, 2, 3]
    };
    await apiClient.updateWorkspaceState(workspaceId, initialState);
    
    // 4. Assign content to workspace
    const content = {
      type: 'task',
      text: 'Complete quarterly financial report',
      tags: ['finance', 'quarterly', 'urgent']
    };
    const assignResponse = await apiClient.assignContent(workspaceId, content);
    expect(assignResponse.overall_compatibility).toBeGreaterThan(0.5);
    
    // 5. Update ambient sound
    await apiClient.updateAmbientSound(workspaceId, 'office_ambience');
    
    // 6. Get analytics
    const analytics = await apiClient.getAnalytics(workspaceId);
    expect(analytics.workspace_name).toBe('Project Alpha');
    expect(analytics.ai_insights.productivity_score).toBeDefined();
    
    // 7. Update workspace settings
    await apiClient.updateWorkspace(workspaceId, {
      description: 'Main project workspace for Q4 2024',
      theme: 'dark',
      color: '#2563eb'
    });
    
    // 8. Verify all changes persisted
    const finalWorkspace = await apiClient.getWorkspace(workspaceId);
    expect(finalWorkspace.description).toContain('Q4 2024');
    expect(finalWorkspace.theme).toBe('dark');
    expect(finalWorkspace.ambient_sound).toBe('office_ambience');
    
    const finalState = await apiClient.getWorkspaceState(workspaceId);
    expect(finalState.state).toMatchObject(initialState);
  });

  test('multi-workspace workflow', async () => {
    // Create multiple workspaces for different purposes
    const workspaces = await Promise.all([
      apiClient.createFromTemplate('work', 'Main Office', 1),
      apiClient.createFromTemplate('personal', 'Home Tasks', 1),
      apiClient.createFromTemplate('creative', 'Side Projects', 1)
    ]);
    
    workspaces.forEach(w => createdWorkspaceIds.push(w.workspace.id));
    
    // Set different states for each workspace
    const states = [
      { context: 'work', activeProjects: ['client-a', 'client-b'] },
      { context: 'personal', todoLists: ['groceries', 'chores'] },
      { context: 'creative', ideas: ['app-idea-1', 'blog-post-2'] }
    ];
    
    await Promise.all(
      workspaces.map((w, i) => 
        apiClient.updateWorkspaceState(w.workspace.id, states[i])
      )
    );
    
    // Switch between workspaces and verify states are maintained
    for (let i = 0; i < workspaces.length; i++) {
      const switchResponse = await apiClient.switchWorkspace(workspaces[i].workspace.id);
      expect(switchResponse.state).toMatchObject(states[i]);
    }
    
    // Update ambient sounds for each workspace
    const sounds = ['office_ambience', 'nature_sounds', 'creativity_boost'];
    await Promise.all(
      workspaces.map((w, i) => 
        apiClient.updateAmbientSound(w.workspace.id, sounds[i])
      )
    );
    
    // Verify each workspace maintains its own configuration
    const verifiedWorkspaces = await Promise.all(
      workspaces.map(w => apiClient.getWorkspace(w.workspace.id))
    );
    
    expect(verifiedWorkspaces[0].ambient_sound).toBe('office_ambience');
    expect(verifiedWorkspaces[1].ambient_sound).toBe('nature_sounds');
    expect(verifiedWorkspaces[2].ambient_sound).toBe('creativity_boost');
  });

  test('workspace template coverage', async () => {
    // Test creating workspaces from all available templates
    const createdWorkspaces = [];
    
    for (const template of workspaceTemplates) {
      const response = await apiClient.createFromTemplate(
        template,
        `Test ${template} Workspace`,
        1
      );
      createdWorkspaces.push(response.workspace);
      createdWorkspaceIds.push(response.workspace.id);
    }
    
    // Verify each workspace has appropriate characteristics
    expect(createdWorkspaces.length).toBe(workspaceTemplates.length);
    
    // Check that each workspace has unique configuration
    const themes = new Set(createdWorkspaces.map(w => w.theme));
    const sounds = new Set(createdWorkspaces.map(w => w.ambient_sound));
    
    expect(themes.size).toBeGreaterThan(3);
    expect(sounds.size).toBeGreaterThan(4);
    
    // Verify widget configurations are different
    const widgetSets = createdWorkspaces.map(w => 
      JSON.stringify(w.layout_config.widgets.sort())
    );
    const uniqueWidgetSets = new Set(widgetSets);
    expect(uniqueWidgetSets.size).toBeGreaterThan(4);
  });

  test('workspace organization workflow', async () => {
    // Create a workspace for organizing mixed content
    const orgWorkspace = await apiClient.createWorkspace({
      name: 'Organization Hub',
      description: 'Central workspace for organizing various content types',
      theme: 'minimal',
      user_id: 1
    });
    createdWorkspaceIds.push(orgWorkspace.id);
    
    // Test content assignment for different types
    const contentItems = [
      { type: 'document', text: 'Annual budget spreadsheet for 2024' },
      { type: 'task', text: 'Review and approve marketing campaign' },
      { type: 'note', text: 'Ideas for improving team productivity' },
      { type: 'file', text: 'Customer feedback analysis report' }
    ];
    
    const assignments = await Promise.all(
      contentItems.map(content => 
        apiClient.assignContent(orgWorkspace.id, content)
      )
    );
    
    // Verify AI provides appropriate suggestions for each content type
    assignments.forEach((assignment, index) => {
      expect(assignment.content_analysis).toBeDefined();
      expect(assignment.organization_suggestions).toBeInstanceOf(Array);
      expect(assignment.organization_suggestions.length).toBeGreaterThan(0);
    });
    
    // Get workspace suggestions based on content
    const suggestions = await apiClient.request.get(
      `/api/workspaces/${orgWorkspace.id}/suggestions`
    );
    const suggestionsData = await suggestions.json();
    
    expect(suggestionsData.suggestions).toBeInstanceOf(Array);
    expect(suggestionsData.suggestions.length).toBeGreaterThan(0);
  });

  test('workspace performance under load', async () => {
    // Create multiple workspaces rapidly
    const workspaceCount = 10;
    const createPromises = [];
    
    for (let i = 0; i < workspaceCount; i++) {
      const promise = apiClient.createWorkspace({
        name: `Load Test Workspace ${i}`,
        description: `Testing workspace creation performance ${i}`,
        theme: i % 2 === 0 ? 'dark' : 'light',
        user_id: 1
      });
      createPromises.push(promise);
    }
    
    const startTime = Date.now();
    const createdWorkspaces = await Promise.all(createPromises);
    const endTime = Date.now();
    
    createdWorkspaces.forEach(w => createdWorkspaceIds.push(w.id));
    
    // Verify all workspaces were created
    expect(createdWorkspaces.length).toBe(workspaceCount);
    
    // Check performance (should complete in reasonable time)
    const totalTime = endTime - startTime;
    expect(totalTime).toBeLessThan(30000); // 30 seconds max
    
    // Update states concurrently
    const statePromises = createdWorkspaces.map((w, i) => 
      apiClient.updateWorkspaceState(w.id, {
        index: i,
        timestamp: Date.now(),
        data: `State for workspace ${i}`
      })
    );
    
    await Promise.all(statePromises);
    
    // Verify states were saved correctly
    const verifyPromises = createdWorkspaces.map(async (w, i) => {
      const state = await apiClient.getWorkspaceState(w.id);
      expect(state.state.index).toBe(i);
    });
    
    await Promise.all(verifyPromises);
  });

  test('workspace migration scenario', async () => {
    // Simulate migrating from one workspace to another
    
    // 1. Create source workspace with content
    const sourceWorkspace = await apiClient.createWorkspace({
      name: 'Old Project Workspace',
      description: 'Legacy workspace to be migrated',
      theme: 'professional',
      user_id: 1
    });
    createdWorkspaceIds.push(sourceWorkspace.id);
    
    // 2. Set up complex state in source workspace
    const sourceState = {
      projects: ['project-a', 'project-b', 'project-c'],
      settings: {
        notifications: true,
        autoSave: true,
        theme: 'dark'
      },
      customData: {
        clientInfo: { name: 'ACME Corp', id: '12345' },
        deadlines: { 'project-a': '2024-12-31', 'project-b': '2025-01-15' }
      }
    };
    await apiClient.updateWorkspaceState(sourceWorkspace.id, sourceState);
    
    // 3. Create destination workspace from template
    const destResponse = await apiClient.createFromTemplate(
      'work',
      'New Project Workspace',
      1
    );
    createdWorkspaceIds.push(destResponse.workspace.id);
    
    // 4. Get source state and transfer to destination
    const sourceStateResponse = await apiClient.getWorkspaceState(sourceWorkspace.id);
    await apiClient.updateWorkspaceState(
      destResponse.workspace.id,
      sourceStateResponse.state
    );
    
    // 5. Copy settings
    await apiClient.updateWorkspace(destResponse.workspace.id, {
      description: `Migrated from ${sourceWorkspace.name}`,
      theme: sourceWorkspace.theme,
      ambient_sound: sourceWorkspace.ambient_sound || 'none'
    });
    
    // 6. Verify migration
    const destState = await apiClient.getWorkspaceState(destResponse.workspace.id);
    expect(destState.state).toEqual(sourceState);
    
    const destWorkspace = await apiClient.getWorkspace(destResponse.workspace.id);
    expect(destWorkspace.description).toContain('Migrated from');
  });
});