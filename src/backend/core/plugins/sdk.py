"""
Plugin Development SDK

Provides comprehensive SDK for plugin development including
utilities, helpers, and framework components.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
from abc import ABC, abstractmethod
import json
import hashlib
import uuid

from .base import (
    PluginBase, PluginMetadata, PluginType, PluginPriority,
    IntegrationPlugin, UIComponentPlugin, WorkflowPlugin, 
    AIEnhancementPlugin, DataProcessorPlugin
)
from .config import ConfigDefinition, ConfigType, ConfigScope, PluginConfigManager
from .permissions import Permission, PermissionType, ResourceType, PermissionScope
from .event_system import Event, EventPriority, EventScope
from .communication import Message, MessageType, MessagePriority


logger = logging.getLogger(__name__)


class PluginSDK:
    """Main SDK class for plugin development"""
    
    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self.logger = logging.getLogger(f"plugin.{plugin_id}")
        self._config_manager: Optional[PluginConfigManager] = None
        self._event_system = None
        self._communication_bus = None
        self._permission_manager = None
        self._analytics = None
    
    def set_managers(self, config_manager, event_system, communication_bus, 
                    permission_manager, analytics):
        """Set manager instances (called by plugin manager)"""
        self._config_manager = config_manager
        self._event_system = event_system
        self._communication_bus = communication_bus
        self._permission_manager = permission_manager
        self._analytics = analytics
    
    # Configuration API
    async def get_config(self, key: str = None, default: Any = None,
                        workspace_id: str = None, user_id: str = None) -> Any:
        """Get plugin configuration"""
        if not self._config_manager:
            return default
        
        try:
            if workspace_id or user_id:
                config = await self._config_manager.get_effective_config(
                    self.plugin_id, workspace_id, user_id
                )
                if key:
                    return config.get(key, default)
                return config
            else:
                return await self._config_manager.get_config(
                    self.plugin_id, key
                ) or default
        except Exception as e:
            self.logger.error(f"Failed to get config {key}: {e}")
            return default
    
    async def set_config(self, key: str, value: Any, 
                        scope: ConfigScope = ConfigScope.PLUGIN,
                        scope_id: str = "default") -> bool:
        """Set plugin configuration"""
        if not self._config_manager:
            return False
        
        try:
            return await self._config_manager.set_config(
                self.plugin_id, key, value, scope, scope_id, "plugin"
            )
        except Exception as e:
            self.logger.error(f"Failed to set config {key}: {e}")
            return False
    
    # Event System API
    async def emit_event(self, event_type: str, data: Dict[str, Any] = None,
                        target_plugin: str = None, scope: EventScope = EventScope.GLOBAL,
                        priority: EventPriority = EventPriority.NORMAL) -> str:
        """Emit an event"""
        if not self._event_system:
            raise RuntimeError("Event system not available")
        
        return await self._event_system.emit(
            event_type, data, self.plugin_id, target_plugin, scope, priority
        )
    
    def add_event_handler(self, event_type: str, handler: Callable,
                         priority: EventPriority = EventPriority.NORMAL,
                         once: bool = False, conditions: Dict[str, Any] = None) -> str:
        """Add an event handler"""
        if not self._event_system:
            raise RuntimeError("Event system not available")
        
        return self._event_system.add_handler(
            self.plugin_id, event_type, handler, priority, once, conditions
        )
    
    def remove_event_handler(self, handler_id: str) -> bool:
        """Remove an event handler"""
        if not self._event_system:
            return False
        
        return self._event_system.remove_handler(handler_id)
    
    # Communication API
    async def send_message(self, target_plugin: str, data: Dict[str, Any],
                          message_type: MessageType = MessageType.NOTIFICATION,
                          priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Send a message to another plugin"""
        if not self._communication_bus:
            raise RuntimeError("Communication bus not available")
        
        return await self._communication_bus.send_message(
            self.plugin_id, target_plugin, data, message_type, priority
        )
    
    async def call_rpc(self, target_plugin: str, method: str, *args, 
                      timeout: float = 30.0, **kwargs) -> Any:
        """Make an RPC call to another plugin"""
        if not self._communication_bus:
            raise RuntimeError("Communication bus not available")
        
        return await self._communication_bus.call_rpc(
            self.plugin_id, target_plugin, method, *args, timeout=timeout, **kwargs
        )
    
    async def broadcast_message(self, data: Dict[str, Any],
                              exclude: List[str] = None,
                              priority: MessagePriority = MessagePriority.NORMAL) -> List[str]:
        """Broadcast a message to all plugins"""
        if not self._communication_bus:
            raise RuntimeError("Communication bus not available")
        
        return await self._communication_bus.broadcast_message(
            self.plugin_id, data, set(exclude or []), priority
        )
    
    # Permission API
    async def check_permission(self, permission_id: str, resource_path: str = "",
                             context: Dict[str, Any] = None) -> bool:
        """Check if plugin has a permission"""
        if not self._permission_manager:
            return False
        
        return await self._permission_manager.check_permission(
            self.plugin_id, permission_id, resource_path, context=context
        )
    
    async def request_permission(self, permission_id: str, reason: str = "") -> bool:
        """Request a permission (for interactive approval)"""
        # This would trigger a permission request flow
        self.logger.info(f"Permission request: {permission_id} - {reason}")
        return False  # Placeholder
    
    # Analytics API
    async def track_feature_usage(self, feature: str, user_id: str = None):
        """Track feature usage"""
        if self._analytics:
            await self._analytics.track_feature_usage(self.plugin_id, feature, user_id)
    
    async def track_error(self, error_type: str, error_message: str,
                         context: Dict[str, Any] = None):
        """Track an error"""
        if self._analytics:
            await self._analytics.track_error(self.plugin_id, error_type, error_message, context)
    
    async def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a custom metric"""
        if self._analytics:
            from .analytics import MetricType
            await self._analytics.record_metric(
                name, value, MetricType.GAUGE, self.plugin_id, tags
            )
    
    # Utility Methods
    def create_id(self) -> str:
        """Create a unique ID"""
        return str(uuid.uuid4())
    
    def hash_data(self, data: str) -> str:
        """Create a hash of data"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_timestamp(self) -> datetime:
        """Get current timestamp"""
        return datetime.utcnow()
    
    async def schedule_task(self, coro, delay: float = 0):
        """Schedule an async task"""
        if delay > 0:
            await asyncio.sleep(delay)
        return await coro
    
    def validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate data against JSON schema"""
        try:
            import jsonschema
            jsonschema.validate(data, schema)
            return True
        except:
            return False


class PluginBuilder:
    """Builder class for creating plugin metadata and configurations"""
    
    def __init__(self, plugin_id: str, name: str):
        self.metadata = PluginMetadata(
            id=plugin_id,
            name=name,
            version="1.0.0",
            description="",
            author="",
            plugin_type=PluginType.INTEGRATION,
            entry_point="Plugin",
            module_path="plugin",
            bluebirdHub_version=">=1.0.0",
            python_version=">=3.8"
        )
        self.config_definitions: List[ConfigDefinition] = []
        self.permissions: List[Permission] = []
    
    def version(self, version: str) -> 'PluginBuilder':
        """Set plugin version"""
        self.metadata.version = version
        return self
    
    def description(self, description: str) -> 'PluginBuilder':
        """Set plugin description"""
        self.metadata.description = description
        return self
    
    def author(self, author: str, email: str = None) -> 'PluginBuilder':
        """Set plugin author"""
        self.metadata.author = author
        if email:
            self.metadata.author_email = email
        return self
    
    def type(self, plugin_type: PluginType) -> 'PluginBuilder':
        """Set plugin type"""
        self.metadata.plugin_type = plugin_type
        return self
    
    def entry_point(self, entry_point: str, module_path: str = None) -> 'PluginBuilder':
        """Set plugin entry point"""
        self.metadata.entry_point = entry_point
        if module_path:
            self.metadata.module_path = module_path
        return self
    
    def priority(self, priority: PluginPriority) -> 'PluginBuilder':
        """Set plugin priority"""
        self.metadata.priority = priority
        return self
    
    def auto_start(self, auto_start: bool = True) -> 'PluginBuilder':
        """Set auto-start behavior"""
        self.metadata.auto_start = auto_start
        return self
    
    def sandbox(self, sandbox_mode: bool = True) -> 'PluginBuilder':
        """Set sandbox mode"""
        self.metadata.sandbox_mode = sandbox_mode
        return self
    
    def category(self, category: str) -> 'PluginBuilder':
        """Set plugin category"""
        self.metadata.category = category
        return self
    
    def tags(self, *tags: str) -> 'PluginBuilder':
        """Add tags"""
        self.metadata.tags.extend(tags)
        return self
    
    def homepage(self, url: str) -> 'PluginBuilder':
        """Set homepage URL"""
        self.metadata.homepage = url
        return self
    
    def repository(self, url: str) -> 'PluginBuilder':
        """Set repository URL"""
        self.metadata.repository = url
        return self
    
    def requires_bluebirdHub(self, version: str) -> 'PluginBuilder':
        """Set required BlueBirdHub version"""
        self.metadata.bluebirdHub_version = version
        return self
    
    def requires_python(self, version: str) -> 'PluginBuilder':
        """Set required Python version"""
        self.metadata.python_version = version
        return self
    
    def add_config(self, key: str, config_type: ConfigType, description: str,
                  default_value: Any = None, required: bool = False,
                  secret: bool = False, choices: List[Any] = None,
                  min_value: Union[int, float] = None,
                  max_value: Union[int, float] = None,
                  pattern: str = None, category: str = "general") -> 'PluginBuilder':
        """Add a configuration definition"""
        config_def = ConfigDefinition(
            key=key,
            config_type=config_type,
            description=description,
            default_value=default_value,
            required=required,
            secret=secret,
            choices=choices,
            min_value=min_value,
            max_value=max_value,
            pattern=pattern,
            category=category
        )
        self.config_definitions.append(config_def)
        return self
    
    def add_permission(self, permission_id: str, description: str,
                      resource_type: ResourceType, permission_type: PermissionType,
                      scope: PermissionScope = PermissionScope.PLUGIN,
                      required: bool = False) -> 'PluginBuilder':
        """Add a permission requirement"""
        from .base import PluginPermission
        permission = PluginPermission(
            permission=permission_id,
            scope=scope.value,
            description=description,
            required=required
        )
        self.metadata.permissions.append(permission)
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the plugin manifest"""
        return {
            "metadata": self.metadata,
            "config_definitions": self.config_definitions,
            "permissions": self.permissions
        }


class APIHelper:
    """Helper for making API calls"""
    
    def __init__(self, sdk: PluginSDK):
        self.sdk = sdk
    
    async def get(self, url: str, headers: Dict[str, str] = None,
                 params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make GET request"""
        # Check network permission
        if not await self.sdk.check_permission("net.http"):
            raise PermissionError("Network access not permitted")
        
        # Implementation would use aiohttp or similar
        return {"status": "success", "data": {}}
    
    async def post(self, url: str, data: Dict[str, Any] = None,
                  headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Make POST request"""
        if not await self.sdk.check_permission("net.http"):
            raise PermissionError("Network access not permitted")
        
        return {"status": "success", "data": {}}


class DatabaseHelper:
    """Helper for database operations"""
    
    def __init__(self, sdk: PluginSDK):
        self.sdk = sdk
    
    async def query(self, sql: str, params: List[Any] = None) -> List[Dict[str, Any]]:
        """Execute a database query"""
        if not await self.sdk.check_permission("db.read"):
            raise PermissionError("Database read access not permitted")
        
        # Implementation would use actual database connection
        return []
    
    async def execute(self, sql: str, params: List[Any] = None) -> int:
        """Execute a database command"""
        if not await self.sdk.check_permission("db.write"):
            raise PermissionError("Database write access not permitted")
        
        return 0


class FileHelper:
    """Helper for file operations"""
    
    def __init__(self, sdk: PluginSDK):
        self.sdk = sdk
    
    async def read_file(self, file_path: str) -> str:
        """Read file contents"""
        if not await self.sdk.check_permission("fs.read", file_path):
            raise PermissionError("File read access not permitted")
        
        # Implementation would read actual file
        return ""
    
    async def write_file(self, file_path: str, content: str) -> bool:
        """Write file contents"""
        if not await self.sdk.check_permission("fs.write", file_path):
            raise PermissionError("File write access not permitted")
        
        return True


class WorkspaceHelper:
    """Helper for workspace operations"""
    
    def __init__(self, sdk: PluginSDK):
        self.sdk = sdk
    
    async def get_workspace_data(self, workspace_id: str) -> Dict[str, Any]:
        """Get workspace data"""
        if not await self.sdk.check_permission("workspace.read", context={"workspace_id": workspace_id}):
            raise PermissionError("Workspace read access not permitted")
        
        return {}
    
    async def update_workspace_data(self, workspace_id: str, data: Dict[str, Any]) -> bool:
        """Update workspace data"""
        if not await self.sdk.check_permission("workspace.write", context={"workspace_id": workspace_id}):
            raise PermissionError("Workspace write access not permitted")
        
        return True


class TaskHelper:
    """Helper for task operations"""
    
    def __init__(self, sdk: PluginSDK):
        self.sdk = sdk
    
    async def create_task(self, title: str, description: str = "", 
                         workspace_id: str = None) -> str:
        """Create a new task"""
        task_data = {
            "title": title,
            "description": description,
            "workspace_id": workspace_id,
            "created_by": self.sdk.plugin_id
        }
        
        # Emit task creation event
        await self.sdk.emit_event("task.created", task_data)
        
        return self.sdk.create_id()


# Template classes for common plugin types

class BaseIntegrationPlugin(IntegrationPlugin):
    """Base class for integration plugins with SDK support"""
    
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.sdk = PluginSDK(metadata.id)
        self.api = APIHelper(self.sdk)
    
    async def setup_sdk(self, managers):
        """Setup SDK with manager instances"""
        self.sdk.set_managers(*managers)


class BaseUIPlugin(UIComponentPlugin):
    """Base class for UI plugins with SDK support"""
    
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.sdk = PluginSDK(metadata.id)
    
    async def setup_sdk(self, managers):
        """Setup SDK with manager instances"""
        self.sdk.set_managers(*managers)


class BaseWorkflowPlugin(WorkflowPlugin):
    """Base class for workflow plugins with SDK support"""
    
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.sdk = PluginSDK(metadata.id)
        self.tasks = TaskHelper(self.sdk)
        self.workspace = WorkspaceHelper(self.sdk)
    
    async def setup_sdk(self, managers):
        """Setup SDK with manager instances"""
        self.sdk.set_managers(*managers)


class BaseAIPlugin(AIEnhancementPlugin):
    """Base class for AI plugins with SDK support"""
    
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.sdk = PluginSDK(metadata.id)
        self.api = APIHelper(self.sdk)
    
    async def setup_sdk(self, managers):
        """Setup SDK with manager instances"""
        self.sdk.set_managers(*managers)


class BaseDataPlugin(DataProcessorPlugin):
    """Base class for data processing plugins with SDK support"""
    
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.sdk = PluginSDK(metadata.id)
        self.files = FileHelper(self.sdk)
        self.database = DatabaseHelper(self.sdk)
    
    async def setup_sdk(self, managers):
        """Setup SDK with manager instances"""
        self.sdk.set_managers(*managers)


# Utility functions for plugin development

def create_plugin_builder(plugin_id: str, name: str) -> PluginBuilder:
    """Create a new plugin builder"""
    return PluginBuilder(plugin_id, name)


def validate_plugin_manifest(manifest: Dict[str, Any]) -> List[str]:
    """Validate plugin manifest and return list of errors"""
    errors = []
    
    if "metadata" not in manifest:
        errors.append("Missing metadata section")
        return errors
    
    metadata = manifest["metadata"]
    
    # Required fields
    required_fields = ["id", "name", "version", "description", "author", 
                      "plugin_type", "entry_point", "module_path"]
    
    for field in required_fields:
        if field not in metadata:
            errors.append(f"Missing required field: {field}")
    
    # Version validation
    if "version" in metadata:
        try:
            import semver
            semver.VersionInfo.parse(metadata["version"])
        except:
            errors.append("Invalid version format (must be semver)")
    
    return errors


def generate_plugin_template(plugin_type: PluginType) -> str:
    """Generate a plugin template based on type"""
    templates = {
        PluginType.INTEGRATION: """
from bluebirdhub.plugins.sdk import BaseIntegrationPlugin, PluginBuilder, ConfigType

# Plugin configuration
builder = PluginBuilder("my-integration", "My Integration")
builder.version("1.0.0")
builder.description("Integration with external service")
builder.author("Your Name", "your.email@example.com")
builder.type(PluginType.INTEGRATION)
builder.add_config("api_key", ConfigType.STRING, "API Key", required=True, secret=True)
builder.add_config("base_url", ConfigType.STRING, "Base URL", default_value="https://api.example.com")

class MyIntegrationPlugin(BaseIntegrationPlugin):
    async def authenticate(self) -> bool:
        api_key = await self.sdk.get_config("api_key")
        # Implement authentication logic
        return True
    
    async def sync_data(self) -> bool:
        # Implement data synchronization
        return True
""",
        PluginType.UI_COMPONENT: """
from bluebirdhub.plugins.sdk import BaseUIPlugin, PluginBuilder

# Plugin configuration
builder = PluginBuilder("my-ui-component", "My UI Component")
builder.version("1.0.0")
builder.description("Custom UI component")
builder.author("Your Name", "your.email@example.com")
builder.type(PluginType.UI_COMPONENT)

class MyUIPlugin(BaseUIPlugin):
    def get_components(self) -> Dict[str, Any]:
        return {
            "MyComponent": {
                "type": "react",
                "props": ["title", "data"],
                "events": ["onClick", "onLoad"]
            }
        }
""",
        PluginType.WORKFLOW: """
from bluebirdhub.plugins.sdk import BaseWorkflowPlugin, PluginBuilder

# Plugin configuration
builder = PluginBuilder("my-workflow", "My Workflow")
builder.version("1.0.0")
builder.description("Custom workflow automation")
builder.author("Your Name", "your.email@example.com")
builder.type(PluginType.WORKFLOW)

class MyWorkflowPlugin(BaseWorkflowPlugin):
    def get_triggers(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "file_uploaded",
                "name": "File Uploaded",
                "description": "Triggered when a file is uploaded"
            }
        ]
    
    def get_actions(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "process_file",
                "name": "Process File",
                "description": "Process uploaded file"
            }
        ]
    
    async def execute_action(self, action: str, context: Dict[str, Any]) -> Any:
        if action == "process_file":
            # Implement file processing
            pass
"""
    }
    
    return templates.get(plugin_type, "# Plugin template not available for this type")


__all__ = [
    'PluginSDK',
    'PluginBuilder', 
    'APIHelper',
    'DatabaseHelper',
    'FileHelper',
    'WorkspaceHelper',
    'TaskHelper',
    'BaseIntegrationPlugin',
    'BaseUIPlugin', 
    'BaseWorkflowPlugin',
    'BaseAIPlugin',
    'BaseDataPlugin',
    'create_plugin_builder',
    'validate_plugin_manifest',
    'generate_plugin_template'
]