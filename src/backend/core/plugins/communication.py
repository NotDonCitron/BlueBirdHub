"""
Plugin Communication Bus

Provides secure inter-plugin communication with message passing,
RPC calls, and data sharing capabilities.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Callable, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import weakref
from collections import defaultdict

from .base import PluginBase, PluginException, PluginSecurityException
from .event_system import Event, EventPriority


logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message types for plugin communication"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    RPC_CALL = "rpc_call"
    RPC_RESPONSE = "rpc_response"


class MessagePriority(Enum):
    """Message priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class Message:
    """Inter-plugin message"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.NOTIFICATION
    priority: MessagePriority = MessagePriority.NORMAL
    source_plugin: str = ""
    target_plugin: Optional[str] = None
    method: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl: Optional[timedelta] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    encrypted: bool = False
    signature: Optional[str] = None


@dataclass
class RPCCall:
    """RPC call tracking"""
    id: str
    source_plugin: str
    target_plugin: str
    method: str
    args: List[Any]
    kwargs: Dict[str, Any]
    future: asyncio.Future
    timeout: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MessageChannel:
    """Message channel configuration"""
    name: str
    owner_plugin: str
    subscribers: Set[str] = field(default_factory=set)
    max_size: int = 1000
    persistent: bool = False
    encrypted: bool = False
    access_control: Dict[str, str] = field(default_factory=dict)  # plugin_id -> permission


class PluginCommunicationBus:
    """Central communication bus for inter-plugin messaging"""
    
    def __init__(self, max_queue_size: int = 10000):
        self.max_queue_size = max_queue_size
        
        # Message routing
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.message_history: Dict[str, List[Message]] = defaultdict(lambda: [])
        
        # Plugin registry
        self.plugins: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        self.plugin_interfaces: Dict[str, Dict[str, Callable]] = defaultdict(dict)
        
        # RPC management
        self.pending_rpcs: Dict[str, RPCCall] = {}
        self.rpc_timeout_task: Optional[asyncio.Task] = None
        
        # Channels
        self.channels: Dict[str, MessageChannel] = {}
        self.channel_messages: Dict[str, List[Message]] = defaultdict(list)
        
        # Security
        self.permissions: Dict[str, Set[str]] = defaultdict(set)  # plugin_id -> allowed_targets
        self.rate_limits: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Processing state
        self._processing = False
        self._processor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "rpc_calls": 0,
            "rpc_timeouts": 0
        }
    
    async def start(self):
        """Start the communication bus"""
        if not self._processing:
            self._processing = True
            self._processor_task = asyncio.create_task(self._process_messages())
            self.rpc_timeout_task = asyncio.create_task(self._cleanup_rpc_timeouts())
            logger.info("Plugin Communication Bus started")
    
    async def stop(self):
        """Stop the communication bus"""
        if self._processing:
            self._processing = False
            self._shutdown_event.set()
            
            # Cancel tasks
            for task in [self._processor_task, self.rpc_timeout_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Cancel pending RPCs
            for rpc_call in self.pending_rpcs.values():
                if not rpc_call.future.done():
                    rpc_call.future.cancel()
            
            logger.info("Plugin Communication Bus stopped")
    
    async def register_plugin(self, plugin_id: str, plugin_instance: PluginBase):
        """Register a plugin with the communication bus"""
        self.plugins[plugin_id] = plugin_instance
        
        # Register plugin's public interface
        interface = self._discover_plugin_interface(plugin_instance)
        self.plugin_interfaces[plugin_id] = interface
        
        logger.debug(f"Registered plugin {plugin_id} with communication bus")
    
    async def unregister_plugin(self, plugin_id: str):
        """Unregister a plugin from the communication bus"""
        # Remove from registries
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
        if plugin_id in self.plugin_interfaces:
            del self.plugin_interfaces[plugin_id]
        if plugin_id in self.permissions:
            del self.permissions[plugin_id]
        if plugin_id in self.rate_limits:
            del self.rate_limits[plugin_id]
        
        # Cancel RPCs from this plugin
        for rpc_id, rpc_call in list(self.pending_rpcs.items()):
            if rpc_call.source_plugin == plugin_id or rpc_call.target_plugin == plugin_id:
                if not rpc_call.future.done():
                    rpc_call.future.cancel()
                del self.pending_rpcs[rpc_id]
        
        # Remove from channels
        for channel in self.channels.values():
            channel.subscribers.discard(plugin_id)
        
        # Remove owned channels
        owned_channels = [name for name, channel in self.channels.items() 
                         if channel.owner_plugin == plugin_id]
        for channel_name in owned_channels:
            del self.channels[channel_name]
            if channel_name in self.channel_messages:
                del self.channel_messages[channel_name]
        
        logger.debug(f"Unregistered plugin {plugin_id} from communication bus")
    
    async def send_message(self, source_plugin: str, target_plugin: str, 
                          data: Dict[str, Any], message_type: MessageType = MessageType.NOTIFICATION,
                          priority: MessagePriority = MessagePriority.NORMAL,
                          context: Dict[str, Any] = None,
                          ttl: Optional[timedelta] = None) -> str:
        """Send a message to another plugin"""
        # Check permissions
        if not self._check_send_permission(source_plugin, target_plugin):
            raise PluginSecurityException(f"Plugin {source_plugin} not allowed to send to {target_plugin}")
        
        # Check rate limits
        if not self._check_rate_limit(source_plugin, target_plugin):
            raise PluginException(f"Rate limit exceeded for {source_plugin} -> {target_plugin}")
        
        message = Message(
            type=message_type,
            priority=priority,
            source_plugin=source_plugin,
            target_plugin=target_plugin,
            data=data,
            context=context or {},
            ttl=ttl
        )
        
        try:
            await self.message_queue.put(message)
            self.stats["messages_sent"] += 1
            logger.debug(f"Queued message {message.id} from {source_plugin} to {target_plugin}")
            return message.id
        except asyncio.QueueFull:
            self.stats["messages_failed"] += 1
            raise PluginException("Message queue full")
    
    async def broadcast_message(self, source_plugin: str, data: Dict[str, Any],
                              exclude: Set[str] = None,
                              priority: MessagePriority = MessagePriority.NORMAL) -> List[str]:
        """Broadcast a message to all plugins"""
        exclude = exclude or set()
        exclude.add(source_plugin)  # Don't send to self
        
        message_ids = []
        for plugin_id in self.plugins.keys():
            if plugin_id not in exclude:
                try:
                    msg_id = await self.send_message(
                        source_plugin, plugin_id, data,
                        MessageType.BROADCAST, priority
                    )
                    message_ids.append(msg_id)
                except Exception as e:
                    logger.warning(f"Failed to broadcast to {plugin_id}: {e}")
        
        return message_ids
    
    async def call_rpc(self, source_plugin: str, target_plugin: str, 
                      method: str, *args, timeout: float = 30.0, **kwargs) -> Any:
        """Make an RPC call to another plugin"""
        # Check if target plugin exists and has the method
        if target_plugin not in self.plugin_interfaces:
            raise PluginException(f"Plugin {target_plugin} not found")
        
        if method not in self.plugin_interfaces[target_plugin]:
            raise PluginException(f"Method {method} not found in plugin {target_plugin}")
        
        # Create RPC call
        rpc_id = str(uuid.uuid4())
        future = asyncio.Future()
        
        rpc_call = RPCCall(
            id=rpc_id,
            source_plugin=source_plugin,
            target_plugin=target_plugin,
            method=method,
            args=list(args),
            kwargs=kwargs,
            future=future,
            timeout=timeout
        )
        
        self.pending_rpcs[rpc_id] = rpc_call
        
        # Send RPC message
        message = Message(
            type=MessageType.RPC_CALL,
            priority=MessagePriority.HIGH,
            source_plugin=source_plugin,
            target_plugin=target_plugin,
            method=method,
            data={
                "rpc_id": rpc_id,
                "args": args,
                "kwargs": kwargs
            },
            correlation_id=rpc_id
        )
        
        try:
            await self.message_queue.put(message)
            self.stats["rpc_calls"] += 1
            
            # Wait for response
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
            
        except asyncio.TimeoutError:
            self.stats["rpc_timeouts"] += 1
            if rpc_id in self.pending_rpcs:
                del self.pending_rpcs[rpc_id]
            raise PluginException(f"RPC call to {target_plugin}.{method} timed out")
        except Exception as e:
            if rpc_id in self.pending_rpcs:
                del self.pending_rpcs[rpc_id]
            raise
    
    async def create_channel(self, plugin_id: str, channel_name: str,
                           max_size: int = 1000, persistent: bool = False,
                           encrypted: bool = False) -> bool:
        """Create a message channel"""
        if channel_name in self.channels:
            raise PluginException(f"Channel {channel_name} already exists")
        
        channel = MessageChannel(
            name=channel_name,
            owner_plugin=plugin_id,
            max_size=max_size,
            persistent=persistent,
            encrypted=encrypted
        )
        
        self.channels[channel_name] = channel
        logger.info(f"Created channel {channel_name} by plugin {plugin_id}")
        return True
    
    async def join_channel(self, plugin_id: str, channel_name: str) -> bool:
        """Join a message channel"""
        if channel_name not in self.channels:
            raise PluginException(f"Channel {channel_name} not found")
        
        channel = self.channels[channel_name]
        
        # Check access control
        if channel.access_control and plugin_id not in channel.access_control:
            raise PluginSecurityException(f"Plugin {plugin_id} not authorized for channel {channel_name}")
        
        channel.subscribers.add(plugin_id)
        logger.debug(f"Plugin {plugin_id} joined channel {channel_name}")
        return True
    
    async def leave_channel(self, plugin_id: str, channel_name: str) -> bool:
        """Leave a message channel"""
        if channel_name in self.channels:
            self.channels[channel_name].subscribers.discard(plugin_id)
            logger.debug(f"Plugin {plugin_id} left channel {channel_name}")
            return True
        return False
    
    async def send_to_channel(self, plugin_id: str, channel_name: str, 
                            data: Dict[str, Any],
                            priority: MessagePriority = MessagePriority.NORMAL) -> List[str]:
        """Send a message to all channel subscribers"""
        if channel_name not in self.channels:
            raise PluginException(f"Channel {channel_name} not found")
        
        channel = self.channels[channel_name]
        
        if plugin_id not in channel.subscribers:
            raise PluginException(f"Plugin {plugin_id} not subscribed to channel {channel_name}")
        
        message_ids = []
        subscribers = channel.subscribers.copy()
        subscribers.discard(plugin_id)  # Don't send to self
        
        for subscriber_id in subscribers:
            try:
                msg_id = await self.send_message(
                    plugin_id, subscriber_id, data,
                    MessageType.NOTIFICATION, priority,
                    context={"channel": channel_name}
                )
                message_ids.append(msg_id)
            except Exception as e:
                logger.warning(f"Failed to send to {subscriber_id} on channel {channel_name}: {e}")
        
        # Store in channel history
        message = Message(
            source_plugin=plugin_id,
            data=data,
            priority=priority,
            context={"channel": channel_name}
        )
        
        channel_messages = self.channel_messages[channel_name]
        channel_messages.append(message)
        
        # Trim channel history
        if len(channel_messages) > channel.max_size:
            channel_messages[:] = channel_messages[-channel.max_size:]
        
        return message_ids
    
    def set_plugin_permissions(self, plugin_id: str, allowed_targets: Set[str]):
        """Set communication permissions for a plugin"""
        self.permissions[plugin_id] = allowed_targets
    
    def add_plugin_permission(self, plugin_id: str, target_plugin: str):
        """Add permission for a plugin to communicate with another"""
        self.permissions[plugin_id].add(target_plugin)
    
    def remove_plugin_permission(self, plugin_id: str, target_plugin: str):
        """Remove permission for a plugin to communicate with another"""
        self.permissions[plugin_id].discard(target_plugin)
    
    def get_plugin_messages(self, plugin_id: str, limit: int = 100) -> List[Message]:
        """Get message history for a plugin"""
        messages = self.message_history[plugin_id]
        return messages[-limit:]
    
    def get_channel_messages(self, channel_name: str, limit: int = 100) -> List[Message]:
        """Get message history for a channel"""
        if channel_name in self.channel_messages:
            messages = self.channel_messages[channel_name]
            return messages[-limit:]
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get communication bus statistics"""
        return {
            **self.stats,
            "queue_size": self.message_queue.qsize(),
            "registered_plugins": len(self.plugins),
            "pending_rpcs": len(self.pending_rpcs),
            "channels": len(self.channels),
            "total_subscribers": sum(len(channel.subscribers) for channel in self.channels.values())
        }
    
    async def _process_messages(self):
        """Main message processing loop"""
        while self._processing and not self._shutdown_event.is_set():
            try:
                try:
                    message = await asyncio.wait_for(
                        self.message_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                await self._deliver_message(message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _deliver_message(self, message: Message):
        """Deliver a message to its target"""
        try:
            # Check if message has expired
            if message.ttl and datetime.utcnow() - message.timestamp > message.ttl:
                logger.debug(f"Message {message.id} expired, skipping")
                return
            
            # Add to history
            self.message_history[message.target_plugin].append(message)
            
            # Deliver based on message type
            if message.type == MessageType.RPC_CALL:
                await self._handle_rpc_call(message)
            elif message.type == MessageType.RPC_RESPONSE:
                await self._handle_rpc_response(message)
            else:
                await self._deliver_regular_message(message)
            
            self.stats["messages_delivered"] += 1
            
        except Exception as e:
            logger.error(f"Failed to deliver message {message.id}: {e}")
            self.stats["messages_failed"] += 1
    
    async def _deliver_regular_message(self, message: Message):
        """Deliver a regular message to the target plugin"""
        if message.target_plugin not in self.plugins:
            logger.warning(f"Target plugin {message.target_plugin} not found")
            return
        
        plugin_instance = self.plugins[message.target_plugin]
        
        # Check if plugin has a message handler
        if hasattr(plugin_instance, 'handle_message'):
            try:
                if asyncio.iscoroutinefunction(plugin_instance.handle_message):
                    await plugin_instance.handle_message(message)
                else:
                    plugin_instance.handle_message(message)
            except Exception as e:
                logger.error(f"Plugin {message.target_plugin} message handler failed: {e}")
    
    async def _handle_rpc_call(self, message: Message):
        """Handle an RPC call message"""
        if message.target_plugin not in self.plugin_interfaces:
            await self._send_rpc_error(message, "Target plugin not found")
            return
        
        if message.method not in self.plugin_interfaces[message.target_plugin]:
            await self._send_rpc_error(message, f"Method {message.method} not found")
            return
        
        try:
            # Get the method
            plugin_instance = self.plugins[message.target_plugin]
            method = getattr(plugin_instance, message.method)
            
            # Call the method
            args = message.data.get("args", [])
            kwargs = message.data.get("kwargs", {})
            
            if asyncio.iscoroutinefunction(method):
                result = await method(*args, **kwargs)
            else:
                result = method(*args, **kwargs)
            
            # Send response
            await self._send_rpc_response(message, result)
            
        except Exception as e:
            logger.error(f"RPC call {message.method} failed: {e}")
            await self._send_rpc_error(message, str(e))
    
    async def _handle_rpc_response(self, message: Message):
        """Handle an RPC response message"""
        rpc_id = message.correlation_id
        if rpc_id not in self.pending_rpcs:
            logger.warning(f"No pending RPC for response {rpc_id}")
            return
        
        rpc_call = self.pending_rpcs[rpc_id]
        
        try:
            if "error" in message.data:
                rpc_call.future.set_exception(PluginException(message.data["error"]))
            else:
                rpc_call.future.set_result(message.data.get("result"))
        except Exception as e:
            logger.error(f"Failed to set RPC result: {e}")
        finally:
            del self.pending_rpcs[rpc_id]
    
    async def _send_rpc_response(self, original_message: Message, result: Any):
        """Send RPC response"""
        response = Message(
            type=MessageType.RPC_RESPONSE,
            priority=MessagePriority.HIGH,
            source_plugin=original_message.target_plugin,
            target_plugin=original_message.source_plugin,
            data={"result": result},
            correlation_id=original_message.data.get("rpc_id")
        )
        
        await self.message_queue.put(response)
    
    async def _send_rpc_error(self, original_message: Message, error: str):
        """Send RPC error response"""
        response = Message(
            type=MessageType.RPC_RESPONSE,
            priority=MessagePriority.HIGH,
            source_plugin=original_message.target_plugin,
            target_plugin=original_message.source_plugin,
            data={"error": error},
            correlation_id=original_message.data.get("rpc_id")
        )
        
        await self.message_queue.put(response)
    
    async def _cleanup_rpc_timeouts(self):
        """Clean up timed out RPC calls"""
        while self._processing and not self._shutdown_event.is_set():
            try:
                current_time = datetime.utcnow()
                
                # Check for timed out RPCs
                timed_out = []
                for rpc_id, rpc_call in self.pending_rpcs.items():
                    if rpc_call.timeout:
                        elapsed = (current_time - rpc_call.created_at).total_seconds()
                        if elapsed > rpc_call.timeout:
                            timed_out.append(rpc_id)
                
                # Remove timed out RPCs
                for rpc_id in timed_out:
                    rpc_call = self.pending_rpcs[rpc_id]
                    if not rpc_call.future.done():
                        rpc_call.future.set_exception(asyncio.TimeoutError("RPC call timed out"))
                    del self.pending_rpcs[rpc_id]
                    self.stats["rpc_timeouts"] += 1
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in RPC timeout cleanup: {e}")
                await asyncio.sleep(1)
    
    def _discover_plugin_interface(self, plugin_instance: PluginBase) -> Dict[str, Callable]:
        """Discover the public interface of a plugin"""
        interface = {}
        
        # Get all public methods that don't start with underscore
        for attr_name in dir(plugin_instance):
            if not attr_name.startswith('_'):
                attr = getattr(plugin_instance, attr_name)
                if callable(attr) and not attr_name in ['initialize', 'activate', 'deactivate', 'cleanup']:
                    interface[attr_name] = attr
        
        return interface
    
    def _check_send_permission(self, source_plugin: str, target_plugin: str) -> bool:
        """Check if source plugin can send to target plugin"""
        if source_plugin not in self.permissions:
            return True  # No restrictions by default
        
        allowed_targets = self.permissions[source_plugin]
        if "*" in allowed_targets:
            return True
        
        return target_plugin in allowed_targets
    
    def _check_rate_limit(self, source_plugin: str, target_plugin: str) -> bool:
        """Check rate limiting for plugin communication"""
        # Simple rate limiting - could be more sophisticated
        current_minute = datetime.utcnow().replace(second=0, microsecond=0)
        key = f"{source_plugin}:{target_plugin}:{current_minute}"
        
        current_count = self.rate_limits[source_plugin][key]
        if current_count >= 100:  # 100 messages per minute limit
            return False
        
        self.rate_limits[source_plugin][key] += 1
        return True