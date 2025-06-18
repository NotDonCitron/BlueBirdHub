export const testWorkspaces = {
  basic: {
    name: 'Test Workspace',
    description: 'A test workspace for E2E testing',
    theme: 'professional',
    color: '#3b82f6',
    user_id: 1
  },
  
  minimal: {
    name: 'Minimal Workspace',
    description: 'Minimal workspace with basic features',
    theme: 'minimal',
    color: '#6b7280',
    user_id: 1
  },
  
  creative: {
    name: 'Creative Studio',
    description: 'Creative workspace for design projects',
    theme: 'colorful',
    color: '#ea580c',
    user_id: 1,
    ambient_sound: 'creativity_boost'
  },
  
  withState: {
    name: 'Stateful Workspace',
    description: 'Workspace with custom state',
    theme: 'dark',
    color: '#1f2937',
    user_id: 1,
    layout_config: {
      widgets: ['calendar', 'tasks', 'notes'],
      positions: {
        calendar: { x: 0, y: 0, w: 4, h: 3 },
        tasks: { x: 4, y: 0, w: 4, h: 3 },
        notes: { x: 8, y: 0, w: 4, h: 3 }
      }
    }
  }
};

export const testStates = {
  basic: {
    activeTab: 'dashboard',
    sidebarOpen: true,
    lastViewedFile: null
  },
  
  complex: {
    activeTab: 'files',
    sidebarOpen: false,
    lastViewedFile: '/documents/report.pdf',
    customSettings: {
      theme: 'dark',
      fontSize: 14,
      autoSave: true
    },
    widgetPositions: {
      calendar: { x: 0, y: 0, w: 6, h: 4 },
      tasks: { x: 6, y: 0, w: 6, h: 4 }
    }
  }
};

export const testContent = {
  document: {
    type: 'document',
    text: 'Quarterly financial report for Q4 2024',
    tags: ['finance', 'reports', 'quarterly']
  },
  
  task: {
    type: 'task',
    text: 'Complete the design mockups for the new landing page',
    tags: ['design', 'frontend', 'urgent']
  },
  
  note: {
    type: 'note',
    text: 'Meeting notes from project kickoff - discussed timeline and deliverables',
    tags: ['meetings', 'project-management']
  },
  
  code: {
    type: 'file',
    text: 'Python script for data analysis and visualization',
    tags: ['programming', 'python', 'data-science']
  }
};

export const availableAmbientSounds = [
  'none',
  'office_ambience',
  'nature_sounds',
  'study_music',
  'creativity_boost',
  'white_noise',
  'meditation_sounds',
  'rain',
  'forest',
  'ocean',
  'cafe'
];

export const workspaceTemplates = [
  'work',
  'personal',
  'study',
  'creative',
  'focus',
  'wellness'
];