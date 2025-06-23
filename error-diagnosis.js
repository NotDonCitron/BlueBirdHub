const axios = require('axios');
const fs = require('fs');

class ErrorDiagnosis {
    constructor() {
        this.findings = {
            timestamp: new Date().toISOString(),
            backend: {},
            frontend: {},
            api: {},
            recommendations: []
        };
    }

    async diagnoseBackendErrors() {
        console.log('🔍 Diagnosing Backend Errors');
        
        // Test OpenAPI Schema endpoint specifically
        try {
            const response = await axios.get('http://127.0.0.1:8001/openapi.json', {
                timeout: 5000,
                validateStatus: status => true // Accept all status codes
            });
            
            this.findings.backend.openapi = {
                status: response.status,
                error: response.status >= 400 ? response.data : null,
                headers: response.headers
            };
            
            console.log(`  OpenAPI Schema: ${response.status}`);
            if (response.status >= 400) {
                console.log(`  Error: ${JSON.stringify(response.data)}`);
            }
            
        } catch (error) {
            this.findings.backend.openapi = {
                error: error.message,
                code: error.code
            };
            console.log(`  OpenAPI Schema failed: ${error.message}`);
        }

        // Test Workspaces endpoint
        try {
            const response = await axios.get('http://127.0.0.1:8001/api/workspaces', {
                timeout: 5000,
                validateStatus: status => true
            });
            
            this.findings.backend.workspaces = {
                status: response.status,
                data: response.data,
                headers: response.headers
            };
            
            console.log(`  Workspaces API: ${response.status}`);
            
        } catch (error) {
            this.findings.backend.workspaces = {
                error: error.message,
                code: error.code
            };
            console.log(`  Workspaces API failed: ${error.message}`);
        }

        // Check what endpoints are actually available
        await this.discoverAvailableEndpoints();
    }

    async discoverAvailableEndpoints() {
        console.log('🕵️ Discovering Available API Endpoints');
        
        const commonEndpoints = [
            '/health',
            '/docs',
            '/api/workspaces',
            '/api/tasks',
            '/api/files',
            '/api/users',
            '/api/dashboard',
            '/api/ai',
            '/api/search'
        ];

        const available = [];
        const notFound = [];

        for (const endpoint of commonEndpoints) {
            try {
                const response = await axios.get(`http://127.0.0.1:8001${endpoint}`, {
                    timeout: 3000,
                    validateStatus: status => status < 500
                });
                
                available.push({
                    path: endpoint,
                    status: response.status,
                    method: 'GET'
                });
                
            } catch (error) {
                if (error.response && error.response.status === 404) {
                    notFound.push(endpoint);
                } else {
                    available.push({
                        path: endpoint,
                        error: error.message,
                        method: 'GET'
                    });
                }
            }
        }

        this.findings.api.available = available;
        this.findings.api.notFound = notFound;

        console.log(`  Available endpoints: ${available.length}`);
        console.log(`  Not found: ${notFound.length}`);
    }

    async analyzeFrontendHTML() {
        console.log('📄 Analyzing Frontend HTML Structure');
        
        try {
            const response = await axios.get('http://localhost:3002', { timeout: 10000 });
            const html = response.data;
            
            // Extract and analyze JavaScript errors from HTML
            const scriptMatches = html.match(/<script[^>]*>(.*?)<\/script>/gs) || [];
            const inlineScripts = scriptMatches.map(script => 
                script.replace(/<script[^>]*>|<\/script>/g, '').trim()
            ).filter(script => script.length > 0);

            // Look for common error patterns
            const errorPatterns = {
                uncaughtException: /uncaught|unhandled/i,
                reactErrors: /react.*error|error.*react/i,
                moduleErrors: /module.*not.*found|cannot.*resolve/i,
                syntaxErrors: /syntaxerror|unexpected token/i,
                networkErrors: /network.*error|fetch.*failed/i
            };

            const detectedIssues = [];
            const fullText = html.toLowerCase();

            for (const [pattern, regex] of Object.entries(errorPatterns)) {
                if (regex.test(fullText)) {
                    detectedIssues.push(pattern);
                }
            }

            this.findings.frontend = {
                htmlSize: html.length,
                scriptTags: scriptMatches.length,
                inlineScripts: inlineScripts.length,
                detectedIssues,
                hasReactRoot: html.includes('id="root"') || html.includes('id="app"'),
                hasViteClient: html.includes('vite/client') || html.includes('@vite'),
                hasErrorBoundary: html.includes('ErrorBoundary') || html.includes('error-boundary')
            };

            console.log(`  HTML size: ${html.length} chars`);
            console.log(`  Script tags: ${scriptMatches.length}`);
            console.log(`  Potential issues: ${detectedIssues.length}`);
            
        } catch (error) {
            this.findings.frontend.error = error.message;
            console.log(`  Frontend analysis failed: ${error.message}`);
        }
    }

    async testAPIAuthentication() {
        console.log('🔐 Testing API Authentication Requirements');
        
        const protectedEndpoints = [
            '/api/workspaces',
            '/api/tasks',
            '/api/files',
            '/api/users'
        ];

        for (const endpoint of protectedEndpoints) {
            try {
                // Test without auth
                const noAuthResponse = await axios.get(`http://127.0.0.1:8001${endpoint}`, {
                    timeout: 3000,
                    validateStatus: status => true
                });

                // Test with potentially required headers
                const withHeadersResponse = await axios.get(`http://127.0.0.1:8001${endpoint}`, {
                    timeout: 3000,
                    validateStatus: status => true,
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                });

                console.log(`  ${endpoint}: ${noAuthResponse.status} (no auth), ${withHeadersResponse.status} (with headers)`);
                
            } catch (error) {
                console.log(`  ${endpoint}: Error - ${error.message}`);
            }
        }
    }

    async checkDatabaseConnection() {
        console.log('🗄️ Checking Database Connection');
        
        try {
            // The health endpoint should include database status
            const response = await axios.get('http://127.0.0.1:8001/health');
            
            this.findings.database = response.data;
            
            if (response.data.database === 'operational') {
                console.log('  ✅ Database connection: OK');
            } else {
                console.log('  ❌ Database connection: Issues detected');
            }
            
        } catch (error) {
            this.findings.database = { error: error.message };
            console.log(`  ❌ Database check failed: ${error.message}`);
        }
    }

    async runNetworkDiagnostics() {
        console.log('🌐 Running Network Diagnostics');
        
        const services = [
            { name: 'Frontend', url: 'http://localhost:3002' },
            { name: 'Backend', url: 'http://127.0.0.1:8001' },
            { name: 'Debug MCP', url: 'http://localhost:3004' }
        ];

        for (const service of services) {
            const startTime = Date.now();
            
            try {
                const response = await axios.get(service.url, {
                    timeout: 5000,
                    validateStatus: status => status < 500
                });
                
                const responseTime = Date.now() - startTime;
                
                console.log(`  ${service.name}: ✅ ${response.status} (${responseTime}ms)`);
                
            } catch (error) {
                const responseTime = Date.now() - startTime;
                console.log(`  ${service.name}: ❌ ${error.message} (${responseTime}ms)`);
            }
        }
    }

    generateRecommendations() {
        console.log('🔧 Generating Recommendations');
        
        const recommendations = [];

        // Backend issues
        if (this.findings.backend.openapi?.status === 500) {
            recommendations.push({
                priority: 'HIGH',
                component: 'Backend',
                issue: 'OpenAPI schema generation failing',
                solution: 'Check FastAPI model definitions and imports for circular dependencies or invalid schemas'
            });
        }

        if (this.findings.backend.workspaces?.error) {
            recommendations.push({
                priority: 'MEDIUM',
                component: 'Backend',
                issue: 'Workspaces API endpoint unavailable',
                solution: 'Verify workspace router is properly registered in main FastAPI app'
            });
        }

        // Frontend issues
        if (this.findings.frontend.detectedIssues?.length > 0) {
            recommendations.push({
                priority: 'MEDIUM',
                component: 'Frontend',
                issue: `Potential JavaScript issues detected: ${this.findings.frontend.detectedIssues.join(', ')}`,
                solution: 'Check browser console for detailed error messages and fix JavaScript errors'
            });
        }

        if (!this.findings.frontend.hasErrorBoundary) {
            recommendations.push({
                priority: 'LOW',
                component: 'Frontend',
                issue: 'No React Error Boundary detected',
                solution: 'Implement Error Boundary components to catch and handle React errors gracefully'
            });
        }

        // Database issues
        if (this.findings.database?.database !== 'operational') {
            recommendations.push({
                priority: 'HIGH',
                component: 'Database',
                issue: 'Database connection issues',
                solution: 'Check SQLite database file permissions and connection string configuration'
            });
        }

        this.findings.recommendations = recommendations;

        console.log(`  Generated ${recommendations.length} recommendations`);
        
        recommendations.forEach((rec, i) => {
            console.log(`  ${i + 1}. [${rec.priority}] ${rec.component}: ${rec.issue}`);
        });
    }

    async saveReport() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `./logs/debug-session/error-diagnosis-${timestamp}.json`;
        
        fs.writeFileSync(filename, JSON.stringify(this.findings, null, 2));
        
        // Create readable summary
        const summaryFile = `./logs/debug-session/error-summary-${timestamp}.txt`;
        const summary = this.createReadableSummary();
        fs.writeFileSync(summaryFile, summary);

        console.log(`\n📊 Error diagnosis saved to: ${filename}`);
        console.log(`📋 Summary saved to: ${summaryFile}`);
    }

    createReadableSummary() {
        return `
OrdnungsHub Error Diagnosis Report
==================================
Timestamp: ${this.findings.timestamp}

🔍 BACKEND ANALYSIS
-------------------
OpenAPI Schema: ${this.findings.backend.openapi?.status || 'Unknown'}
${this.findings.backend.openapi?.error ? `Error: ${JSON.stringify(this.findings.backend.openapi.error)}` : ''}

Workspaces API: ${this.findings.backend.workspaces?.status || 'Error'}
${this.findings.backend.workspaces?.error ? `Error: ${this.findings.backend.workspaces.error}` : ''}

📄 FRONTEND ANALYSIS
--------------------
HTML Size: ${this.findings.frontend.htmlSize || 'Unknown'} characters
React Root: ${this.findings.frontend.hasReactRoot ? 'Found' : 'Missing'}
Vite Client: ${this.findings.frontend.hasViteClient ? 'Present' : 'Missing'}
Error Boundary: ${this.findings.frontend.hasErrorBoundary ? 'Present' : 'Missing'}
Detected Issues: ${this.findings.frontend.detectedIssues?.length || 0}

🗄️ DATABASE STATUS
------------------
Status: ${this.findings.database?.database || 'Unknown'}
Backend: ${this.findings.database?.backend || 'Unknown'}

📡 API ENDPOINTS
----------------
Available: ${this.findings.api.available?.length || 0}
Not Found: ${this.findings.api.notFound?.length || 0}

${this.findings.api.available?.length > 0 ? `
Working Endpoints:
${this.findings.api.available.map(ep => `• ${ep.path} (${ep.status})`).join('\n')}
` : ''}

🔧 RECOMMENDATIONS
------------------
${this.findings.recommendations.map((rec, i) => 
    `${i + 1}. [${rec.priority}] ${rec.component}\n   Issue: ${rec.issue}\n   Solution: ${rec.solution}`
).join('\n\n')}

End of Diagnosis
================
        `.trim();
    }
}

async function runErrorDiagnosis() {
    const diagnosis = new ErrorDiagnosis();
    
    console.log('🚀 Starting Comprehensive Error Diagnosis');
    console.log('==========================================');
    
    try {
        await diagnosis.diagnoseBackendErrors();
        await diagnosis.analyzeFrontendHTML();
        await diagnosis.testAPIAuthentication();
        await diagnosis.checkDatabaseConnection();
        await diagnosis.runNetworkDiagnostics();
        
        diagnosis.generateRecommendations();
        await diagnosis.saveReport();
        
        console.log('\n🎉 Error Diagnosis Completed!');
        return diagnosis.findings;
        
    } catch (error) {
        console.error('💥 Error diagnosis failed:', error.message);
        throw error;
    }
}

module.exports = { ErrorDiagnosis, runErrorDiagnosis };

if (require.main === module) {
    runErrorDiagnosis()
        .then(() => process.exit(0))
        .catch(error => {
            console.error('Diagnosis failed:', error);
            process.exit(1);
        });
}