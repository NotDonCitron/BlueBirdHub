"""
Plugin Lifecycle Management

Handles plugin installation, updates, and uninstallation with proper
dependency management and rollback capabilities.
"""

import asyncio
import logging
import shutil
import json
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime
import tempfile
from dataclasses import dataclass
import semver

from .base import PluginMetadata, PluginException
from .registry import PluginRegistry
from .marketplace import PluginMarketplace
from .security import PluginSecurity


logger = logging.getLogger(__name__)


@dataclass
class InstallationPlan:
    """Plugin installation plan with dependencies"""
    target_plugin: str
    version: str
    dependencies: List[str]
    install_order: List[str]
    size_estimate: int
    conflicts: List[str]
    warnings: List[str]


@dataclass
class InstallationResult:
    """Result of plugin installation"""
    success: bool
    plugin_id: str
    version: str
    install_path: str
    errors: List[str]
    warnings: List[str]
    dependencies_installed: List[str]
    rollback_info: Optional[Dict[str, Any]] = None


class PluginLifecycleManager:
    """Manages plugin installation, updates, and removal lifecycle"""
    
    def __init__(self, registry: PluginRegistry, marketplace: PluginMarketplace, 
                 data_dir: str = "/tmp/bluebirdhub_plugins"):
        self.registry = registry
        self.marketplace = marketplace
        self.security = PluginSecurity()
        self.data_dir = Path(data_dir)
        self.install_dir = self.data_dir / "plugins"
        self.backup_dir = self.data_dir / "backups"
        self.temp_dir = self.data_dir / "temp"
        
        # Create directories
        for directory in [self.install_dir, self.backup_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self._lock = asyncio.Lock()
        self.active_installations: Set[str] = set()
    
    async def plan_installation(self, plugin_id: str, version: str = None) -> InstallationPlan:
        """Create installation plan with dependency resolution"""
        try:
            # Get plugin info from marketplace
            async with self.marketplace as marketplace:
                plugin_info = await marketplace.get_plugin_details(plugin_id)
                if not plugin_info:
                    raise PluginException(f"Plugin {plugin_id} not found in marketplace")
            
            target_version = version or plugin_info.version
            
            # Check if already installed
            existing = await self.registry.get_plugin(plugin_id)
            if existing:
                if existing.version == target_version:
                    return InstallationPlan(
                        target_plugin=plugin_id,
                        version=target_version,
                        dependencies=[],
                        install_order=[],
                        size_estimate=0,
                        conflicts=[],
                        warnings=[f"Plugin {plugin_id} v{target_version} already installed"]
                    )
            
            # Get plugin metadata (would need to download and parse)
            metadata = await self._get_plugin_metadata(plugin_id, target_version)
            
            # Resolve dependencies
            dependencies = await self._resolve_dependencies(metadata)
            
            # Determine installation order
            install_order = await self._calculate_install_order(plugin_id, dependencies)
            
            # Check for conflicts
            conflicts = await self._check_conflicts(plugin_id, dependencies)
            
            # Calculate size estimate
            size_estimate = await self._estimate_install_size(plugin_id, dependencies)
            
            # Generate warnings
            warnings = []
            if conflicts:
                warnings.append(f"Potential conflicts detected: {', '.join(conflicts)}")
            
            return InstallationPlan(
                target_plugin=plugin_id,
                version=target_version,
                dependencies=dependencies,
                install_order=install_order,
                size_estimate=size_estimate,
                conflicts=conflicts,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to create installation plan for {plugin_id}: {e}")
            raise PluginException(f"Installation planning failed: {e}", plugin_id)
    
    async def install_plugin(self, plugin_id: str, version: str = None, 
                           force: bool = False) -> InstallationResult:
        """Install a plugin with dependencies"""
        async with self._lock:
            if plugin_id in self.active_installations:
                raise PluginException(f"Plugin {plugin_id} installation already in progress")
            
            self.active_installations.add(plugin_id)
            
            try:
                # Create installation plan
                plan = await self.plan_installation(plugin_id, version)
                
                # Check for conflicts
                if plan.conflicts and not force:
                    raise PluginException(f"Installation conflicts detected: {plan.conflicts}")
                
                # Create rollback point
                rollback_info = await self._create_rollback_point(plugin_id)
                
                result = InstallationResult(
                    success=False,
                    plugin_id=plugin_id,
                    version=plan.version,
                    install_path="",
                    errors=[],
                    warnings=plan.warnings,
                    dependencies_installed=[],
                    rollback_info=rollback_info
                )
                
                try:
                    # Install dependencies first
                    for dep_id in plan.dependencies:
                        if not await self.registry.get_plugin(dep_id):
                            dep_result = await self._install_single_plugin(dep_id)
                            if not dep_result.success:
                                result.errors.extend([f"Dependency {dep_id}: {e}" for e in dep_result.errors])
                                raise PluginException(f"Failed to install dependency {dep_id}")
                            result.dependencies_installed.append(dep_id)
                    
                    # Install main plugin
                    main_result = await self._install_single_plugin(plugin_id, plan.version)
                    
                    if main_result.success:
                        result.success = True
                        result.install_path = main_result.install_path
                        result.warnings.extend(main_result.warnings)
                        
                        logger.info(f"Successfully installed plugin {plugin_id} v{plan.version}")
                    else:
                        result.errors.extend(main_result.errors)
                        raise PluginException(f"Main plugin installation failed: {main_result.errors}")
                
                except Exception as e:
                    # Rollback on failure
                    logger.error(f"Installation failed, rolling back: {e}")
                    await self._rollback_installation(rollback_info)
                    result.errors.append(str(e))
                    result.success = False
                
                return result
                
            finally:
                self.active_installations.discard(plugin_id)
    
    async def update_plugin(self, plugin_id: str, target_version: str = None) -> InstallationResult:
        """Update a plugin to a newer version"""
        async with self._lock:
            try:
                # Check if plugin is installed
                current = await self.registry.get_plugin(plugin_id)
                if not current:
                    raise PluginException(f"Plugin {plugin_id} not installed")
                
                # Get latest version from marketplace
                async with self.marketplace as marketplace:
                    latest_info = await marketplace.get_plugin_details(plugin_id)
                    if not latest_info:
                        raise PluginException(f"Plugin {plugin_id} not found in marketplace")
                
                new_version = target_version or latest_info.version
                
                # Check if update is needed
                if semver.compare(new_version, current.version) <= 0:
                    return InstallationResult(
                        success=True,
                        plugin_id=plugin_id,
                        version=current.version,
                        install_path="",
                        errors=[],
                        warnings=[f"Plugin {plugin_id} is already up to date or newer"],
                        dependencies_installed=[]
                    )
                
                # Create backup
                backup_path = await self._backup_plugin(plugin_id)
                
                # Uninstall current version
                await self._uninstall_plugin_files(plugin_id)
                
                # Install new version
                try:
                    result = await self.install_plugin(plugin_id, new_version)
                    
                    if result.success:
                        # Remove backup on successful update
                        if backup_path and Path(backup_path).exists():
                            shutil.rmtree(backup_path)
                        
                        logger.info(f"Successfully updated plugin {plugin_id} from v{current.version} to v{new_version}")
                    else:
                        # Restore from backup on failure
                        await self._restore_from_backup(plugin_id, backup_path)
                        result.errors.append("Update failed, restored previous version")
                    
                    return result
                    
                except Exception as e:
                    # Restore from backup on error
                    await self._restore_from_backup(plugin_id, backup_path)
                    raise PluginException(f"Update failed and rolled back: {e}")
                
            except Exception as e:
                logger.error(f"Failed to update plugin {plugin_id}: {e}")
                raise PluginException(f"Plugin update failed: {e}", plugin_id)
    
    async def uninstall_plugin(self, plugin_id: str, remove_dependencies: bool = False, 
                             remove_data: bool = False) -> bool:
        """Uninstall a plugin and optionally its dependencies"""
        async with self._lock:
            try:
                # Check if plugin is installed
                plugin = await self.registry.get_plugin(plugin_id)
                if not plugin:
                    logger.warning(f"Plugin {plugin_id} not installed")
                    return True
                
                # Check if other plugins depend on this one
                dependents = await self._find_dependents(plugin_id)
                if dependents and not remove_dependencies:
                    raise PluginException(f"Cannot uninstall {plugin_id}: required by {dependents}")
                
                # Create backup before uninstall
                backup_path = await self._backup_plugin(plugin_id)
                
                try:
                    # Uninstall dependents first if requested
                    if remove_dependencies:
                        for dependent in dependents:
                            await self.uninstall_plugin(dependent, True, remove_data)
                    
                    # Remove plugin files
                    await self._uninstall_plugin_files(plugin_id)
                    
                    # Remove from registry
                    await self.registry.unregister_plugin(plugin_id)
                    
                    # Remove plugin data if requested
                    if remove_data:
                        await self._remove_plugin_data(plugin_id)
                    
                    logger.info(f"Successfully uninstalled plugin {plugin_id}")
                    return True
                    
                except Exception as e:
                    # Restore from backup on failure
                    await self._restore_from_backup(plugin_id, backup_path)
                    raise e
                
            except Exception as e:
                logger.error(f"Failed to uninstall plugin {plugin_id}: {e}")
                raise PluginException(f"Plugin uninstallation failed: {e}", plugin_id)
    
    async def repair_plugin(self, plugin_id: str) -> bool:
        """Repair a corrupted plugin installation"""
        try:
            plugin = await self.registry.get_plugin(plugin_id)
            if not plugin:
                raise PluginException(f"Plugin {plugin_id} not found")
            
            # Get plugin from marketplace
            async with self.marketplace as marketplace:
                result = await marketplace.install_plugin(plugin_id, plugin.version)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to repair plugin {plugin_id}: {e}")
            return False
    
    async def verify_installation(self, plugin_id: str) -> Dict[str, Any]:
        """Verify plugin installation integrity"""
        try:
            plugin = await self.registry.get_plugin(plugin_id)
            if not plugin:
                return {"valid": False, "error": "Plugin not found in registry"}
            
            stats = await self.registry.get_plugin_stats(plugin_id)
            install_path = stats.get("install_path")
            
            if not install_path or not Path(install_path).exists():
                return {"valid": False, "error": "Installation directory not found"}
            
            # Verify required files
            required_files = ["plugin.json"]
            missing_files = []
            
            for file_name in required_files:
                file_path = Path(install_path) / file_name
                if not file_path.exists():
                    missing_files.append(file_name)
            
            if missing_files:
                return {
                    "valid": False,
                    "error": f"Missing required files: {missing_files}"
                }
            
            # Verify checksum if available
            stored_checksum = stats.get("checksum")
            if stored_checksum:
                current_checksum = self.security._calculate_checksum(Path(install_path))
                if current_checksum != stored_checksum:
                    return {
                        "valid": False,
                        "error": "Checksum mismatch - installation may be corrupted"
                    }
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def get_installation_history(self, plugin_id: str) -> List[Dict[str, Any]]:
        """Get installation history for a plugin"""
        # This would be implemented with a proper audit log
        return [
            {
                "action": "install",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "success": True
            }
        ]
    
    async def _install_single_plugin(self, plugin_id: str, version: str = None) -> InstallationResult:
        """Install a single plugin without dependencies"""
        try:
            async with self.marketplace as marketplace:
                success = await marketplace.install_plugin(plugin_id, version)
            
            if success:
                plugin = await self.registry.get_plugin(plugin_id)
                stats = await self.registry.get_plugin_stats(plugin_id)
                
                return InstallationResult(
                    success=True,
                    plugin_id=plugin_id,
                    version=plugin.version if plugin else version or "unknown",
                    install_path=stats.get("install_path", ""),
                    errors=[],
                    warnings=[],
                    dependencies_installed=[]
                )
            else:
                return InstallationResult(
                    success=False,
                    plugin_id=plugin_id,
                    version=version or "unknown",
                    install_path="",
                    errors=["Installation failed"],
                    warnings=[],
                    dependencies_installed=[]
                )
                
        except Exception as e:
            return InstallationResult(
                success=False,
                plugin_id=plugin_id,
                version=version or "unknown",
                install_path="",
                errors=[str(e)],
                warnings=[],
                dependencies_installed=[]
            )
    
    async def _get_plugin_metadata(self, plugin_id: str, version: str) -> PluginMetadata:
        """Get plugin metadata from marketplace"""
        async with self.marketplace as marketplace:
            plugin_info = await marketplace.get_plugin_details(plugin_id)
            if not plugin_info:
                raise PluginException(f"Plugin {plugin_id} not found")
        
        # This is a simplified conversion - real implementation would download and parse manifest
        return PluginMetadata(
            id=plugin_id,
            name=plugin_info.name,
            version=version,
            description=plugin_info.description,
            author=plugin_info.author,
            plugin_type="integration",  # Would be parsed from manifest
            entry_point="main",  # Would be parsed from manifest
            module_path="plugin",  # Would be parsed from manifest
            bluebirdHub_version=">=1.0.0",  # Would be parsed from manifest
            python_version=">=3.8"  # Would be parsed from manifest
        )
    
    async def _resolve_dependencies(self, metadata: PluginMetadata) -> List[str]:
        """Resolve plugin dependencies"""
        dependencies = []
        
        for dep in metadata.dependencies:
            # Check if dependency is already installed
            existing = await self.registry.get_plugin(dep.name)
            if not existing:
                dependencies.append(dep.name)
            elif not self._is_version_compatible(dep.version, existing.version):
                dependencies.append(dep.name)  # Need to update
        
        return dependencies
    
    async def _calculate_install_order(self, plugin_id: str, dependencies: List[str]) -> List[str]:
        """Calculate optimal installation order"""
        # Simple topological sort - real implementation would handle complex dependency graphs
        order = list(dependencies)
        order.append(plugin_id)
        return order
    
    async def _check_conflicts(self, plugin_id: str, dependencies: List[str]) -> List[str]:
        """Check for installation conflicts"""
        conflicts = []
        
        # Check if any dependency conflicts with installed plugins
        for dep_id in dependencies:
            existing = await self.registry.get_plugin(dep_id)
            if existing:
                # Check for version conflicts
                # This would be more sophisticated in a real implementation
                pass
        
        return conflicts
    
    async def _estimate_install_size(self, plugin_id: str, dependencies: List[str]) -> int:
        """Estimate installation size in bytes"""
        # This would query marketplace for actual sizes
        base_size = 1024 * 1024  # 1MB base
        dep_size = len(dependencies) * 512 * 1024  # 512KB per dependency
        return base_size + dep_size
    
    async def _create_rollback_point(self, plugin_id: str) -> Dict[str, Any]:
        """Create rollback point before installation"""
        return {
            "plugin_id": plugin_id,
            "timestamp": datetime.utcnow().isoformat(),
            "registry_backup": await self._backup_registry(),
            "existing_plugin": await self.registry.get_plugin(plugin_id)
        }
    
    async def _rollback_installation(self, rollback_info: Dict[str, Any]):
        """Rollback installation to previous state"""
        if not rollback_info:
            return
        
        plugin_id = rollback_info["plugin_id"]
        
        # Restore registry
        await self._restore_registry(rollback_info["registry_backup"])
        
        # Remove any files that were installed
        plugin_install_dir = self.install_dir / plugin_id
        if plugin_install_dir.exists():
            shutil.rmtree(plugin_install_dir)
    
    async def _backup_plugin(self, plugin_id: str) -> str:
        """Create backup of plugin installation"""
        stats = await self.registry.get_plugin_stats(plugin_id)
        install_path = stats.get("install_path")
        
        if not install_path or not Path(install_path).exists():
            return None
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{plugin_id}_{timestamp}"
        
        shutil.copytree(install_path, backup_path)
        return str(backup_path)
    
    async def _restore_from_backup(self, plugin_id: str, backup_path: str):
        """Restore plugin from backup"""
        if not backup_path or not Path(backup_path).exists():
            return
        
        install_dir = self.install_dir / plugin_id
        if install_dir.exists():
            shutil.rmtree(install_dir)
        
        shutil.copytree(backup_path, install_dir)
    
    async def _uninstall_plugin_files(self, plugin_id: str):
        """Remove plugin files from disk"""
        stats = await self.registry.get_plugin_stats(plugin_id)
        install_path = stats.get("install_path")
        
        if install_path and Path(install_path).exists():
            shutil.rmtree(install_path)
    
    async def _remove_plugin_data(self, plugin_id: str):
        """Remove plugin data directory"""
        data_dir = self.data_dir / "data" / plugin_id
        if data_dir.exists():
            shutil.rmtree(data_dir)
    
    async def _find_dependents(self, plugin_id: str) -> List[str]:
        """Find plugins that depend on this plugin"""
        dependents = []
        all_plugins = await self.registry.list_plugins()
        
        for plugin in all_plugins:
            for dep in plugin.dependencies:
                if dep.name == plugin_id:
                    dependents.append(plugin.id)
                    break
        
        return dependents
    
    def _is_version_compatible(self, required: str, available: str) -> bool:
        """Check if available version satisfies requirement"""
        try:
            return semver.match(available, required)
        except:
            return required == available
    
    async def _backup_registry(self) -> str:
        """Backup registry to temporary file"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        backup_path = temp_file.name
        temp_file.close()
        
        await self.registry.export_registry(backup_path)
        return backup_path
    
    async def _restore_registry(self, backup_path: str):
        """Restore registry from backup"""
        if backup_path and Path(backup_path).exists():
            await self.registry.import_registry(backup_path)
            Path(backup_path).unlink()  # Clean up backup file