-- OrdnungsHub Database Schema for MCP Integration
-- Optimized for AI-powered file organization and analysis

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Workspaces table
CREATE TABLE IF NOT EXISTS workspaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    path TEXT,
    color TEXT DEFAULT '#2563eb',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    metadata JSON
);

-- File metadata table with AI insights
CREATE TABLE IF NOT EXISTS file_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    category TEXT DEFAULT 'general',
    subcategory TEXT,
    priority TEXT DEFAULT 'medium', -- low, medium, high, urgent
    ai_category TEXT,               -- AI-determined category
    ai_confidence REAL DEFAULT 0.0, -- AI confidence score (0-1)
    tags JSON,                      -- JSON array of tags
    ai_tags JSON,                   -- AI-generated tags
    content_preview TEXT,           -- First few lines for text files
    content_hash TEXT,              -- For duplicate detection
    similarity_hash TEXT,           -- LSH hash for similarity
    extracted_entities JSON,        -- JSON object of extracted entities
    sentiment_score REAL,           -- Sentiment analysis score
    complexity_score REAL,          -- Content complexity score
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_accessed DATETIME,
    is_archived BOOLEAN DEFAULT 0,
    
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

-- Tasks table for task management
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending', -- pending, in_progress, completed, cancelled
    priority TEXT DEFAULT 'medium',
    category TEXT DEFAULT 'general',
    ai_category TEXT,              -- AI-suggested category
    ai_suggestions JSON,           -- AI-generated suggestions
    due_date DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    tags JSON,
    metadata JSON,
    
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

-- AI analysis results table
CREATE TABLE IF NOT EXISTS ai_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,     -- 'file', 'task', 'workspace'
    entity_id INTEGER NOT NULL,
    analysis_type TEXT NOT NULL,   -- 'categorization', 'sentiment', 'priority', 'similarity'
    analysis_version TEXT DEFAULT '1.0',
    input_data JSON,               -- Input data for analysis
    result_data JSON,              -- Analysis results
    confidence_score REAL DEFAULT 0.0,
    processing_time REAL,          -- Processing time in milliseconds
    model_used TEXT,               -- Model/service used for analysis
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- File clusters table for organization insights
CREATE TABLE IF NOT EXISTS file_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_name TEXT NOT NULL,
    cluster_method TEXT,           -- 'ml_kmeans', 'rule_based', 'manual'
    dominant_category TEXT,
    file_count INTEGER DEFAULT 0,
    avg_similarity REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- File cluster membership
CREATE TABLE IF NOT EXISTS file_cluster_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER,
    file_id INTEGER,
    similarity_score REAL DEFAULT 0.0,
    
    FOREIGN KEY (cluster_id) REFERENCES file_clusters(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES file_metadata(id) ON DELETE CASCADE,
    UNIQUE(cluster_id, file_id)
);

-- User actions for learning
CREATE TABLE IF NOT EXISTS user_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,     -- 'categorize', 'prioritize', 'tag', 'move', 'archive'
    entity_type TEXT NOT NULL,     -- 'file', 'task'
    entity_id INTEGER NOT NULL,
    old_value TEXT,
    new_value TEXT,
    user_context JSON,             -- Additional context
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type TEXT NOT NULL,     -- 'categorization_accuracy', 'processing_time', 'user_satisfaction'
    metric_value REAL NOT NULL,
    context JSON,                  -- Additional context about the metric
    measured_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Search index for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS file_search USING fts5(
    filename,
    content_preview,
    tags,
    category,
    content=file_metadata,
    content_rowid=id
);

-- Triggers to maintain search index
CREATE TRIGGER IF NOT EXISTS file_metadata_ai AFTER INSERT ON file_metadata BEGIN
    INSERT INTO file_search(rowid, filename, content_preview, tags, category)
    VALUES (new.id, new.filename, new.content_preview, new.tags, new.category);
END;

CREATE TRIGGER IF NOT EXISTS file_metadata_au AFTER UPDATE ON file_metadata BEGIN
    UPDATE file_search SET 
        filename = new.filename,
        content_preview = new.content_preview,
        tags = new.tags,
        category = new.category
    WHERE rowid = new.id;
END;

CREATE TRIGGER IF NOT EXISTS file_metadata_ad AFTER DELETE ON file_metadata BEGIN
    DELETE FROM file_search WHERE rowid = old.id;
END;

-- Trigger to update timestamps
CREATE TRIGGER IF NOT EXISTS update_file_metadata_timestamp 
AFTER UPDATE ON file_metadata
BEGIN
    UPDATE file_metadata SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_workspace_timestamp 
AFTER UPDATE ON workspaces
BEGIN
    UPDATE workspaces SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_task_timestamp 
AFTER UPDATE ON tasks
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_file_metadata_workspace ON file_metadata(workspace_id);
CREATE INDEX IF NOT EXISTS idx_file_metadata_category ON file_metadata(category);
CREATE INDEX IF NOT EXISTS idx_file_metadata_type ON file_metadata(file_type);
CREATE INDEX IF NOT EXISTS idx_file_metadata_created ON file_metadata(created_at);
CREATE INDEX IF NOT EXISTS idx_file_metadata_hash ON file_metadata(content_hash);
CREATE INDEX IF NOT EXISTS idx_file_metadata_similarity ON file_metadata(similarity_hash);

CREATE INDEX IF NOT EXISTS idx_tasks_workspace ON tasks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);

CREATE INDEX IF NOT EXISTS idx_ai_analysis_entity ON ai_analysis(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_type ON ai_analysis(analysis_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(measured_at);
CREATE INDEX IF NOT EXISTS idx_user_actions_entity ON user_actions(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_user_actions_type ON user_actions(action_type);

-- Initial data
INSERT OR IGNORE INTO workspaces (name, description, path, color) VALUES 
('Default', 'Default workspace for general files', '/', '#2563eb'),
('Documents', 'Document organization workspace', '/documents', '#059669'),
('Projects', 'Development and project files', '/projects', '#dc2626'),
('Archive', 'Archived and old files', '/archive', '#6b7280');

-- Views for common queries
CREATE VIEW IF NOT EXISTS file_stats AS
SELECT 
    category,
    file_type,
    COUNT(*) as file_count,
    AVG(file_size) as avg_size,
    MIN(created_at) as earliest,
    MAX(created_at) as latest,
    AVG(ai_confidence) as avg_ai_confidence
FROM file_metadata 
GROUP BY category, file_type;

CREATE VIEW IF NOT EXISTS workspace_summary AS
SELECT 
    w.id,
    w.name,
    w.description,
    COUNT(f.id) as file_count,
    COUNT(t.id) as task_count,
    AVG(f.ai_confidence) as avg_ai_confidence,
    MAX(f.updated_at) as last_file_update
FROM workspaces w
LEFT JOIN file_metadata f ON w.id = f.workspace_id
LEFT JOIN tasks t ON w.id = t.workspace_id
GROUP BY w.id, w.name, w.description;

CREATE VIEW IF NOT EXISTS ai_performance AS
SELECT 
    analysis_type,
    COUNT(*) as analysis_count,
    AVG(confidence_score) as avg_confidence,
    AVG(processing_time) as avg_processing_time,
    model_used
FROM ai_analysis 
GROUP BY analysis_type, model_used;

-- Utility functions (SQLite doesn't support custom functions directly, but these are example queries)

-- Function to calculate category distribution
-- SELECT category, COUNT(*) * 100.0 / (SELECT COUNT(*) FROM file_metadata) as percentage FROM file_metadata GROUP BY category;

-- Function to find similar files by hash
-- SELECT f1.filename as file1, f2.filename as file2, f1.similarity_hash FROM file_metadata f1 JOIN file_metadata f2 ON f1.similarity_hash = f2.similarity_hash WHERE f1.id < f2.id;

-- Function to get AI accuracy
-- SELECT 
--   SUM(CASE WHEN f.category = f.ai_category THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as accuracy_percentage
-- FROM file_metadata f 
-- WHERE f.ai_category IS NOT NULL;

PRAGMA user_version = 1;