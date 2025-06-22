"""
MCP (Model Context Protocol) Integration API
Provides endpoints for AI agents to access external data sources
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from ..database import get_db
from ..dependencies.auth import get_current_active_user
from ..models.user import User
from ..services.mcp_client import mcp_client
from loguru import logger

router = APIRouter(prefix="/api/mcp", tags=["mcp-integration"])

# Pydantic Models
class MCPServerInfo(BaseModel):
    name: str
    description: str
    capabilities: List[str]
    resources_count: int
    tools_count: int

class MCPResourceRequest(BaseModel):
    server_name: str = Field(..., description="Name of the MCP server")
    uri: str = Field(..., description="Resource URI to read")

class MCPToolRequest(BaseModel):
    server_name: str = Field(..., description="Name of the MCP server")
    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")

class MCPResourceResponse(BaseModel):
    uri: str
    content: Dict[str, Any]
    server_name: str

class MCPToolResponse(BaseModel):
    server_name: str
    tool_name: str
    result: Dict[str, Any]
    success: bool

@router.on_event("startup")
async def initialize_mcp():
    """Initialize MCP client on startup"""
    try:
        await mcp_client.initialize()
        logger.info("MCP client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MCP client: {e}")

@router.on_event("shutdown")
async def cleanup_mcp():
    """Cleanup MCP client on shutdown"""
    try:
        await mcp_client.close()
        logger.info("MCP client closed successfully")
    except Exception as e:
        logger.error(f"Failed to close MCP client: {e}")

@router.get("/servers", response_model=Dict[str, MCPServerInfo])
async def list_mcp_servers(
    current_user: User = Depends(get_current_active_user)
):
    """
    List all available MCP servers and their capabilities
    """
    try:
        servers = await mcp_client.list_all_servers()
        return servers
    except Exception as e:
        logger.error(f"Failed to list MCP servers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list servers: {str(e)}")

@router.get("/servers/{server_name}/resources")
async def list_server_resources(
    server_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    List available resources from a specific MCP server
    """
    try:
        resources = await mcp_client.list_resources(server_name)
        return {
            "server_name": server_name,
            "resources": [resource.dict() for resource in resources]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list resources for {server_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list resources: {str(e)}")

@router.get("/servers/{server_name}/tools")
async def list_server_tools(
    server_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    List available tools from a specific MCP server
    """
    try:
        tools = await mcp_client.list_tools(server_name)
        return {
            "server_name": server_name,
            "tools": [tool.dict() for tool in tools]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list tools for {server_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@router.post("/resource/read", response_model=MCPResourceResponse)
async def read_mcp_resource(
    request: MCPResourceRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Read a resource from an MCP server
    """
    try:
        content = await mcp_client.read_resource(request.server_name, request.uri)
        return MCPResourceResponse(
            uri=request.uri,
            content=content,
            server_name=request.server_name
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to read resource {request.uri} from {request.server_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read resource: {str(e)}")

@router.post("/tool/call", response_model=MCPToolResponse)
async def call_mcp_tool(
    request: MCPToolRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Call a tool on an MCP server
    """
    try:
        result = await mcp_client.call_tool(
            request.server_name,
            request.tool_name,
            request.arguments
        )
        
        return MCPToolResponse(
            server_name=request.server_name,
            tool_name=request.tool_name,
            result=result,
            success=True
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to call tool {request.tool_name} on {request.server_name}: {e}")
        return MCPToolResponse(
            server_name=request.server_name,
            tool_name=request.tool_name,
            result={"error": str(e)},
            success=False
        )

@router.get("/capabilities")
async def get_mcp_capabilities():
    """
    Get overall MCP integration capabilities
    """
    try:
        servers = await mcp_client.list_all_servers()
        
        total_resources = sum(server["resources_count"] for server in servers.values())
        total_tools = sum(server["tools_count"] for server in servers.values())
        
        return {
            "mcp_enabled": True,
            "servers_available": len(servers),
            "total_resources": total_resources,
            "total_tools": total_tools,
            "supported_protocols": ["file://", "sqlite://", "http://", "https://"],
            "servers": servers
        }
    except Exception as e:
        logger.error(f"Failed to get MCP capabilities: {e}")
        return {
            "mcp_enabled": False,
            "error": str(e),
            "servers_available": 0,
            "total_resources": 0,
            "total_tools": 0
        }

# AI Agent Helper Endpoints

@router.post("/ai/context/workspace")
async def get_workspace_context(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive workspace context for AI agents using MCP
    """
    try:
        # Get workspace data via MCP database tool
        workspace_result = await mcp_client.call_tool(
            "database",
            "query_workspaces",
            {"user_id": current_user.id}
        )
        
        # Get tasks data via MCP
        tasks_result = await mcp_client.call_tool(
            "database",
            "query_tasks",
            {"workspace_id": workspace_id}
        )
        
        # Get file listing via MCP filesystem tool
        try:
            files_result = await mcp_client.call_tool(
                "filesystem",
                "list_directory",
                {"path": "./data"}
            )
        except Exception:
            files_result = {"success": False, "files": []}
        
        return {
            "workspace_id": workspace_id,
            "context": {
                "workspaces": workspace_result.get("workspaces", []),
                "tasks": tasks_result.get("tasks", []),
                "files": files_result.get("files", []),
                "user_id": current_user.id
            },
            "mcp_sources": ["database", "filesystem"],
            "timestamp": "2025-06-22T15:50:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get workspace context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")

@router.post("/ai/search")
async def ai_search_with_mcp(
    query: str,
    include_web: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform comprehensive search using multiple MCP sources
    """
    try:
        results = {
            "query": query,
            "sources": {},
            "timestamp": "2025-06-22T15:50:00Z"
        }
        
        # Search local files
        try:
            file_search = await mcp_client.call_tool(
                "filesystem",
                "list_directory",
                {"path": "./data"}
            )
            # Filter files that might match the query
            matching_files = [
                f for f in file_search.get("files", [])
                if query.lower() in f.get("name", "").lower()
            ]
            results["sources"]["local_files"] = matching_files
        except Exception as e:
            logger.warning(f"Local file search failed: {e}")
            results["sources"]["local_files"] = []
        
        # Search web if requested
        if include_web:
            try:
                web_search = await mcp_client.call_tool(
                    "web_search",
                    "search_web",
                    {"query": query, "count": 5}
                )
                results["sources"]["web"] = web_search.get("results", [])
            except Exception as e:
                logger.warning(f"Web search failed: {e}")
                results["sources"]["web"] = []
        
        return results
        
    except Exception as e:
        logger.error(f"AI search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/status")
async def get_mcp_status():
    """
    Get current status of MCP integration
    """
    try:
        # Test connection to each server
        server_status = {}
        for server_name in ["filesystem", "database", "web_search"]:
            try:
                capabilities = await mcp_client.get_server_capabilities(server_name)
                server_status[server_name] = {
                    "status": "available",
                    "capabilities": capabilities
                }
            except Exception as e:
                server_status[server_name] = {
                    "status": "unavailable",
                    "error": str(e)
                }
        
        overall_status = "healthy" if any(
            s["status"] == "available" for s in server_status.values()
        ) else "degraded"
        
        return {
            "overall_status": overall_status,
            "servers": server_status,
            "timestamp": "2025-06-22T15:50:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get MCP status: {e}")
        return {
            "overall_status": "error",
            "error": str(e),
            "servers": {},
            "timestamp": "2025-06-22T15:50:00Z"
        }