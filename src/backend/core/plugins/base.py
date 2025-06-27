"""
Plugin Base Classes and Interfaces

Defines the core plugin architecture with standardized APIs and interfaces.
"""

import abc
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
import uuid
import semver


logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Plugin types supported by BlueBirdHub"""
    INTEGRATION = "integration"
    UI_COMPONENT = "ui_component"
    THEME = "theme"
    WORKFLOW = "workflow"
    DATA_PROCESSOR = "data_processor"
    AI_ENHANCEMENT = "ai_enhancement"
    FIELD_TYPE = "field_type"
    API_EXTENSION = "api_extension"
    BACKGROUND_SERVICE = "background_service"
    SCHEMA_EXTENSION = "schema_extension"
    AUTH_PROVIDER = "auth_provider"


class PluginStatus(Enum):
    """Plugin status states"""
    INSTALLED = "installed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UPDATING = "updating"
    UNINSTALLING = "uninstalling"


class PluginPriority(Enum):
    """Plugin execution priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class PluginDependency:
    """Plugin dependency specification"""
    name: str
    version: str
    optional: bool = False
    minimum_version: Optional[str] = None
    maximum_version: Optional[str] = None


@dataclass
class PluginPermission:
    """Plugin permission specification"""
    permission: str
    scope: str
    description: str
    required: bool = True


class PluginMetadata(BaseModel):
    """Plugin metadata and manifest"""
    
    # Basic Information
    id: str = Field(..., description="Unique plugin identifier")
    name: str = Field(..., description="Human-readable plugin name")
    version: str = Field(..., description="Plugin version (semver)")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    author_email: Optional[str] = Field(None, description="Author email")
    homepage: Optional[str] = Field(None, description="Plugin homepage URL")
    repository: Optional[str] = Field(None, description="Plugin repository URL")
    
    # Plugin Configuration
    plugin_type: PluginType = Field(..., description="Type of plugin")
    entry_point: str = Field(..., description="Main plugin class or function")
    module_path: str = Field(..., description="Python module path")
    
    # Compatibility and Dependencies
    bluebirdHub_version: str = Field(..., description="Compatible BlueBirdHub version")
    python_version: str = Field(..., description="Required Python version")
    dependencies: List[PluginDependency] = Field(default_factory=list)
    
    # Permissions and Security
    permissions: List[PluginPermission] = Field(default_factory=list)
    sandbox_mode: bool = Field(True, description="Run in sandboxed environment")
    
    # Runtime Configuration
    priority: PluginPriority = Field(default=PluginPriority.NORMAL)
    auto_start: bool = Field(True, description="Auto-start with BlueBirdHub")
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    category: str = Field("general", description="Plugin category")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Installation Info
    install_size: Optional[int] = Field(None, description="Installation size in bytes")
    install_path: Optional[str] = Field(None, description="Installation directory")
    checksum: Optional[str] = Field(None, description="Package checksum")
    
    @validator('version')
    def validate_version(cls, v):
        """Validate semver format"""
        try:
            semver.VersionInfo.parse(v)
            return v
        except ValueError:
            raise ValueError("Version must be in semver format (e.g., '1.0.0')")
    
    @validator('id')
    def validate_id(cls, v):
        """Validate plugin ID format"""
        if not v.replace('-', '').replace('_', '').replace('.', '').isalnum():
            raise ValueError("Plugin ID must contain only alphanumeric characters, hyphens, underscores, and dots")
        return v

    class Config:
        use_enum_values = True


class PluginInterface(abc.ABC):
    """Base interface that all plugins must implement"""
    
    def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
        self.metadata = metadata
        self.config = config or {}
        self.status = PluginStatus.INSTALLED
        self.logger = logging.getLogger(f"plugin.{metadata.id}")
        self._event_handlers: Dict[str, List[Callable]] = {}
        
    @abc.abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin. Returns True if successful."""
        pass
    
    @abc.abstractmethod
    async def activate(self) -> bool:
        """Activate the plugin. Returns True if successful."""
        pass
    
    @abc.abstractmethod
    async def deactivate(self) -> bool:
        """Deactivate the plugin. Returns True if successful."""
        pass
    
    @abc.abstractmethod
    async def cleanup(self) -> bool:
        """Clean up plugin resources. Returns True if successful."""
        pass
    
    async def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the plugin with new settings."""
        self.config.update(config)
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get plugin health status"""
        return {
            "status": self.status.value,
            "metadata": self.metadata.dict(),
            "uptime": getattr(self, 'start_time', None),
            "memory_usage": self._get_memory_usage(),
            "error_count": getattr(self, 'error_count', 0)
        }
    
    def _get_memory_usage(self) -> int:
        """Get plugin memory usage"""
        # Implementation would use psutil or similar
        return 0


class PluginBase(PluginInterface):
    """Base plugin class with common functionality"""
    
    def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
        super().__init__(metadata, config)
        self.start_time: Optional[datetime] = None
        self.error_count: int = 0
        self.hooks: Dict[str, List[Callable]] = {}
        
    async def initialize(self) -> bool:
        """Default initialization"""
        try:
            self.logger.info(f"Initializing plugin {self.metadata.name}")
            await self._setup_hooks()
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize plugin: {e}")
            self.error_count += 1
            return False
    
    async def activate(self) -> bool:
        """Default activation"""
        try:
            self.logger.info(f"Activating plugin {self.metadata.name}")
            self.status = PluginStatus.ACTIVE
            self.start_time = datetime.utcnow()
            await self._register_hooks()
            return True
        except Exception as e:
            self.logger.error(f"Failed to activate plugin: {e}")
            self.status = PluginStatus.ERROR
            self.error_count += 1
            return False
    
    async def deactivate(self) -> bool:
        """Default deactivation"""
        try:
            self.logger.info(f"Deactivating plugin {self.metadata.name}")
            await self._unregister_hooks()
            self.status = PluginStatus.INACTIVE
            self.start_time = None
            return True
        except Exception as e:
            self.logger.error(f"Failed to deactivate plugin: {e}")
            self.error_count += 1
            return False
    
    async def cleanup(self) -> bool:
        """Default cleanup"""
        try:
            self.logger.info(f"Cleaning up plugin {self.metadata.name}")
            await self._cleanup_resources()
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup plugin: {e}")
            self.error_count += 1
            return False
    
    async def _setup_hooks(self):
        """Setup plugin hooks - to be overridden by subclasses"""
        pass
    
    async def _register_hooks(self):
        """Register plugin hooks with the system"""
        pass
    
    async def _unregister_hooks(self):
        """Unregister plugin hooks from the system"""
        pass
    
    async def _cleanup_resources(self):
        """Cleanup plugin-specific resources"""
        pass
    
    def add_hook(self, event: str, handler: Callable):
        """Add a hook handler for an event"""
        if event not in self.hooks:
            self.hooks[event] = []
        self.hooks[event].append(handler)
    
    def remove_hook(self, event: str, handler: Callable):
        """Remove a hook handler for an event"""
        if event in self.hooks and handler in self.hooks[event]:
            self.hooks[event].remove(handler)


class IntegrationPlugin(PluginBase):
    """Base class for integration plugins (Slack, Notion, etc.)"""
    
    def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
        super().__init__(metadata, config)
        self.api_client = None
        self.webhook_endpoints: List[str] = []
    
    @abc.abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the external service"""
        pass
    
    @abc.abstractmethod
    async def sync_data(self) -> bool:
        """Sync data with the external service"""
        pass
    
    async def setup_webhooks(self) -> bool:
        """Setup webhooks for real-time updates"""
        return True


class UIComponentPlugin(PluginBase):
    """Base class for UI component plugins"""
    
    def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
        super().__init__(metadata, config)
        self.component_definitions: Dict[str, Any] = {}
        self.styles: Dict[str, str] = {}
    
    @abc.abstractmethod
    def get_components(self) -> Dict[str, Any]:
        """Get component definitions"""
        pass
    
    async def register_components(self) -> bool:
        """Register components with the UI system"""
        try:
            components = self.get_components()
            # Register with frontend component registry
            return True
        except Exception as e:
            self.logger.error(f"Failed to register components: {e}")
            return False


class WorkflowPlugin(PluginBase):
    """Base class for workflow automation plugins"""
    
    def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
        super().__init__(metadata, config)
        self.triggers: List[Dict[str, Any]] = []
        self.actions: List[Dict[str, Any]] = []
    
    @abc.abstractmethod
    def get_triggers(self) -> List[Dict[str, Any]]:
        """Get available triggers"""
        pass
    
    @abc.abstractmethod
    def get_actions(self) -> List[Dict[str, Any]]:
        """Get available actions"""
        pass
    
    @abc.abstractmethod
    async def execute_action(self, action: str, context: Dict[str, Any]) -> Any:
        """Execute a workflow action"""
        pass


class AIEnhancementPlugin(PluginBase):
    """Base class for AI enhancement plugins"""
    
    def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
        super().__init__(metadata, config)
        self.models: Dict[str, Any] = {}
        self.capabilities: List[str] = []
    
    @abc.abstractmethod
    async def process(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Process data with AI enhancement"""
        pass
    
    @abc.abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get AI capabilities provided by this plugin"""
        pass


class DataProcessorPlugin(PluginBase):
    """Base class for data import/export plugins"""
    
    def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
        super().__init__(metadata, config)
        self.supported_formats: List[str] = []
    
    @abc.abstractmethod
    async def import_data(self, source: str, format: str) -> Any:
        """Import data from external source"""
        pass
    
    @abc.abstractmethod
    async def export_data(self, data: Any, destination: str, format: str) -> bool:
        """Export data to external destination"""
        pass
    
    @abc.abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get supported data formats"""
        pass


class PluginException(Exception):
    """Base exception for plugin-related errors"""
    
    def __init__(self, message: str, plugin_id: str = None, error_code: str = None):
        super().__init__(message)
        self.plugin_id = plugin_id
        self.error_code = error_code
        self.timestamp = datetime.utcnow()


class PluginSecurityException(PluginException):
    """Exception for plugin security violations"""
    pass


class PluginCompatibilityException(PluginException):
    """Exception for plugin compatibility issues"""
    pass