/**
 * Professional Translation Service Integration
 * Provides integration with professional translation services like Crowdin, Lokalise, Transifex, etc.
 */

export interface TranslationProject {
  id: string;
  name: string;
  sourceLanguage: string;
  targetLanguages: string[];
  status: 'active' | 'completed' | 'paused';
  progress: Record<string, number>;
  deadline?: Date;
  budget?: number;
  description?: string;
}

export interface TranslationJob {
  id: string;
  projectId: string;
  sourceLanguage: string;
  targetLanguage: string;
  keys: string[];
  status: 'pending' | 'in_progress' | 'review' | 'completed' | 'rejected';
  translatorId?: string;
  reviewerId?: string;
  deadline?: Date;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  instructions?: string;
  estimatedWords: number;
  completedWords: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface TranslationProvider {
  id: string;
  name: string;
  type: 'crowdin' | 'lokalise' | 'transifex' | 'phrase' | 'weblate' | 'custom';
  apiEndpoint: string;
  authenticated: boolean;
  supportedLanguages: string[];
  features: {
    autoTranslation: boolean;
    humanTranslation: boolean;
    review: boolean;
    qa: boolean;
    tm: boolean; // Translation Memory
    glossary: boolean;
  };
}

export interface TranslationMemory {
  sourceText: string;
  targetText: string;
  sourceLanguage: string;
  targetLanguage: string;
  confidence: number;
  context?: string;
  domain?: string;
  lastUsed: Date;
}

export interface TranslationOrder {
  id: string;
  projectId: string;
  providerId: string;
  keys: string[];
  sourceLanguage: string;
  targetLanguages: string[];
  type: 'human' | 'machine' | 'hybrid';
  quality: 'basic' | 'professional' | 'premium';
  deadline: Date;
  instructions: string;
  status: 'draft' | 'submitted' | 'in_progress' | 'completed' | 'cancelled';
  estimatedCost: number;
  actualCost?: number;
  deliveryDate?: Date;
}

export class TranslationService {
  private providers: Map<string, TranslationProvider> = new Map();
  private apiKey: string | null = null;
  private baseUrl: string;

  constructor(baseUrl: string = '/api/translations') {
    this.baseUrl = baseUrl;
    this.loadProviders();
  }

  // Provider Management
  async addProvider(provider: Omit<TranslationProvider, 'id'>): Promise<TranslationProvider> {
    const response = await fetch(`${this.baseUrl}/providers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(provider)
    });

    if (!response.ok) {
      throw new Error(`Failed to add provider: ${response.statusText}`);
    }

    const newProvider = await response.json();
    this.providers.set(newProvider.id, newProvider);
    return newProvider;
  }

  async removeProvider(providerId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/providers/${providerId}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error(`Failed to remove provider: ${response.statusText}`);
    }

    this.providers.delete(providerId);
  }

  async authenticateProvider(providerId: string, credentials: any): Promise<boolean> {
    const response = await fetch(`${this.baseUrl}/providers/${providerId}/auth`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });

    if (!response.ok) {
      throw new Error(`Authentication failed: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (result.success) {
      const provider = this.providers.get(providerId);
      if (provider) {
        provider.authenticated = true;
        this.providers.set(providerId, provider);
      }
    }

    return result.success;
  }

  private async loadProviders(): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/providers`);
      if (response.ok) {
        const providers = await response.json();
        providers.forEach((provider: TranslationProvider) => {
          this.providers.set(provider.id, provider);
        });
      }
    } catch (error) {
      console.error('Failed to load translation providers:', error);
    }
  }

  // Project Management
  async createProject(project: Omit<TranslationProject, 'id' | 'status' | 'progress'>): Promise<TranslationProject> {
    const response = await fetch(`${this.baseUrl}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...project,
        status: 'active',
        progress: project.targetLanguages.reduce((acc, lang) => {
          acc[lang] = 0;
          return acc;
        }, {} as Record<string, number>)
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to create project: ${response.statusText}`);
    }

    return response.json();
  }

  async getProjects(): Promise<TranslationProject[]> {
    const response = await fetch(`${this.baseUrl}/projects`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch projects: ${response.statusText}`);
    }

    return response.json();
  }

  async getProject(projectId: string): Promise<TranslationProject> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch project: ${response.statusText}`);
    }

    return response.json();
  }

  async updateProject(projectId: string, updates: Partial<TranslationProject>): Promise<TranslationProject> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });

    if (!response.ok) {
      throw new Error(`Failed to update project: ${response.statusText}`);
    }

    return response.json();
  }

  // Translation Orders
  async createOrder(order: Omit<TranslationOrder, 'id' | 'status'>): Promise<TranslationOrder> {
    const response = await fetch(`${this.baseUrl}/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...order,
        status: 'draft'
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to create order: ${response.statusText}`);
    }

    return response.json();
  }

  async submitOrder(orderId: string): Promise<TranslationOrder> {
    const response = await fetch(`${this.baseUrl}/orders/${orderId}/submit`, {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error(`Failed to submit order: ${response.statusText}`);
    }

    return response.json();
  }

  async getOrders(projectId?: string): Promise<TranslationOrder[]> {
    const url = projectId 
      ? `${this.baseUrl}/orders?projectId=${projectId}`
      : `${this.baseUrl}/orders`;
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch orders: ${response.statusText}`);
    }

    return response.json();
  }

  async cancelOrder(orderId: string, reason?: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/orders/${orderId}/cancel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    });

    if (!response.ok) {
      throw new Error(`Failed to cancel order: ${response.statusText}`);
    }
  }

  // Translation Jobs
  async getJobs(projectId?: string, status?: string): Promise<TranslationJob[]> {
    let url = `${this.baseUrl}/jobs`;
    const params = new URLSearchParams();
    
    if (projectId) params.set('projectId', projectId);
    if (status) params.set('status', status);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch jobs: ${response.statusText}`);
    }

    return response.json();
  }

  async approveJob(jobId: string, feedback?: string): Promise<TranslationJob> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback })
    });

    if (!response.ok) {
      throw new Error(`Failed to approve job: ${response.statusText}`);
    }

    return response.json();
  }

  async rejectJob(jobId: string, reason: string): Promise<TranslationJob> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    });

    if (!response.ok) {
      throw new Error(`Failed to reject job: ${response.statusText}`);
    }

    return response.json();
  }

  // Translation Memory
  async searchTranslationMemory(
    text: string, 
    sourceLanguage: string, 
    targetLanguage: string,
    threshold: number = 0.7
  ): Promise<TranslationMemory[]> {
    const params = new URLSearchParams({
      text,
      sourceLanguage,
      targetLanguage,
      threshold: threshold.toString()
    });

    const response = await fetch(`${this.baseUrl}/tm/search?${params}`);
    
    if (!response.ok) {
      throw new Error(`Failed to search translation memory: ${response.statusText}`);
    }

    return response.json();
  }

  async addToTranslationMemory(entry: Omit<TranslationMemory, 'lastUsed'>): Promise<void> {
    const response = await fetch(`${this.baseUrl}/tm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...entry,
        lastUsed: new Date()
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to add to translation memory: ${response.statusText}`);
    }
  }

  // Machine Translation
  async getMachineTranslation(
    text: string,
    sourceLanguage: string,
    targetLanguage: string,
    provider?: string
  ): Promise<string> {
    const response = await fetch(`${this.baseUrl}/mt/translate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        sourceLanguage,
        targetLanguage,
        provider
      })
    });

    if (!response.ok) {
      throw new Error(`Machine translation failed: ${response.statusText}`);
    }

    const result = await response.json();
    return result.translatedText;
  }

  // Quality Assurance
  async runQualityCheck(
    sourceText: string,
    translatedText: string,
    sourceLanguage: string,
    targetLanguage: string
  ): Promise<{
    score: number;
    issues: Array<{
      type: 'spelling' | 'grammar' | 'terminology' | 'consistency' | 'completeness';
      severity: 'low' | 'medium' | 'high';
      message: string;
      position?: { start: number; end: number };
    }>;
  }> {
    const response = await fetch(`${this.baseUrl}/qa/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sourceText,
        translatedText,
        sourceLanguage,
        targetLanguage
      })
    });

    if (!response.ok) {
      throw new Error(`Quality check failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Export/Import
  async exportTranslations(
    projectId: string,
    languages: string[],
    format: 'json' | 'csv' | 'xlsx' | 'xliff' | 'gettext' = 'json'
  ): Promise<Blob> {
    const params = new URLSearchParams({
      format,
      languages: languages.join(',')
    });

    const response = await fetch(`${this.baseUrl}/projects/${projectId}/export?${params}`);
    
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.blob();
  }

  async importTranslations(
    projectId: string,
    file: File,
    targetLanguage: string,
    format: 'json' | 'csv' | 'xlsx' | 'xliff' | 'gettext',
    options?: {
      overwrite?: boolean;
      skipEmpty?: boolean;
      createKeys?: boolean;
    }
  ): Promise<{
    imported: number;
    skipped: number;
    errors: string[];
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('targetLanguage', targetLanguage);
    formData.append('format', format);
    
    if (options) {
      formData.append('options', JSON.stringify(options));
    }

    const response = await fetch(`${this.baseUrl}/projects/${projectId}/import`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Import failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Analytics and Reporting
  async getTranslationMetrics(projectId: string, timeRange?: { start: Date; end: Date }): Promise<{
    totalWords: number;
    translatedWords: number;
    reviewedWords: number;
    completionRate: Record<string, number>;
    qualityScore: Record<string, number>;
    velocity: Record<string, number>; // words per day
    cost: Record<string, number>;
    timeline: Array<{
      date: Date;
      words: number;
      cost: number;
    }>;
  }> {
    let url = `${this.baseUrl}/projects/${projectId}/metrics`;
    
    if (timeRange) {
      const params = new URLSearchParams({
        start: timeRange.start.toISOString(),
        end: timeRange.end.toISOString()
      });
      url += `?${params}`;
    }

    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch metrics: ${response.statusText}`);
    }

    return response.json();
  }

  async generateReport(
    projectId: string,
    type: 'progress' | 'quality' | 'cost' | 'timeline',
    format: 'pdf' | 'xlsx' | 'csv' = 'pdf'
  ): Promise<Blob> {
    const params = new URLSearchParams({ type, format });
    
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/report?${params}`);
    
    if (!response.ok) {
      throw new Error(`Report generation failed: ${response.statusText}`);
    }

    return response.blob();
  }

  // Webhook Management
  async configureWebhook(
    projectId: string,
    url: string,
    events: string[],
    secret?: string
  ): Promise<{ id: string; url: string; events: string[] }> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/webhooks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, events, secret })
    });

    if (!response.ok) {
      throw new Error(`Webhook configuration failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Utility Methods
  getProvider(providerId: string): TranslationProvider | undefined {
    return this.providers.get(providerId);
  }

  getAvailableProviders(): TranslationProvider[] {
    return Array.from(this.providers.values());
  }

  getAuthenticatedProviders(): TranslationProvider[] {
    return Array.from(this.providers.values()).filter(p => p.authenticated);
  }

  estimateTranslationCost(
    wordCount: number,
    sourceLanguage: string,
    targetLanguages: string[],
    quality: 'basic' | 'professional' | 'premium' = 'professional'
  ): Promise<Record<string, number>> {
    // This would typically call the provider APIs for accurate estimates
    const baseRates = {
      basic: 0.08,      // $0.08 per word
      professional: 0.12, // $0.12 per word
      premium: 0.18     // $0.18 per word
    };

    const languageMultipliers: Record<string, number> = {
      'en': 1.0,
      'es': 1.1,
      'fr': 1.1,
      'de': 1.2,
      'zh': 1.5,
      'ja': 1.6,
      'ar': 1.4,
      'he': 1.4
    };

    const baseRate = baseRates[quality];
    const estimates: Record<string, number> = {};

    targetLanguages.forEach(lang => {
      const multiplier = languageMultipliers[lang] || 1.3;
      estimates[lang] = Math.round(wordCount * baseRate * multiplier * 100) / 100;
    });

    return Promise.resolve(estimates);
  }
}

// Global instance
export const translationService = new TranslationService();

// Hook for React components
export function useTranslationService() {
  return translationService;
}