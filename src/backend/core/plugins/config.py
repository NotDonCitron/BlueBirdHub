"""
Plugin Configuration and Settings Management

Handles plugin configuration storage, validation, and dynamic updates
with support for environment-specific settings and user preferences.
"""

import json
import logging
import sqlite3
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import asyncio
import jsonschema
from copy import deepcopy

from .base import PluginMetadata, PluginException


logger = logging.getLogger(__name__)


class ConfigScope(Enum):
    """Configuration scope levels"""
    GLOBAL = "global"
    WORKSPACE = "workspace"
    USER = "user"
    PLUGIN = "plugin"
    ENVIRONMENT = "environment"


class ConfigType(Enum):
    """Configuration value types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    SECRET = "secret"


@dataclass
class ConfigDefinition:
    """Configuration field definition"""
    key: str
    config_type: ConfigType
    description: str
    default_value: Any = None
    required: bool = False
    secret: bool = False
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    choices: Optional[List[Any]] = None
    pattern: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    scope: ConfigScope = ConfigScope.PLUGIN
    category: str = "general"
    order: int = 0


@dataclass
class ConfigValue:
    """Configuration value with metadata"""
    key: str
    value: Any
    scope: ConfigScope
    scope_id: str  # workspace_id, user_id, etc.
    plugin_id: str
    set_by: str = "system"
    set_at: datetime = field(default_factory=datetime.utcnow)
    encrypted: bool = False


@dataclass
class ConfigTemplate:
    """Configuration template for plugin setup"""
    name: str
    description: str
    plugin_id: str
    values: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)


class PluginConfigManager:
    """Manages plugin configuration and settings"""
    
    def __init__(self, data_dir: str = "/tmp/bluebirdhub_plugins"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(self.data_dir / "config.db")
        
        # Configuration registry
        self.config_definitions: Dict[str, Dict[str, ConfigDefinition]] = {}
        self.config_cache: Dict[str, Dict[str, Any]] = {}
        self.templates: Dict[str, ConfigTemplate] = {}
        
        # Validation schemas
        self.schemas: Dict[str, Dict[str, Any]] = {}
        
        # Change listeners
        self.change_listeners: Dict[str, List[callable]] = {}
        
        # Initialize database
        asyncio.create_task(self._init_database())
    
    async def _init_database(self):
        """Initialize configuration database"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS config_definitions (
                    plugin_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    config_type TEXT NOT NULL,
                    description TEXT,
                    default_value TEXT,
                    required BOOLEAN DEFAULT FALSE,
                    secret BOOLEAN DEFAULT FALSE,
                    min_value REAL,
                    max_value REAL,
                    choices TEXT,
                    pattern TEXT,
                    schema TEXT,
                    scope TEXT DEFAULT 'plugin',
                    category TEXT DEFAULT 'general',
                    order_index INTEGER DEFAULT 0,
                    PRIMARY KEY (plugin_id, key)
                );
                
                CREATE TABLE IF NOT EXISTS config_values (
                    plugin_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    scope_id TEXT NOT NULL,
                    set_by TEXT NOT NULL,
                    set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    encrypted BOOLEAN DEFAULT FALSE,
                    PRIMARY KEY (plugin_id, key, scope, scope_id)
                );
                
                CREATE TABLE IF NOT EXISTS config_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    plugin_id TEXT NOT NULL,
                    values TEXT NOT NULL,
                    tags TEXT,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_config_plugin ON config_values (plugin_id);
                CREATE INDEX IF NOT EXISTS idx_config_scope ON config_values (scope, scope_id);
                CREATE INDEX IF NOT EXISTS idx_templates_plugin ON config_templates (plugin_id);
            """)
            conn.commit()
        finally:
            conn.close()
    
    async def register_plugin_config(self, metadata: PluginMetadata, 
                                   config_definitions: List[ConfigDefinition]) -> bool:
        """Register configuration definitions for a plugin"""
        try:
            plugin_id = metadata.id
            
            # Store definitions
            self.config_definitions[plugin_id] = {}
            for config_def in config_definitions:
                self.config_definitions[plugin_id][config_def.key] = config_def
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            try:
                # Clear existing definitions
                conn.execute("DELETE FROM config_definitions WHERE plugin_id = ?", (plugin_id,))
                
                # Insert new definitions
                for config_def in config_definitions:
                    conn.execute("""
                        INSERT INTO config_definitions 
                        (plugin_id, key, config_type, description, default_value, required,
                         secret, min_value, max_value, choices, pattern, schema, scope, 
                         category, order_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        plugin_id, config_def.key, config_def.config_type.value,
                        config_def.description, json.dumps(config_def.default_value),
                        config_def.required, config_def.secret, config_def.min_value,
                        config_def.max_value, json.dumps(config_def.choices),
                        config_def.pattern, json.dumps(config_def.schema),
                        config_def.scope.value, config_def.category, config_def.order
                    ))
                
                conn.commit()
                
                # Create JSON schema for validation
                await self._create_validation_schema(plugin_id, config_definitions)
                
                logger.info(f"Registered {len(config_definitions)} config definitions for plugin {plugin_id}")
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Failed to register config for plugin {plugin_id}: {e}")
            return False
    
    async def set_config(self, plugin_id: str, key: str, value: Any,
                        scope: ConfigScope = ConfigScope.PLUGIN,
                        scope_id: str = "default", set_by: str = "user") -> bool:
        """Set a configuration value"""
        try:
            # Validate configuration exists
            if plugin_id not in self.config_definitions:
                raise PluginException(f"Plugin {plugin_id} has no registered config")
            
            if key not in self.config_definitions[plugin_id]:
                raise PluginException(f"Config key {key} not found for plugin {plugin_id}")
            
            config_def = self.config_definitions[plugin_id][key]
            
            # Validate value
            validated_value = await self._validate_config_value(config_def, value)
            
            # Create config value
            config_value = ConfigValue(
                key=key,
                value=validated_value,
                scope=scope,
                scope_id=scope_id,
                plugin_id=plugin_id,
                set_by=set_by,
                encrypted=config_def.secret
            )
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            try:
                value_json = json.dumps(validated_value) if not config_def.secret else self._encrypt_value(validated_value)
                
                conn.execute("""
                    INSERT OR REPLACE INTO config_values 
                    (plugin_id, key, value, scope, scope_id, set_by, encrypted)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    plugin_id, key, value_json, scope.value, scope_id, 
                    set_by, config_def.secret
                ))
                conn.commit()
            finally:
                conn.close()
            
            # Update cache
            cache_key = f"{plugin_id}:{scope.value}:{scope_id}"
            if cache_key not in self.config_cache:
                self.config_cache[cache_key] = {}
            self.config_cache[cache_key][key] = validated_value
            
            # Notify listeners
            await self._notify_config_change(plugin_id, key, validated_value, scope, scope_id)
            
            logger.debug(f"Set config {plugin_id}.{key} = {validated_value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set config {plugin_id}.{key}: {e}")
            raise PluginException(f"Config update failed: {e}")
    
    async def get_config(self, plugin_id: str, key: str = None,
                        scope: ConfigScope = ConfigScope.PLUGIN,
                        scope_id: str = "default") -> Union[Any, Dict[str, Any]]:
        """Get configuration value(s)"""
        try:
            cache_key = f"{plugin_id}:{scope.value}:{scope_id}"
            
            # Try cache first
            if cache_key in self.config_cache:
                if key:
                    return self.config_cache[cache_key].get(key)
                else:
                    return self.config_cache[cache_key].copy()
            
            # Load from database
            config_values = await self._load_config_from_db(plugin_id, scope, scope_id)
            
            # Apply defaults for missing values
            if plugin_id in self.config_definitions:
                for def_key, config_def in self.config_definitions[plugin_id].items():
                    if def_key not in config_values and config_def.default_value is not None:
                        config_values[def_key] = config_def.default_value
            
            # Cache the values
            self.config_cache[cache_key] = config_values
            
            if key:
                return config_values.get(key)
            else:
                return config_values
                
        except Exception as e:
            logger.error(f"Failed to get config {plugin_id}.{key}: {e}")
            if key:
                # Return default value if available
                if (plugin_id in self.config_definitions and 
                    key in self.config_definitions[plugin_id]):
                    return self.config_definitions[plugin_id][key].default_value
            return None
    
    async def get_effective_config(self, plugin_id: str, 
                                 workspace_id: str = None, 
                                 user_id: str = None) -> Dict[str, Any]:
        """Get effective configuration with scope precedence"""
        config = {}
        
        # Start with global config
        global_config = await self.get_config(plugin_id, scope=ConfigScope.GLOBAL, scope_id="global")
        if global_config:
            config.update(global_config)
        
        # Apply workspace config
        if workspace_id:
            workspace_config = await self.get_config(plugin_id, scope=ConfigScope.WORKSPACE, scope_id=workspace_id)
            if workspace_config:
                config.update(workspace_config)
        
        # Apply user config (highest priority)
        if user_id:
            user_config = await self.get_config(plugin_id, scope=ConfigScope.USER, scope_id=user_id)
            if user_config:
                config.update(user_config)
        
        # Apply plugin-specific config
        plugin_config = await self.get_config(plugin_id, scope=ConfigScope.PLUGIN, scope_id="default")
        if plugin_config:
            config.update(plugin_config)
        
        return config
    
    async def validate_config(self, plugin_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a complete configuration object"""
        if plugin_id not in self.schemas:
            raise PluginException(f"No validation schema for plugin {plugin_id}")
        
        try:
            # Validate against JSON schema
            jsonschema.validate(config, self.schemas[plugin_id])
            
            # Additional validation for each field
            validated_config = {}
            for key, value in config.items():
                if key in self.config_definitions[plugin_id]:
                    config_def = self.config_definitions[plugin_id][key]
                    validated_config[key] = await self._validate_config_value(config_def, value)
                else:
                    logger.warning(f"Unknown config key {key} for plugin {plugin_id}")
                    validated_config[key] = value
            
            return validated_config
            
        except jsonschema.ValidationError as e:
            raise PluginException(f"Configuration validation failed: {e.message}")
    
    async def reset_config(self, plugin_id: str, 
                         scope: ConfigScope = ConfigScope.PLUGIN,
                         scope_id: str = "default") -> bool:
        """Reset configuration to defaults"""
        try:
            # Delete from database
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    DELETE FROM config_values 
                    WHERE plugin_id = ? AND scope = ? AND scope_id = ?
                """, (plugin_id, scope.value, scope_id))
                conn.commit()
            finally:
                conn.close()
            
            # Clear cache
            cache_key = f"{plugin_id}:{scope.value}:{scope_id}"
            if cache_key in self.config_cache:
                del self.config_cache[cache_key]
            
            logger.info(f"Reset config for plugin {plugin_id} scope {scope.value}:{scope_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset config for plugin {plugin_id}: {e}")
            return False
    
    async def export_config(self, plugin_id: str,
                          scope: ConfigScope = ConfigScope.PLUGIN,
                          scope_id: str = "default",
                          include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration to a dictionary"""
        config = await self.get_config(plugin_id, scope=scope, scope_id=scope_id)
        
        if not include_secrets and plugin_id in self.config_definitions:
            # Filter out secret values
            filtered_config = {}
            for key, value in config.items():
                if key in self.config_definitions[plugin_id]:
                    config_def = self.config_definitions[plugin_id][key]
                    if not config_def.secret:
                        filtered_config[key] = value
                else:
                    filtered_config[key] = value
            config = filtered_config
        
        return {
            "plugin_id": plugin_id,
            "scope": scope.value,
            "scope_id": scope_id,
            "config": config,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    async def import_config(self, config_data: Dict[str, Any], 
                          set_by: str = "import") -> bool:
        """Import configuration from a dictionary"""
        try:
            plugin_id = config_data["plugin_id"]
            scope = ConfigScope(config_data["scope"])
            scope_id = config_data["scope_id"]
            config = config_data["config"]
            
            # Validate configuration
            validated_config = await self.validate_config(plugin_id, config)
            
            # Set each configuration value
            for key, value in validated_config.items():
                await self.set_config(plugin_id, key, value, scope, scope_id, set_by)
            
            logger.info(f"Imported config for plugin {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
            return False
    
    async def create_template(self, name: str, description: str, plugin_id: str,
                            config: Dict[str, Any], tags: List[str] = None,
                            created_by: str = "user") -> str:
        """Create a configuration template"""
        try:
            # Validate configuration
            await self.validate_config(plugin_id, config)
            
            template = ConfigTemplate(
                name=name,
                description=description,
                plugin_id=plugin_id,
                values=config,
                tags=tags or [],
                created_by=created_by
            )
            
            template_id = f"{plugin_id}:{name}:{datetime.utcnow().timestamp()}"
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    INSERT INTO config_templates 
                    (id, name, description, plugin_id, values, tags, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    template_id, name, description, plugin_id,
                    json.dumps(config), json.dumps(tags or []), created_by
                ))
                conn.commit()
            finally:
                conn.close()
            
            # Cache template
            self.templates[template_id] = template
            
            logger.info(f"Created config template {name} for plugin {plugin_id}")
            return template_id
            
        except Exception as e:
            logger.error(f"Failed to create config template: {e}")
            raise PluginException(f"Template creation failed: {e}")
    
    async def apply_template(self, template_id: str, 
                           scope: ConfigScope = ConfigScope.PLUGIN,
                           scope_id: str = "default",
                           set_by: str = "template") -> bool:
        """Apply a configuration template"""
        try:
            # Load template
            if template_id not in self.templates:
                await self._load_template(template_id)
            
            if template_id not in self.templates:
                raise PluginException(f"Template {template_id} not found")
            
            template = self.templates[template_id]
            
            # Apply configuration
            for key, value in template.values.items():
                await self.set_config(template.plugin_id, key, value, scope, scope_id, set_by)
            
            logger.info(f"Applied template {template.name} to {template.plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply template {template_id}: {e}")
            return False
    
    async def list_templates(self, plugin_id: str = None) -> List[Dict[str, Any]]:
        """List available configuration templates"""
        conn = sqlite3.connect(self.db_path)
        try:
            if plugin_id:
                cursor = conn.execute("""
                    SELECT * FROM config_templates WHERE plugin_id = ?
                    ORDER BY created_at DESC
                """, (plugin_id,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM config_templates ORDER BY created_at DESC
                """)
            
            templates = []
            for row in cursor.fetchall():
                templates.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "plugin_id": row[3],
                    "tags": json.loads(row[5] or "[]"),
                    "created_by": row[6],
                    "created_at": row[7]
                })
            
            return templates
            
        finally:
            conn.close()
    
    def add_change_listener(self, plugin_id: str, callback: callable):
        """Add a configuration change listener"""
        if plugin_id not in self.change_listeners:
            self.change_listeners[plugin_id] = []
        self.change_listeners[plugin_id].append(callback)
    
    def remove_change_listener(self, plugin_id: str, callback: callable):
        """Remove a configuration change listener"""
        if plugin_id in self.change_listeners:
            try:
                self.change_listeners[plugin_id].remove(callback)
            except ValueError:
                pass
    
    async def get_config_schema(self, plugin_id: str) -> Dict[str, Any]:
        """Get configuration schema for a plugin"""
        if plugin_id not in self.config_definitions:
            return {}
        
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for key, config_def in self.config_definitions[plugin_id].items():
            prop_schema = {
                "type": config_def.config_type.value,
                "description": config_def.description
            }
            
            if config_def.default_value is not None:
                prop_schema["default"] = config_def.default_value
            
            if config_def.choices:
                prop_schema["enum"] = config_def.choices
            
            if config_def.min_value is not None:
                prop_schema["minimum"] = config_def.min_value
            
            if config_def.max_value is not None:
                prop_schema["maximum"] = config_def.max_value
            
            if config_def.pattern:
                prop_schema["pattern"] = config_def.pattern
            
            schema["properties"][key] = prop_schema
            
            if config_def.required:
                schema["required"].append(key)
        
        return schema
    
    async def _validate_config_value(self, config_def: ConfigDefinition, value: Any) -> Any:
        """Validate a single configuration value"""
        # Type validation
        if config_def.config_type == ConfigType.STRING and not isinstance(value, str):
            if value is not None:
                value = str(value)
        elif config_def.config_type == ConfigType.INTEGER:
            if not isinstance(value, int):
                value = int(value)
        elif config_def.config_type == ConfigType.FLOAT:
            if not isinstance(value, (int, float)):
                value = float(value)
        elif config_def.config_type == ConfigType.BOOLEAN:
            if not isinstance(value, bool):
                value = bool(value)
        elif config_def.config_type == ConfigType.ARRAY:
            if not isinstance(value, list):
                raise PluginException(f"Config {config_def.key} must be an array")
        elif config_def.config_type == ConfigType.OBJECT:
            if not isinstance(value, dict):
                raise PluginException(f"Config {config_def.key} must be an object")
        
        # Range validation
        if config_def.min_value is not None and value < config_def.min_value:
            raise PluginException(f"Config {config_def.key} must be >= {config_def.min_value}")
        
        if config_def.max_value is not None and value > config_def.max_value:
            raise PluginException(f"Config {config_def.key} must be <= {config_def.max_value}")
        
        # Choice validation
        if config_def.choices and value not in config_def.choices:
            raise PluginException(f"Config {config_def.key} must be one of {config_def.choices}")
        
        # Pattern validation
        if config_def.pattern and isinstance(value, str):
            import re
            if not re.match(config_def.pattern, value):
                raise PluginException(f"Config {config_def.key} does not match pattern {config_def.pattern}")
        
        return value
    
    async def _load_config_from_db(self, plugin_id: str, scope: ConfigScope, scope_id: str) -> Dict[str, Any]:
        """Load configuration from database"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT key, value, encrypted FROM config_values 
                WHERE plugin_id = ? AND scope = ? AND scope_id = ?
            """, (plugin_id, scope.value, scope_id))
            
            config = {}
            for row in cursor.fetchall():
                key, value_json, encrypted = row
                if encrypted:
                    value = self._decrypt_value(value_json)
                else:
                    value = json.loads(value_json)
                config[key] = value
            
            return config
            
        finally:
            conn.close()
    
    async def _create_validation_schema(self, plugin_id: str, config_definitions: List[ConfigDefinition]):
        """Create JSON schema for configuration validation"""
        schema = await self.get_config_schema(plugin_id)
        self.schemas[plugin_id] = schema
    
    async def _notify_config_change(self, plugin_id: str, key: str, value: Any,
                                  scope: ConfigScope, scope_id: str):
        """Notify listeners of configuration changes"""
        if plugin_id in self.change_listeners:
            for callback in self.change_listeners[plugin_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(plugin_id, key, value, scope, scope_id)
                    else:
                        callback(plugin_id, key, value, scope, scope_id)
                except Exception as e:
                    logger.error(f"Config change listener failed: {e}")
    
    async def _load_template(self, template_id: str):
        """Load template from database"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT * FROM config_templates WHERE id = ?
            """, (template_id,))
            
            row = cursor.fetchone()
            if row:
                template = ConfigTemplate(
                    name=row[1],
                    description=row[2],
                    plugin_id=row[3],
                    values=json.loads(row[4]),
                    tags=json.loads(row[5] or "[]"),
                    created_by=row[6]
                )
                self.templates[template_id] = template
                
        finally:
            conn.close()
    
    def _encrypt_value(self, value: Any) -> str:
        """Encrypt a secret value (placeholder implementation)"""
        # In a real implementation, this would use proper encryption
        import base64
        return base64.b64encode(json.dumps(value).encode()).decode()
    
    def _decrypt_value(self, encrypted_value: str) -> Any:
        """Decrypt a secret value (placeholder implementation)"""
        # In a real implementation, this would use proper decryption
        import base64
        return json.loads(base64.b64decode(encrypted_value.encode()).decode())