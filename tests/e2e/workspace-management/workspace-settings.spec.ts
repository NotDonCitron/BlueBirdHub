import { test, expect } from '@playwright/test';
import { WorkspaceAPIClient } from '../helpers/api-client';
import { testWorkspaces, availableAmbientSounds } from '../helpers/test-data';

test.describe('Workspace Settings and Configurations', () => {
  let apiClient: WorkspaceAPIClient;
  let testWorkspaceId: number;

  test.beforeAll(async ({ request }) => {
    apiClient = new WorkspaceAPIClient(request);
    // Create a test workspace
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

  test('should update ambient sound setting', async () => {
    const response = await apiClient.updateAmbientSound(testWorkspaceId, 'rain');
    
    expect(response).toHaveProperty('workspace_id');
    expect(response).toHaveProperty('ambient_sound');
    expect(response).toHaveProperty('sound_name');
    expect(response).toHaveProperty('message');
    expect(response).toHaveProperty('available_sounds');
    
    expect(response.workspace_id).toBe(testWorkspaceId);
    expect(response.ambient_sound).toBe('rain');
    expect(response.sound_name).toBe('Rain sounds');
    expect(response.message).toContain('Ambient sound updated');
  });

  test('should list all available ambient sounds', async () => {
    const response = await apiClient.updateAmbientSound(testWorkspaceId, 'none');
    
    expect(response.available_sounds).toBeDefined();
    const sounds = Object.keys(response.available_sounds);
    
    // Verify all expected sounds are available
    for (const sound of availableAmbientSounds) {
      expect(sounds).toContain(sound);
    }
  });

  test('should handle invalid ambient sound', async () => {
    try {
      await apiClient.updateAmbientSound(testWorkspaceId, 'invalid_sound');
      expect(true).toBe(false); // Should not reach here
    } catch (error: any) {
      expect(error.response?.status).toBe(400);
      const errorData = await error.response?.json();
      expect(errorData.detail).toContain('Invalid ambient sound');
      expect(errorData.detail).toContain('Available options');
    }
  });

  test('should update multiple ambient sounds sequentially', async () => {
    const soundsToTest = ['ocean', 'forest', 'cafe', 'white_noise', 'none'];
    
    for (const sound of soundsToTest) {
      const response = await apiClient.updateAmbientSound(testWorkspaceId, sound);
      expect(response.ambient_sound).toBe(sound);
      
      // Verify the change persisted
      const workspace = await apiClient.getWorkspace(testWorkspaceId);
      expect(workspace.ambient_sound).toBe(sound);
    }
  });

  test('should update workspace theme', async () => {
    const themes = ['professional', 'minimal', 'dark', 'colorful', 'light'];
    
    for (const theme of themes) {
      const updated = await apiClient.updateWorkspace(testWorkspaceId, { theme });
      expect(updated.theme).toBe(theme);
    }
  });

  test('should update workspace color', async () => {
    const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff'];
    
    for (const color of colors) {
      const updated = await apiClient.updateWorkspace(testWorkspaceId, { color });
      expect(updated.color).toBe(color);
    }
  });

  test('should update layout configuration', async () => {
    const newLayout = {
      widgets: ['calendar', 'weather', 'news', 'stocks'],
      positions: {
        calendar: { x: 0, y: 0, w: 6, h: 4 },
        weather: { x: 6, y: 0, w: 3, h: 2 },
        news: { x: 9, y: 0, w: 3, h: 2 },
        stocks: { x: 6, y: 2, w: 6, h: 2 }
      },
      settings: {
        autoRefresh: true,
        refreshInterval: 300,
        compactMode: false
      }
    };
    
    const updated = await apiClient.updateWorkspace(testWorkspaceId, {
      layout_config: newLayout
    });
    
    expect(updated.layout_config).toEqual(newLayout);
  });

  test('should toggle workspace active status', async () => {
    // Deactivate workspace
    let updated = await apiClient.updateWorkspace(testWorkspaceId, {
      is_active: false
    });
    expect(updated.is_active).toBe(false);
    
    // Reactivate workspace
    updated = await apiClient.updateWorkspace(testWorkspaceId, {
      is_active: true
    });
    expect(updated.is_active).toBe(true);
  });

  test('should set workspace as default', async () => {
    const updated = await apiClient.updateWorkspace(testWorkspaceId, {
      is_default: true
    });
    expect(updated.is_default).toBe(true);
    
    // Unset default
    const updated2 = await apiClient.updateWorkspace(testWorkspaceId, {
      is_default: false
    });
    expect(updated2.is_default).toBe(false);
  });

  test('should handle complex configuration updates', async () => {
    const complexUpdate = {
      name: 'Advanced Workspace',
      description: 'Workspace with advanced configuration',
      theme: 'dark',
      color: '#8b5cf6',
      is_active: true,
      layout_config: {
        widgets: ['analytics', 'performance', 'logs', 'metrics'],
        layout: 'grid',
        density: 'comfortable',
        sidebar: {
          collapsed: false,
          width: 280,
          sections: ['favorites', 'recent', 'shared']
        },
        header: {
          showSearch: true,
          showNotifications: true,
          customActions: ['export', 'share', 'archive']
        }
      }
    };
    
    const updated = await apiClient.updateWorkspace(testWorkspaceId, complexUpdate);
    
    expect(updated.name).toBe(complexUpdate.name);
    expect(updated.description).toBe(complexUpdate.description);
    expect(updated.theme).toBe(complexUpdate.theme);
    expect(updated.color).toBe(complexUpdate.color);
    expect(updated.layout_config).toEqual(complexUpdate.layout_config);
  });

  test('should preserve unmodified fields during partial updates', async () => {
    // Get current state
    const original = await apiClient.getWorkspace(testWorkspaceId);
    
    // Update only name
    const updated = await apiClient.updateWorkspace(testWorkspaceId, {
      name: 'Renamed Workspace'
    });
    
    // Verify only name changed
    expect(updated.name).toBe('Renamed Workspace');
    expect(updated.theme).toBe(original.theme);
    expect(updated.color).toBe(original.color);
    expect(updated.description).toBe(original.description);
    expect(updated.layout_config).toEqual(original.layout_config);
  });

  test('should validate color format', async () => {
    // Valid hex colors
    const validColors = ['#123456', '#abcdef', '#ABCDEF', '#000000', '#ffffff'];
    
    for (const color of validColors) {
      const updated = await apiClient.updateWorkspace(testWorkspaceId, { color });
      expect(updated.color).toBe(color);
    }
    
    // Note: The API might accept various color formats or have validation
    // This test assumes hex format validation
  });

  test('should handle workspace icon updates', async () => {
    const icons = ['📊', '💼', '🎯', '🚀', '⚡'];
    
    for (const icon of icons) {
      const updated = await apiClient.updateWorkspace(testWorkspaceId, { icon });
      expect(updated.icon).toBe(icon);
    }
    
    // Test removing icon
    const updated = await apiClient.updateWorkspace(testWorkspaceId, { icon: null });
    expect(updated.icon).toBeNull();
  });
});