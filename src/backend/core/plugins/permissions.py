"""
Plugin Permissions and Access Control System

Manages plugin permissions, access control, and security policies
to ensure plugins operate within authorized boundaries.
"""

import logging
import json
import sqlite3
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from pathlib import Path
import hashlib

from .base import PluginMetadata, PluginException, PluginSecurityException


logger = logging.getLogger(__name__)


class PermissionType(Enum):
    """Types of permissions"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"


class ResourceType(Enum):
    """Types of resources that can be protected"""
    FILE_SYSTEM = "filesystem"
    DATABASE = "database"
    NETWORK = "network"
    API = "api"
    WORKSPACE = "workspace"
    USER_DATA = "user_data"
    SYSTEM = "system"
    PLUGIN = "plugin"
    EVENT = "event"
    CONFIGURATION = "configuration"


class PermissionScope(Enum):
    """Scope of permissions"""
    GLOBAL = "global"
    WORKSPACE = "workspace"
    USER = "user"
    PLUGIN = "plugin"
    RESOURCE = "resource"


@dataclass
class Permission:
    """Permission definition"""
    id: str
    name: str
    description: str
    resource_type: ResourceType
    permission_type: PermissionType
    scope: PermissionScope
    required: bool = False
    dangerous: bool = False
    auto_grant: bool = False
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionGrant:
    """Permission grant record"""
    id: str
    plugin_id: str
    permission_id: str
    scope_value: Optional[str] = None  # Specific workspace, user, etc.
    granted_by: str = "system"
    granted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessRequest:
    """Access request for auditing"""
    id: str
    plugin_id: str
    permission_id: str
    resource_path: str
    scope_value: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    granted: bool = False
    reason: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


class PluginPermissionManager:
    """Manages plugin permissions and access control"""
    
    def __init__(self, data_dir: str = "/tmp/bluebirdhub_plugins"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(self.data_dir / "permissions.db")
        
        # Permission definitions
        self.permissions: Dict[str, Permission] = {}
        self.plugin_grants: Dict[str, Set[str]] = {}  # plugin_id -> permission_ids
        self.access_log: List[AccessRequest] = []
        
        # Security policies
        self.security_policies: Dict[str, Dict[str, Any]] = {}
        self.rate_limits: Dict[str, Dict[str, int]] = {}
        
        # Initialize standard permissions
        self._init_standard_permissions()
        
        # Initialize database
        asyncio.create_task(self._init_database())
    
    async def _init_database(self):
        """Initialize the permissions database"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS permissions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    resource_type TEXT NOT NULL,
                    permission_type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    required BOOLEAN DEFAULT FALSE,
                    dangerous BOOLEAN DEFAULT FALSE,
                    auto_grant BOOLEAN DEFAULT FALSE,
                    conditions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS permission_grants (
                    id TEXT PRIMARY KEY,
                    plugin_id TEXT NOT NULL,
                    permission_id TEXT NOT NULL,
                    scope_value TEXT,
                    granted_by TEXT NOT NULL,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    revoked BOOLEAN DEFAULT FALSE,
                    revoked_at TIMESTAMP,
                    revoked_by TEXT,
                    conditions TEXT,
                    FOREIGN KEY (permission_id) REFERENCES permissions (id)
                );
                
                CREATE TABLE IF NOT EXISTS access_requests (
                    id TEXT PRIMARY KEY,
                    plugin_id TEXT NOT NULL,
                    permission_id TEXT NOT NULL,
                    resource_path TEXT NOT NULL,
                    scope_value TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    granted BOOLEAN DEFAULT FALSE,
                    reason TEXT,
                    context TEXT,
                    FOREIGN KEY (permission_id) REFERENCES permissions (id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_grants_plugin ON permission_grants (plugin_id);
                CREATE INDEX IF NOT EXISTS idx_grants_permission ON permission_grants (permission_id);
                CREATE INDEX IF NOT EXISTS idx_access_plugin ON access_requests (plugin_id);
                CREATE INDEX IF NOT EXISTS idx_access_timestamp ON access_requests (timestamp);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def _init_standard_permissions(self):
        """Initialize standard BlueBirdHub permissions"""
        standard_perms = [
            # File System
            Permission("fs.read", "Read Files", "Read files and directories", 
                      ResourceType.FILE_SYSTEM, PermissionType.READ, PermissionScope.GLOBAL),
            Permission("fs.write", "Write Files", "Create and modify files", 
                      ResourceType.FILE_SYSTEM, PermissionType.WRITE, PermissionScope.GLOBAL, dangerous=True),
            Permission("fs.delete", "Delete Files", "Delete files and directories", 
                      ResourceType.FILE_SYSTEM, PermissionType.DELETE, PermissionScope.GLOBAL, dangerous=True),
            
            # Database
            Permission("db.read", "Read Database", "Read from database", 
                      ResourceType.DATABASE, PermissionType.READ, PermissionScope.GLOBAL),
            Permission("db.write", "Write Database", "Write to database", 
                      ResourceType.DATABASE, PermissionType.WRITE, PermissionScope.GLOBAL),
            Permission("db.schema", "Modify Schema", "Modify database schema", 
                      ResourceType.DATABASE, PermissionType.ADMIN, PermissionScope.GLOBAL, dangerous=True),
            
            # Network
            Permission("net.http", "HTTP Requests", "Make HTTP requests", 
                      ResourceType.NETWORK, PermissionType.EXECUTE, PermissionScope.GLOBAL),
            Permission("net.socket", "Socket Access", "Create network sockets", 
                      ResourceType.NETWORK, PermissionType.EXECUTE, PermissionScope.GLOBAL, dangerous=True),
            
            # API
            Permission("api.read", "Read API", "Access read-only API endpoints", 
                      ResourceType.API, PermissionType.READ, PermissionScope.GLOBAL, auto_grant=True),
            Permission("api.write", "Write API", "Access write API endpoints", 
                      ResourceType.API, PermissionType.WRITE, PermissionScope.GLOBAL),
            Permission("api.admin", "Admin API", "Access administrative API endpoints", 
                      ResourceType.API, PermissionType.ADMIN, PermissionScope.GLOBAL, dangerous=True),
            
            # Workspace
            Permission("workspace.read", "Read Workspace", "Read workspace data", 
                      ResourceType.WORKSPACE, PermissionType.READ, PermissionScope.WORKSPACE, auto_grant=True),
            Permission("workspace.write", "Write Workspace", "Modify workspace data", 
                      ResourceType.WORKSPACE, PermissionType.WRITE, PermissionScope.WORKSPACE),
            Permission("workspace.admin", "Admin Workspace", "Administer workspace", 
                      ResourceType.WORKSPACE, PermissionType.ADMIN, PermissionScope.WORKSPACE, dangerous=True),
            
            # User Data
            Permission("user.read", "Read User Data", "Read user profile and settings", 
                      ResourceType.USER_DATA, PermissionType.READ, PermissionScope.USER),
            Permission("user.write", "Write User Data", "Modify user profile and settings", 
                      ResourceType.USER_DATA, PermissionType.WRITE, PermissionScope.USER, dangerous=True),
            
            # System
            Permission("system.config", "System Config", "Access system configuration", 
                      ResourceType.SYSTEM, PermissionType.READ, PermissionScope.GLOBAL, dangerous=True),
            Permission("system.admin", "System Admin", "System administration", 
                      ResourceType.SYSTEM, PermissionType.ADMIN, PermissionScope.GLOBAL, dangerous=True),
            
            # Plugin Management
            Permission("plugin.manage", "Manage Plugins", "Install/uninstall plugins", 
                      ResourceType.PLUGIN, PermissionType.ADMIN, PermissionScope.GLOBAL, dangerous=True),
            Permission("plugin.communicate", "Plugin Communication", "Communicate with other plugins", 
                      ResourceType.PLUGIN, PermissionType.EXECUTE, PermissionScope.GLOBAL, auto_grant=True),
            
            # Events
            Permission("event.emit", "Emit Events", "Emit system events", 
                      ResourceType.EVENT, PermissionType.EXECUTE, PermissionScope.GLOBAL, auto_grant=True),
            Permission("event.listen", "Listen Events", "Listen to system events", 
                      ResourceType.EVENT, PermissionType.READ, PermissionScope.GLOBAL, auto_grant=True),
        ]
        
        for perm in standard_perms:
            self.permissions[perm.id] = perm
    
    async def register_plugin_permissions(self, metadata: PluginMetadata) -> bool:
        """Register permissions required by a plugin"""
        try:
            plugin_id = metadata.id
            
            # Check if all required permissions exist
            missing_permissions = []
            for perm_req in metadata.permissions:
                if perm_req.permission not in self.permissions:
                    missing_permissions.append(perm_req.permission)
            
            if missing_permissions:
                logger.warning(f"Plugin {plugin_id} requires unknown permissions: {missing_permissions}")
            
            # Auto-grant safe permissions
            auto_granted = []
            for perm_req in metadata.permissions:
                if perm_req.permission in self.permissions:
                    perm = self.permissions[perm_req.permission]
                    if perm.auto_grant and not perm.dangerous:
                        await self.grant_permission(plugin_id, perm_req.permission, 
                                                   scope_value=perm_req.scope)
                        auto_granted.append(perm_req.permission)
            
            if auto_granted:
                logger.info(f"Auto-granted permissions to {plugin_id}: {auto_granted}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register permissions for {plugin_id}: {e}")
            return False
    
    async def grant_permission(self, plugin_id: str, permission_id: str,
                             scope_value: Optional[str] = None,
                             granted_by: str = "system",
                             expires_at: Optional[datetime] = None,
                             conditions: Dict[str, Any] = None) -> str:
        """Grant a permission to a plugin"""
        if permission_id not in self.permissions:
            raise PluginException(f"Permission {permission_id} not found")
        
        grant_id = hashlib.md5(f"{plugin_id}:{permission_id}:{scope_value}".encode()).hexdigest()
        
        grant = PermissionGrant(
            id=grant_id,
            plugin_id=plugin_id,
            permission_id=permission_id,
            scope_value=scope_value,
            granted_by=granted_by,
            expires_at=expires_at,
            conditions=conditions or {}
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO permission_grants 
                (id, plugin_id, permission_id, scope_value, granted_by, expires_at, conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                grant.id, grant.plugin_id, grant.permission_id, grant.scope_value,
                grant.granted_by, grant.expires_at, json.dumps(grant.conditions)
            ))
            conn.commit()
        finally:
            conn.close()
        
        # Update in-memory cache
        if plugin_id not in self.plugin_grants:
            self.plugin_grants[plugin_id] = set()
        self.plugin_grants[plugin_id].add(grant_id)
        
        logger.info(f"Granted permission {permission_id} to plugin {plugin_id}")
        return grant_id
    
    async def revoke_permission(self, plugin_id: str, permission_id: str,
                              scope_value: Optional[str] = None,
                              revoked_by: str = "system") -> bool:
        """Revoke a permission from a plugin"""
        grant_id = hashlib.md5(f"{plugin_id}:{permission_id}:{scope_value}".encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                UPDATE permission_grants 
                SET revoked = TRUE, revoked_at = CURRENT_TIMESTAMP, revoked_by = ?
                WHERE id = ? AND plugin_id = ?
            """, (revoked_by, grant_id, plugin_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                
                # Update in-memory cache
                if plugin_id in self.plugin_grants:
                    self.plugin_grants[plugin_id].discard(grant_id)
                
                logger.info(f"Revoked permission {permission_id} from plugin {plugin_id}")
                return True
            else:
                return False
                
        finally:
            conn.close()
    
    async def check_permission(self, plugin_id: str, permission_id: str,
                             resource_path: str = "", scope_value: Optional[str] = None,
                             context: Dict[str, Any] = None) -> bool:
        """Check if a plugin has a specific permission"""
        try:
            # Create access request for auditing
            request = AccessRequest(
                id=hashlib.md5(f"{plugin_id}:{permission_id}:{resource_path}:{datetime.utcnow()}".encode()).hexdigest(),
                plugin_id=plugin_id,
                permission_id=permission_id,
                resource_path=resource_path,
                scope_value=scope_value,
                context=context or {}
            )
            
            # Check if permission exists
            if permission_id not in self.permissions:
                request.granted = False
                request.reason = f"Permission {permission_id} not found"
                await self._log_access_request(request)
                return False
            
            permission = self.permissions[permission_id]
            
            # Check for active grant
            grant_id = hashlib.md5(f"{plugin_id}:{permission_id}:{scope_value}".encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute("""
                    SELECT * FROM permission_grants 
                    WHERE id = ? AND plugin_id = ? AND revoked = FALSE
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, (grant_id, plugin_id))
                
                grant_row = cursor.fetchone()
                
                if not grant_row:
                    request.granted = False
                    request.reason = "Permission not granted or expired"
                    await self._log_access_request(request)
                    return False
                
                # Check conditions if any
                grant_conditions = json.loads(grant_row[10] or "{}")
                if not await self._check_conditions(grant_conditions, context or {}):
                    request.granted = False
                    request.reason = "Permission conditions not met"
                    await self._log_access_request(request)
                    return False
                
                # Check rate limits
                if not await self._check_rate_limit(plugin_id, permission_id):
                    request.granted = False
                    request.reason = "Rate limit exceeded"
                    await self._log_access_request(request)
                    return False
                
                request.granted = True
                request.reason = "Permission granted"
                await self._log_access_request(request)
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error checking permission {permission_id} for {plugin_id}: {e}")
            return False
    
    async def check_plugin_permissions(self, plugin_id: str) -> bool:
        """Check if plugin has all required permissions"""
        # This would be called during plugin activation
        # For now, return True (implementation would check metadata requirements)
        return True
    
    async def list_plugin_permissions(self, plugin_id: str) -> List[Dict[str, Any]]:
        """List all permissions granted to a plugin"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT pg.*, p.name, p.description, p.dangerous
                FROM permission_grants pg
                JOIN permissions p ON pg.permission_id = p.id
                WHERE pg.plugin_id = ? AND pg.revoked = FALSE
                AND (pg.expires_at IS NULL OR pg.expires_at > CURRENT_TIMESTAMP)
            """, (plugin_id,))
            
            permissions = []
            for row in cursor.fetchall():
                permissions.append({
                    "grant_id": row[0],
                    "permission_id": row[2],
                    "permission_name": row[11],
                    "description": row[12],
                    "dangerous": bool(row[13]),
                    "scope_value": row[3],
                    "granted_by": row[4],
                    "granted_at": row[5],
                    "expires_at": row[6]
                })
            
            return permissions
            
        finally:
            conn.close()
    
    async def get_permission_requests(self, plugin_id: str = None, 
                                    limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent permission access requests"""
        conn = sqlite3.connect(self.db_path)
        try:
            if plugin_id:
                cursor = conn.execute("""
                    SELECT * FROM access_requests 
                    WHERE plugin_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (plugin_id, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM access_requests 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            requests = []
            for row in cursor.fetchall():
                requests.append({
                    "id": row[0],
                    "plugin_id": row[1],
                    "permission_id": row[2],
                    "resource_path": row[3],
                    "scope_value": row[4],
                    "timestamp": row[5],
                    "granted": bool(row[6]),
                    "reason": row[7],
                    "context": json.loads(row[8] or "{}")
                })
            
            return requests
            
        finally:
            conn.close()
    
    async def create_custom_permission(self, permission_id: str, name: str, 
                                     description: str, resource_type: ResourceType,
                                     permission_type: PermissionType,
                                     scope: PermissionScope, dangerous: bool = False) -> bool:
        """Create a custom permission"""
        if permission_id in self.permissions:
            raise PluginException(f"Permission {permission_id} already exists")
        
        permission = Permission(
            id=permission_id,
            name=name,
            description=description,
            resource_type=resource_type,
            permission_type=permission_type,
            scope=scope,
            dangerous=dangerous
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO permissions 
                (id, name, description, resource_type, permission_type, scope, dangerous)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                permission.id, permission.name, permission.description,
                permission.resource_type.value, permission.permission_type.value,
                permission.scope.value, permission.dangerous
            ))
            conn.commit()
        finally:
            conn.close()
        
        # Update in-memory cache
        self.permissions[permission_id] = permission
        
        logger.info(f"Created custom permission: {permission_id}")
        return True
    
    async def set_security_policy(self, plugin_id: str, policy: Dict[str, Any]):
        """Set security policy for a plugin"""
        self.security_policies[plugin_id] = policy
        logger.info(f"Set security policy for plugin {plugin_id}")
    
    async def get_security_policy(self, plugin_id: str) -> Dict[str, Any]:
        """Get security policy for a plugin"""
        return self.security_policies.get(plugin_id, {})
    
    async def audit_permissions(self) -> Dict[str, Any]:
        """Audit plugin permissions and return security report"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Get permission statistics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_grants,
                    COUNT(CASE WHEN p.dangerous = 1 THEN 1 END) as dangerous_grants,
                    COUNT(DISTINCT pg.plugin_id) as plugins_with_perms
                FROM permission_grants pg
                JOIN permissions p ON pg.permission_id = p.id
                WHERE pg.revoked = FALSE
            """)
            stats = cursor.fetchone()
            
            # Get top permission users
            cursor = conn.execute("""
                SELECT plugin_id, COUNT(*) as perm_count
                FROM permission_grants
                WHERE revoked = FALSE
                GROUP BY plugin_id
                ORDER BY perm_count DESC
                LIMIT 10
            """)
            top_users = cursor.fetchall()
            
            # Get recent failed access attempts
            cursor = conn.execute("""
                SELECT plugin_id, permission_id, COUNT(*) as failures
                FROM access_requests
                WHERE granted = FALSE AND timestamp > datetime('now', '-24 hours')
                GROUP BY plugin_id, permission_id
                ORDER BY failures DESC
                LIMIT 10
            """)
            failed_attempts = cursor.fetchall()
            
            return {
                "total_grants": stats[0],
                "dangerous_grants": stats[1],
                "plugins_with_permissions": stats[2],
                "top_permission_users": [{"plugin_id": row[0], "permission_count": row[1]} for row in top_users],
                "recent_failures": [{"plugin_id": row[0], "permission_id": row[1], "failure_count": row[2]} for row in failed_attempts],
                "audit_timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            conn.close()
    
    async def _log_access_request(self, request: AccessRequest):
        """Log access request to database and memory"""
        self.access_log.append(request)
        
        # Keep only recent requests in memory
        if len(self.access_log) > 1000:
            self.access_log = self.access_log[-1000:]
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO access_requests 
                (id, plugin_id, permission_id, resource_path, scope_value, granted, reason, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.id, request.plugin_id, request.permission_id,
                request.resource_path, request.scope_value, request.granted,
                request.reason, json.dumps(request.context)
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to log access request: {e}")
        finally:
            conn.close()
    
    async def _check_conditions(self, conditions: Dict[str, Any], 
                              context: Dict[str, Any]) -> bool:
        """Check if permission conditions are met"""
        for key, expected_value in conditions.items():
            if key not in context or context[key] != expected_value:
                return False
        return True
    
    async def _check_rate_limit(self, plugin_id: str, permission_id: str) -> bool:
        """Check rate limiting for permission usage"""
        # Simple rate limiting implementation
        current_minute = datetime.utcnow().replace(second=0, microsecond=0)
        key = f"{plugin_id}:{permission_id}:{current_minute}"
        
        if plugin_id not in self.rate_limits:
            self.rate_limits[plugin_id] = {}
        
        current_count = self.rate_limits[plugin_id].get(key, 0)
        limit = 100  # 100 permission checks per minute
        
        if current_count >= limit:
            return False
        
        self.rate_limits[plugin_id][key] = current_count + 1
        return True