import { test, expect } from '@playwright/test';
import { WorkspaceAPIClient } from '../helpers/api-client';
import { workspaceTemplates } from '../helpers/test-data';

test.describe('Workspace Templates and Themes', () => {
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

  test('should get available workspace templates', async () => {
    const response = await apiClient.getTemplates();
    
    expect(response).toHaveProperty('templates');
    expect(response).toHaveProperty('total');
    expect(response).toHaveProperty('categories');
    
    const templates = response.templates;
    expect(Object.keys(templates)).toEqual(expect.arrayContaining(workspaceTemplates));
    
    // Verify template structure
    for (const templateName of workspaceTemplates) {
      const template = templates[templateName];
      expect(template).toHaveProperty('name');
      expect(template).toHaveProperty('display_name');
      expect(template).toHaveProperty('description');
      expect(template).toHaveProperty('theme');
      expect(template).toHaveProperty('color');
      expect(template).toHaveProperty('icon');
      expect(template).toHaveProperty('default_widgets');
      expect(template).toHaveProperty('ambient_sound');
      expect(template).toHaveProperty('features');
      expect(template).toHaveProperty('recommended_for');
    }
  });

  test('should get available themes', async () => {
    const response = await apiClient.getThemes();
    
    expect(response).toHaveProperty('builtin_themes');
    expect(response).toHaveProperty('custom_themes');
    expect(response).toHaveProperty('total_themes');
    
    const builtinThemes = response.builtin_themes;
    const expectedThemes = ['professional', 'minimal', 'dark', 'colorful', 'light'];
    
    expect(Object.keys(builtinThemes)).toEqual(expect.arrayContaining(expectedThemes));
    
    // Verify theme structure
    for (const themeName of expectedThemes) {
      const theme = builtinThemes[themeName];
      expect(theme).toHaveProperty('name');
      expect(theme).toHaveProperty('display_name');
      expect(theme).toHaveProperty('description');
      expect(theme).toHaveProperty('primary_color');
      expect(theme).toHaveProperty('secondary_color');
      expect(theme).toHaveProperty('accent_color');
      expect(theme).toHaveProperty('background_color');
      expect(theme).toHaveProperty('text_color');
      expect(theme).toHaveProperty('is_dark_mode');
      expect(theme).toHaveProperty('is_system');
      expect(theme.is_system).toBe(true);
    }
  });

  test('should create workspace from work template', async () => {
    const response = await apiClient.createFromTemplate('work', 'My Work Space', 1);
    
    expect(response).toHaveProperty('workspace');
    expect(response).toHaveProperty('template_used');
    expect(response).toHaveProperty('message');
    
    const workspace = response.workspace;
    createdWorkspaceIds.push(workspace.id);
    
    expect(workspace.name).toBe('My Work Space');
    expect(workspace.theme).toBe('professional');
    expect(workspace.description).toContain('Professional workspace');
    expect(workspace.ambient_sound).toBe('office_ambience');
    expect(workspace.layout_config.widgets).toEqual(['calendar', 'tasks', 'notes', 'quick_actions']);
    expect(workspace.layout_config.created_from_template).toBe('work');
  });

  test('should create workspace from study template', async () => {
    const response = await apiClient.createFromTemplate('study', 'Study Session', 1);
    
    const workspace = response.workspace;
    createdWorkspaceIds.push(workspace.id);
    
    expect(workspace.name).toBe('Study Session');
    expect(workspace.theme).toBe('light');
    expect(workspace.description).toContain('Study workspace');
    expect(workspace.ambient_sound).toBe('study_music');
    expect(workspace.layout_config.widgets).toEqual(['notes', 'timer', 'calendar', 'files']);
    expect(workspace.layout_config.color_scheme).toBe('purple');
  });

  test('should create workspace from creative template', async () => {
    const response = await apiClient.createFromTemplate('creative', 'Art Studio', 1);
    
    const workspace = response.workspace;
    createdWorkspaceIds.push(workspace.id);
    
    expect(workspace.name).toBe('Art Studio');
    expect(workspace.theme).toBe('colorful');
    expect(workspace.ambient_sound).toBe('creativity_boost');
    expect(workspace.layout_config.widgets).toContain('gallery');
    expect(workspace.layout_config.widgets).toContain('music');
  });

  test('should create workspace from wellness template', async () => {
    const response = await apiClient.createFromTemplate('wellness', 'Health Tracker', 1);
    
    const workspace = response.workspace;
    createdWorkspaceIds.push(workspace.id);
    
    expect(workspace.name).toBe('Health Tracker');
    expect(workspace.theme).toBe('light');
    expect(workspace.ambient_sound).toBe('meditation_sounds');
    expect(workspace.layout_config.widgets).toContain('timer');
    expect(workspace.layout_config.color_scheme).toBe('green');
  });

  test('should handle invalid template name', async () => {
    try {
      await apiClient.createFromTemplate('invalid_template', 'Test Workspace', 1);
      expect(true).toBe(false); // Should not reach here
    } catch (error: any) {
      expect(error.response?.status).toBe(400);
      const errorData = await error.response?.json();
      expect(errorData.detail).toContain('Template');
      expect(errorData.detail).toContain('not found');
    }
  });

  test('should verify all templates have unique characteristics', async () => {
    const response = await apiClient.getTemplates();
    const templates = response.templates;
    
    const themes = new Set();
    const colors = new Set();
    const sounds = new Set();
    
    for (const templateName in templates) {
      const template = templates[templateName];
      themes.add(template.theme);
      colors.add(template.color);
      sounds.add(template.ambient_sound);
    }
    
    // Each template should have some unique characteristics
    expect(themes.size).toBeGreaterThan(3); // At least 3 different themes
    expect(colors.size).toBeGreaterThan(4); // At least 4 different colors
    expect(sounds.size).toBeGreaterThan(4); // At least 4 different sounds
  });

  test('should create multiple workspaces from same template', async () => {
    // Create two workspaces from the same template
    const response1 = await apiClient.createFromTemplate('focus', 'Focus Session 1', 1);
    const response2 = await apiClient.createFromTemplate('focus', 'Focus Session 2', 1);
    
    createdWorkspaceIds.push(response1.workspace.id);
    createdWorkspaceIds.push(response2.workspace.id);
    
    // They should have different IDs but same template characteristics
    expect(response1.workspace.id).not.toBe(response2.workspace.id);
    expect(response1.workspace.theme).toBe(response2.workspace.theme);
    expect(response1.workspace.ambient_sound).toBe(response2.workspace.ambient_sound);
    expect(response1.workspace.layout_config.widgets).toEqual(response2.workspace.layout_config.widgets);
  });

  test('should validate theme compatibility with templates', async () => {
    const templatesResponse = await apiClient.getTemplates();
    const themesResponse = await apiClient.getThemes();
    
    const templates = templatesResponse.templates;
    const themes = themesResponse.builtin_themes;
    
    // Verify that all template themes exist in available themes
    for (const templateName in templates) {
      const template = templates[templateName];
      expect(themes).toHaveProperty(template.theme);
    }
  });
});