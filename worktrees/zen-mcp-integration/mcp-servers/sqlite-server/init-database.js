#!/usr/bin/env node

/**
 * Database Initialization Script for OrdnungsHub SQLite MCP Server
 */

import Database from 'better-sqlite3';
import { readFileSync, existsSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Configuration
const DB_PATH = process.env.ORDNUNGSHUB_DB_PATH || join(__dirname, '../../../data/ordnungshub.db');
const SCHEMA_PATH = join(__dirname, 'schema.sql');

console.log('🚀 Initializing OrdnungsHub Database...');
console.log(`📍 Database Path: ${DB_PATH}`);

// Ensure data directory exists
const dataDir = dirname(DB_PATH);
if (!existsSync(dataDir)) {
    mkdirSync(dataDir, { recursive: true });
    console.log(`📁 Created data directory: ${dataDir}`);
}

try {
    // Initialize database
    const db = new Database(DB_PATH);
    
    // Set SQLite optimizations
    db.pragma('journal_mode = WAL');
    db.pragma('synchronous = NORMAL');
    db.pragma('cache_size = 1000000');
    db.pragma('foreign_keys = ON');
    db.pragma('temp_store = MEMORY');
    
    console.log('⚙️  SQLite optimizations applied');
    
    // Load and execute schema
    if (existsSync(SCHEMA_PATH)) {
        const schema = readFileSync(SCHEMA_PATH, 'utf8');
        db.exec(schema);
        console.log('📊 Database schema created successfully');
    } else {
        console.error('❌ Schema file not found:', SCHEMA_PATH);
        process.exit(1);
    }
    
    // Insert sample data for testing
    console.log('📝 Inserting sample data...');
    
    const sampleData = {
        workspaces: [
            {
                name: 'AI Development',
                description: 'Machine learning and AI projects',
                path: '/projects/ai',
                color: '#8b5cf6'
            },
            {
                name: 'Documentation',
                description: 'Project documentation and guides',
                path: '/docs',
                color: '#10b981'
            }
        ],
        files: [
            {
                workspace_id: 1,
                filename: 'neural_network.py',
                file_path: '/projects/ai/neural_network.py',
                file_type: 'code',
                file_size: 15840,
                category: 'ai_ml',
                ai_category: 'machine_learning',
                ai_confidence: 0.95,
                tags: JSON.stringify(['python', 'ml', 'neural-network']),
                content_preview: 'import tensorflow as tf\nimport numpy as np\n\nclass NeuralNetwork:',
                content_hash: 'sha256:abc123...',
                similarity_hash: '1010110101'
            },
            {
                workspace_id: 2,
                filename: 'README.md',
                file_path: '/docs/README.md',
                file_type: 'document',
                file_size: 3240,
                category: 'documentation',
                ai_category: 'documentation',
                ai_confidence: 0.88,
                tags: JSON.stringify(['documentation', 'readme', 'guide']),
                content_preview: '# OrdnungsHub\n\nAI-powered file organization system...',
                content_hash: 'sha256:def456...',
                similarity_hash: '0101101010'
            }
        ],
        tasks: [
            {
                workspace_id: 1,
                title: 'Implement CNN model',
                description: 'Create convolutional neural network for image classification',
                status: 'in_progress',
                priority: 'high',
                category: 'development',
                ai_suggestions: JSON.stringify([
                    'Use transfer learning with pre-trained models',
                    'Implement data augmentation',
                    'Add proper validation split'
                ])
            },
            {
                workspace_id: 2,
                title: 'Update documentation',
                description: 'Update API documentation with new endpoints',
                status: 'pending',
                priority: 'medium',
                category: 'documentation'
            }
        ]
    };
    
    // Insert workspaces
    const insertWorkspace = db.prepare(`
        INSERT INTO workspaces (name, description, path, color) 
        VALUES (?, ?, ?, ?)
    `);
    
    for (const workspace of sampleData.workspaces) {
        insertWorkspace.run(workspace.name, workspace.description, workspace.path, workspace.color);
    }
    
    // Insert files
    const insertFile = db.prepare(`
        INSERT INTO file_metadata (
            workspace_id, filename, file_path, file_type, file_size, 
            category, ai_category, ai_confidence, tags, content_preview, 
            content_hash, similarity_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    
    for (const file of sampleData.files) {
        insertFile.run(
            file.workspace_id, file.filename, file.file_path, file.file_type,
            file.file_size, file.category, file.ai_category, file.ai_confidence,
            file.tags, file.content_preview, file.content_hash, file.similarity_hash
        );
    }
    
    // Insert tasks
    const insertTask = db.prepare(`
        INSERT INTO tasks (workspace_id, title, description, status, priority, category, ai_suggestions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
    
    for (const task of sampleData.tasks) {
        insertTask.run(
            task.workspace_id, task.title, task.description, task.status,
            task.priority, task.category, task.ai_suggestions || null
        );
    }
    
    // Insert some AI analysis records
    const insertAnalysis = db.prepare(`
        INSERT INTO ai_analysis (entity_type, entity_id, analysis_type, result_data, confidence_score, model_used)
        VALUES (?, ?, ?, ?, ?, ?)
    `);
    
    insertAnalysis.run('file', 1, 'categorization', JSON.stringify({category: 'ai_ml', subcategory: 'neural_networks'}), 0.95, 'local_ai_service');
    insertAnalysis.run('file', 2, 'categorization', JSON.stringify({category: 'documentation', subcategory: 'readme'}), 0.88, 'local_ai_service');
    
    // Verify installation
    const workspaceCount = db.prepare('SELECT COUNT(*) as count FROM workspaces').get();
    const fileCount = db.prepare('SELECT COUNT(*) as count FROM file_metadata').get();
    const taskCount = db.prepare('SELECT COUNT(*) as count FROM tasks').get();
    
    console.log('✅ Database initialized successfully!');
    console.log(`📊 Statistics:`);
    console.log(`   - Workspaces: ${workspaceCount.count}`);
    console.log(`   - Files: ${fileCount.count}`);
    console.log(`   - Tasks: ${taskCount.count}`);
    
    // Test a query
    console.log('\n🧪 Testing database queries...');
    
    const testQuery = db.prepare(`
        SELECT w.name as workspace, COUNT(f.id) as file_count
        FROM workspaces w
        LEFT JOIN file_metadata f ON w.id = f.workspace_id
        GROUP BY w.id, w.name
    `).all();
    
    console.log('📈 Workspace file counts:');
    testQuery.forEach(row => {
        console.log(`   - ${row.workspace}: ${row.file_count} files`);
    });
    
    // Close database
    db.close();
    
    console.log('\n🎉 Database initialization complete!');
    console.log(`🔗 MCP Server can now connect to: ${DB_PATH}`);
    
} catch (error) {
    console.error('❌ Database initialization failed:', error);
    process.exit(1);
}