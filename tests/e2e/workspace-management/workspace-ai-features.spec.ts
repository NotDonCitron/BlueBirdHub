import { test, expect } from '@playwright/test';
import { WorkspaceAPIClient } from '../helpers/api-client';
import { testWorkspaces, testContent } from '../helpers/test-data';

test.describe('Workspace AI Features', () => {
  let apiClient: WorkspaceAPIClient;
  let testWorkspaceId: number;
  let creativeWorkspaceId: number;
  let studyWorkspaceId: number;

  test.beforeAll(async ({ request }) => {
    apiClient = new WorkspaceAPIClient(request);
    
    // Create test workspaces for AI feature testing
    const workspace1 = await apiClient.createWorkspace({
      ...testWorkspaces.basic,
      name: 'Finance Workspace',
      description: 'Workspace for financial reports and analysis'
    });
    testWorkspaceId = workspace1.id;
    
    const workspace2 = await apiClient.createWorkspace({
      ...testWorkspaces.creative,
      name: 'Design Studio',
      description: 'Creative workspace for UI/UX design projects'
    });
    creativeWorkspaceId = workspace2.id;
    
    const workspace3 = await apiClient.createWorkspace({
      ...testWorkspaces.minimal,
      name: 'Research Hub',
      description: 'Academic research and study workspace'
    });
    studyWorkspaceId = workspace3.id;
  });

  test.afterAll(async () => {
    // Cleanup
    const workspaceIds = [testWorkspaceId, creativeWorkspaceId, studyWorkspaceId];
    for (const id of workspaceIds) {
      if (id) {
        try {
          await apiClient.deleteWorkspace(id);
        } catch (error) {
          console.error(`Failed to cleanup workspace ${id}:`, error);
        }
      }
    }
  });

  test('should analyze content and suggest workspace assignment', async () => {
    const response = await apiClient.assignContent(testWorkspaceId, testContent.document);
    
    expect(response).toHaveProperty('workspace_id');
    expect(response).toHaveProperty('workspace_name');
    expect(response).toHaveProperty('content_analysis');
    expect(response).toHaveProperty('compatibility_factors');
    expect(response).toHaveProperty('overall_compatibility');
    expect(response).toHaveProperty('recommendation');
    expect(response).toHaveProperty('reasoning');
    expect(response).toHaveProperty('organization_suggestions');
    expect(response).toHaveProperty('alternative_workspaces');
    
    // Verify AI analysis
    const analysis = response.content_analysis;
    expect(analysis).toHaveProperty('category');
    expect(analysis).toHaveProperty('sentiment');
    expect(analysis).toHaveProperty('entities');
    
    // Financial content should have high compatibility with finance workspace
    expect(response.overall_compatibility).toBeGreaterThan(0.5);
  });

  test('should suggest appropriate workspace for design content', async () => {
    const response = await apiClient.assignContent(creativeWorkspaceId, testContent.task);
    
    expect(response.workspace_name).toBe('Design Studio');
    expect(response.content_analysis.category).toBeDefined();
    
    // Design task should be compatible with creative workspace
    expect(response.recommendation).toBeDefined();
    expect(response.organization_suggestions).toBeInstanceOf(Array);
  });

  test('should provide alternative workspace suggestions', async () => {
    const response = await apiClient.assignContent(testWorkspaceId, testContent.code);
    
    expect(response.alternative_workspaces).toBeInstanceOf(Array);
    expect(response.alternative_workspaces.length).toBeGreaterThan(0);
    
    // Each alternative should have workspace info and compatibility score
    if (response.alternative_workspaces.length > 0) {
      const alternative = response.alternative_workspaces[0];
      expect(alternative).toHaveProperty('workspace_id');
      expect(alternative).toHaveProperty('workspace_name');
      expect(alternative).toHaveProperty('compatibility_score');
      expect(alternative).toHaveProperty('reason');
    }
  });

  test('should handle content without text gracefully', async () => {
    try {
      await apiClient.assignContent(testWorkspaceId, {
        type: 'empty',
        tags: ['test']
      });
      expect(true).toBe(false); // Should not reach here
    } catch (error: any) {
      expect(error.response?.status).toBe(400);
      const errorData = await error.response?.json();
      expect(errorData.detail).toContain('Content text is required');
    }
  });

  test('should provide workspace suggestions', async () => {
    const response = await apiClient.getWorkspace(testWorkspaceId);
    const suggestions = await apiClient.request.get(`/api/workspaces/${testWorkspaceId}/suggestions`);
    const suggestionsData = await suggestions.json();
    
    expect(suggestionsData).toHaveProperty('workspace_id');
    expect(suggestionsData).toHaveProperty('suggestions');
    expect(suggestionsData).toHaveProperty('generated_at');
    
    expect(suggestionsData.suggestions).toBeInstanceOf(Array);
    
    // Verify suggestion structure
    if (suggestionsData.suggestions.length > 0) {
      const suggestion = suggestionsData.suggestions[0];
      expect(suggestion).toHaveProperty('type');
      expect(suggestion).toHaveProperty('suggestion');
      expect(suggestion).toHaveProperty('reason');
    }
  });

  test('should analyze different content types appropriately', async () => {
    const contentTypes = [
      { content: testContent.document, expectedCategory: ['finance', 'business', 'general'] },
      { content: testContent.task, expectedCategory: ['design', 'work', 'general'] },
      { content: testContent.note, expectedCategory: ['work', 'personal', 'general'] },
      { content: testContent.code, expectedCategory: ['work', 'education', 'general'] }
    ];
    
    for (const { content, expectedCategory } of contentTypes) {
      const response = await apiClient.assignContent(testWorkspaceId, content);
      
      expect(response.content_analysis).toBeDefined();
      expect(expectedCategory).toContain(response.content_analysis.category);
      expect(response.compatibility_factors).toBeDefined();
      expect(response.compatibility_factors.total_score).toBeGreaterThanOrEqual(0);
      expect(response.compatibility_factors.total_score).toBeLessThanOrEqual(1);
    }
  });

  test('should provide detailed compatibility factors', async () => {
    const response = await apiClient.assignContent(studyWorkspaceId, testContent.note);
    
    const factors = response.compatibility_factors;
    expect(factors).toHaveProperty('total_score');
    expect(factors).toHaveProperty('recommendation');
    expect(factors).toHaveProperty('detailed_reasoning');
    
    // Verify score is normalized between 0 and 1
    expect(factors.total_score).toBeGreaterThanOrEqual(0);
    expect(factors.total_score).toBeLessThanOrEqual(1);
  });

  test('should generate workspace analytics with AI insights', async () => {
    const analytics = await apiClient.getAnalytics(testWorkspaceId);
    
    expect(analytics).toHaveProperty('workspace_id');
    expect(analytics).toHaveProperty('workspace_name');
    expect(analytics).toHaveProperty('analytics_period');
    expect(analytics).toHaveProperty('usage_stats');
    expect(analytics).toHaveProperty('ai_insights');
    expect(analytics).toHaveProperty('recommendations');
    
    // Verify usage stats
    const stats = analytics.usage_stats;
    expect(stats).toHaveProperty('total_tasks');
    expect(stats).toHaveProperty('completed_tasks');
    expect(stats).toHaveProperty('completion_rate');
    expect(stats).toHaveProperty('estimated_time_spent_hours');
    expect(stats).toHaveProperty('last_accessed');
    
    // Verify AI insights
    const insights = analytics.ai_insights;
    expect(insights).toHaveProperty('productivity_score');
    expect(insights).toHaveProperty('suggested_improvements');
    expect(insights).toHaveProperty('category');
    expect(insights).toHaveProperty('sentiment');
    
    expect(insights.productivity_score).toBeGreaterThanOrEqual(0);
    expect(insights.productivity_score).toBeLessThanOrEqual(100);
    expect(insights.suggested_improvements).toBeInstanceOf(Array);
  });

  test('should provide contextual recommendations based on usage', async () => {
    const analytics = await apiClient.getAnalytics(creativeWorkspaceId);
    
    expect(analytics.recommendations).toBeInstanceOf(Array);
    expect(analytics.recommendations.length).toBeGreaterThan(0);
    
    const recommendation = analytics.recommendations[0];
    expect(recommendation).toHaveProperty('type');
    expect(recommendation).toHaveProperty('suggestion');
    expect(recommendation).toHaveProperty('reason');
    
    // Recommendations should be contextual
    expect(['widget', 'optimization', 'feature', 'workflow']).toContain(recommendation.type);
  });
});