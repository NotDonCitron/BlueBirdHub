#!/usr/bin/env node

/**
 * SQLite MCP Server for OrdnungsHub
 * Provides database integration capabilities for AI-powered organization
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  CallToolResult,
  TextContent,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import Database from 'better-sqlite3';
import { readFileSync, existsSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Database configuration
const DB_PATH = process.env.ORDNUNGSHUB_DB_PATH || join(__dirname, '../../../data/ordnungshub.db');
const SCHEMA_PATH = join(__dirname, 'schema.sql');

class SqliteMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'sqlite-ordnungshub',
        version: '1.0.0',
        description: 'SQLite MCP server for OrdnungsHub database operations',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.db = null;
    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  initializeDatabase() {
    try {
      // Initialize SQLite database
      this.db = new Database(DB_PATH);
      this.db.pragma('journal_mode = WAL');
      this.db.pragma('foreign_keys = ON');
      
      // Create schema if not exists
      if (existsSync(SCHEMA_PATH)) {
        const schema = readFileSync(SCHEMA_PATH, 'utf8');
        this.db.exec(schema);
      }

      console.error('📊 SQLite database initialized:', DB_PATH);
      return true;
    } catch (error) {
      console.error('❌ Database initialization failed:', error);
      return false;
    }
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'query_database',
            description: 'Execute SELECT queries on the OrdnungsHub database',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'SELECT SQL query to execute'
                },
                params: {
                  type: 'array',
                  description: 'Query parameters for prepared statements',
                  items: { type: 'string' }
                }
              },
              required: ['query']
            }
          },
          {
            name: 'execute_database',
            description: 'Execute INSERT, UPDATE, DELETE operations on the database',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'SQL query to execute (INSERT, UPDATE, DELETE)'
                },
                params: {
                  type: 'array',
                  description: 'Query parameters for prepared statements',
                  items: { type: 'string' }
                }
              },
              required: ['query']
            }
          },
          {
            name: 'get_schema',
            description: 'Get database schema information',
            inputSchema: {
              type: 'object',
              properties: {
                table: {
                  type: 'string',
                  description: 'Specific table name (optional)'
                }
              }
            }
          },
          {
            name: 'backup_database',
            description: 'Create a backup of the database',
            inputSchema: {
              type: 'object',
              properties: {
                backup_path: {
                  type: 'string',
                  description: 'Path for backup file'
                }
              }
            }
          },
          {
            name: 'analyze_file_data',
            description: 'Analyze file organization patterns from database',
            inputSchema: {
              type: 'object',
              properties: {
                workspace_id: {
                  type: 'string',
                  description: 'Workspace ID to analyze (optional)'
                },
                category: {
                  type: 'string',
                  description: 'File category to analyze (optional)'
                }
              }
            }
          },
          {
            name: 'get_ai_insights',
            description: 'Generate AI insights from database patterns',
            inputSchema: {
              type: 'object',
              properties: {
                insight_type: {
                  type: 'string',
                  enum: ['file_patterns', 'user_behavior', 'workspace_efficiency', 'category_distribution'],
                  description: 'Type of insight to generate'
                },
                time_range: {
                  type: 'string',
                  description: 'Time range for analysis (e.g., "7 days", "30 days")'
                }
              },
              required: ['insight_type']
            }
          }
        ]
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'query_database':
            return await this.handleQueryDatabase(args);
          case 'execute_database':
            return await this.handleExecuteDatabase(args);
          case 'get_schema':
            return await this.handleGetSchema(args);
          case 'backup_database':
            return await this.handleBackupDatabase(args);
          case 'analyze_file_data':
            return await this.handleAnalyzeFileData(args);
          case 'get_ai_insights':
            return await this.handleGetAIInsights(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error executing ${name}: ${error.message}`
            }
          ],
          isError: true
        };
      }
    });
  }

  setupErrorHandling() {
    this.server.onerror = (error) => {
      console.error('MCP Server Error:', error);
    };

    process.on('SIGINT', async () => {
      if (this.db) {
        this.db.close();
      }
      await this.server.close();
      process.exit(0);
    });
  }

  async handleQueryDatabase(args) {
    const { query, params = [] } = args;

    // Security: Only allow SELECT queries
    if (!query.trim().toLowerCase().startsWith('select')) {
      throw new Error('Only SELECT queries are allowed for query_database');
    }

    try {
      const stmt = this.db.prepare(query);
      const results = stmt.all(...params);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Query execution failed: ${error.message}`);
    }
  }

  async handleExecuteDatabase(args) {
    const { query, params = [] } = args;

    // Security: Prevent SELECT queries and dangerous operations
    const queryLower = query.trim().toLowerCase();
    if (queryLower.startsWith('select')) {
      throw new Error('Use query_database for SELECT operations');
    }
    if (queryLower.includes('drop table') || queryLower.includes('drop database')) {
      throw new Error('DROP operations are not allowed');
    }

    try {
      const stmt = this.db.prepare(query);
      const result = stmt.run(...params);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              changes: result.changes,
              lastInsertRowid: result.lastInsertRowid,
              success: true
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Execute operation failed: ${error.message}`);
    }
  }

  async handleGetSchema(args) {
    const { table } = args;

    try {
      let query, results;

      if (table) {
        // Get schema for specific table
        query = `PRAGMA table_info(${table})`;
        results = this.db.prepare(query).all();
      } else {
        // Get all tables
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name";
        const tables = this.db.prepare(query).all();

        results = {
          tables: tables.map(t => t.name),
          schema: {}
        };

        // Get schema for each table
        for (const table of tables) {
          const tableInfo = this.db.prepare(`PRAGMA table_info(${table.name})`).all();
          results.schema[table.name] = tableInfo;
        }
      }

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Schema retrieval failed: ${error.message}`);
    }
  }

  async handleBackupDatabase(args) {
    const { backup_path } = args;

    try {
      const backup = new Database(backup_path);
      await this.db.backup(backup);
      backup.close();

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              backup_path: backup_path,
              timestamp: new Date().toISOString()
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Backup failed: ${error.message}`);
    }
  }

  async handleAnalyzeFileData(args) {
    const { workspace_id, category } = args;

    try {
      let baseQuery = `
        SELECT 
          f.category,
          f.file_type,
          COUNT(*) as file_count,
          AVG(f.file_size) as avg_size,
          MIN(f.created_at) as earliest_file,
          MAX(f.created_at) as latest_file
        FROM file_metadata f
      `;

      const conditions = [];
      const params = [];

      if (workspace_id) {
        conditions.push('f.workspace_id = ?');
        params.push(workspace_id);
      }

      if (category) {
        conditions.push('f.category = ?');
        params.push(category);
      }

      if (conditions.length > 0) {
        baseQuery += ' WHERE ' + conditions.join(' AND ');
      }

      baseQuery += ' GROUP BY f.category, f.file_type ORDER BY file_count DESC';

      const results = this.db.prepare(baseQuery).all(...params);

      // Additional insights
      const totalFiles = this.db.prepare(`
        SELECT COUNT(*) as total FROM file_metadata 
        ${conditions.length > 0 ? 'WHERE ' + conditions.join(' AND ') : ''}
      `).get(...params);

      const categoryDistribution = this.db.prepare(`
        SELECT category, COUNT(*) as count, 
               ROUND(COUNT(*) * 100.0 / ?, 2) as percentage
        FROM file_metadata 
        ${conditions.length > 0 ? 'WHERE ' + conditions.join(' AND ') : ''}
        GROUP BY category 
        ORDER BY count DESC
      `).all(totalFiles.total, ...params);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              analysis: results,
              total_files: totalFiles.total,
              category_distribution: categoryDistribution,
              analyzed_at: new Date().toISOString()
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`File data analysis failed: ${error.message}`);
    }
  }

  async handleGetAIInsights(args) {
    const { insight_type, time_range = '30 days' } = args;

    try {
      let insights = {};

      const timeCondition = time_range ? 
        `AND created_at >= datetime('now', '-${time_range}')` : '';

      switch (insight_type) {
        case 'file_patterns':
          insights = await this.getFilePatternInsights(timeCondition);
          break;
        case 'user_behavior':
          insights = await this.getUserBehaviorInsights(timeCondition);
          break;
        case 'workspace_efficiency':
          insights = await this.getWorkspaceEfficiencyInsights(timeCondition);
          break;
        case 'category_distribution':
          insights = await this.getCategoryDistributionInsights(timeCondition);
          break;
        default:
          throw new Error(`Unknown insight type: ${insight_type}`);
      }

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              insight_type,
              time_range,
              insights,
              generated_at: new Date().toISOString()
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`AI insights generation failed: ${error.message}`);
    }
  }

  async getFilePatternInsights(timeCondition) {
    const patterns = this.db.prepare(`
      SELECT 
        file_type,
        category,
        COUNT(*) as frequency,
        AVG(file_size) as avg_size,
        CASE 
          WHEN strftime('%H', created_at) BETWEEN '09' AND '17' THEN 'work_hours'
          ELSE 'off_hours'
        END as time_pattern
      FROM file_metadata 
      WHERE 1=1 ${timeCondition}
      GROUP BY file_type, category, time_pattern
      ORDER BY frequency DESC
    `).all();

    return {
      patterns,
      insights: [
        'File creation patterns analyzed',
        `Most common file type: ${patterns[0]?.file_type || 'N/A'}`,
        `Primary category: ${patterns[0]?.category || 'N/A'}`
      ]
    };
  }

  async getUserBehaviorInsights(timeCondition) {
    const behavior = this.db.prepare(`
      SELECT 
        strftime('%H', created_at) as hour,
        COUNT(*) as activity_count
      FROM file_metadata 
      WHERE 1=1 ${timeCondition}
      GROUP BY hour
      ORDER BY activity_count DESC
    `).all();

    const peakHour = behavior[0]?.hour || 'N/A';
    
    return {
      hourly_activity: behavior,
      insights: [
        `Peak activity hour: ${peakHour}:00`,
        `Total activities analyzed: ${behavior.reduce((sum, h) => sum + h.activity_count, 0)}`
      ]
    };
  }

  async getWorkspaceEfficiencyInsights(timeCondition) {
    const efficiency = this.db.prepare(`
      SELECT 
        w.name as workspace_name,
        COUNT(f.id) as file_count,
        COUNT(DISTINCT f.category) as category_diversity,
        AVG(f.file_size) as avg_file_size
      FROM workspaces w
      LEFT JOIN file_metadata f ON w.id = f.workspace_id
      WHERE 1=1 ${timeCondition}
      GROUP BY w.id, w.name
      ORDER BY file_count DESC
    `).all();

    return {
      workspace_stats: efficiency,
      insights: [
        `Most active workspace: ${efficiency[0]?.workspace_name || 'N/A'}`,
        `Average category diversity per workspace: ${(efficiency.reduce((sum, w) => sum + w.category_diversity, 0) / efficiency.length).toFixed(1)}`
      ]
    };
  }

  async getCategoryDistributionInsights(timeCondition) {
    const distribution = this.db.prepare(`
      SELECT 
        category,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM file_metadata WHERE 1=1 ${timeCondition}), 2) as percentage
      FROM file_metadata 
      WHERE 1=1 ${timeCondition}
      GROUP BY category
      ORDER BY count DESC
    `).all();

    return {
      distribution,
      insights: [
        `Most common category: ${distribution[0]?.category || 'N/A'} (${distribution[0]?.percentage || 0}%)`,
        `Total categories: ${distribution.length}`,
        'Category distribution shows organizational patterns'
      ]
    };
  }

  async start() {
    if (!this.initializeDatabase()) {
      process.exit(1);
    }

    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('🚀 SQLite MCP Server for OrdnungsHub started');
  }
}

// Start the server
const server = new SqliteMCPServer();
server.start().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});