const express = require('express');
const cors = require('cors');
const axios = require('axios');
const cheerio = require('cheerio');
const WebSocket = require('ws');
const path = require('path');
const fs = require('fs');

const app = express();
const port = 3002;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// WebSocket Server
const wss = new WebSocket.Server({ port: 3003 });

wss.on('connection', (ws) => {
    console.log('WebSocket client connected');
    
    ws.on('message', (message) => {
        console.log('Received:', message);
        ws.send(`Echo: ${message}`);
    });
    
    ws.on('close', () => {
        console.log('WebSocket client disconnected');
    });
});

// API Routes

// Fetch webpage and return its content
app.post('/fetch', async (req, res) => {
    const { url } = req.body;
    
    if (!url) {
        return res.status(400).json({ error: 'URL is required' });
    }
    
    try {
        const response = await axios.get(url);
        const $ = cheerio.load(response.data);
        
        // Extract useful information
        const title = $('title').text();
        const links = [];
        $('a').each((i, el) => {
            links.push({
                text: $(el).text().trim(),
                href: $(el).attr('href')
            });
        });
        
        res.json({
            title,
            url: response.request.res.responseUrl, // Get final URL after redirects
            status: response.status,
            headers: response.headers,
            links,
            // You can add more extracted data as needed
        });
    } catch (error) {
        res.status(500).json({ 
            error: 'Failed to fetch URL',
            details: error.message 
        });
    }
});

// File operations
app.post('/file/write', (req, res) => {
    const { path: filePath, content } = req.body;
    
    if (!filePath || content === undefined) {
        return res.status(400).json({ error: 'Path and content are required' });
    }
    
    try {
        fs.writeFileSync(filePath, content);
        res.json({ success: true, message: 'File written successfully' });
    } catch (error) {
        res.status(500).json({ error: 'Failed to write file', details: error.message });
    }
});

app.get('/file/read', (req, res) => {
    const { path: filePath } = req.query;
    
    if (!filePath) {
        return res.status(400).json({ error: 'Path is required' });
    }
    
    try {
        const content = fs.readFileSync(filePath, 'utf8');
        res.json({ success: true, content });
    } catch (error) {
        res.status(500).json({ error: 'Failed to read file', details: error.message });
    }
});

// Start the HTTP server
const server = app.listen(port, () => {
    console.log(`Web Dev MCP Server running on http://localhost:${port}`);
    console.log(`WebSocket Server running on ws://localhost:3003`);
});

// Handle server shutdown
process.on('SIGINT', () => {
    console.log('Shutting down servers...');
    server.close(() => {
        console.log('HTTP server closed');
    });
    wss.close(() => {
        console.log('WebSocket server closed');
        process.exit(0);
    });
});
