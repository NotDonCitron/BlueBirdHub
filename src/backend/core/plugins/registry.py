"""
Plugin Registry System

Manages plugin registration, discovery, and metadata storage.
Provides centralized plugin information and dependency resolution.
"""

import json
import logging
import sqlite3
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime
import asyncio
import aiofiles
from contextlib import asynccontextmanager
import semver

from .base import PluginMetadata, PluginStatus, PluginType, PluginException
from .security import PluginSecurity


logger = logging.getLogger(__name__)


class PluginRegistry:
    """Central registry for managing plugin metadata and state"""
    
    def __init__(self, db_path: str = None, data_dir: str = "/tmp/bluebirdhub_plugins"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path or str(self.data_dir / "plugin_registry.db")
        self.security = PluginSecurity(str(self.data_dir))
        self._plugins: Dict[str, PluginMetadata] = {}
        self._plugin_status: Dict[str, PluginStatus] = {}
        self._plugin_instances: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        
        # Initialize database
        asyncio.create_task(self._init_database())
    
    async def _init_database(self):
        """Initialize the SQLite database for plugin metadata"""
        async with aiofiles.open(self.db_path, 'w') as f:
            pass  # Create file if it doesn't exist
        
        # Create tables
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS plugins (
                    id TEXT PRIMARY KEY,
                    metadata TEXT NOT NULL,
                    status TEXT NOT NULL,
                    install_path TEXT,
                    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_error TEXT,
                    usage_count INTEGER DEFAULT 0,
                    checksum TEXT
                );
                
                CREATE TABLE IF NOT EXISTS plugin_dependencies (
                    plugin_id TEXT NOT NULL,
                    dependency_id TEXT NOT NULL,
                    version_requirement TEXT NOT NULL,
                    optional BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (plugin_id) REFERENCES plugins (id),
                    PRIMARY KEY (plugin_id, dependency_id)
                );
                
                CREATE TABLE IF NOT EXISTS plugin_permissions (
                    plugin_id TEXT NOT NULL,
                    permission TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    granted BOOLEAN DEFAULT FALSE,
                    granted_at TIMESTAMP,
                    FOREIGN KEY (plugin_id) REFERENCES plugins (id),
                    PRIMARY KEY (plugin_id, permission, scope)
                );
                
                CREATE INDEX IF NOT EXISTS idx_plugins_status ON plugins (status);
                CREATE INDEX IF NOT EXISTS idx_plugins_type ON plugins (json_extract(metadata, '$.plugin_type'));
                CREATE INDEX IF NOT EXISTS idx_plugins_category ON plugins (json_extract(metadata, '$.category'));
            """)
            conn.commit()
        finally:
            conn.close()
    
    async def register_plugin(self, metadata: PluginMetadata, install_path: str = None) -> bool:
        """Register a new plugin in the registry"""
        async with self._lock:
            try:
                # Validate plugin metadata
                await self._validate_plugin_metadata(metadata)
                
                # Check for conflicts
                if metadata.id in self._plugins:
                    existing = self._plugins[metadata.id]
                    if existing.version == metadata.version:
                        raise PluginException(f"Plugin {metadata.id} version {metadata.version} already registered")
                
                # Store in memory
                self._plugins[metadata.id] = metadata
                self._plugin_status[metadata.id] = PluginStatus.INSTALLED
                
                # Store in database
                await self._store_plugin_metadata(metadata, install_path)
                
                logger.info(f"Registered plugin: {metadata.name} ({metadata.id}) v{metadata.version}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to register plugin {metadata.id}: {e}")
                raise PluginException(f"Plugin registration failed: {e}", metadata.id)
    
    async def unregister_plugin(self, plugin_id: str) -> bool:
        """Unregister a plugin from the registry"""
        async with self._lock:
            try:
                if plugin_id not in self._plugins:
                    raise PluginException(f"Plugin {plugin_id} not found", plugin_id)
                
                # Remove from memory
                del self._plugins[plugin_id]
                if plugin_id in self._plugin_status:
                    del self._plugin_status[plugin_id]
                if plugin_id in self._plugin_instances:
                    del self._plugin_instances[plugin_id]
                
                # Remove from database
                await self._remove_plugin_metadata(plugin_id)
                
                logger.info(f"Unregistered plugin: {plugin_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unregister plugin {plugin_id}: {e}")
                raise PluginException(f"Plugin unregistration failed: {e}", plugin_id)
    
    async def get_plugin(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by ID"""
        if plugin_id not in self._plugins:
            await self._load_plugin_from_db(plugin_id)
        return self._plugins.get(plugin_id)
    
    async def list_plugins(self, 
                          status: Optional[PluginStatus] = None,
                          plugin_type: Optional[PluginType] = None,
                          category: Optional[str] = None) -> List[PluginMetadata]:
        """List plugins with optional filtering"""
        plugins = []
        
        for plugin_id, metadata in self._plugins.items():
            # Apply filters
            if status and self._plugin_status.get(plugin_id) != status:
                continue
            if plugin_type and metadata.plugin_type != plugin_type:
                continue
            if category and metadata.category != category:
                continue
            
            plugins.append(metadata)
        
        return sorted(plugins, key=lambda p: p.name)
    
    async def search_plugins(self, query: str) -> List[PluginMetadata]:
        """Search plugins by name, description, or tags"""
        query = query.lower()
        results = []
        
        for metadata in self._plugins.values():
            if (query in metadata.name.lower() or
                query in metadata.description.lower() or
                any(query in tag.lower() for tag in metadata.tags)):
                results.append(metadata)
        
        return sorted(results, key=lambda p: p.name)
    
    async def get_plugin_dependencies(self, plugin_id: str) -> List[str]:
        """Get list of plugin dependencies"""
        plugin = await self.get_plugin(plugin_id)
        if not plugin:
            return []
        
        return [dep.name for dep in plugin.dependencies]
    
    async def resolve_dependencies(self, plugin_id: str) -> List[str]:
        """Resolve plugin dependency tree"""
        resolved = []
        visited = set()
        
        async def _resolve(pid: str):
            if pid in visited:
                return
            visited.add(pid)
            
            dependencies = await self.get_plugin_dependencies(pid)
            for dep_id in dependencies:
                await _resolve(dep_id)
                if dep_id not in resolved:
                    resolved.append(dep_id)
        
        await _resolve(plugin_id)
        return resolved
    
    async def check_compatibility(self, plugin_id: str, target_version: str = None) -> Dict[str, Any]:
        """Check plugin compatibility with system and dependencies"""
        plugin = await self.get_plugin(plugin_id)
        if not plugin:
            return {"compatible": False, "error": "Plugin not found"}
        
        result = {
            "compatible": True,
            "warnings": [],
            "errors": [],
            "dependencies": {}
        }
        
        try:
            # Check BlueBirdHub version compatibility
            # This would check against actual system version
            system_version = "1.0.0"  # Placeholder
            if not self._is_version_compatible(plugin.bluebirdHub_version, system_version):
                result["errors"].append(f"Incompatible BlueBirdHub version: requires {plugin.bluebirdHub_version}, have {system_version}")
                result["compatible"] = False
            
            # Check dependencies
            for dep in plugin.dependencies:
                dep_plugin = await self.get_plugin(dep.name)
                if not dep_plugin and not dep.optional:
                    result["errors"].append(f"Missing required dependency: {dep.name}")
                    result["compatible"] = False
                elif dep_plugin:
                    if not self._is_version_compatible(dep.version, dep_plugin.version):
                        result["warnings"].append(f"Dependency version mismatch: {dep.name} requires {dep.version}, have {dep_plugin.version}")
                
                result["dependencies"][dep.name] = {
                    "required": dep.version,
                    "available": dep_plugin.version if dep_plugin else None,
                    "optional": dep.optional
                }
        
        except Exception as e:
            result["compatible"] = False
            result["errors"].append(f"Compatibility check failed: {e}")
        
        return result
    
    def _is_version_compatible(self, required: str, available: str) -> bool:
        """Check if available version satisfies requirement"""
        try:
            return semver.match(available, required)
        except:
            return required == available
    
    async def update_plugin_status(self, plugin_id: str, status: PluginStatus, error: str = None):
        """Update plugin status"""
        async with self._lock:
            if plugin_id in self._plugin_status:
                self._plugin_status[plugin_id] = status
                
                # Update in database
                conn = sqlite3.connect(self.db_path)
                try:
                    conn.execute("""
                        UPDATE plugins 
                        SET status = ?, last_error = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (status.value, error, plugin_id))
                    conn.commit()
                finally:
                    conn.close()
    
    async def get_plugin_status(self, plugin_id: str) -> Optional[PluginStatus]:
        """Get current plugin status"""
        return self._plugin_status.get(plugin_id)
    
    async def set_plugin_instance(self, plugin_id: str, instance: Any):
        """Store plugin instance reference"""
        self._plugin_instances[plugin_id] = instance
    
    async def get_plugin_instance(self, plugin_id: str) -> Optional[Any]:
        """Get plugin instance reference"""
        return self._plugin_instances.get(plugin_id)
    
    async def increment_usage_count(self, plugin_id: str):
        """Increment plugin usage counter"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                UPDATE plugins 
                SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (plugin_id,))
            conn.commit()
        finally:
            conn.close()
    
    async def get_plugin_stats(self, plugin_id: str) -> Dict[str, Any]:
        """Get plugin usage statistics"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT usage_count, installed_at, updated_at, last_error
                FROM plugins WHERE id = ?
            """, (plugin_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "usage_count": row[0],
                    "installed_at": row[1],
                    "updated_at": row[2],
                    "last_error": row[3]
                }
            return {}
        finally:
            conn.close()
    
    async def _validate_plugin_metadata(self, metadata: PluginMetadata):
        """Validate plugin metadata"""
        # Check for required fields
        if not metadata.id or not metadata.name or not metadata.version:
            raise PluginException("Missing required metadata fields")
        
        # Validate version format
        try:
            semver.VersionInfo.parse(metadata.version)
        except ValueError:
            raise PluginException(f"Invalid version format: {metadata.version}")
        
        # Check for ID conflicts
        existing = await self.get_plugin(metadata.id)
        if existing and existing.version == metadata.version:
            raise PluginException(f"Plugin {metadata.id} v{metadata.version} already exists")
    
    async def _store_plugin_metadata(self, metadata: PluginMetadata, install_path: str = None):
        """Store plugin metadata in database"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Store main plugin data
            conn.execute("""
                INSERT OR REPLACE INTO plugins 
                (id, metadata, status, install_path, updated_at) 
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                metadata.id,
                metadata.json(),
                PluginStatus.INSTALLED.value,
                install_path
            ))
            
            # Store dependencies
            conn.execute("DELETE FROM plugin_dependencies WHERE plugin_id = ?", (metadata.id,))
            for dep in metadata.dependencies:
                conn.execute("""
                    INSERT INTO plugin_dependencies 
                    (plugin_id, dependency_id, version_requirement, optional) 
                    VALUES (?, ?, ?, ?)
                """, (metadata.id, dep.name, dep.version, dep.optional))
            
            # Store permissions
            conn.execute("DELETE FROM plugin_permissions WHERE plugin_id = ?", (metadata.id,))
            for perm in metadata.permissions:
                conn.execute("""
                    INSERT INTO plugin_permissions 
                    (plugin_id, permission, scope, granted) 
                    VALUES (?, ?, ?, ?)
                """, (metadata.id, perm.permission, perm.scope, False))
            
            conn.commit()
        finally:
            conn.close()
    
    async def _remove_plugin_metadata(self, plugin_id: str):
        """Remove plugin metadata from database"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("DELETE FROM plugin_permissions WHERE plugin_id = ?", (plugin_id,))
            conn.execute("DELETE FROM plugin_dependencies WHERE plugin_id = ?", (plugin_id,))
            conn.execute("DELETE FROM plugins WHERE id = ?", (plugin_id,))
            conn.commit()
        finally:
            conn.close()
    
    async def _load_plugin_from_db(self, plugin_id: str):
        """Load plugin metadata from database"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT metadata, status FROM plugins WHERE id = ?
            """, (plugin_id,))
            row = cursor.fetchone()
            
            if row:
                metadata = PluginMetadata.parse_raw(row[0])
                status = PluginStatus(row[1])
                
                self._plugins[plugin_id] = metadata
                self._plugin_status[plugin_id] = status
        finally:
            conn.close()
    
    async def export_registry(self, export_path: str) -> bool:
        """Export plugin registry to JSON file"""
        try:
            export_data = {
                "plugins": {},
                "exported_at": datetime.utcnow().isoformat()
            }
            
            for plugin_id, metadata in self._plugins.items():
                export_data["plugins"][plugin_id] = {
                    "metadata": metadata.dict(),
                    "status": self._plugin_status.get(plugin_id, PluginStatus.INSTALLED).value
                }
            
            async with aiofiles.open(export_path, 'w') as f:
                await f.write(json.dumps(export_data, indent=2))
            
            return True
        except Exception as e:
            logger.error(f"Failed to export registry: {e}")
            return False
    
    async def import_registry(self, import_path: str) -> bool:
        """Import plugin registry from JSON file"""
        try:
            async with aiofiles.open(import_path, 'r') as f:
                import_data = json.loads(await f.read())
            
            for plugin_id, plugin_data in import_data["plugins"].items():
                metadata = PluginMetadata(**plugin_data["metadata"])
                await self.register_plugin(metadata)
                
                status = PluginStatus(plugin_data["status"])
                await self.update_plugin_status(plugin_id, status)
            
            return True
        except Exception as e:
            logger.error(f"Failed to import registry: {e}")
            return False