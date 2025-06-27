"""
Plugin Manager

Central management system for plugin lifecycle, activation, and coordination.
Handles plugin loading, initialization, and inter-plugin communication.
"""

import asyncio
import logging
import importlib
import importlib.util
import sys
from typing import Dict, List, Optional, Any, Set, Callable
from pathlib import Path
from datetime import datetime
import threading
import weakref
from contextlib import asynccontextmanager

from .base import (
    PluginBase, PluginMetadata, PluginStatus, PluginType, 
    PluginException, PluginSecurityException
)
from .registry import PluginRegistry
from .security import PluginSecurity, PluginSandbox
from .event_system import PluginEventSystem
from .permissions import PluginPermissionManager


logger = logging.getLogger(__name__)


class PluginManager:
    """Central plugin management system"""
    
    def __init__(self, data_dir: str = "/tmp/bluebirdhub_plugins"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Core components
        self.registry = PluginRegistry(data_dir=str(self.data_dir))
        self.security = PluginSecurity(str(self.data_dir))
        self.event_system = PluginEventSystem()
        self.permission_manager = PluginPermissionManager()
        
        # Runtime state
        self.active_plugins: Dict[str, PluginBase] = {}
        self.plugin_threads: Dict[str, threading.Thread] = {}
        self.plugin_sandboxes: Dict[str, PluginSandbox] = {}
        self.startup_order: List[str] = []
        
        # Hooks and callbacks
        self.lifecycle_hooks: Dict[str, List[Callable]] = {
            "before_load": [],
            "after_load": [],
            "before_activate": [],
            "after_activate": [],
            "before_deactivate": [],
            "after_deactivate": [],
            "before_unload": [],
            "after_unload": []
        }
        
        # Management state
        self._lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> bool:
        """Initialize the plugin manager"""
        try:
            logger.info("Initializing Plugin Manager")
            
            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._health_monitor())
            
            # Load auto-start plugins
            await self._load_autostart_plugins()
            
            logger.info("Plugin Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Plugin Manager: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the plugin manager"""
        try:
            logger.info("Shutting down Plugin Manager")
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Stop health monitoring
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Deactivate all plugins
            await self.deactivate_all_plugins()
            
            # Unload all plugins
            await self.unload_all_plugins()
            
            logger.info("Plugin Manager shutdown complete")
            return True
            
        except Exception as e:
            logger.error(f"Error during Plugin Manager shutdown: {e}")
            return False
    
    async def load_plugin(self, plugin_id: str) -> bool:
        """Load a plugin into memory"""
        async with self._lock:
            try:
                if plugin_id in self.active_plugins:
                    logger.warning(f"Plugin {plugin_id} already loaded")
                    return True
                
                # Get plugin metadata
                metadata = await self.registry.get_plugin(plugin_id)
                if not metadata:
                    raise PluginException(f"Plugin {plugin_id} not found in registry")
                
                # Check compatibility
                compatibility = await self.registry.check_compatibility(plugin_id)
                if not compatibility["compatible"]:
                    raise PluginException(f"Plugin {plugin_id} is not compatible: {compatibility['errors']}")
                
                # Execute lifecycle hooks
                await self._execute_hooks("before_load", plugin_id, metadata)
                
                # Load plugin module
                plugin_instance = await self._load_plugin_module(metadata)
                
                # Create sandbox if required
                if metadata.sandbox_mode:
                    sandbox = self.security.create_sandbox(plugin_id)
                    self.plugin_sandboxes[plugin_id] = sandbox
                
                # Initialize plugin
                success = await plugin_instance.initialize()
                if not success:
                    raise PluginException(f"Plugin {plugin_id} initialization failed")
                
                # Store instance
                self.active_plugins[plugin_id] = plugin_instance
                await self.registry.set_plugin_instance(plugin_id, plugin_instance)
                await self.registry.update_plugin_status(plugin_id, PluginStatus.INSTALLED)
                
                # Execute lifecycle hooks
                await self._execute_hooks("after_load", plugin_id, metadata)
                
                logger.info(f"Successfully loaded plugin: {plugin_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_id}: {e}")
                await self.registry.update_plugin_status(plugin_id, PluginStatus.ERROR, str(e))
                # Cleanup on failure
                if plugin_id in self.active_plugins:
                    del self.active_plugins[plugin_id]
                if plugin_id in self.plugin_sandboxes:
                    self.security.remove_sandbox(plugin_id)
                    del self.plugin_sandboxes[plugin_id]
                raise PluginException(f"Plugin loading failed: {e}", plugin_id)
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin from memory"""
        async with self._lock:
            try:
                if plugin_id not in self.active_plugins:
                    logger.warning(f"Plugin {plugin_id} not loaded")
                    return True
                
                plugin_instance = self.active_plugins[plugin_id]
                metadata = plugin_instance.metadata
                
                # Execute lifecycle hooks
                await self._execute_hooks("before_unload", plugin_id, metadata)
                
                # Deactivate if active
                if await self.registry.get_plugin_status(plugin_id) == PluginStatus.ACTIVE:
                    await self.deactivate_plugin(plugin_id)
                
                # Cleanup plugin
                await plugin_instance.cleanup()
                
                # Remove from active plugins
                del self.active_plugins[plugin_id]
                
                # Cleanup sandbox
                if plugin_id in self.plugin_sandboxes:
                    self.security.remove_sandbox(plugin_id)
                    del self.plugin_sandboxes[plugin_id]
                
                # Update status
                await self.registry.update_plugin_status(plugin_id, PluginStatus.INSTALLED)
                
                # Execute lifecycle hooks
                await self._execute_hooks("after_unload", plugin_id, metadata)
                
                logger.info(f"Successfully unloaded plugin: {plugin_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unload plugin {plugin_id}: {e}")
                await self.registry.update_plugin_status(plugin_id, PluginStatus.ERROR, str(e))
                return False
    
    async def activate_plugin(self, plugin_id: str) -> bool:
        """Activate a loaded plugin"""
        async with self._lock:
            try:
                if plugin_id not in self.active_plugins:
                    # Try to load first
                    success = await self.load_plugin(plugin_id)
                    if not success:
                        return False
                
                plugin_instance = self.active_plugins[plugin_id]
                current_status = await self.registry.get_plugin_status(plugin_id)
                
                if current_status == PluginStatus.ACTIVE:
                    logger.warning(f"Plugin {plugin_id} already active")
                    return True
                
                # Check permissions
                if not await self.permission_manager.check_plugin_permissions(plugin_id):
                    raise PluginSecurityException(f"Plugin {plugin_id} lacks required permissions")
                
                # Execute lifecycle hooks
                await self._execute_hooks("before_activate", plugin_id, plugin_instance.metadata)
                
                # Activate in sandbox if required
                if plugin_id in self.plugin_sandboxes:
                    sandbox = self.plugin_sandboxes[plugin_id]
                    with sandbox.execute():
                        success = await plugin_instance.activate()
                else:
                    success = await plugin_instance.activate()
                
                if not success:
                    raise PluginException(f"Plugin {plugin_id} activation failed")
                
                # Update status
                await self.registry.update_plugin_status(plugin_id, PluginStatus.ACTIVE)
                
                # Register with event system
                await self.event_system.register_plugin(plugin_id, plugin_instance)
                
                # Execute lifecycle hooks
                await self._execute_hooks("after_activate", plugin_id, plugin_instance.metadata)
                
                logger.info(f"Successfully activated plugin: {plugin_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to activate plugin {plugin_id}: {e}")
                await self.registry.update_plugin_status(plugin_id, PluginStatus.ERROR, str(e))
                return False
    
    async def deactivate_plugin(self, plugin_id: str) -> bool:
        """Deactivate an active plugin"""
        async with self._lock:
            try:
                if plugin_id not in self.active_plugins:
                    logger.warning(f"Plugin {plugin_id} not loaded")
                    return True
                
                plugin_instance = self.active_plugins[plugin_id]
                current_status = await self.registry.get_plugin_status(plugin_id)
                
                if current_status != PluginStatus.ACTIVE:
                    logger.warning(f"Plugin {plugin_id} not active")
                    return True
                
                # Execute lifecycle hooks
                await self._execute_hooks("before_deactivate", plugin_id, plugin_instance.metadata)
                
                # Deactivate plugin
                success = await plugin_instance.deactivate()
                if not success:
                    logger.warning(f"Plugin {plugin_id} deactivation returned false")
                
                # Unregister from event system
                await self.event_system.unregister_plugin(plugin_id)
                
                # Update status
                await self.registry.update_plugin_status(plugin_id, PluginStatus.INACTIVE)
                
                # Execute lifecycle hooks
                await self._execute_hooks("after_deactivate", plugin_id, plugin_instance.metadata)
                
                logger.info(f"Successfully deactivated plugin: {plugin_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to deactivate plugin {plugin_id}: {e}")
                await self.registry.update_plugin_status(plugin_id, PluginStatus.ERROR, str(e))
                return False
    
    async def reload_plugin(self, plugin_id: str) -> bool:
        """Reload a plugin (deactivate, unload, load, activate)"""
        try:
            # Remember if it was active
            was_active = await self.registry.get_plugin_status(plugin_id) == PluginStatus.ACTIVE
            
            # Deactivate and unload
            if was_active:
                await self.deactivate_plugin(plugin_id)
            await self.unload_plugin(plugin_id)
            
            # Load and activate
            await self.load_plugin(plugin_id)
            if was_active:
                await self.activate_plugin(plugin_id)
            
            logger.info(f"Successfully reloaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload plugin {plugin_id}: {e}")
            return False
    
    async def get_plugin_instance(self, plugin_id: str) -> Optional[PluginBase]:
        """Get active plugin instance"""
        return self.active_plugins.get(plugin_id)
    
    async def list_active_plugins(self) -> List[str]:
        """Get list of active plugin IDs"""
        active = []
        for plugin_id in self.active_plugins.keys():
            status = await self.registry.get_plugin_status(plugin_id)
            if status == PluginStatus.ACTIVE:
                active.append(plugin_id)
        return active
    
    async def get_plugin_health(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin health status"""
        if plugin_id not in self.active_plugins:
            return None
        
        plugin_instance = self.active_plugins[plugin_id]
        health = plugin_instance.get_health_status()
        
        # Add sandbox resource usage if available
        if plugin_id in self.plugin_sandboxes:
            sandbox = self.plugin_sandboxes[plugin_id]
            health["resources"] = sandbox.get_resource_usage()
        
        return health
    
    async def activate_all_plugins(self) -> Dict[str, bool]:
        """Activate all installed plugins"""
        results = {}
        plugins = await self.registry.list_plugins()
        
        # Sort by priority for startup order
        sorted_plugins = sorted(plugins, key=lambda p: p.priority.value)
        
        for plugin in sorted_plugins:
            try:
                success = await self.activate_plugin(plugin.id)
                results[plugin.id] = success
            except Exception as e:
                logger.error(f"Failed to activate plugin {plugin.id}: {e}")
                results[plugin.id] = False
        
        return results
    
    async def deactivate_all_plugins(self) -> Dict[str, bool]:
        """Deactivate all active plugins"""
        results = {}
        active_plugins = await self.list_active_plugins()
        
        # Deactivate in reverse order
        for plugin_id in reversed(active_plugins):
            try:
                success = await self.deactivate_plugin(plugin_id)
                results[plugin_id] = success
            except Exception as e:
                logger.error(f"Failed to deactivate plugin {plugin_id}: {e}")
                results[plugin_id] = False
        
        return results
    
    async def unload_all_plugins(self) -> Dict[str, bool]:
        """Unload all loaded plugins"""
        results = {}
        loaded_plugins = list(self.active_plugins.keys())
        
        for plugin_id in loaded_plugins:
            try:
                success = await self.unload_plugin(plugin_id)
                results[plugin_id] = success
            except Exception as e:
                logger.error(f"Failed to unload plugin {plugin_id}: {e}")
                results[plugin_id] = False
        
        return results
    
    def add_lifecycle_hook(self, event: str, handler: Callable):
        """Add a lifecycle hook handler"""
        if event in self.lifecycle_hooks:
            self.lifecycle_hooks[event].append(handler)
    
    def remove_lifecycle_hook(self, event: str, handler: Callable):
        """Remove a lifecycle hook handler"""
        if event in self.lifecycle_hooks and handler in self.lifecycle_hooks[event]:
            self.lifecycle_hooks[event].remove(handler)
    
    async def _load_plugin_module(self, metadata: PluginMetadata) -> PluginBase:
        """Load plugin module and create instance"""
        try:
            # Get plugin stats to find installation path
            stats = await self.registry.get_plugin_stats(metadata.id)
            install_path = stats.get("install_path")
            
            if not install_path:
                raise PluginException(f"Plugin {metadata.id} installation path not found")
            
            # Add plugin directory to Python path temporarily
            plugin_dir = Path(install_path)
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))
            
            try:
                # Load the module
                module_path = metadata.module_path.replace('.', '/')
                module_file = plugin_dir / f"{module_path}.py"
                
                if not module_file.exists():
                    raise PluginException(f"Plugin module file not found: {module_file}")
                
                spec = importlib.util.spec_from_file_location(metadata.module_path, module_file)
                if not spec or not spec.loader:
                    raise PluginException(f"Failed to create module spec for {metadata.module_path}")
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Get the plugin class
                plugin_class = getattr(module, metadata.entry_point)
                if not plugin_class:
                    raise PluginException(f"Plugin entry point {metadata.entry_point} not found")
                
                # Create plugin instance
                plugin_instance = plugin_class(metadata)
                
                if not isinstance(plugin_instance, PluginBase):
                    raise PluginException(f"Plugin {metadata.id} does not inherit from PluginBase")
                
                return plugin_instance
                
            finally:
                # Remove from path
                if str(plugin_dir) in sys.path:
                    sys.path.remove(str(plugin_dir))
                    
        except Exception as e:
            raise PluginException(f"Failed to load plugin module: {e}", metadata.id)
    
    async def _execute_hooks(self, event: str, plugin_id: str, metadata: PluginMetadata):
        """Execute lifecycle hooks for an event"""
        if event in self.lifecycle_hooks:
            for handler in self.lifecycle_hooks[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(plugin_id, metadata)
                    else:
                        handler(plugin_id, metadata)
                except Exception as e:
                    logger.error(f"Lifecycle hook {event} failed for plugin {plugin_id}: {e}")
    
    async def _load_autostart_plugins(self):
        """Load plugins marked for auto-start"""
        plugins = await self.registry.list_plugins()
        autostart_plugins = [p for p in plugins if p.auto_start]
        
        # Sort by priority
        autostart_plugins.sort(key=lambda p: p.priority.value)
        
        for plugin in autostart_plugins:
            try:
                await self.activate_plugin(plugin.id)
                self.startup_order.append(plugin.id)
            except Exception as e:
                logger.error(f"Failed to auto-start plugin {plugin.id}: {e}")
    
    async def _health_monitor(self):
        """Background task to monitor plugin health"""
        while not self._shutdown_event.is_set():
            try:
                for plugin_id in list(self.active_plugins.keys()):
                    try:
                        health = await self.get_plugin_health(plugin_id)
                        if health:
                            # Check for error conditions
                            if health.get("error_count", 0) > 10:
                                logger.warning(f"Plugin {plugin_id} has high error count: {health['error_count']}")
                            
                            # Check resource usage from sandbox
                            resources = health.get("resources")
                            if resources:
                                memory_mb = resources.get("memory_usage_mb", 0)
                                cpu_percent = resources.get("cpu_usage_percent", 0)
                                
                                if memory_mb > 500:  # 500MB threshold
                                    logger.warning(f"Plugin {plugin_id} high memory usage: {memory_mb}MB")
                                
                                if cpu_percent > 80:  # 80% threshold
                                    logger.warning(f"Plugin {plugin_id} high CPU usage: {cpu_percent}%")
                    
                    except Exception as e:
                        logger.error(f"Health check failed for plugin {plugin_id}: {e}")
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(10)