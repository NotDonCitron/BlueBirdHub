"""
BlueBirdHub Plugin System

A comprehensive plugin architecture that enables secure and scalable extensibility
for BlueBirdHub functionality while maintaining system stability and security.
"""

from .base import PluginBase, PluginMetadata, PluginInterface
from .manager import PluginManager
from .registry import PluginRegistry
from .security import PluginSecurity, PluginSandbox
from .lifecycle import PluginLifecycleManager
from .marketplace import PluginMarketplace
from .event_system import PluginEventSystem
from .communication import PluginCommunicationBus
from .permissions import PluginPermissionManager
from .analytics import PluginAnalyticsManager
from .sdk import PluginSDK

__all__ = [
    'PluginBase',
    'PluginMetadata', 
    'PluginInterface',
    'PluginManager',
    'PluginRegistry',
    'PluginSecurity',
    'PluginSandbox',
    'PluginLifecycleManager',
    'PluginMarketplace',
    'PluginEventSystem',
    'PluginCommunicationBus',
    'PluginPermissionManager',
    'PluginAnalyticsManager',
    'PluginSDK'
]