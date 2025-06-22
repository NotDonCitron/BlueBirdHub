"""
Model Context Protocol (MCP) Client for connecting to external data sources
Based on Anthropic's MCP specification for AI data integration
"""

import asyncio
import json
import aiohttp
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

class MCPResource(BaseModel):
    """MCP Resource definition"""
    uri: str
    name: str
    description: str
    mimeType: Optional[str] = None

class MCPTool(BaseModel):
    """MCP Tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]

class MCPServer(BaseModel):
    """MCP Server configuration"""
    name: str
    url: str
    description: str
    capabilities: List[str]
    resources: List[MCPResource] = []
    tools: List[MCPTool] = []

class MCPClient:
    """
    Model Context Protocol client for connecting OrdnungsHub to external data sources
    """
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self._initialized = False
        
        # Initialize default MCP servers
        self._setup_default_servers()
    
    def _setup_default_servers(self):
        """Setup default MCP servers for common data sources"""
        
        # Filesystem MCP Server
        filesystem_server = MCPServer(
            name="filesystem",
            url="mcp://localhost:3001/filesystem",
            description="Local filesystem access with security boundaries",
            capabilities=["resources", "tools"],
            resources=[
                MCPResource(
                    uri="file://",
                    name="Local Files",
                    description="Access to allowed local file directories",
                    mimeType="application/octet-stream"
                )
            ],
            tools=[
                MCPTool(
                    name="read_file",
                    description="Read contents of a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path to read"}
                        },
                        "required": ["path"]
                    }
                ),
                MCPTool(
                    name="list_directory",
                    description="List files in a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path to list"}
                        },
                        "required": ["path"]
                    }
                )
            ]
        )
        
        # Database MCP Server
        database_server = MCPServer(
            name="database",
            url="mcp://localhost:3002/database",
            description="SQLite database access for workspace data",
            capabilities=["resources", "tools"],
            resources=[
                MCPResource(
                    uri="sqlite://data/ordnungshub.db",
                    name="OrdnungsHub Database",
                    description="Access to workspace and task data",
                    mimeType="application/x-sqlite3"
                )
            ],
            tools=[
                MCPTool(
                    name="query_workspaces",
                    description="Query workspace information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "integer", "description": "User ID to query workspaces for"}
                        },
                        "required": ["user_id"]
                    }
                ),
                MCPTool(
                    name="query_tasks",
                    description="Query task information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workspace_id": {"type": "integer", "description": "Workspace ID to query tasks for"}
                        }
                    }
                )
            ]
        )
        
        # Web Search MCP Server (using Brave Search)
        web_server = MCPServer(
            name="web_search",
            url="mcp://localhost:3003/brave_search",
            description="Web search capabilities using Brave Search API",
            capabilities=["tools"],
            tools=[
                MCPTool(
                    name="search_web",
                    description="Search the web for information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "count": {"type": "integer", "default": 10, "description": "Number of results"}
                        },
                        "required": ["query"]
                    }
                )
            ]
        )
        
        self.servers = {
            "filesystem": filesystem_server,
            "database": database_server,
            "web_search": web_server
        }
    
    async def initialize(self):
        """Initialize the MCP client"""
        if self._initialized:
            return
            
        self.session = aiohttp.ClientSession()
        
        # Try to connect to available MCP servers
        for server_name, server in self.servers.items():
            try:
                await self._test_server_connection(server)
                logger.info(f"MCP server '{server_name}' is available")
            except Exception as e:
                logger.warning(f"MCP server '{server_name}' is not available: {e}")
        
        self._initialized = True
    
    async def _test_server_connection(self, server: MCPServer) -> bool:
        """Test connection to an MCP server"""
        try:
            # For now, simulate connection test
            # In a real implementation, this would make an actual HTTP request
            logger.debug(f"Testing connection to {server.name} at {server.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server.name}: {e}")
            return False
    
    async def list_resources(self, server_name: str) -> List[MCPResource]:
        """List available resources from an MCP server"""
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        server = self.servers[server_name]
        return server.resources
    
    async def list_tools(self, server_name: str) -> List[MCPTool]:
        """List available tools from an MCP server"""
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        server = self.servers[server_name]
        return server.tools
    
    async def read_resource(self, server_name: str, uri: str) -> Dict[str, Any]:
        """Read a resource from an MCP server"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Simulate resource reading for demonstration
            # In a real implementation, this would make an MCP request
            
            if server_name == "filesystem" and uri.startswith("file://"):
                return await self._read_filesystem_resource(uri)
            elif server_name == "database" and uri.startswith("sqlite://"):
                return await self._read_database_resource(uri)
            else:
                raise ValueError(f"Unsupported resource URI: {uri}")
                
        except Exception as e:
            logger.error(f"Failed to read resource {uri} from {server_name}: {e}")
            raise
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on an MCP server"""
        if not self._initialized:
            await self.initialize()
        
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        server = self.servers[server_name]
        tool = next((t for t in server.tools if t.name == tool_name), None)
        
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name} on server {server_name}")
        
        try:
            # Route to appropriate handler based on server and tool
            if server_name == "filesystem":
                return await self._handle_filesystem_tool(tool_name, arguments)
            elif server_name == "database":
                return await self._handle_database_tool(tool_name, arguments)
            elif server_name == "web_search":
                return await self._handle_web_search_tool(tool_name, arguments)
            else:
                raise ValueError(f"No handler for server: {server_name}")
                
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {server_name}: {e}")
            raise
    
    async def _read_filesystem_resource(self, uri: str) -> Dict[str, Any]:
        """Read filesystem resource (simulated)"""
        import os
        from pathlib import Path
        
        # Extract path from URI
        path = uri.replace("file://", "")
        file_path = Path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # Security check - only allow access to certain directories
        allowed_dirs = ["./data", "./uploads", "./logs"]
        if not any(str(file_path).startswith(allowed_dir) for allowed_dir in allowed_dirs):
            raise PermissionError(f"Access denied to: {path}")
        
        return {
            "uri": uri,
            "mimeType": "text/plain",
            "text": file_path.read_text() if file_path.is_file() else "Directory",
            "size": file_path.stat().st_size if file_path.is_file() else 0
        }
    
    async def _read_database_resource(self, uri: str) -> Dict[str, Any]:
        """Read database resource (simulated)"""
        return {
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps({"message": "Database resource simulation"}),
            "tables": ["users", "workspaces", "tasks", "files"]
        }
    
    async def _handle_filesystem_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle filesystem tool calls"""
        from pathlib import Path
        
        if tool_name == "read_file":
            path = arguments.get("path")
            if not path:
                raise ValueError("Missing required argument: path")
            
            file_path = Path(path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            return {
                "success": True,
                "content": file_path.read_text(),
                "size": file_path.stat().st_size
            }
        
        elif tool_name == "list_directory":
            path = arguments.get("path", ".")
            dir_path = Path(path)
            
            if not dir_path.exists() or not dir_path.is_dir():
                raise ValueError(f"Directory not found: {path}")
            
            files = []
            for item in dir_path.iterdir():
                files.append({
                    "name": item.name,
                    "type": "file" if item.is_file() else "directory",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            return {
                "success": True,
                "files": files,
                "path": str(dir_path)
            }
        
        else:
            raise ValueError(f"Unknown filesystem tool: {tool_name}")
    
    async def _handle_database_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle database tool calls"""
        # This would integrate with the actual database
        # For now, return simulated data
        
        if tool_name == "query_workspaces":
            user_id = arguments.get("user_id")
            return {
                "success": True,
                "workspaces": [
                    {"id": 1, "name": "Personal", "user_id": user_id},
                    {"id": 2, "name": "Work Projects", "user_id": user_id}
                ]
            }
        
        elif tool_name == "query_tasks":
            workspace_id = arguments.get("workspace_id")
            return {
                "success": True,
                "tasks": [
                    {"id": 1, "title": "Complete project", "workspace_id": workspace_id},
                    {"id": 2, "title": "Review documentation", "workspace_id": workspace_id}
                ]
            }
        
        else:
            raise ValueError(f"Unknown database tool: {tool_name}")
    
    async def _handle_web_search_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle web search tool calls"""
        if tool_name == "search_web":
            query = arguments.get("query")
            count = arguments.get("count", 10)
            
            # Simulate web search results
            # In a real implementation, this would call the Brave Search API
            return {
                "success": True,
                "query": query,
                "results": [
                    {
                        "title": f"Result {i+1} for '{query}'",
                        "url": f"https://example.com/result-{i+1}",
                        "description": f"Description for result {i+1} about {query}"
                    }
                    for i in range(min(count, 5))  # Simulate up to 5 results
                ]
            }
        
        else:
            raise ValueError(f"Unknown web search tool: {tool_name}")
    
    async def get_server_capabilities(self, server_name: str) -> Dict[str, Any]:
        """Get capabilities of an MCP server"""
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        server = self.servers[server_name]
        return {
            "name": server.name,
            "description": server.description,
            "capabilities": server.capabilities,
            "resources_count": len(server.resources),
            "tools_count": len(server.tools)
        }
    
    async def list_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """List all available MCP servers and their capabilities"""
        result = {}
        for server_name in self.servers:
            result[server_name] = await self.get_server_capabilities(server_name)
        return result
    
    async def close(self):
        """Close the MCP client and cleanup resources"""
        if self.session:
            await self.session.close()
        self._initialized = False

# Global MCP client instance
mcp_client = MCPClient()