const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const simpleGit = require('simple-git');
const path = require('path');

const app = express();
const port = 3001;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Git operations
const git = simpleGit();

// Get repository status
app.get('/status', async (req, res) => {
    try {
        const status = await git.status();
        res.json(status);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get commit history
app.get('/log', async (req, res) => {
    try {
        const log = await git.log();
        res.json(log);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Create a new commit
app.post('/commit', async (req, res) => {
    const { message, files } = req.body;
    
    try {
        // Add files if specified
        if (files && files.length > 0) {
            await git.add(files);
        } else {
            await git.add('.');
        }
        
        // Create commit
        const commit = await git.commit(message);
        res.json(commit);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get current branch
app.get('/branch', async (req, res) => {
    try {
        const branch = await git.branchLocal();
        res.json(branch);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Create a new branch
app.post('/branch', async (req, res) => {
    const { name } = req.body;
    
    try {
        const result = await git.branch([name]);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Checkout a branch
app.post('/checkout', async (req, res) => {
    const { branch } = req.body;
    
    try {
        await git.checkout(branch);
        res.json({ message: `Switched to branch '${branch}'` });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Start server
app.listen(port, () => {
    console.log(`Git MCP Server running on http://localhost:${port}`);
});
