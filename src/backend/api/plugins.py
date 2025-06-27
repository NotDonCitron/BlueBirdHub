"""
Plugin Management API Endpoints

REST API endpoints for plugin management, configuration, and monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.security import HTTPBearer
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import tempfile
import shutil
from pathlib import Path

from ..core.plugins import (
    PluginManager, PluginRegistry, PluginMarketplace, PluginLifecycleManager,
    PluginPermissionManager, PluginAnalyticsManager, PluginConfigManager
)
from ..core.plugins.base import PluginMetadata, PluginStatus, PluginType
from ..core.plugins.config import ConfigScope
from ..core.plugins.permissions import PermissionScope, ResourceType, PermissionType
from ..schemas.validation import validate_plugin_data


router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])
security = HTTPBearer()


# Dependency injection for plugin components
async def get_plugin_manager():
    """Get plugin manager instance"""
    # This would be injected from the main application
    return PluginManager()


async def get_current_user(token: str = Depends(security)):
    """Get current authenticated user"""
    # This would validate the token and return user info
    return {"id": "user123", "name": "Test User", "role": "admin"}


# Plugin Management Endpoints

@router.get("/")
async def list_plugins(
    status: Optional[PluginStatus] = None,
    plugin_type: Optional[PluginType] = None,
    category: Optional[str] = None,
    manager: PluginManager = Depends(get_plugin_manager)
):
    """List all plugins with optional filtering"""
    try:
        plugins = await manager.registry.list_plugins(status, plugin_type, category)
        
        result = []
        for plugin in plugins:
            plugin_data = plugin.dict()
            plugin_data["status"] = await manager.registry.get_plugin_status(plugin.id)
            plugin_data["health"] = await manager.get_plugin_health(plugin.id)
            result.append(plugin_data)
        
        return {
            "plugins": result,
            "total": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_id}")
async def get_plugin(
    plugin_id: str,
    manager: PluginManager = Depends(get_plugin_manager)
):
    """Get detailed plugin information"""
    try:
        plugin = await manager.registry.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")
        
        plugin_data = plugin.dict()
        plugin_data["status"] = await manager.registry.get_plugin_status(plugin_id)
        plugin_data["health"] = await manager.get_plugin_health(plugin_id)
        plugin_data["stats"] = await manager.registry.get_plugin_stats(plugin_id)
        
        return plugin_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_id}/activate")
async def activate_plugin(
    plugin_id: str,
    background_tasks: BackgroundTasks,
    manager: PluginManager = Depends(get_plugin_manager),
    user = Depends(get_current_user)
):
    """Activate a plugin"""
    try:
        # Check if user has permission
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        success = await manager.activate_plugin(plugin_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to activate plugin")
        
        return {"message": f"Plugin {plugin_id} activated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_id}/deactivate")
async def deactivate_plugin(
    plugin_id: str,
    manager: PluginManager = Depends(get_plugin_manager),
    user = Depends(get_current_user)
):
    """Deactivate a plugin"""
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        success = await manager.deactivate_plugin(plugin_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to deactivate plugin")
        
        return {"message": f"Plugin {plugin_id} deactivated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_id}/reload")
async def reload_plugin(
    plugin_id: str,
    manager: PluginManager = Depends(get_plugin_manager),
    user = Depends(get_current_user)
):
    """Reload a plugin"""
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        success = await manager.reload_plugin(plugin_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to reload plugin")
        
        return {"message": f"Plugin {plugin_id} reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{plugin_id}")
async def uninstall_plugin(
    plugin_id: str,
    remove_data: bool = False,
    manager: PluginManager = Depends(get_plugin_manager),
    user = Depends(get_current_user)
):
    """Uninstall a plugin"""
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        lifecycle = PluginLifecycleManager(manager.registry, None)
        success = await lifecycle.uninstall_plugin(plugin_id, remove_data=remove_data)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to uninstall plugin")
        
        return {"message": f"Plugin {plugin_id} uninstalled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Marketplace Endpoints

@router.get("/marketplace/search")
async def search_marketplace(
    query: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    sort_by: str = "relevance",
    limit: int = 50,
    manager: PluginManager = Depends(get_plugin_manager)
):
    """Search plugins in marketplace"""
    try:
        marketplace = PluginMarketplace(manager.registry)
        
        tag_list = tags.split(",") if tags else None
        
        async with marketplace:
            results = await marketplace.search_plugins(
                query, category, tag_list, sort_by, limit
            )
        
        return {
            "plugins": [entry.__dict__ for entry in results],
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/install")
async def install_from_marketplace(
    plugin_id: str,
    version: Optional[str] = None,
    repository: Optional[str] = None,
    background_tasks: BackgroundTasks,
    manager: PluginManager = Depends(get_plugin_manager),
    user = Depends(get_current_user)
):
    """Install a plugin from marketplace"""
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        marketplace = PluginMarketplace(manager.registry)
        
        async with marketplace:
            success = await marketplace.install_plugin(plugin_id, version, repository)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to install plugin")
        
        return {"message": f"Plugin {plugin_id} installed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace/update/{plugin_id}")
async def update_plugin(
    plugin_id: str,
    target_version: Optional[str] = None,
    background_tasks: BackgroundTasks,
    manager: PluginManager = Depends(get_plugin_manager),
    user = Depends(get_current_user)
):
    """Update a plugin from marketplace"""
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        lifecycle = PluginLifecycleManager(manager.registry, None)
        result = await lifecycle.update_plugin(plugin_id, target_version)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=f"Update failed: {result.errors}")
        
        return {"message": f"Plugin {plugin_id} updated successfully to v{result.version}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketplace/updates")
async def check_updates(
    manager: PluginManager = Depends(get_plugin_manager)
):
    """Check for available plugin updates"""
    try:
        marketplace = PluginMarketplace(manager.registry)
        
        async with marketplace:
            updates = await marketplace.check_updates()
        
        return {"updates": updates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Configuration Endpoints

@router.get("/{plugin_id}/config")
async def get_plugin_config(
    plugin_id: str,
    workspace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    manager: PluginManager = Depends(get_plugin_manager)
):
    """Get plugin configuration"""
    try:
        config_manager = PluginConfigManager()
        
        if workspace_id or user_id:
            config = await config_manager.get_effective_config(plugin_id, workspace_id, user_id)
        else:
            config = await config_manager.get_config(plugin_id)
        
        return {"config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_id}/config")
async def update_plugin_config(
    plugin_id: str,
    config: Dict[str, Any],
    scope: ConfigScope = ConfigScope.PLUGIN,
    scope_id: str = "default",
    manager: PluginManager = Depends(get_plugin_manager),
    user = Depends(get_current_user)
):
    """Update plugin configuration"""
    try:
        config_manager = PluginConfigManager()
        
        # Validate configuration
        validated_config = await config_manager.validate_config(plugin_id, config)
        
        # Set each configuration value
        for key, value in validated_config.items():
            await config_manager.set_config(plugin_id, key, value, scope, scope_id, user["id"])
        
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_id}/config/schema")
async def get_config_schema(
    plugin_id: str,
    manager: PluginManager = Depends(get_plugin_manager)
):
    """Get plugin configuration schema"""
    try:
        config_manager = PluginConfigManager()
        schema = await config_manager.get_config_schema(plugin_id)
        
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Permission Endpoints

@router.get("/{plugin_id}/permissions")
async def get_plugin_permissions(
    plugin_id: str,
    manager: PluginManager = Depends(get_plugin_manager)
):
    """Get plugin permissions"""
    try:
        permission_manager = PluginPermissionManager()
        permissions = await permission_manager.list_plugin_permissions(plugin_id)
        
        return {"permissions": permissions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_id}/permissions/{permission_id}/grant")
async def grant_permission(
    plugin_id: str,
    permission_id: str,
    scope_value: Optional[str] = None,
    manager: PluginManager = Depends(get_plugin_manager),
    user = Depends(get_current_user)
):
    """Grant a permission to a plugin"""
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        permission_manager = PluginPermissionManager()
        grant_id = await permission_manager.grant_permission(
            plugin_id, permission_id, scope_value, user["id"]
        )
        
        return {"message": "Permission granted", "grant_id": grant_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_id}/permissions/{permission_id}/revoke")
async def revoke_permission(
    plugin_id: str,
    permission_id: str,
    scope_value: Optional[str] = None,
    manager: PluginManager = Depends(get_plugin_manager),
    user = Depends(get_current_user)
):
    """Revoke a permission from a plugin"""
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        permission_manager = PluginPermissionManager()
        success = await permission_manager.revoke_permission(
            plugin_id, permission_id, scope_value, user["id"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Permission not found")
        
        return {"message": "Permission revoked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Endpoints

@router.get("/{plugin_id}/analytics")
async def get_plugin_analytics(
    plugin_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    manager: PluginManager = Depends(get_plugin_manager)
):
    """Get plugin analytics and statistics"""
    try:
        analytics = PluginAnalyticsManager()
        stats = await analytics.get_plugin_stats(plugin_id, start_date, end_date)
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/overview")
async def get_system_analytics(
    manager: PluginManager = Depends(get_plugin_manager)
):
    """Get system-wide plugin analytics"""
    try:
        analytics = PluginAnalyticsManager()
        overview = await analytics.get_system_overview()
        
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/alerts")
async def get_alerts(
    plugin_id: Optional[str] = None,
    resolved: Optional[bool] = None,
    manager: PluginManager = Depends(get_plugin_manager)
):
    """Get system alerts"""
    try:
        analytics = PluginAnalyticsManager()
        alerts = await analytics.get_alerts(plugin_id, resolved)
        
        return {"alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    manager: PluginManager = Depends(get_plugin_manager),
    user = Depends(get_current_user)
):
    """Resolve a system alert"""
    try:
        analytics = PluginAnalyticsManager()
        success = await analytics.resolve_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": "Alert resolved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Upload and Installation Endpoints

@router.post("/upload")
async def upload_plugin(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    manager: PluginManager = Depends(get_plugin_manager),
    user = Depends(get_current_user)
):
    """Upload and install a plugin package"""
    try:
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        try:
            # Validate package
            security = manager.security
            validation_result = security.validate_plugin_package(temp_path)
            
            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Package validation failed: {validation_result['violations']}"
                )
            
            # Extract and install
            lifecycle = PluginLifecycleManager(manager.registry, None)
            
            # This would need to be implemented with proper package extraction
            # and metadata loading from the uploaded file
            
            return {
                "message": "Plugin uploaded and validation passed",
                "checksum": validation_result["checksum"],
                "warnings": validation_result["warnings"]
            }
            
        finally:
            # Clean up temp file
            Path(temp_path).unlink()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Development and Testing Endpoints

@router.post("/validate")
async def validate_plugin_manifest(
    manifest: Dict[str, Any]
):
    """Validate a plugin manifest"""
    try:
        errors = validate_plugin_data(manifest)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{plugin_type}")
async def get_plugin_template(
    plugin_type: PluginType
):
    """Get plugin template for development"""
    try:
        from ..core.plugins.sdk import generate_plugin_template
        
        template = generate_plugin_template(plugin_type)
        
        return {
            "plugin_type": plugin_type.value,
            "template": template
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health and Status Endpoints

@router.get("/health")
async def get_system_health(
    manager: PluginManager = Depends(get_plugin_manager)
):
    """Get plugin system health status"""
    try:
        active_plugins = await manager.list_active_plugins()
        
        health_data = {
            "status": "healthy",
            "active_plugins": len(active_plugins),
            "total_plugins": len(await manager.registry.list_plugins()),
            "plugin_health": {}
        }
        
        for plugin_id in active_plugins:
            health = await manager.get_plugin_health(plugin_id)
            if health:
                health_data["plugin_health"][plugin_id] = health
        
        return health_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_system_stats(
    manager: PluginManager = Depends(get_plugin_manager)
):
    """Get plugin system statistics"""
    try:
        stats = {
            "event_system": manager.event_system.get_statistics(),
            "communication_bus": manager.communication_bus.get_statistics() if hasattr(manager, 'communication_bus') else {},
            "plugins": {}
        }
        
        plugins = await manager.registry.list_plugins()
        for plugin in plugins:
            plugin_stats = await manager.registry.get_plugin_stats(plugin.id)
            stats["plugins"][plugin.id] = plugin_stats
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))