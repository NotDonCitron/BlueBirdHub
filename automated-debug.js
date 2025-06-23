const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class AutomatedDebugger {
    constructor() {
        this.browser = null;
        this.page = null;
        this.logs = [];
        this.errors = [];
        this.performance = {};
        this.screenshots = [];
    }

    async init() {
        console.log('🚀 Starting Automated OrdnungsHub Debug Session');
        
        // Create debug output directory
        const debugDir = './logs/debug-session/automated';
        if (!fs.existsSync(debugDir)) {
            fs.mkdirSync(debugDir, { recursive: true });
        }

        // Launch browser with debugging flags
        this.browser = await puppeteer.launch({
            headless: false, // Show browser for visual debugging
            devtools: true,  // Open DevTools
            args: [
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        });

        this.page = await this.browser.newPage();
        
        // Set viewport
        await this.page.setViewport({ width: 1280, height: 720 });
        
        // Enable console logging
        this.page.on('console', msg => {
            const log = {
                type: msg.type(),
                text: msg.text(),
                timestamp: new Date().toISOString(),
                location: msg.location()
            };
            this.logs.push(log);
            console.log(`📝 Console [${msg.type()}]:`, msg.text());
        });

        // Capture errors
        this.page.on('pageerror', error => {
            const errorLog = {
                message: error.message,
                stack: error.stack,
                timestamp: new Date().toISOString()
            };
            this.errors.push(errorLog);
            console.log('❌ Page Error:', error.message);
        });

        // Capture network failures
        this.page.on('requestfailed', request => {
            console.log('🌐 Request Failed:', request.url(), request.failure().errorText);
        });

        console.log('✅ Browser initialized with DevTools');
    }

    async testFrontend() {
        console.log('\n🌐 Testing Frontend (http://localhost:3002)');
        
        const startTime = performance.now();
        
        try {
            await this.page.goto('http://localhost:3002', { 
                waitUntil: 'networkidle2',
                timeout: 30000 
            });
            
            const loadTime = performance.now() - startTime;
            this.performance.frontendLoad = `${Math.round(loadTime)}ms`;
            
            // Take screenshot
            const screenshot = await this.page.screenshot({ 
                fullPage: true,
                path: './logs/debug-session/automated/frontend-loaded.png'
            });
            
            console.log(`✅ Frontend loaded in ${Math.round(loadTime)}ms`);
            
            // Wait a moment for any dynamic content
            await this.page.waitForTimeout(3000);
            
            // Check for specific elements
            const elements = await this.checkPageElements();
            
            // Test basic interactions
            await this.testInteractions();
            
            return {
                success: true,
                loadTime,
                elements,
                screenshot: './logs/debug-session/automated/frontend-loaded.png'
            };
            
        } catch (error) {
            console.log('❌ Frontend test failed:', error.message);
            
            // Take error screenshot
            await this.page.screenshot({ 
                path: './logs/debug-session/automated/frontend-error.png'
            });
            
            return {
                success: false,
                error: error.message,
                screenshot: './logs/debug-session/automated/frontend-error.png'
            };
        }
    }

    async checkPageElements() {
        console.log('🔍 Checking page elements...');
        
        const elements = {};
        
        // Check for common React elements
        const selectors = {
            'App Container': '[id="root"], [id="app"]',
            'Navigation': 'nav, [role="navigation"]',
            'Header': 'header, .header',
            'Main Content': 'main, .main-content',
            'Buttons': 'button',
            'Links': 'a[href]',
            'Forms': 'form',
            'Inputs': 'input, textarea, select'
        };

        for (const [name, selector] of Object.entries(selectors)) {
            try {
                const count = await this.page.$$eval(selector, els => els.length);
                elements[name] = count;
                console.log(`  ${name}: ${count} found`);
            } catch (error) {
                elements[name] = 0;
                console.log(`  ${name}: 0 found`);
            }
        }

        return elements;
    }

    async testInteractions() {
        console.log('🧪 Testing basic interactions...');
        
        try {
            // Try to find and click buttons
            const buttons = await this.page.$$('button:not([disabled])');
            
            if (buttons.length > 0) {
                console.log(`  Found ${buttons.length} clickable buttons`);
                
                // Click first button if available
                try {
                    await buttons[0].click();
                    console.log('  ✅ First button clicked successfully');
                    
                    // Wait for any reactions
                    await this.page.waitForTimeout(1000);
                    
                } catch (error) {
                    console.log('  ⚠️ Button click failed:', error.message);
                }
            }
            
            // Try to find and focus inputs
            const inputs = await this.page.$$('input[type="text"], input[type="email"], textarea');
            
            if (inputs.length > 0) {
                console.log(`  Found ${inputs.length} text inputs`);
                
                try {
                    await inputs[0].focus();
                    await inputs[0].type('test input');
                    console.log('  ✅ Input field interaction successful');
                } catch (error) {
                    console.log('  ⚠️ Input interaction failed:', error.message);
                }
            }
            
        } catch (error) {
            console.log('  ❌ Interaction testing failed:', error.message);
        }
    }

    async testAPIEndpoints() {
        console.log('\n📡 Testing API Endpoints');
        
        const endpoints = [
            { name: 'Health Check', url: 'http://127.0.0.1:8001/health' },
            { name: 'API Docs', url: 'http://127.0.0.1:8001/docs' },
            { name: 'OpenAPI Schema', url: 'http://127.0.0.1:8001/openapi.json' }
        ];

        const results = {};

        for (const endpoint of endpoints) {
            try {
                const response = await this.page.evaluate(async (url) => {
                    const resp = await fetch(url);
                    return {
                        status: resp.status,
                        ok: resp.ok,
                        headers: Object.fromEntries(resp.headers.entries())
                    };
                }, endpoint.url);

                results[endpoint.name] = {
                    success: true,
                    status: response.status,
                    ok: response.ok
                };
                
                console.log(`  ✅ ${endpoint.name}: ${response.status}`);
                
            } catch (error) {
                results[endpoint.name] = {
                    success: false,
                    error: error.message
                };
                console.log(`  ❌ ${endpoint.name}: ${error.message}`);
            }
        }

        return results;
    }

    async runPerformanceAudit() {
        console.log('\n⚡ Running Performance Audit');
        
        try {
            // Navigate to frontend
            await this.page.goto('http://localhost:3002', { waitUntil: 'networkidle2' });
            
            // Get performance metrics
            const metrics = await this.page.metrics();
            
            // Get paint timings
            const paintTimings = await this.page.evaluate(() => {
                const paint = performance.getEntriesByType('paint');
                const navigation = performance.getEntriesByType('navigation')[0];
                
                return {
                    firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
                    firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                    domContentLoaded: navigation?.domContentLoadedEventEnd || 0,
                    loadComplete: navigation?.loadEventEnd || 0
                };
            });

            this.performance = {
                ...this.performance,
                metrics,
                paintTimings,
                audit: 'completed'
            };

            console.log('  📊 Performance metrics captured');
            console.log(`  🎨 First Paint: ${Math.round(paintTimings.firstPaint)}ms`);
            console.log(`  🖼️ First Contentful Paint: ${Math.round(paintTimings.firstContentfulPaint)}ms`);
            console.log(`  📄 DOM Content Loaded: ${Math.round(paintTimings.domContentLoaded)}ms`);
            
        } catch (error) {
            console.log('  ❌ Performance audit failed:', error.message);
        }
    }

    async generateReport() {
        console.log('\n📊 Generating Debug Report');
        
        const report = {
            timestamp: new Date().toISOString(),
            session: 'OrdnungsHub Automated Debug',
            summary: {
                totalLogs: this.logs.length,
                totalErrors: this.errors.length,
                performanceAudit: this.performance.audit || 'not completed'
            },
            logs: this.logs,
            errors: this.errors,
            performance: this.performance,
            screenshots: this.screenshots
        };

        // Save detailed report
        const reportPath = './logs/debug-session/automated/debug-report.json';
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

        // Generate summary report
        const summaryPath = './logs/debug-session/automated/debug-summary.txt';
        const summary = this.generateSummaryText(report);
        fs.writeFileSync(summaryPath, summary);

        console.log(`✅ Debug report saved to: ${reportPath}`);
        console.log(`📋 Summary saved to: ${summaryPath}`);

        return report;
    }

    generateSummaryText(report) {
        return `
OrdnungsHub Debug Session Summary
==================================
Timestamp: ${report.timestamp}

🔍 OVERVIEW
-----------
Total Console Logs: ${report.summary.totalLogs}
Total Errors: ${report.summary.totalErrors}
Performance Audit: ${report.summary.performanceAudit}

📝 CONSOLE LOGS BREAKDOWN
-------------------------
${this.logs.reduce((acc, log) => {
    acc[log.type] = (acc[log.type] || 0) + 1;
    return acc;
}, {})}

${report.summary.totalErrors > 0 ? `
❌ ERRORS FOUND
---------------
${this.errors.map((error, i) => `${i + 1}. ${error.message}`).join('\n')}
` : '✅ NO ERRORS FOUND'}

⚡ PERFORMANCE METRICS
---------------------
${report.performance.frontendLoad ? `Frontend Load Time: ${report.performance.frontendLoad}` : 'Frontend load time not measured'}
${report.performance.paintTimings ? `
First Paint: ${Math.round(report.performance.paintTimings.firstPaint)}ms
First Contentful Paint: ${Math.round(report.performance.paintTimings.firstContentfulPaint)}ms
DOM Content Loaded: ${Math.round(report.performance.paintTimings.domContentLoaded)}ms
` : 'Paint timings not available'}

🔧 RECOMMENDATIONS
------------------
${this.generateRecommendations()}

End of Report
=============
        `.trim();
    }

    generateRecommendations() {
        const recommendations = [];

        if (this.errors.length > 0) {
            recommendations.push('• Fix JavaScript errors found in console');
        }

        if (this.logs.filter(log => log.type === 'error').length > 0) {
            recommendations.push('• Address console errors for better stability');
        }

        if (this.performance.paintTimings?.firstContentfulPaint > 2000) {
            recommendations.push('• Optimize First Contentful Paint (target: <2000ms)');
        }

        if (this.logs.filter(log => log.type === 'warning').length > 5) {
            recommendations.push('• Review and reduce console warnings');
        }

        if (recommendations.length === 0) {
            recommendations.push('• Application appears to be functioning well!');
        }

        return recommendations.join('\n');
    }

    async cleanup() {
        console.log('\n🧹 Cleaning up...');
        if (this.browser) {
            await this.browser.close();
        }
        console.log('✅ Cleanup completed');
    }
}

// Main execution
async function runAutomatedDebug() {
    const debugger = new AutomatedDebugger();
    
    try {
        await debugger.init();
        
        // Run frontend tests
        const frontendResults = await debugger.testFrontend();
        
        // Test API endpoints
        const apiResults = await debugger.testAPIEndpoints();
        
        // Run performance audit
        await debugger.runPerformanceAudit();
        
        // Generate comprehensive report
        const report = await debugger.generateReport();
        
        console.log('\n🎉 Automated Debug Session Completed!');
        console.log('📁 All results saved in: ./logs/debug-session/automated/');
        
        return report;
        
    } catch (error) {
        console.error('💥 Debug session failed:', error.message);
        throw error;
    } finally {
        await debugger.cleanup();
    }
}

// Export for use in other scripts
module.exports = { AutomatedDebugger, runAutomatedDebug };

// Run if called directly
if (require.main === module) {
    runAutomatedDebug()
        .then(() => {
            console.log('Debug session completed successfully');
            process.exit(0);
        })
        .catch((error) => {
            console.error('Debug session failed:', error);
            process.exit(1);
        });
}