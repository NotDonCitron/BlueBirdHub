# Web Development MCP Server

A versatile MCP (Model Control Protocol) server for web development tasks, including web scraping, file operations, and WebSocket communication.

## Features

- **Web Scraping**: Fetch and parse web pages
- **File Operations**: Read and write files
- **WebSocket Server**: Real-time communication
- **RESTful API**: Easy integration with other services

## Getting Started

1. Install dependencies:
   ```
   npm install
   ```

2. Start the server:
   ```
   npm start
   ```

The server will start on `http://localhost:3002` (HTTP) and `ws://localhost:3003` (WebSocket)

## API Endpoints

### Web Scraping
- `POST /fetch` - Fetch and parse a webpage
  - Body: `{ "url": "https://example.com" }`
  - Returns: Page title, links, and other metadata

### File Operations
- `POST /file/write` - Write content to a file
  - Body: `{ "path": "path/to/file.txt", "content": "Hello, World!" }`
  
- `GET /file/read` - Read content from a file
  - Query: `?path=path/to/file.txt`
  - Returns: File content

### WebSocket
- Connect to `ws://localhost:3003` for real-time communication
- Messages sent to the server will be echoed back with an "Echo: " prefix

## Usage with Claude in Windsurf

1. Start the server in your project directory
2. Use the MCP client in Windsurf to connect to `http://localhost:3002`
3. Use the available endpoints to perform web development tasks

## Security Note

This is a basic implementation. For production use, you should add authentication, input validation, and additional security measures.
