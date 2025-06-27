"""
Plugin Event System

Provides centralized event management for plugin communication,
hooks, and inter-plugin messaging with proper isolation and security.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Callable, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import weakref
import uuid
from collections import defaultdict, deque

from .base import PluginBase, PluginException


logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class EventScope(Enum):
    """Event scope definitions"""
    GLOBAL = "global"
    PLUGIN = "plugin"
    USER = "user"
    WORKSPACE = "workspace"
    SYSTEM = "system"


@dataclass
class Event:
    """Event data structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    scope: EventScope = EventScope.GLOBAL
    source_plugin: Optional[str] = None
    target_plugin: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl: Optional[timedelta] = None
    propagation_stopped: bool = False
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class EventHandler:
    """Event handler registration"""
    id: str
    plugin_id: str
    event_type: str
    handler: Callable
    priority: EventPriority
    async_handler: bool
    once: bool = False
    conditions: Dict[str, Any] = field(default_factory=dict)
    rate_limit: Optional[int] = None
    last_called: Optional[datetime] = None


@dataclass
class EventSubscription:
    """Event subscription configuration"""
    subscriber_id: str
    event_pattern: str
    callback: Callable
    filters: Dict[str, Any] = field(default_factory=dict)
    max_events: Optional[int] = None
    events_received: int = 0


class PluginEventSystem:
    """Central event management system for plugins"""
    
    def __init__(self, max_queue_size: int = 10000, max_history: int = 1000):
        self.max_queue_size = max_queue_size
        self.max_history = max_history
        
        # Event handlers and subscriptions
        self.handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self.global_handlers: List[EventHandler] = []
        self.subscriptions: Dict[str, List[EventSubscription]] = defaultdict(list)
        
        # Event processing
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.event_history: deque = deque(maxlen=max_history)
        self.failed_events: deque = deque(maxlen=100)
        
        # Plugin registry
        self.plugins: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        
        # Processing state
        self._processing = False
        self._processor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self.stats = {
            "events_processed": 0,
            "events_failed": 0,
            "handlers_called": 0,
            "subscriptions_notified": 0
        }
        
        # Event type registry
        self.event_types: Dict[str, Dict[str, Any]] = {}
        
    async def start(self):
        """Start the event processing system"""
        if not self._processing:
            self._processing = True
            self._processor_task = asyncio.create_task(self._process_events())
            logger.info("Plugin Event System started")
    
    async def stop(self):
        """Stop the event processing system"""
        if self._processing:
            self._processing = False
            self._shutdown_event.set()
            
            if self._processor_task:
                self._processor_task.cancel()
                try:
                    await self._processor_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Plugin Event System stopped")
    
    async def register_plugin(self, plugin_id: str, plugin_instance: PluginBase):
        """Register a plugin with the event system"""
        self.plugins[plugin_id] = plugin_instance
        logger.debug(f"Registered plugin {plugin_id} with event system")
    
    async def unregister_plugin(self, plugin_id: str):
        """Unregister a plugin from the event system"""
        # Remove all handlers for this plugin
        for event_type in list(self.handlers.keys()):
            self.handlers[event_type] = [
                h for h in self.handlers[event_type] 
                if h.plugin_id != plugin_id
            ]
            if not self.handlers[event_type]:
                del self.handlers[event_type]
        
        # Remove global handlers
        self.global_handlers = [
            h for h in self.global_handlers 
            if h.plugin_id != plugin_id
        ]
        
        # Remove subscriptions
        for event_pattern in list(self.subscriptions.keys()):
            self.subscriptions[event_pattern] = [
                s for s in self.subscriptions[event_pattern]
                if s.subscriber_id != plugin_id
            ]
            if not self.subscriptions[event_pattern]:
                del self.subscriptions[event_pattern]
        
        # Remove from plugin registry
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
        
        logger.debug(f"Unregistered plugin {plugin_id} from event system")
    
    def register_event_type(self, event_type: str, schema: Dict[str, Any], 
                          description: str = ""):
        """Register a new event type with schema"""
        self.event_types[event_type] = {
            "schema": schema,
            "description": description,
            "registered_at": datetime.utcnow(),
            "usage_count": 0
        }
        logger.debug(f"Registered event type: {event_type}")
    
    def add_handler(self, plugin_id: str, event_type: str, handler: Callable,
                   priority: EventPriority = EventPriority.NORMAL,
                   once: bool = False, conditions: Dict[str, Any] = None,
                   rate_limit: Optional[int] = None) -> str:
        """Add an event handler"""
        handler_id = str(uuid.uuid4())
        
        event_handler = EventHandler(
            id=handler_id,
            plugin_id=plugin_id,
            event_type=event_type,
            handler=handler,
            priority=priority,
            async_handler=asyncio.iscoroutinefunction(handler),
            once=once,
            conditions=conditions or {},
            rate_limit=rate_limit
        )
        
        if event_type == "*":
            self.global_handlers.append(event_handler)
        else:
            self.handlers[event_type].append(event_handler)
        
        # Sort handlers by priority
        if event_type == "*":
            self.global_handlers.sort(key=lambda h: h.priority.value)
        else:
            self.handlers[event_type].sort(key=lambda h: h.priority.value)
        
        logger.debug(f"Added handler {handler_id} for event {event_type} from plugin {plugin_id}")
        return handler_id
    
    def remove_handler(self, handler_id: str) -> bool:
        """Remove an event handler"""
        # Check global handlers
        for i, handler in enumerate(self.global_handlers):
            if handler.id == handler_id:
                del self.global_handlers[i]
                logger.debug(f"Removed global handler {handler_id}")
                return True
        
        # Check event-specific handlers
        for event_type, handlers in self.handlers.items():
            for i, handler in enumerate(handlers):
                if handler.id == handler_id:
                    del handlers[i]
                    logger.debug(f"Removed handler {handler_id} for event {event_type}")
                    return True
        
        return False
    
    def subscribe(self, subscriber_id: str, event_pattern: str, callback: Callable,
                 filters: Dict[str, Any] = None, max_events: Optional[int] = None) -> str:
        """Subscribe to events matching a pattern"""
        subscription = EventSubscription(
            subscriber_id=subscriber_id,
            event_pattern=event_pattern,
            callback=callback,
            filters=filters or {},
            max_events=max_events
        )
        
        self.subscriptions[event_pattern].append(subscription)
        
        subscription_id = f"{subscriber_id}:{event_pattern}:{id(subscription)}"
        logger.debug(f"Created subscription {subscription_id}")
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        parts = subscription_id.split(":", 2)
        if len(parts) < 2:
            return False
        
        subscriber_id, event_pattern = parts[0], parts[1]
        
        if event_pattern in self.subscriptions:
            original_count = len(self.subscriptions[event_pattern])
            self.subscriptions[event_pattern] = [
                s for s in self.subscriptions[event_pattern]
                if s.subscriber_id != subscriber_id
            ]
            
            removed = original_count - len(self.subscriptions[event_pattern])
            if removed > 0:
                logger.debug(f"Removed {removed} subscriptions for {subscription_id}")
                return True
        
        return False
    
    async def emit(self, event_type: str, data: Dict[str, Any] = None,
                  source_plugin: str = None, target_plugin: str = None,
                  scope: EventScope = EventScope.GLOBAL,
                  priority: EventPriority = EventPriority.NORMAL,
                  context: Dict[str, Any] = None) -> str:
        """Emit an event"""
        event = Event(
            type=event_type,
            scope=scope,
            source_plugin=source_plugin,
            target_plugin=target_plugin,
            data=data or {},
            context=context or {},
            priority=priority
        )
        
        # Validate event if schema is registered
        if event_type in self.event_types:
            self.event_types[event_type]["usage_count"] += 1
            # Schema validation would go here
        
        try:
            await self.event_queue.put(event)
            logger.debug(f"Emitted event {event.id} of type {event_type}")
            return event.id
        except asyncio.QueueFull:
            logger.error(f"Event queue full, dropping event {event.id}")
            self.stats["events_failed"] += 1
            raise PluginException("Event queue full")
    
    async def emit_sync(self, event_type: str, data: Dict[str, Any] = None,
                       source_plugin: str = None, target_plugin: str = None,
                       scope: EventScope = EventScope.GLOBAL,
                       priority: EventPriority = EventPriority.NORMAL,
                       context: Dict[str, Any] = None) -> List[Any]:
        """Emit an event and wait for all handlers to complete"""
        event = Event(
            type=event_type,
            scope=scope,
            source_plugin=source_plugin,
            target_plugin=target_plugin,
            data=data or {},
            context=context or {},
            priority=priority
        )
        
        return await self._process_event_sync(event)
    
    async def _process_events(self):
        """Main event processing loop"""
        while self._processing and not self._shutdown_event.is_set():
            try:
                # Wait for event or timeout
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the event
                await self._process_event(event)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_event(self, event: Event):
        """Process a single event"""
        try:
            # Check if event has expired
            if event.ttl and datetime.utcnow() - event.timestamp > event.ttl:
                logger.debug(f"Event {event.id} expired, skipping")
                return
            
            # Add to history
            self.event_history.append(event)
            
            # Get applicable handlers
            handlers = self._get_handlers_for_event(event)
            
            # Process handlers
            results = []
            for handler in handlers:
                try:
                    if await self._should_call_handler(handler, event):
                        result = await self._call_handler(handler, event)
                        results.append(result)
                        
                        # Remove one-time handlers
                        if handler.once:
                            self.remove_handler(handler.id)
                        
                        # Stop propagation if requested
                        if event.propagation_stopped:
                            break
                            
                except Exception as e:
                    logger.error(f"Handler {handler.id} failed for event {event.id}: {e}")
                    self.stats["events_failed"] += 1
            
            # Notify subscriptions
            await self._notify_subscriptions(event)
            
            self.stats["events_processed"] += 1
            
        except Exception as e:
            logger.error(f"Failed to process event {event.id}: {e}")
            self.failed_events.append({
                "event": event,
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            self.stats["events_failed"] += 1
    
    async def _process_event_sync(self, event: Event) -> List[Any]:
        """Process event synchronously and return results"""
        handlers = self._get_handlers_for_event(event)
        results = []
        
        for handler in handlers:
            try:
                if await self._should_call_handler(handler, event):
                    result = await self._call_handler(handler, event)
                    results.append(result)
                    
                    if event.propagation_stopped:
                        break
                        
            except Exception as e:
                logger.error(f"Handler {handler.id} failed for event {event.id}: {e}")
                results.append({"error": str(e)})
        
        await self._notify_subscriptions(event)
        return results
    
    def _get_handlers_for_event(self, event: Event) -> List[EventHandler]:
        """Get all handlers that should process this event"""
        handlers = []
        
        # Add global handlers
        handlers.extend(self.global_handlers)
        
        # Add event-specific handlers
        if event.type in self.handlers:
            handlers.extend(self.handlers[event.type])
        
        # Filter by target plugin if specified
        if event.target_plugin:
            handlers = [h for h in handlers if h.plugin_id == event.target_plugin]
        
        return sorted(handlers, key=lambda h: h.priority.value)
    
    async def _should_call_handler(self, handler: EventHandler, event: Event) -> bool:
        """Check if handler should be called for this event"""
        # Check rate limiting
        if handler.rate_limit and handler.last_called:
            time_since_last = datetime.utcnow() - handler.last_called
            if time_since_last.total_seconds() < handler.rate_limit:
                return False
        
        # Check conditions
        for key, expected_value in handler.conditions.items():
            if key in event.data:
                if event.data[key] != expected_value:
                    return False
            elif key in event.context:
                if event.context[key] != expected_value:
                    return False
            else:
                return False
        
        return True
    
    async def _call_handler(self, handler: EventHandler, event: Event) -> Any:
        """Call an event handler"""
        handler.last_called = datetime.utcnow()
        self.stats["handlers_called"] += 1
        
        try:
            if handler.async_handler:
                result = await handler.handler(event)
            else:
                result = handler.handler(event)
            
            return result
            
        except Exception as e:
            logger.error(f"Handler {handler.id} failed: {e}")
            raise
    
    async def _notify_subscriptions(self, event: Event):
        """Notify event subscriptions"""
        for pattern, subscriptions in self.subscriptions.items():
            if self._event_matches_pattern(event.type, pattern):
                for subscription in subscriptions[:]:  # Copy to avoid modification during iteration
                    try:
                        # Check filters
                        if self._event_matches_filters(event, subscription.filters):
                            # Call callback
                            if asyncio.iscoroutinefunction(subscription.callback):
                                await subscription.callback(event)
                            else:
                                subscription.callback(event)
                            
                            subscription.events_received += 1
                            self.stats["subscriptions_notified"] += 1
                            
                            # Check max events limit
                            if (subscription.max_events and 
                                subscription.events_received >= subscription.max_events):
                                subscriptions.remove(subscription)
                                
                    except Exception as e:
                        logger.error(f"Subscription callback failed: {e}")
    
    def _event_matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches subscription pattern"""
        if pattern == "*":
            return True
        if pattern == event_type:
            return True
        
        # Support wildcard patterns
        if "*" in pattern:
            import fnmatch
            return fnmatch.fnmatch(event_type, pattern)
        
        return False
    
    def _event_matches_filters(self, event: Event, filters: Dict[str, Any]) -> bool:
        """Check if event matches subscription filters"""
        for key, expected_value in filters.items():
            if key == "source_plugin":
                if event.source_plugin != expected_value:
                    return False
            elif key == "scope":
                if event.scope != expected_value:
                    return False
            elif key in event.data:
                if event.data[key] != expected_value:
                    return False
            elif key in event.context:
                if event.context[key] != expected_value:
                    return False
            else:
                return False
        
        return True
    
    def get_event_history(self, event_type: str = None, limit: int = 100) -> List[Event]:
        """Get event history"""
        events = list(self.event_history)
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        return events[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event system statistics"""
        return {
            **self.stats,
            "queue_size": self.event_queue.qsize(),
            "handlers_count": sum(len(handlers) for handlers in self.handlers.values()) + len(self.global_handlers),
            "subscriptions_count": sum(len(subs) for subs in self.subscriptions.values()),
            "registered_plugins": len(self.plugins),
            "registered_event_types": len(self.event_types),
            "failed_events_count": len(self.failed_events)
        }
    
    def get_plugin_handlers(self, plugin_id: str) -> List[Dict[str, Any]]:
        """Get all handlers registered by a plugin"""
        handlers = []
        
        # Global handlers
        for handler in self.global_handlers:
            if handler.plugin_id == plugin_id:
                handlers.append({
                    "id": handler.id,
                    "event_type": "*",
                    "priority": handler.priority.name,
                    "once": handler.once,
                    "conditions": handler.conditions
                })
        
        # Event-specific handlers
        for event_type, event_handlers in self.handlers.items():
            for handler in event_handlers:
                if handler.plugin_id == plugin_id:
                    handlers.append({
                        "id": handler.id,
                        "event_type": event_type,
                        "priority": handler.priority.name,
                        "once": handler.once,
                        "conditions": handler.conditions
                    })
        
        return handlers