"""
FastAPI MCP Client for OrdnungsHub
Connects FastAPI backend to SQLite MCP Server for analytics and database operations
"""

import asyncio
import json
import subprocess
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import signal
import os

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Client for communicating with MCP (Model Context Protocol) servers
    Specifically designed for OrdnungsHub SQLite MCP Server integration
    """
    
    def __init__(self, server_config: Dict[str, Any]):
        self.server_config = server_config
        self.process = None
        self.is_connected = False
        self.request_id_counter = 0
        
        # MCP Server configuration
        self.server_command = server_config.get('command', 'node')
        self.server_args = server_config.get('args', [])
        self.server_cwd = server_config.get('cwd', '.')
        self.server_env = server_config.get('env', {})
        
        # Communication settings
        self.timeout = server_config.get('timeout', 30.0)
        self.retry_attempts = server_config.get('retry_attempts', 3)
        
        # Available tools
        self.available_tools = []
        
    async def connect(self) -> bool:
        """Connect to the MCP server"""
        try:
            logger.info(f"Starting MCP server: {self.server_command} {' '.join(self.server_args)}")
            
            # Prepare environment
            env = os.environ.copy()
            env.update(self.server_env)
            
            # Start MCP server process
            self.process = await asyncio.create_subprocess_exec(
                self.server_command,
                *self.server_args,
                cwd=self.server_cwd,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Initialize MCP connection
            initialization_result = await self._initialize_connection()
            
            if initialization_result:
                self.is_connected = True
                logger.info("MCP server connected successfully")
                
                # Get available tools
                await self._fetch_available_tools()
                return True
            else:
                logger.error("Failed to initialize MCP connection")
                await self.disconnect()
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            await self.disconnect()
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server: {e}")
            finally:
                self.process = None
                self.is_connected = False
                logger.info("MCP server disconnected")
    
    async def _initialize_connection(self) -> bool:
        """Initialize the MCP connection with handshake"""
        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "ordnungshub-fastapi",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self._send_request(init_request)
            
            if response and response.get("result"):
                logger.info("MCP initialization successful")
                
                # Send initialized notification
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                
                await self._send_notification(initialized_notification)
                return True
            else:
                logger.error("MCP initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"MCP initialization error: {e}")
            return False
    
    async def _fetch_available_tools(self):
        """Fetch list of available tools from MCP server"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "tools/list"
            }
            
            response = await self._send_request(request)
            
            if response and response.get("result") and "tools" in response["result"]:
                self.available_tools = response["result"]["tools"]
                tool_names = [tool["name"] for tool in self.available_tools]
                logger.info(f"Available MCP tools: {tool_names}")
            else:
                logger.warning("No tools received from MCP server")
                
        except Exception as e:
            logger.error(f"Failed to fetch available tools: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on the MCP server"""
        if not self.is_connected:
            raise Exception("MCP client not connected")
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = await self._send_request(request)
            
            if response and response.get("result"):
                return response["result"]
            elif response and response.get("error"):
                raise Exception(f"MCP tool error: {response['error']}")
            else:
                raise Exception("Invalid response from MCP server")
                
        except Exception as e:
            logger.error(f"MCP tool call failed ({tool_name}): {e}")
            raise
    
    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a request to the MCP server and wait for response"""
        if not self.process or not self.process.stdin:
            raise Exception("MCP server process not available")
        
        try:
            # Send request
            request_json = json.dumps(request) + '\n'
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            
            # Read response
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(), 
                timeout=self.timeout
            )
            
            if response_line:
                response = json.loads(response_line.decode().strip())
                return response
            else:
                raise Exception("No response from MCP server")
                
        except asyncio.TimeoutError:
            raise Exception(f"MCP request timeout after {self.timeout}s")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from MCP server: {e}")
        except Exception as e:
            raise Exception(f"MCP communication error: {e}")
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send a notification to the MCP server (no response expected)"""
        if not self.process or not self.process.stdin:
            raise Exception("MCP server process not available")
        
        try:
            notification_json = json.dumps(notification) + '\n'
            self.process.stdin.write(notification_json.encode())
            await self.process.stdin.drain()
            
        except Exception as e:
            logger.error(f"Failed to send MCP notification: {e}")
            raise
    
    def _get_request_id(self) -> int:
        """Generate unique request ID"""
        self.request_id_counter += 1
        return self.request_id_counter
    
    # High-level tool methods for OrdnungsHub
    
    async def query_database(self, query: str, params: List[Any] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query on the database"""
        arguments = {"query": query}
        if params:
            arguments["params"] = params
        
        result = await self.call_tool("query_database", arguments)
        
        # Parse the response
        if "content" in result and result["content"]:
            content = result["content"][0]
            if content["type"] == "text":
                return json.loads(content["text"])
        
        return []
    
    async def execute_database(self, query: str, params: List[Any] = None) -> Dict[str, Any]:
        """Execute an INSERT/UPDATE/DELETE query"""
        arguments = {"query": query}
        if params:
            arguments["params"] = params
        
        result = await self.call_tool("execute_database", arguments)
        
        # Parse the response
        if "content" in result and result["content"]:
            content = result["content"][0]
            if content["type"] == "text":
                return json.loads(content["text"])
        
        return {}
    
    async def get_database_schema(self, table: str = None) -> Dict[str, Any]:
        """Get database schema information"""
        arguments = {}
        if table:
            arguments["table"] = table
        
        result = await self.call_tool("get_schema", arguments)
        
        # Parse the response
        if "content" in result and result["content"]:
            content = result["content"][0]
            if content["type"] == "text":
                return json.loads(content["text"])
        
        return {}
    
    async def analyze_file_data(self, workspace_id: str = None, category: str = None) -> Dict[str, Any]:
        """Analyze file organization patterns"""
        arguments = {}
        if workspace_id:
            arguments["workspace_id"] = workspace_id
        if category:
            arguments["category"] = category
        
        result = await self.call_tool("analyze_file_data", arguments)
        
        # Parse the response
        if "content" in result and result["content"]:
            content = result["content"][0]
            if content["type"] == "text":
                return json.loads(content["text"])
        
        return {}
    
    async def get_ai_insights(self, insight_type: str, time_range: str = "30 days") -> Dict[str, Any]:
        """Generate AI insights from database patterns"""
        arguments = {
            "insight_type": insight_type,
            "time_range": time_range
        }
        
        result = await self.call_tool("get_ai_insights", arguments)
        
        # Parse the response
        if "content" in result and result["content"]:
            content = result["content"][0]
            if content["type"] == "text":
                return json.loads(content["text"])
        
        return {}
    
    async def backup_database(self, backup_path: str) -> bool:
        """Create a database backup"""
        arguments = {"backup_path": backup_path}
        
        try:
            result = await self.call_tool("backup_database", arguments)
            
            # Parse the response
            if "content" in result and result["content"]:
                content = result["content"][0]
                if content["type"] == "text":
                    backup_result = json.loads(content["text"])
                    return backup_result.get("success", False)
            
            return False
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MCP server health and connection status"""
        try:
            if not self.is_connected:
                return {
                    "status": "disconnected",
                    "error": "MCP client not connected"
                }
            
            # Try a simple query to test connectivity
            test_result = await self.query_database("SELECT COUNT(*) as count FROM workspaces")
            
            if test_result:
                return {
                    "status": "healthy",
                    "connected": True,
                    "available_tools": len(self.available_tools),
                    "server_responsive": True,
                    "test_query_result": test_result[0] if test_result else None
                }
            else:
                return {
                    "status": "unhealthy",
                    "connected": True,
                    "error": "Server not responding to queries"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "connected": self.is_connected,
                "error": str(e)
            }


# Global MCP client instance
mcp_client = None

async def get_mcp_client() -> MCPClient:
    """Get or create the global MCP client instance"""
    global mcp_client
    
    if mcp_client is None or not mcp_client.is_connected:
        # MCP Server configuration
        server_config = {
            "command": "node",
            "args": ["./mcp-servers/sqlite-server/server.js"],
            "cwd": "/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/95273afa2cf3cfbc67a1caafbc22e8370bc389288e47600bf338dc7dc12dbb26/CascadeProjects/nnewcoededui/worktrees/zen-mcp-integration",
            "env": {
                "ORDNUNGSHUB_DB_PATH": "/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/95273afa2cf3cfbc67a1caafbc22e8370bc389288e47600bf338dc7dc12dbb26/CascadeProjects/nnewcoededui/worktrees/data/ordnungshub.db"
            },
            "timeout": 30.0,
            "retry_attempts": 3
        }
        
        mcp_client = MCPClient(server_config)
        
        # Connect to the server
        if not await mcp_client.connect():
            raise Exception("Failed to connect to MCP server")
    
    return mcp_client

async def cleanup_mcp_client():
    """Cleanup the global MCP client"""
    global mcp_client
    
    if mcp_client:
        await mcp_client.disconnect()
        mcp_client = None