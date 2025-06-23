const axios = require('axios');
const fs = require('fs');

class DirectDebugger {
    constructor() {
        this.results = {
            timestamp: new Date().toISOString(),
            tests: [],
            summary: {}
        };
        this.baseUrls = {
            frontend: 'http://localhost:3002',
            backend: 'http://127.0.0.1:8001',
            debug: 'http://localhost:3004'
        };
    }

    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const symbols = { info: '📋', success: '✅', error: '❌', warning: '⚠️' };
        console.log(`${symbols[type]} [${timestamp}] ${message}`);
    }

    async testService(name, url, expectedStatus = 200) {
        this.log(`Testing ${name} (${url})`);
        
        const startTime = Date.now();
        
        try {
            const response = await axios.get(url, { 
                timeout: 10000,
                validateStatus: status => status < 500 // Accept any status < 500
            });
            
            const responseTime = Date.now() - startTime;
            const result = {
                name,
                url,
                success: true,
                status: response.status,
                responseTime: `${responseTime}ms`,
                headers: response.headers,
                contentLength: response.data?.length || 0
            };
            
            this.results.tests.push(result);
            this.log(`${name}: ${response.status} (${responseTime}ms)`, 'success');
            
            return result;
            
        } catch (error) {
            const responseTime = Date.now() - startTime;
            const result = {
                name,
                url,
                success: false,
                error: error.message,
                responseTime: `${responseTime}ms`,
                code: error.code
            };
            
            this.results.tests.push(result);
            this.log(`${name}: Failed - ${error.message}`, 'error');
            
            return result;
        }
    }

    async testAPIEndpoints() {
        this.log('🔍 Testing API Endpoints', 'info');
        
        const endpoints = [
            { name: 'Backend Health', url: `${this.baseUrls.backend}/health` },
            { name: 'API Documentation', url: `${this.baseUrls.backend}/docs` },
            { name: 'OpenAPI Schema', url: `${this.baseUrls.backend}/openapi.json` },
            { name: 'API Workspaces', url: `${this.baseUrls.backend}/api/workspaces` },
            { name: 'API Tasks', url: `${this.baseUrls.backend}/api/tasks` },
            { name: 'API Files', url: `${this.baseUrls.backend}/api/files` }
        ];

        const results = [];
        
        for (const endpoint of endpoints) {
            const result = await this.testService(endpoint.name, endpoint.url);
            results.push(result);
        }

        return results;
    }

    async testFrontendPages() {
        this.log('🌐 Testing Frontend Pages', 'info');
        
        const pages = [
            { name: 'Frontend Root', url: this.baseUrls.frontend },
            { name: 'Frontend Assets', url: `${this.baseUrls.frontend}/assets` }
        ];

        const results = [];
        
        for (const page of pages) {
            const result = await this.testService(page.name, page.url);
            results.push(result);
        }

        return results;
    }

    async testDebugServer() {
        this.log('🤖 Testing MCP Debug Server', 'info');
        
        const debugEndpoints = [
            { name: 'Debug Health Check', url: `${this.baseUrls.debug}/health-check` },
        ];

        const results = [];
        
        for (const endpoint of debugEndpoints) {
            const result = await this.testService(endpoint.name, endpoint.url);
            results.push(result);
        }

        // Test performance audit endpoint
        try {
            this.log('Testing Performance Audit endpoint');
            const perfResponse = await axios.post(`${this.baseUrls.debug}/performance-audit`, {
                url: this.baseUrls.frontend
            }, { timeout: 30000 });
            
            this.log('Performance audit completed (limited data due to browser constraints)', 'warning');
            
        } catch (error) {
            this.log(`Performance audit failed: ${error.message}`, 'error');
        }

        return results;
    }

    async checkHTMLContent() {
        this.log('📄 Analyzing Frontend Content', 'info');
        
        try {
            const response = await axios.get(this.baseUrls.frontend, { timeout: 10000 });
            const html = response.data;
            
            // Basic HTML analysis
            const analysis = {
                hasReactRoot: html.includes('id="root"') || html.includes('id="app"'),
                hasTitle: /<title>.*<\/title>/.test(html),
                hasMetaCharset: html.includes('charset='),
                hasViewport: html.includes('viewport'),
                scriptTags: (html.match(/<script/g) || []).length,
                styleTags: (html.match(/<style/g) || []).length,
                linkTags: (html.match(/<link/g) || []).length,
                size: html.length
            };

            this.log(`Frontend HTML: ${analysis.size} chars, ${analysis.scriptTags} scripts, ${analysis.linkTags} links`);
            
            if (analysis.hasReactRoot) {
                this.log('React root element found', 'success');
            } else {
                this.log('React root element not found', 'warning');
            }

            this.results.htmlAnalysis = analysis;
            
        } catch (error) {
            this.log(`HTML analysis failed: ${error.message}`, 'error');
        }
    }

    async loadTestAPIs() {
        this.log('🚀 Running Load Test on APIs', 'info');
        
        const requests = [];
        const startTime = Date.now();
        
        // Create 10 concurrent requests
        for (let i = 0; i < 10; i++) {
            requests.push(
                axios.get(`${this.baseUrls.backend}/health`, { timeout: 5000 })
                    .then(response => ({ success: true, status: response.status }))
                    .catch(error => ({ success: false, error: error.message }))
            );
        }

        try {
            const results = await Promise.all(requests);
            const endTime = Date.now();
            const totalTime = endTime - startTime;
            
            const successful = results.filter(r => r.success).length;
            const failed = results.length - successful;
            
            this.log(`Load test: ${successful}/${results.length} successful in ${totalTime}ms`, 
                    failed === 0 ? 'success' : 'warning');
            
            this.results.loadTest = {
                totalRequests: results.length,
                successful,
                failed,
                totalTime: `${totalTime}ms`,
                avgTime: `${Math.round(totalTime / results.length)}ms`
            };
            
        } catch (error) {
            this.log(`Load test failed: ${error.message}`, 'error');
        }
    }

    generateSummary() {
        const successful = this.results.tests.filter(t => t.success).length;
        const failed = this.results.tests.length - successful;
        
        this.results.summary = {
            totalTests: this.results.tests.length,
            successful,
            failed,
            successRate: `${Math.round((successful / this.results.tests.length) * 100)}%`,
            avgResponseTime: this.calculateAverageResponseTime()
        };

        this.log(`\n📊 Test Summary: ${successful}/${this.results.tests.length} passed (${this.results.summary.successRate})`, 
                failed === 0 ? 'success' : 'warning');
    }

    calculateAverageResponseTime() {
        const responseTimes = this.results.tests
            .filter(t => t.success && t.responseTime)
            .map(t => parseInt(t.responseTime.replace('ms', '')));
        
        if (responseTimes.length === 0) return 'N/A';
        
        const avg = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
        return `${Math.round(avg)}ms`;
    }

    async saveResults() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `./logs/debug-session/direct-debug-${timestamp}.json`;
        
        // Ensure directory exists
        const dir = './logs/debug-session';
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }

        fs.writeFileSync(filename, JSON.stringify(this.results, null, 2));
        
        // Create readable summary
        const summaryFile = `./logs/debug-session/debug-summary-${timestamp}.txt`;
        const summary = this.createReadableSummary();
        fs.writeFileSync(summaryFile, summary);

        this.log(`Results saved to: ${filename}`, 'success');
        this.log(`Summary saved to: ${summaryFile}`, 'success');
    }

    createReadableSummary() {
        return `
OrdnungsHub Direct Debug Report
===============================
Timestamp: ${this.results.timestamp}

🎯 OVERALL SUMMARY
------------------
Total Tests: ${this.results.summary.totalTests}
Successful: ${this.results.summary.successful}
Failed: ${this.results.summary.failed}
Success Rate: ${this.results.summary.successRate}
Average Response Time: ${this.results.summary.avgResponseTime}

📋 DETAILED TEST RESULTS
------------------------
${this.results.tests.map(test => 
    `${test.success ? '✅' : '❌'} ${test.name}: ${test.success ? test.status + ' (' + test.responseTime + ')' : test.error}`
).join('\n')}

${this.results.htmlAnalysis ? `
📄 FRONTEND ANALYSIS
-------------------
HTML Size: ${this.results.htmlAnalysis.size} characters
React Root: ${this.results.htmlAnalysis.hasReactRoot ? 'Found' : 'Missing'}
Script Tags: ${this.results.htmlAnalysis.scriptTags}
Link Tags: ${this.results.htmlAnalysis.linkTags}
` : ''}

${this.results.loadTest ? `
🚀 LOAD TEST RESULTS
-------------------
Total Requests: ${this.results.loadTest.totalRequests}
Successful: ${this.results.loadTest.successful}
Failed: ${this.results.loadTest.failed}
Total Time: ${this.results.loadTest.totalTime}
Average Time: ${this.results.loadTest.avgTime}
` : ''}

🔧 RECOMMENDATIONS
------------------
${this.generateRecommendations()}

End of Report
=============
        `.trim();
    }

    generateRecommendations() {
        const recommendations = [];
        
        if (this.results.summary.failed > 0) {
            recommendations.push('• Fix failed API endpoints for better reliability');
        }
        
        if (this.results.htmlAnalysis && !this.results.htmlAnalysis.hasReactRoot) {
            recommendations.push('• Ensure React root element is present in HTML');
        }
        
        const avgTime = parseInt(this.results.summary.avgResponseTime?.replace('ms', '') || '0');
        if (avgTime > 1000) {
            recommendations.push('• Optimize API response times (currently averaging ' + this.results.summary.avgResponseTime + ')');
        }
        
        if (this.results.loadTest && this.results.loadTest.failed > 0) {
            recommendations.push('• Investigate load handling - some concurrent requests failed');
        }
        
        if (recommendations.length === 0) {
            recommendations.push('• All systems appear to be functioning well!');
            recommendations.push('• Consider implementing additional monitoring for production');
        }
        
        return recommendations.join('\n');
    }
}

async function runDirectDebug() {
    const debugSession = new DirectDebugger();
    
    console.log('🚀 Starting Direct Debug Session for OrdnungsHub');
    console.log('================================================');
    
    try {
        // Test all components
        await debugSession.testAPIEndpoints();
        await debugSession.testFrontendPages();
        await debugSession.testDebugServer();
        await debugSession.checkHTMLContent();
        await debugSession.loadTestAPIs();
        
        // Generate summary
        debugSession.generateSummary();
        
        // Save results
        await debugSession.saveResults();
        
        console.log('\n🎉 Direct Debug Session Completed Successfully!');
        return debugSession.results;
        
    } catch (error) {
        console.error('💥 Debug session failed:', error.message);
        throw error;
    }
}

// Export for use
module.exports = { DirectDebugger, runDirectDebug };

// Run if called directly
if (require.main === module) {
    runDirectDebug()
        .then(() => process.exit(0))
        .catch(error => {
            console.error('Debug failed:', error);
            process.exit(1);
        });
}