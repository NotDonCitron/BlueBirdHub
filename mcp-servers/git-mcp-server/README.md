# Git MCP Server

A simple MCP (Model Control Protocol) server for Git operations.

## Getting Started

1. Install dependencies:
   ```
   npm install
   ```

2. Start the server:
   ```
   npm start
   ```

The server will start on `http://localhost:3001`

## API Endpoints

- `GET /status` - Get repository status
- `GET /log` - Get commit history
- `POST /commit` - Create a new commit
  - Body: `{ "message": "commit message", "files": ["file1.txt", "file2.js"] }`
- `GET /branch` - Get current branch
- `POST /branch` - Create a new branch
  - Body: `{ "name": "branch-name" }`
- `POST /checkout` - Checkout a branch
  - Body: `{ "branch": "branch-name" }`

## Usage with Claude in Windsurf

1. Start the server in your project directory
2. Use the MCP client in Windsurf to connect to `http://localhost:3001`
3. Use the available endpoints to perform Git operations

## Security Note

This is a basic implementation. For production use, you should add authentication and additional security measures.
