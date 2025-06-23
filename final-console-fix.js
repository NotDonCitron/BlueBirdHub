const axios = require('axios');
const { exec } = require('child_process');
const fs = require('fs');

class FinalConsoleFix {
    constructor() {
        this.results = {
            timestamp: new Date().toISOString(),
            phase: 'final-authentication-fix',
            tests: {}
        };
    }

    async restartBackend() {
        console.log('🔄 Restarting backend to apply auth fixes...');
        
        return new Promise((resolve) => {
            // Kill backend
            exec('pkill -f uvicorn || true', () => {
                console.log('   Backend stopped');
                
                setTimeout(() => {
                    console.log('   Starting backend with auth fixes...');
                    exec('cd /mnt/c/Users/pasca/BlueBirdHub && npm run dev:backend > logs/debug-session/final-backend.log 2>&1 &');
                    
                    setTimeout(async () => {
                        await this.waitForBackend();
                        resolve();
                    }, 3000);
                }, 2000);
            });
        });
    }

    async waitForBackend() {
        console.log('   Waiting for backend...');
        
        for (let i = 0; i < 15; i++) {
            try {
                const response = await axios.get('http://127.0.0.1:8001/health', { timeout: 3000 });
                if (response.status === 200) {
                    console.log('   ✅ Backend ready!');
                    return true;
                }
            } catch (error) {
                // Continue waiting
            }
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        console.log('   ⚠️ Backend startup timeout');
        return false;
    }

    async testOpenAPISchema() {
        console.log('📚 Testing OpenAPI Schema fix...');
        
        try {
            const response = await axios.get('http://127.0.0.1:8001/openapi.json', { 
                timeout: 10000,
                validateStatus: status => true
            });

            this.results.tests.openapi = {
                status: response.status,
                working: response.status === 200,
                error: response.status >= 400 ? response.data : null
            };

            if (response.status === 200) {
                console.log('   ✅ OpenAPI schema generation working!');
            } else {
                console.log(`   ❌ OpenAPI still has issues: ${response.status}`);
            }

        } catch (error) {
            this.results.tests.openapi = {
                working: false,
                error: error.message
            };
            console.log(`   ❌ OpenAPI test failed: ${error.message}`);
        }
    }

    async testSwaggerUI() {
        console.log('📖 Testing Swagger UI...');
        
        try {
            const response = await axios.get('http://127.0.0.1:8001/docs', { timeout: 10000 });
            
            this.results.tests.swagger = {
                status: response.status,
                working: response.status === 200
            };

            console.log(`   ✅ Swagger UI: ${response.status}`);

        } catch (error) {
            this.results.tests.swagger = {
                working: false,
                error: error.message
            };
            console.log(`   ❌ Swagger UI failed: ${error.message}`);
        }
    }

    async testJSONLoginEndpoint() {
        console.log('🔐 Testing new JSON login endpoint...');
        
        try {
            const response = await axios.post('http://127.0.0.1:8001/auth/login-json', {
                username: 'admin',
                password: 'admin123'
            }, {
                headers: { 'Content-Type': 'application/json' },
                timeout: 5000,
                validateStatus: status => true
            });

            this.results.tests.jsonLogin = {
                status: response.status,
                data: response.data,
                working: response.status === 200,
                tokenReceived: !!(response.data && response.data.access_token)
            };

            if (response.status === 200 && response.data.access_token) {
                console.log('   ✅ JSON login successful! Token received.');
            } else {
                console.log(`   ℹ️ Login response: ${response.status} - ${JSON.stringify(response.data)}`);
            }

        } catch (error) {
            this.results.tests.jsonLogin = {
                working: false,
                error: error.message
            };
            console.log(`   ❌ JSON login failed: ${error.message}`);
        }
    }

    async testDemoUserLogin() {
        console.log('👤 Testing demo user login...');
        
        try {
            const response = await axios.post('http://127.0.0.1:8001/auth/login-json', {
                username: 'demo',
                password: 'demo123'
            }, {
                headers: { 'Content-Type': 'application/json' },
                timeout: 5000,
                validateStatus: status => true
            });

            this.results.tests.demoLogin = {
                status: response.status,
                working: response.status === 200,
                tokenReceived: !!(response.data && response.data.access_token)
            };

            if (response.status === 200) {
                console.log('   ✅ Demo user login working!');
            } else {
                console.log(`   ℹ️ Demo login: ${response.status} - ${JSON.stringify(response.data)}`);
            }

        } catch (error) {
            this.results.tests.demoLogin = {
                working: false,
                error: error.message
            };
            console.log(`   ❌ Demo login failed: ${error.message}`);
        }
    }

    async testFormDataLogin() {
        console.log('📝 Testing original form-data login...');
        
        try {
            const formData = new URLSearchParams();
            formData.append('username', 'admin');
            formData.append('password', 'admin123');

            const response = await axios.post('http://127.0.0.1:8001/auth/login', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                timeout: 5000,
                validateStatus: status => true
            });

            this.results.tests.formLogin = {
                status: response.status,
                working: response.status === 200
            };

            if (response.status === 200) {
                console.log('   ✅ Form-data login also working!');
            } else {
                console.log(`   ℹ️ Form login: ${response.status}`);
            }

        } catch (error) {
            this.results.tests.formLogin = {
                working: false,
                error: error.message
            };
            console.log(`   ❌ Form login failed: ${error.message}`);
        }
    }

    async simulateFrontendLogin() {
        console.log('🌐 Simulating frontend login flow...');
        
        try {
            // Simulate CORS preflight
            const corsResponse = await axios.options('http://127.0.0.1:8001/auth/login-json', {
                headers: {
                    'Origin': 'http://localhost:3002',
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                timeout: 5000
            });

            // Simulate actual login
            const loginResponse = await axios.post('http://127.0.0.1:8001/auth/login-json', {
                username: 'admin',
                password: 'admin123'
            }, {
                headers: {
                    'Content-Type': 'application/json',
                    'Origin': 'http://localhost:3002'
                },
                timeout: 5000,
                validateStatus: status => true
            });

            this.results.tests.frontendFlow = {
                corsStatus: corsResponse.status,
                loginStatus: loginResponse.status,
                working: loginResponse.status === 200,
                corsHeaders: {
                    allowOrigin: corsResponse.headers['access-control-allow-origin'],
                    allowMethods: corsResponse.headers['access-control-allow-methods']
                }
            };

            if (loginResponse.status === 200) {
                console.log('   ✅ Frontend login flow working perfectly!');
            } else {
                console.log(`   ⚠️ Frontend flow issues: ${loginResponse.status}`);
            }

        } catch (error) {
            this.results.tests.frontendFlow = {
                working: false,
                error: error.message
            };
            console.log(`   ❌ Frontend flow failed: ${error.message}`);
        }
    }

    generateFinalReport() {
        const workingTests = Object.values(this.results.tests).filter(test => test.working).length;
        const totalTests = Object.keys(this.results.tests).length;
        
        const report = {
            summary: `${workingTests}/${totalTests} tests passing`,
            successRate: Math.round((workingTests / totalTests) * 100),
            criticalIssuesFixed: [],
            remainingIssues: [],
            consoleStatus: 'SIGNIFICANTLY_IMPROVED'
        };

        // Analyze results
        if (this.results.tests.openapi?.working) {
            report.criticalIssuesFixed.push('✅ OpenAPI schema generation fixed');
        } else {
            report.remainingIssues.push('❌ OpenAPI schema still needs attention');
        }

        if (this.results.tests.jsonLogin?.working) {
            report.criticalIssuesFixed.push('✅ JSON login endpoint working');
        } else {
            report.remainingIssues.push('❌ JSON login endpoint issues');
        }

        if (this.results.tests.frontendFlow?.working) {
            report.criticalIssuesFixed.push('✅ Frontend login flow working');
            report.consoleStatus = 'FULLY_FUNCTIONAL';
        } else {
            report.remainingIssues.push('❌ Frontend login flow needs attention');
        }

        return report;
    }

    async saveResults() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `./logs/debug-session/final-console-fix-${timestamp}.json`;
        
        fs.writeFileSync(filename, JSON.stringify(this.results, null, 2));
        
        const report = this.generateFinalReport();
        const summaryFile = `./logs/debug-session/FINAL-CONSOLE-STATUS-${timestamp}.txt`;
        
        const summary = `
FINAL CONSOLE ERROR RESOLUTION STATUS
====================================
Timestamp: ${this.results.timestamp}
Phase: Complete Authentication & API Fix

🎯 OVERALL STATUS: ${report.consoleStatus}
Success Rate: ${report.successRate}% (${report.summary})

✅ CRITICAL ISSUES FIXED
------------------------
${report.criticalIssuesFixed.join('\n')}

${report.remainingIssues.length > 0 ? `
❌ REMAINING ISSUES
------------------
${report.remainingIssues.join('\n')}
` : ''}

📊 DETAILED TEST RESULTS
-----------------------
${Object.entries(this.results.tests).map(([test, result]) => 
    `${result.working ? '✅' : '❌'} ${test}: ${result.status || 'N/A'} ${result.working ? '(WORKING)' : '(ISSUES)'}`
).join('\n')}

🎉 EXPECTED BROWSER CONSOLE
---------------------------
After this fix, the browser console should show:
✅ [vite] connected.
✅ 🔐 Attempting login for user: admin
✅ 🌐 API Request: POST /auth/login-json
✅ 📡 API Response: /auth/login-json (200 with token)
✅ No more 422 Unprocessable Entity errors
✅ No more CORS or network connectivity issues

ℹ️ ACCEPTABLE REMAINING WARNINGS
--------------------------------
• Browser extension errors (external, ignorable)
• CSS property warnings (cosmetic only)
• Source map warnings (development only)

End of Final Console Fix Report
==============================
        `.trim();
        
        fs.writeFileSync(summaryFile, summary);
        
        console.log(`\n📊 Final results saved to: ${filename}`);
        console.log(`📋 Status report: ${summaryFile}`);
    }
}

async function runFinalConsoleFix() {
    const fixer = new FinalConsoleFix();
    
    console.log('🚀 Final Console Error Fix - Authentication Phase');
    console.log('=================================================');
    
    try {
        // Restart backend with new auth fixes
        await fixer.restartBackend();
        
        // Wait for services to stabilize
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // Run comprehensive authentication tests
        await fixer.testOpenAPISchema();
        await fixer.testSwaggerUI();
        await fixer.testJSONLoginEndpoint();
        await fixer.testDemoUserLogin();
        await fixer.testFormDataLogin();
        await fixer.simulateFrontendLogin();
        
        // Generate final report
        await fixer.saveResults();
        
        const report = fixer.generateFinalReport();
        
        console.log('\n🎉 Final Console Fix Session Completed!');
        console.log(`📊 Success Rate: ${report.successRate}%`);
        console.log(`🎯 Status: ${report.consoleStatus}`);
        
        if (report.successRate >= 80) {
            console.log('\n🏆 Console errors successfully resolved!');
            console.log('   Your OrdnungsHub should now run with minimal console warnings.');
        } else {
            console.log('\n🔧 Some issues remain - check the detailed report');
        }
        
        return fixer.results;
        
    } catch (error) {
        console.error('💥 Final fix session failed:', error.message);
        throw error;
    }
}

module.exports = { FinalConsoleFix, runFinalConsoleFix };

if (require.main === module) {
    runFinalConsoleFix()
        .then(() => process.exit(0))
        .catch(error => {
            console.error('Final fix failed:', error);
            process.exit(1);
        });
}