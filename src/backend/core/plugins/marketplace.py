"""
Plugin Marketplace System

Provides plugin discovery, installation, and marketplace functionality
with support for remote repositories and package management.
"""

import json
import logging
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import tempfile
import shutil
import zipfile
import tarfile
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import semver

from .base import PluginMetadata, PluginException
from .registry import PluginRegistry
from .security import PluginSecurity


logger = logging.getLogger(__name__)


@dataclass
class MarketplaceEntry:
    """Marketplace plugin entry"""
    plugin_id: str
    name: str
    description: str
    version: str
    author: str
    category: str
    tags: List[str]
    download_url: str
    homepage: str
    repository: str
    license: str
    price: float
    rating: float
    download_count: int
    last_updated: datetime
    screenshots: List[str]
    is_verified: bool
    is_featured: bool


@dataclass
class MarketplaceRepository:
    """Marketplace repository configuration"""
    name: str
    url: str
    enabled: bool
    priority: int
    auth_token: Optional[str] = None
    last_sync: Optional[datetime] = None


class PluginMarketplace:
    """Plugin marketplace for discovery and installation"""
    
    def __init__(self, registry: PluginRegistry, data_dir: str = "/tmp/bluebirdhub_plugins"):
        self.registry = registry
        self.security = PluginSecurity()
        self.data_dir = Path(data_dir)
        self.cache_dir = self.data_dir / "marketplace_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Default repositories
        self.repositories: Dict[str, MarketplaceRepository] = {
            "official": MarketplaceRepository(
                name="BlueBirdHub Official",
                url="https://marketplace.bluebirdhub.com",
                enabled=True,
                priority=1
            ),
            "community": MarketplaceRepository(
                name="Community Plugins",
                url="https://community.bluebirdhub.com/plugins",
                enabled=True,
                priority=2
            )
        }
        
        self.cache: Dict[str, List[MarketplaceEntry]] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_plugins(self, 
                           query: str = None,
                           category: str = None,
                           tags: List[str] = None,
                           sort_by: str = "relevance",
                           limit: int = 50) -> List[MarketplaceEntry]:
        """Search for plugins in the marketplace"""
        results = []
        
        # Search across all enabled repositories
        for repo_name, repo in self.repositories.items():
            if not repo.enabled:
                continue
                
            try:
                repo_results = await self._search_repository(
                    repo, query, category, tags, sort_by, limit
                )
                results.extend(repo_results)
            except Exception as e:
                logger.warning(f"Failed to search repository {repo_name}: {e}")
        
        # Deduplicate and sort results
        unique_results = self._deduplicate_results(results)
        return self._sort_results(unique_results, sort_by)[:limit]
    
    async def get_plugin_details(self, plugin_id: str, repository: str = None) -> Optional[MarketplaceEntry]:
        """Get detailed information about a plugin"""
        if repository:
            repo = self.repositories.get(repository)
            if repo and repo.enabled:
                return await self._get_plugin_from_repository(repo, plugin_id)
        else:
            # Search all repositories
            for repo in self.repositories.values():
                if not repo.enabled:
                    continue
                try:
                    entry = await self._get_plugin_from_repository(repo, plugin_id)
                    if entry:
                        return entry
                except Exception as e:
                    logger.warning(f"Failed to get plugin from {repo.name}: {e}")
        
        return None
    
    async def install_plugin(self, plugin_id: str, version: str = None, repository: str = None) -> bool:
        """Install a plugin from the marketplace"""
        try:
            # Get plugin details
            entry = await self.get_plugin_details(plugin_id, repository)
            if not entry:
                raise PluginException(f"Plugin {plugin_id} not found in marketplace")
            
            # Use specified version or latest
            target_version = version or entry.version
            
            # Check if already installed
            existing = await self.registry.get_plugin(plugin_id)
            if existing:
                if existing.version == target_version:
                    logger.info(f"Plugin {plugin_id} v{target_version} already installed")
                    return True
                elif semver.compare(existing.version, target_version) > 0:
                    logger.warning(f"Newer version of {plugin_id} already installed")
                    return False
            
            # Download plugin package
            package_path = await self._download_plugin(entry, target_version)
            
            # Validate package security
            validation_result = self.security.validate_plugin_package(package_path)
            if not validation_result["valid"]:
                raise PluginException(f"Security validation failed: {validation_result['violations']}")
            
            # Extract and install
            install_path = await self._extract_plugin(package_path, plugin_id)
            
            # Load plugin metadata
            metadata = await self._load_plugin_metadata(install_path)
            
            # Register with registry
            await self.registry.register_plugin(metadata, str(install_path))
            
            logger.info(f"Successfully installed plugin {plugin_id} v{target_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install plugin {plugin_id}: {e}")
            raise PluginException(f"Plugin installation failed: {e}", plugin_id)
    
    async def uninstall_plugin(self, plugin_id: str, remove_data: bool = False) -> bool:
        """Uninstall a plugin"""
        try:
            # Get plugin info
            plugin = await self.registry.get_plugin(plugin_id)
            if not plugin:
                raise PluginException(f"Plugin {plugin_id} not found")
            
            # Get installation path
            stats = await self.registry.get_plugin_stats(plugin_id)
            install_path = stats.get("install_path")
            
            # Remove from registry
            await self.registry.unregister_plugin(plugin_id)
            
            # Remove files
            if install_path and Path(install_path).exists():
                shutil.rmtree(install_path)
            
            # Remove data if requested
            if remove_data:
                data_path = self.data_dir / "plugins" / plugin_id
                if data_path.exists():
                    shutil.rmtree(data_path)
            
            logger.info(f"Successfully uninstalled plugin {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to uninstall plugin {plugin_id}: {e}")
            raise PluginException(f"Plugin uninstallation failed: {e}", plugin_id)
    
    async def update_plugin(self, plugin_id: str) -> bool:
        """Update a plugin to the latest version"""
        try:
            # Get current plugin
            current = await self.registry.get_plugin(plugin_id)
            if not current:
                raise PluginException(f"Plugin {plugin_id} not installed")
            
            # Get latest version from marketplace
            latest = await self.get_plugin_details(plugin_id)
            if not latest:
                raise PluginException(f"Plugin {plugin_id} not found in marketplace")
            
            # Check if update available
            if semver.compare(latest.version, current.version) <= 0:
                logger.info(f"Plugin {plugin_id} is already up to date")
                return True
            
            # Backup current installation
            backup_path = await self._backup_plugin(plugin_id)
            
            try:
                # Uninstall current version
                await self.uninstall_plugin(plugin_id, remove_data=False)
                
                # Install new version
                success = await self.install_plugin(plugin_id, latest.version)
                
                if success:
                    # Remove backup
                    if backup_path and Path(backup_path).exists():
                        shutil.rmtree(backup_path)
                    return True
                else:
                    # Restore backup
                    await self._restore_plugin(plugin_id, backup_path)
                    return False
                    
            except Exception as e:
                # Restore backup on failure
                await self._restore_plugin(plugin_id, backup_path)
                raise e
            
        except Exception as e:
            logger.error(f"Failed to update plugin {plugin_id}: {e}")
            raise PluginException(f"Plugin update failed: {e}", plugin_id)
    
    async def get_installed_plugins(self) -> List[Dict[str, Any]]:
        """Get list of installed plugins with marketplace info"""
        installed = await self.registry.list_plugins()
        result = []
        
        for plugin in installed:
            marketplace_info = await self.get_plugin_details(plugin.id)
            plugin_info = {
                "metadata": plugin.dict(),
                "status": await self.registry.get_plugin_status(plugin.id),
                "stats": await self.registry.get_plugin_stats(plugin.id),
                "marketplace": marketplace_info.dict() if marketplace_info else None
            }
            result.append(plugin_info)
        
        return result
    
    async def check_updates(self) -> List[Dict[str, Any]]:
        """Check for available plugin updates"""
        updates = []
        installed = await self.registry.list_plugins()
        
        for plugin in installed:
            try:
                latest = await self.get_plugin_details(plugin.id)
                if latest and semver.compare(latest.version, plugin.version) > 0:
                    updates.append({
                        "plugin_id": plugin.id,
                        "current_version": plugin.version,
                        "latest_version": latest.version,
                        "description": latest.description,
                        "last_updated": latest.last_updated
                    })
            except Exception as e:
                logger.warning(f"Failed to check updates for {plugin.id}: {e}")
        
        return updates
    
    async def sync_repositories(self) -> Dict[str, Any]:
        """Sync with all enabled repositories"""
        results = {}
        
        for repo_name, repo in self.repositories.items():
            if not repo.enabled:
                continue
            
            try:
                result = await self._sync_repository(repo)
                results[repo_name] = result
                repo.last_sync = datetime.utcnow()
            except Exception as e:
                logger.error(f"Failed to sync repository {repo_name}: {e}")
                results[repo_name] = {"success": False, "error": str(e)}
        
        return results
    
    async def _search_repository(self, repo: MarketplaceRepository, query: str, 
                               category: str, tags: List[str], sort_by: str, limit: int) -> List[MarketplaceEntry]:
        """Search a specific repository"""
        # Check cache first
        cache_key = f"{repo.name}:search:{query or ''}:{category or ''}:{':'.join(tags or [])}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Build search parameters
        params = {
            "limit": limit,
            "sort": sort_by
        }
        if query:
            params["q"] = query
        if category:
            params["category"] = category
        if tags:
            params["tags"] = ",".join(tags)
        
        try:
            search_url = urljoin(repo.url, "/api/v1/plugins/search")
            headers = {}
            if repo.auth_token:
                headers["Authorization"] = f"Bearer {repo.auth_token}"
            
            async with self.session.get(search_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    entries = [MarketplaceEntry(**item) for item in data.get("plugins", [])]
                    
                    # Cache results
                    self.cache[cache_key] = entries
                    self.cache_expiry[cache_key] = datetime.utcnow() + timedelta(hours=1)
                    
                    return entries
                else:
                    logger.warning(f"Search failed for {repo.name}: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching repository {repo.name}: {e}")
            return []
    
    async def _get_plugin_from_repository(self, repo: MarketplaceRepository, plugin_id: str) -> Optional[MarketplaceEntry]:
        """Get plugin details from a specific repository"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            plugin_url = urljoin(repo.url, f"/api/v1/plugins/{plugin_id}")
            headers = {}
            if repo.auth_token:
                headers["Authorization"] = f"Bearer {repo.auth_token}"
            
            async with self.session.get(plugin_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return MarketplaceEntry(**data)
                elif response.status == 404:
                    return None
                else:
                    logger.warning(f"Failed to get plugin {plugin_id} from {repo.name}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting plugin {plugin_id} from repository {repo.name}: {e}")
            return None
    
    async def _download_plugin(self, entry: MarketplaceEntry, version: str) -> str:
        """Download plugin package"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            async with self.session.get(entry.download_url) as response:
                if response.status == 200:
                    with open(temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    return temp_path
                else:
                    raise PluginException(f"Download failed: HTTP {response.status}")
                    
        except Exception as e:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            raise PluginException(f"Failed to download plugin: {e}")
    
    async def _extract_plugin(self, package_path: str, plugin_id: str) -> str:
        """Extract plugin package to installation directory"""
        install_dir = self.data_dir / "plugins" / plugin_id
        install_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Determine archive type and extract
            if zipfile.is_zipfile(package_path):
                with zipfile.ZipFile(package_path, 'r') as archive:
                    archive.extractall(install_dir)
            elif tarfile.is_tarfile(package_path):
                with tarfile.open(package_path, 'r') as archive:
                    archive.extractall(install_dir)
            else:
                raise PluginException("Unsupported package format")
            
            return str(install_dir)
            
        finally:
            # Clean up downloaded package
            if Path(package_path).exists():
                Path(package_path).unlink()
    
    async def _load_plugin_metadata(self, install_path: str) -> PluginMetadata:
        """Load plugin metadata from installation"""
        manifest_path = Path(install_path) / "plugin.json"
        if not manifest_path.exists():
            raise PluginException("Plugin manifest not found")
        
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        
        return PluginMetadata(**manifest_data)
    
    async def _backup_plugin(self, plugin_id: str) -> str:
        """Create backup of plugin installation"""
        stats = await self.registry.get_plugin_stats(plugin_id)
        install_path = stats.get("install_path")
        
        if not install_path or not Path(install_path).exists():
            return None
        
        backup_dir = self.data_dir / "backups" / plugin_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}"
        
        shutil.copytree(install_path, backup_path)
        return str(backup_path)
    
    async def _restore_plugin(self, plugin_id: str, backup_path: str):
        """Restore plugin from backup"""
        if not backup_path or not Path(backup_path).exists():
            return
        
        install_dir = self.data_dir / "plugins" / plugin_id
        if install_dir.exists():
            shutil.rmtree(install_dir)
        
        shutil.copytree(backup_path, install_dir)
        
        # Re-register plugin
        metadata = await self._load_plugin_metadata(str(install_dir))
        await self.registry.register_plugin(metadata, str(install_dir))
    
    def _deduplicate_results(self, results: List[MarketplaceEntry]) -> List[MarketplaceEntry]:
        """Remove duplicate entries, preferring higher priority repositories"""
        seen = {}
        unique = []
        
        for entry in results:
            if entry.plugin_id not in seen:
                seen[entry.plugin_id] = entry
                unique.append(entry)
            else:
                # Keep entry with higher version or from featured source
                existing = seen[entry.plugin_id]
                if (semver.compare(entry.version, existing.version) > 0 or 
                    (entry.is_featured and not existing.is_featured)):
                    seen[entry.plugin_id] = entry
                    unique = [e for e in unique if e.plugin_id != entry.plugin_id]
                    unique.append(entry)
        
        return unique
    
    def _sort_results(self, results: List[MarketplaceEntry], sort_by: str) -> List[MarketplaceEntry]:
        """Sort marketplace results"""
        if sort_by == "name":
            return sorted(results, key=lambda x: x.name.lower())
        elif sort_by == "rating":
            return sorted(results, key=lambda x: x.rating, reverse=True)
        elif sort_by == "downloads":
            return sorted(results, key=lambda x: x.download_count, reverse=True)
        elif sort_by == "updated":
            return sorted(results, key=lambda x: x.last_updated, reverse=True)
        else:  # relevance (default)
            # Sort by featured, then rating, then downloads
            return sorted(results, key=lambda x: (x.is_featured, x.rating, x.download_count), reverse=True)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self.cache or cache_key not in self.cache_expiry:
            return False
        return datetime.utcnow() < self.cache_expiry[cache_key]
    
    async def _sync_repository(self, repo: MarketplaceRepository) -> Dict[str, Any]:
        """Sync repository metadata"""
        # Implementation would fetch repository metadata and update local cache
        return {"success": True, "plugins_count": 0, "last_sync": datetime.utcnow().isoformat()}