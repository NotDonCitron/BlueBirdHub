#!/usr/bin/env node

/**
 * BlueBirdHub Cursor Helper System
 * Automates feature preparation and generates Claude prompts
 */

const fs = require('fs');
const path = require('path');

class CursorHelper {
    constructor() {
        this.projectRoot = process.cwd();
        this.features = {
            'progress': {
                name: '📊 Progress Visualization',
                searchTerms: ['progress', 'chart', 'stats', 'dashboard', 'visualization'],
                relatedFiles: [
                    'src/frontend/react/components/TaskManager/',
                    'src/frontend/react/components/Dashboard/',
                    'src/frontend/react/lib/',
                    'ultra_simple_backend.py'
                ],
                dependencies: ['recharts', 'chart.js', 'd3'],
                difficulty: 'Easy'
            },
            'search': {
                name: '🔍 Advanced Search',
                searchTerms: ['search', 'filter', 'query', 'find', 'ai'],
                relatedFiles: [
                    'src/frontend/react/lib/agentApi.ts',
                    'src/frontend/react/components/TaskManager/',
                    'ultra_simple_backend.py'
                ],
                dependencies: ['fuse.js', 'elasticsearch'],
                difficulty: 'Medium'
            },
            'calendar': {
                name: '📅 Calendar Sync',
                searchTerms: ['calendar', 'schedule', 'date', 'time', 'sync'],
                relatedFiles: [
                    'src/frontend/react/components/TaskManager/',
                    'src/frontend/react/lib/',
                    'ultra_simple_backend.py'
                ],
                dependencies: ['google-calendar-api', 'outlook-api'],
                difficulty: 'Medium'
            },
            'collaboration': {
                name: '💬 Real-Time Collaboration',
                searchTerms: ['websocket', 'socket', 'real-time', 'collaboration', 'share'],
                relatedFiles: [
                    'src/frontend/react/components/TaskManager/',
                    'src/frontend/react/lib/',
                    'ultra_simple_backend.py'
                ],
                dependencies: ['socket.io', 'ws'],
                difficulty: 'Complex'
            },
            'mobile': {
                name: '📱 Mobile Integration',
                searchTerms: ['mobile', 'responsive', 'voice', 'pwa', 'offline'],
                relatedFiles: [
                    'src/frontend/react/',
                    'package.json',
                    'vite.config.js'
                ],
                dependencies: ['workbox', 'speech-recognition'],
                difficulty: 'Most Complex'
            }
        };
    }

    // Scan codebase for existing patterns
    scanForPatterns(searchTerms) {
        const results = [];
        const extensions = ['.js', '.jsx', '.ts', '.tsx', '.py', '.css'];
        
        const scanDir = (dir) => {
            if (!fs.existsSync(dir)) return;
            
            let items;
            try {
                items = fs.readdirSync(dir);
            } catch (err) {
                return; // Skip inaccessible directories
            }
            
            items.forEach(item => {
                const fullPath = path.join(dir, item);
                let stat;
                try {
                    stat = fs.statSync(fullPath);
                } catch (err) {
                    return; // Skip inaccessible files
                }
                
                if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules' && item !== 'test_env') {
                    scanDir(fullPath);
                } else if (stat.isFile() && extensions.includes(path.extname(item))) {
                    try {
                        const content = fs.readFileSync(fullPath, 'utf8');
                        const matches = searchTerms.filter(term => 
                            content.toLowerCase().includes(term.toLowerCase())
                        );
                        if (matches.length > 0) {
                            results.push({
                                file: fullPath.replace(this.projectRoot, '').replace(/\\/g, '/'),
                                matches: matches,
                                lines: this.getMatchingLines(content, matches)
                            });
                        }
                    } catch (err) {
                        // Skip binary files
                    }
                }
            });
        };
        
        scanDir(this.projectRoot);
        return results;
    }

    getMatchingLines(content, searchTerms) {
        const lines = content.split('\n');
        const matchingLines = [];
        
        lines.forEach((line, index) => {
            const hasMatch = searchTerms.some(term => 
                line.toLowerCase().includes(term.toLowerCase())
            );
            if (hasMatch) {
                matchingLines.push({
                    number: index + 1,
                    content: line.trim()
                });
            }
        });
        
        return matchingLines.slice(0, 5); // Limit to 5 lines
    }

    // Generate file structure for Claude context
    generateFileStructure(relatedPaths) {
        const structure = {};
        
        relatedPaths.forEach(relPath => {
            const fullPath = path.join(this.projectRoot, relPath);
            if (fs.existsSync(fullPath)) {
                const stat = fs.statSync(fullPath);
                if (stat.isDirectory()) {
                    structure[relPath] = this.getDirectoryStructure(fullPath);
                } else {
                    structure[relPath] = 'FILE';
                }
            }
        });
        
        return structure;
    }

    getDirectoryStructure(dir, depth = 0) {
        if (depth > 2) return '...'; // Limit depth
        
        const items = [];
        try {
            fs.readdirSync(dir).forEach(item => {
                const fullPath = path.join(dir, item);
                const stat = fs.statSync(fullPath);
                
                if (stat.isDirectory() && !item.startsWith('.')) {
                    items.push(`${item}/`);
                } else if (['.js', '.jsx', '.ts', '.tsx', '.py', '.css'].includes(path.extname(item))) {
                    items.push(item);
                }
            });
        } catch (err) {
            return 'INACCESSIBLE';
        }
        
        return items.slice(0, 10); // Limit items
    }

    // Generate comprehensive preparation report
    generatePreparationReport(featureKey) {
        const feature = this.features[featureKey];
        if (!feature) {
            console.log('❌ Unknown feature. Available:', Object.keys(this.features).join(', '));
            return;
        }

        console.log(`\n🔍 PREPARING: ${feature.name}`);
        console.log(`📋 Difficulty: ${feature.difficulty}`);
        console.log(`🔍 Scanning codebase...`);

        // Scan for existing patterns
        const patterns = this.scanForPatterns(feature.searchTerms);
        
        // Get file structure
        const structure = this.generateFileStructure(feature.relatedFiles);
        
        return {
            feature,
            patterns,
            structure,
            prompt: this.generateClaudePrompt(feature, patterns, structure)
        };
    }

    // Generate ready-to-use Claude prompt
    generateClaudePrompt(feature, patterns, structure) {
        return `🚀 **IMPLEMENT: ${feature.name}**

**CONTEXT PREPARED BY CURSOR HELPER:**

**📁 Relevant Files Found:**
${Object.keys(structure).map(path => `- ${path}`).join('\n')}

**🔍 Existing Patterns in Codebase:**
${patterns.length > 0 ? patterns.map(p => 
    `- ${p.file}: Found "${p.matches.join(', ')}" patterns`
).join('\n') : '- No existing patterns found (clean slate!)'}

**📋 Suggested Dependencies:**
${feature.dependencies.map(dep => `- ${dep}`).join('\n')}

**🎯 YOUR TASK:**
Implement ${feature.name} feature with:
1. Full integration with existing codebase structure
2. Follow established patterns found above
3. Add comprehensive error handling and testing
4. Ensure mobile-responsive design
5. Include TypeScript types and proper documentation

**⚡ READY TO CODE:**
Please implement this feature now. I've prepared all the context you need!

**Files to focus on:**
${feature.relatedFiles.map(path => `- ${path}`).join('\n')}

Start implementation! 🎉`;
    }

    // Generate step-by-step Cursor workflow
    generateCursorWorkflow(featureKey) {
        const feature = this.features[featureKey];
        
        return `
📋 **CURSOR WORKFLOW FOR: ${feature.name}**

**STEP 1: Open Required Files**
${feature.relatedFiles.map(file => `- Open: ${file}`).join('\n')}

**STEP 2: Search Existing Code**
Use Ctrl+Shift+F to search for:
${feature.searchTerms.map(term => `- "${term}"`).join('\n')}

**STEP 3: Generate Basic Structure** 
Use Ctrl+K to generate:
- Component boilerplate
- API endpoint structure
- Type definitions

**STEP 4: Copy This Prompt to Claude:**
[Copy the generated Claude prompt above]

**STEP 5: Let Claude Implement**
Paste the prompt and let Claude do the heavy lifting!

**STEP 6: Use Cursor for Final Polish**
- Fix syntax issues with Tab autocomplete
- Adjust styling with Ctrl+K
- Test integration points

Ready! 🚀
`;
    }

    // Main method to prepare any feature
    prepareFeature(featureKey) {
        console.clear();
        console.log('🤖 BlueBirdHub Cursor Helper System');
        console.log('=====================================\n');

        const report = this.generatePreparationReport(featureKey);
        if (!report) return;

        // Save detailed report
        const reportPath = `reports/feature-prep-${featureKey}.md`;
        this.ensureDirectoryExists('reports');
        
        const fullReport = `# ${report.feature.name} - Preparation Report

${report.prompt}

${this.generateCursorWorkflow(featureKey)}

## Detailed Scan Results

### Found Patterns:
${JSON.stringify(report.patterns, null, 2)}

### File Structure:
${JSON.stringify(report.structure, null, 2)}

Generated: ${new Date().toISOString()}
`;

        fs.writeFileSync(reportPath, fullReport);
        
        console.log('✅ PREPARATION COMPLETE!\n');
        console.log('📁 Full report saved to:', reportPath);
        console.log('\n🎯 COPY THIS PROMPT TO CLAUDE:\n');
        console.log('='.repeat(50));
        console.log(report.prompt);
        console.log('='.repeat(50));
        console.log('\n📋 Cursor workflow saved to report file.');
        console.log('\n🚀 Ready to implement!');
    }

    ensureDirectoryExists(dir) {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
    }

    // Show available features
    showFeatures() {
        console.clear();
        console.log('🤖 BlueBirdHub Features Available:\n');
        
        Object.entries(this.features).forEach(([key, feature]) => {
            console.log(`${key.padEnd(12)} | ${feature.name}`);
            console.log(`${' '.repeat(12)} | Difficulty: ${feature.difficulty}`);
            console.log(`${' '.repeat(12)} | Dependencies: ${feature.dependencies.join(', ')}`);
            console.log('');
        });
        
        console.log('Usage: node scripts/cursor-helper.js <feature-key>');
        console.log('Example: node scripts/cursor-helper.js progress');
    }
}

// CLI Interface
const args = process.argv.slice(2);
const helper = new CursorHelper();

if (args.length === 0) {
    helper.showFeatures();
} else {
    helper.prepareFeature(args[0]);
} 