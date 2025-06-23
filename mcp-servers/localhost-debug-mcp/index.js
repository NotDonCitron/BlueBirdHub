#!/usr/bin/env node

/**
 * Localhost Debug MCP Server
 * Auto-checks webview localhost for debugging OrdnungsHub
 */

const express = require('express');
const puppeteer = require('puppeteer');
const WebSocket = require('ws');
const axios = require('axios');
const cors = require('cors');

const app = express();
const port = 3004; // Avoid conflict with main app

app.use(cors());
app.use(express.json());

// WebSocket for real-time debugging
const wss = new WebSocket.Server({ port: 3005 });
let connectedClients = [];

wss.on('connection', (ws) => {
    console.log('🔗 Debug client connected');
    connectedClients.push(ws);
    
    ws.on('close', () => {
        connectedClients = connectedClients.filter(client => client !== ws);
        console.log('🔌 Debug client disconnected');
    });
});

// Broadcast to all connected clients
function broadcast(data) {
    connectedClients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(data));
        }
    });
}

// Auto health check for localhost
async function healthCheck() {
    const targets = [
        { name: 'Frontend', url: 'http://localhost:3002' },
        { name: 'Backend API', url: 'http://127.0.0.1:8001/docs' },
        { name: 'Backend Health', url: 'http://127.0.0.1:8001/health' }
    ];
    
    const results = [];
    
    for (const target of targets) {
        try {
            const start = Date.now();
            const response = await axios.get(target.url, { timeout: 5000 });
            const duration = Date.now() - start;
            
            results.push({
                name: target.name,
                url: target.url,
                status: 'healthy',
                statusCode: response.status,
                responseTime: `${duration}ms`,
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            results.push({
                name: target.name,
                url: target.url,
                status: 'unhealthy',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    return results;
}

// Browser automation for UI testing
let browser = null;

async function initBrowser() {
    if (!browser) {
        browser = await puppeteer.launch({
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
    }
    return browser;
}

// API Routes

// Health check endpoint
app.get('/health-check', async (req, res) => {
    try {
        const results = await healthCheck();
        broadcast({ type: 'health-check', data: results });
        res.json({ success: true, results });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Screenshot localhost page
app.post('/screenshot', async (req, res) => {
    const { url = 'http://localhost:3002', selector = null } = req.body;
    
    try {
        const browser = await initBrowser();
        const page = await browser.newPage();
        
        await page.setViewport({ width: 1280, height: 720 });
        await page.goto(url, { waitUntil: 'networkidle2' });
        
        let screenshot;
        if (selector) {
            const element = await page.$(selector);
            screenshot = await element.screenshot({ encoding: 'base64' });
        } else {
            screenshot = await page.screenshot({ encoding: 'base64', fullPage: true });
        }
        
        await page.close();
        
        broadcast({ 
            type: 'screenshot', 
            data: { url, selector, timestamp: new Date().toISOString() }
        });
        
        res.json({ 
            success: true, 
            screenshot: `data:image/png;base64,${screenshot}`,
            url,
            selector
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Console logs capture
app.post('/capture-logs', async (req, res) => {
    const { url = 'http://localhost:3002', duration = 10000 } = req.body;
    
    try {
        const browser = await initBrowser();
        const page = await browser.newPage();
        
        const logs = [];
        page.on('console', msg => {
            logs.push({
                type: msg.type(),
                text: msg.text(),
                timestamp: new Date().toISOString()
            });
        });
        
        page.on('pageerror', error => {
            logs.push({
                type: 'error',
                text: error.message,
                timestamp: new Date().toISOString()
            });
        });
        
        await page.goto(url, { waitUntil: 'networkidle2' });
        
        // Wait for specified duration to capture logs
        await new Promise(resolve => setTimeout(resolve, duration));
        
        await page.close();
        
        broadcast({ 
            type: 'console-logs', 
            data: { url, logs, duration }
        });
        
        res.json({ success: true, logs, url, duration });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Performance audit
app.post('/performance-audit', async (req, res) => {
    const { url = 'http://localhost:3002' } = req.body;
    
    try {
        const browser = await initBrowser();
        const page = await browser.newPage();
        
        // Enable performance monitoring
        await page.setCacheEnabled(false);
        
        const performanceMetrics = [];
        
        page.on('metrics', metrics => {
            performanceMetrics.push({
                ...metrics,
                timestamp: new Date().toISOString()
            });
        });
        
        const start = Date.now();
        await page.goto(url, { waitUntil: 'networkidle2' });
        const loadTime = Date.now() - start;
        
        const metrics = await page.metrics();
        
        await page.close();
        
        const result = {
            url,
            loadTime: `${loadTime}ms`,
            metrics,
            timestamp: new Date().toISOString()
        };
        
        broadcast({ 
            type: 'performance-audit', 
            data: result
        });
        
        res.json({ success: true, ...result });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Auto-monitor (runs continuously)
let monitoringInterval = null;

app.post('/start-monitoring', (req, res) => {
    const { interval = 30000 } = req.body; // Default 30 seconds
    
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
    }
    
    monitoringInterval = setInterval(async () => {
        try {
            const health = await healthCheck();
            broadcast({ 
                type: 'auto-monitor', 
                data: { 
                    health, 
                    timestamp: new Date().toISOString() 
                }
            });
        } catch (error) {
            broadcast({ 
                type: 'monitor-error', 
                data: { 
                    error: error.message, 
                    timestamp: new Date().toISOString() 
                }
            });
        }
    }, interval);
    
    res.json({ success: true, message: `Auto-monitoring started with ${interval}ms interval` });
});

app.post('/stop-monitoring', (req, res) => {
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
        monitoringInterval = null;
    }
    
    res.json({ success: true, message: 'Auto-monitoring stopped' });
});

// Test React components
app.post('/test-component', async (req, res) => {
    const { 
        url = 'http://localhost:3002', 
        selector, 
        action = 'click',
        value = null 
    } = req.body;
    
    try {
        const browser = await initBrowser();
        const page = await browser.newPage();
        
        await page.goto(url, { waitUntil: 'networkidle2' });
        
        let result = {};
        
        if (selector) {
            await page.waitForSelector(selector, { timeout: 5000 });
            
            switch (action) {
                case 'click':
                    await page.click(selector);
                    result.action = 'clicked';
                    break;
                case 'type':
                    if (value) {
                        await page.type(selector, value);
                        result.action = 'typed';
                        result.value = value;
                    }
                    break;
                case 'screenshot':
                    const element = await page.$(selector);
                    const screenshot = await element.screenshot({ encoding: 'base64' });
                    result.screenshot = `data:image/png;base64,${screenshot}`;
                    break;
                case 'text':
                    const text = await page.$eval(selector, el => el.textContent);
                    result.text = text;
                    break;
            }
        }
        
        // Wait a moment for any reactions
        await page.waitForTimeout(1000);
        
        await page.close();
        
        broadcast({ 
            type: 'component-test', 
            data: { url, selector, action, result }
        });
        
        res.json({ success: true, ...result });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Start server
const server = app.listen(port, () => {
    console.log(`🚀 Localhost Debug MCP Server running on http://localhost:${port}`);
    console.log(`🔗 WebSocket Debug Feed: ws://localhost:3005`);
    console.log(`\n📋 Available endpoints:`);
    console.log(`   GET  /health-check - Check all services`);
    console.log(`   POST /screenshot - Take screenshots`);
    console.log(`   POST /capture-logs - Capture console logs`);
    console.log(`   POST /performance-audit - Performance analysis`);
    console.log(`   POST /start-monitoring - Start auto-monitoring`);
    console.log(`   POST /stop-monitoring - Stop auto-monitoring`);
    console.log(`   POST /test-component - Test React components`);
});

// Cleanup
process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down debug server...');
    
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
    }
    
    if (browser) {
        await browser.close();
    }
    
    server.close(() => {
        console.log('🔌 Debug server closed');
        process.exit(0);
    });
});

// Auto-start health monitoring
setTimeout(async () => {
    console.log('🔍 Starting initial health check...');
    const health = await healthCheck();
    console.log('📊 Health check results:', health);
    broadcast({ type: 'initial-health', data: health });
}, 2000);