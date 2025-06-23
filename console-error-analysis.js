// Console Error Analysis for OrdnungsHub
// Based on real browser console output

const consoleErrors = {
    timestamp: new Date().toISOString(),
    errors: [
        {
            type: "TypeError",
            message: "t is undefined",
            file: "content_script.js:2:536882",
            severity: "medium",
            category: "browser_extension"
        },
        {
            type: "TypeError", 
            message: "t is undefined",
            file: "content_script.js:2:208273",
            severity: "medium",
            category: "browser_extension"
        },
        {
            type: "TypeError",
            message: "H.config is undefined", 
            file: "content_script.js:2:527260",
            severity: "medium",
            category: "browser_extension"
        },
        {
            type: "NetworkError",
            message: "Cross-Origin Request Blocked: CORS request did not succeed",
            url: "http://127.0.0.1:8002/auth/login",
            severity: "high",
            category: "cors_api"
        },
        {
            type: "NetworkError",
            message: "NetworkError when attempting to fetch resource",
            severity: "high", 
            category: "network"
        },
        {
            type: "LoginError",
            message: "Login failed: Network error: Unable to connect to server",
            severity: "high",
            category: "authentication"
        },
        {
            type: "CSSWarning",
            message: "Unknown property '-moz-osx-font-smoothing'",
            severity: "low",
            category: "css"
        },
        {
            type: "CSSWarning", 
            message: "Ruleset ignored due to bad selector",
            severity: "low",
            category: "css"
        },
        {
            type: "SourceMapError",
            message: "JSON.parse: unexpected character at line 1 column 1",
            file: "installHook.js.ma",
            severity: "low",
            category: "sourcemap"
        }
    ]
};

const analysis = {
    summary: {
        totalErrors: consoleErrors.errors.length,
        highSeverity: consoleErrors.errors.filter(e => e.severity === 'high').length,
        mediumSeverity: consoleErrors.errors.filter(e => e.severity === 'medium').length,
        lowSeverity: consoleErrors.errors.filter(e => e.severity === 'low').length
    },
    
    categories: {
        browser_extension: consoleErrors.errors.filter(e => e.category === 'browser_extension').length,
        cors_api: consoleErrors.errors.filter(e => e.category === 'cors_api').length,
        network: consoleErrors.errors.filter(e => e.category === 'network').length,
        authentication: consoleErrors.errors.filter(e => e.category === 'authentication').length,
        css: consoleErrors.errors.filter(e => e.category === 'css').length,
        sourcemap: consoleErrors.errors.filter(e => e.category === 'sourcemap').length
    },

    criticalIssues: [
        {
            issue: "Wrong API Port",
            description: "Frontend trying to connect to port 8002, but backend runs on 8001",
            solution: "Update API configuration to use correct port 8001",
            priority: "CRITICAL"
        },
        {
            issue: "CORS Configuration",
            description: "Cross-origin requests being blocked",
            solution: "Configure CORS settings in FastAPI backend",
            priority: "HIGH"
        },
        {
            issue: "Authentication Endpoint Missing",
            description: "Login attempting to access /auth/login endpoint that may not exist",
            solution: "Verify authentication routes are properly registered",
            priority: "HIGH"
        }
    ],

    minorIssues: [
        {
            issue: "Browser Extension Conflicts",
            description: "content_script.js errors from browser extensions",
            solution: "These are external and can be ignored in development",
            priority: "LOW"
        },
        {
            issue: "CSS Compatibility",
            description: "Firefox-specific CSS properties and bad selectors",
            solution: "Clean up CSS, use autoprefixer for vendor prefixes",
            priority: "LOW"
        },
        {
            issue: "Source Map Issues",
            description: "Development source maps not loading correctly",
            solution: "Check Vite source map configuration",
            priority: "LOW"
        }
    ]
};

console.log('Console Error Analysis:', JSON.stringify(analysis, null, 2));

module.exports = { consoleErrors, analysis };