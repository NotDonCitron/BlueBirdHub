# Fix for Claude Flow Error

## The Problem
You're seeing npm 404 errors because `claudeflow` is NOT an npm package. It's a local tool we created in your project.

## The Solution

### Option 1: Use the Windows Batch Script (Recommended for Windows)
```bash
# Navigate to your project directory
cd C:\Users\pasca\CascadeProjects\nnewcoededui

# Run the batch file directly
.\claude-flow.bat setup
.\claude-flow.bat status
.\claude-flow.bat feature "Your feature description"
```

### Option 2: Use NPM Scripts
```bash
# These commands are already in your package.json
npm run claude:setup
npm run claude:status
npm run claude:feature "Your feature description"
```

### Option 3: Run Python Directly
```bash
# Make sure you're in the project directory
cd C:\Users\pasca\CascadeProjects\nnewcoededui

# Run the Python script directly
python src\backend\services\claude_code_orchestrator.py feature "Your feature description"
```

## First-Time Setup

1. **Install Python dependencies** (if not already done):
```bash
# Create virtual environment
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate

# Install dependencies
pip install rich
```

2. **Check if everything is ready**:
```bash
.\claude-flow.bat setup
```

## Common Commands

```bash
# Add a new feature
.\claude-flow.bat feature "Add dark mode support"

# Fix a bug
.\claude-flow.bat fix "File upload crashes on large files"

# Check system status
.\claude-flow.bat status
```

## DO NOT RUN
❌ `npm install claudeflow` - This package doesn't exist!
❌ `npm install claude-flow` - Not an npm package!

## Quick Test
Try this right now:
```bash
cd C:\Users\pasca\CascadeProjects\nnewcoededui
.\claude-flow.bat status
```

This should show you the current status of your Claude Code Flow setup.
