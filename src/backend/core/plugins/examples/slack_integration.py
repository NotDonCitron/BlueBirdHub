"""
Example Slack Integration Plugin

Demonstrates how to create an integration plugin using the BlueBirdHub plugin SDK.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any

from ..sdk import BaseIntegrationPlugin, PluginBuilder, ConfigType
from ..base import PluginType, PluginMetadata


# Plugin configuration using builder pattern
def create_slack_plugin_manifest():
    """Create the plugin manifest for Slack integration"""
    builder = PluginBuilder("slack-integration", "Slack Integration")
    builder.version("1.0.0")
    builder.description("Integration with Slack for notifications and task management")
    builder.author("BlueBirdHub Team", "team@bluebirdhub.com")
    builder.type(PluginType.INTEGRATION)
    builder.entry_point("SlackIntegrationPlugin")
    builder.module_path("slack_integration")
    builder.category("communication")
    builder.tags("slack", "notifications", "messaging", "collaboration")
    builder.homepage("https://github.com/bluebirdhub/plugins/slack")
    builder.repository("https://github.com/bluebirdhub/plugins")
    
    # Configuration fields
    builder.add_config(
        "bot_token",
        ConfigType.STRING,
        "Slack Bot Token",
        required=True,
        secret=True
    )
    
    builder.add_config(
        "workspace_url",
        ConfigType.STRING,
        "Slack Workspace URL",
        default_value="https://yourworkspace.slack.com",
        required=True
    )
    
    builder.add_config(
        "default_channel",
        ConfigType.STRING,
        "Default notification channel",
        default_value="#general"
    )
    
    builder.add_config(
        "notification_types",
        ConfigType.ARRAY,
        "Types of notifications to send",
        default_value=["task_completed", "file_uploaded", "workspace_shared"],
        choices=["task_completed", "task_created", "file_uploaded", "workspace_shared", "user_joined"]
    )
    
    builder.add_config(
        "enable_two_way_sync",
        ConfigType.BOOLEAN,
        "Enable two-way synchronization with Slack",
        default_value=False
    )
    
    # Permissions
    builder.add_permission(
        "net.http",
        "HTTP requests to Slack API",
        "network",
        "execute",
        required=True
    )
    
    builder.add_permission(
        "workspace.write",
        "Create tasks from Slack messages",
        "workspace", 
        "write"
    )
    
    return builder.build()


class SlackIntegrationPlugin(BaseIntegrationPlugin):
    """Slack integration plugin implementation"""
    
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.slack_client = None
        self.bot_token = None
        self.webhook_handlers = {}
        
    async def initialize(self) -> bool:
        """Initialize the Slack plugin"""
        try:
            await super().initialize()
            
            # Get configuration
            self.bot_token = await self.sdk.get_config("bot_token")
            if not self.bot_token:
                self.logger.error("Slack bot token not configured")
                return False
            
            # Setup Slack client
            self.slack_client = SlackClient(self.bot_token, self.sdk)
            
            # Register event handlers
            await self._setup_event_handlers()
            
            self.logger.info("Slack integration initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Slack integration: {e}")
            return False
    
    async def activate(self) -> bool:
        """Activate the Slack plugin"""
        try:
            await super().activate()
            
            # Test Slack connection
            if not await self.authenticate():
                return False
            
            # Start listening for events
            await self._start_event_listeners()
            
            # Register webhook endpoints
            await self._register_webhooks()
            
            self.logger.info("Slack integration activated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate Slack integration: {e}")
            return False
    
    async def deactivate(self) -> bool:
        """Deactivate the Slack plugin"""
        try:
            # Stop event listeners
            await self._stop_event_listeners()
            
            # Unregister webhooks
            await self._unregister_webhooks()
            
            await super().deactivate()
            self.logger.info("Slack integration deactivated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate Slack integration: {e}")
            return False
    
    async def authenticate(self) -> bool:
        """Authenticate with Slack API"""
        try:
            if not self.slack_client:
                return False
                
            # Test API connection
            response = await self.slack_client.test_auth()
            if response.get("ok"):
                self.logger.info(f"Authenticated with Slack as {response.get('user')}")
                return True
            else:
                self.logger.error(f"Slack authentication failed: {response.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Slack authentication error: {e}")
            return False
    
    async def sync_data(self) -> bool:
        """Sync data with Slack"""
        try:
            # Get two-way sync setting
            enable_sync = await self.sdk.get_config("enable_two_way_sync", False)
            if not enable_sync:
                return True
            
            # Sync channels
            await self._sync_channels()
            
            # Sync recent messages if configured
            await self._sync_recent_messages()
            
            self.logger.info("Slack data sync completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Slack data sync failed: {e}")
            return False
    
    async def _setup_event_handlers(self):
        """Setup BlueBirdHub event handlers"""
        # Listen for task events
        self.sdk.add_event_handler("task.created", self._handle_task_created)
        self.sdk.add_event_handler("task.completed", self._handle_task_completed)
        self.sdk.add_event_handler("file.uploaded", self._handle_file_uploaded)
        self.sdk.add_event_handler("workspace.shared", self._handle_workspace_shared)
        self.sdk.add_event_handler("user.joined", self._handle_user_joined)
    
    async def _start_event_listeners(self):
        """Start listening for BlueBirdHub events"""
        notification_types = await self.sdk.get_config("notification_types", [])
        self.logger.info(f"Listening for events: {notification_types}")
    
    async def _stop_event_listeners(self):
        """Stop event listeners"""
        pass
    
    async def _register_webhooks(self):
        """Register Slack webhook endpoints"""
        # This would register webhook endpoints with the main application
        # to receive events from Slack
        pass
    
    async def _unregister_webhooks(self):
        """Unregister Slack webhook endpoints"""
        pass
    
    async def _handle_task_created(self, event):
        """Handle task created event"""
        try:
            if "task.created" not in await self.sdk.get_config("notification_types", []):
                return
            
            task_data = event.data
            message = f"📝 New task created: *{task_data.get('title')}*"
            
            if task_data.get('assigned_to'):
                message += f"\nAssigned to: {task_data['assigned_to']}"
            
            if task_data.get('due_date'):
                message += f"\nDue: {task_data['due_date']}"
            
            await self._send_notification(message)
            await self.sdk.track_feature_usage("task_notification")
            
        except Exception as e:
            self.logger.error(f"Failed to handle task created event: {e}")
            await self.sdk.track_error("event_handling", str(e))
    
    async def _handle_task_completed(self, event):
        """Handle task completed event"""
        try:
            if "task.completed" not in await self.sdk.get_config("notification_types", []):
                return
            
            task_data = event.data
            message = f"✅ Task completed: *{task_data.get('title')}*"
            
            if task_data.get('completed_by'):
                message += f"\nCompleted by: {task_data['completed_by']}"
            
            await self._send_notification(message)
            await self.sdk.track_feature_usage("task_completion_notification")
            
        except Exception as e:
            self.logger.error(f"Failed to handle task completed event: {e}")
            await self.sdk.track_error("event_handling", str(e))
    
    async def _handle_file_uploaded(self, event):
        """Handle file uploaded event"""
        try:
            if "file.uploaded" not in await self.sdk.get_config("notification_types", []):
                return
            
            file_data = event.data
            message = f"📎 File uploaded: *{file_data.get('filename')}*"
            
            if file_data.get('uploaded_by'):
                message += f"\nUploaded by: {file_data['uploaded_by']}"
            
            if file_data.get('size'):
                message += f"\nSize: {self._format_file_size(file_data['size'])}"
            
            await self._send_notification(message)
            await self.sdk.track_feature_usage("file_notification")
            
        except Exception as e:
            self.logger.error(f"Failed to handle file uploaded event: {e}")
            await self.sdk.track_error("event_handling", str(e))
    
    async def _handle_workspace_shared(self, event):
        """Handle workspace shared event"""
        try:
            if "workspace.shared" not in await self.sdk.get_config("notification_types", []):
                return
            
            workspace_data = event.data
            message = f"🤝 Workspace shared: *{workspace_data.get('name')}*"
            
            if workspace_data.get('shared_with'):
                message += f"\nShared with: {workspace_data['shared_with']}"
            
            await self._send_notification(message)
            await self.sdk.track_feature_usage("workspace_sharing_notification")
            
        except Exception as e:
            self.logger.error(f"Failed to handle workspace shared event: {e}")
            await self.sdk.track_error("event_handling", str(e))
    
    async def _handle_user_joined(self, event):
        """Handle user joined event"""
        try:
            if "user.joined" not in await self.sdk.get_config("notification_types", []):
                return
            
            user_data = event.data
            message = f"👋 Welcome {user_data.get('name')} to BlueBirdHub!"
            
            await self._send_notification(message)
            await self.sdk.track_feature_usage("user_welcome_notification")
            
        except Exception as e:
            self.logger.error(f"Failed to handle user joined event: {e}")
            await self.sdk.track_error("event_handling", str(e))
    
    async def _send_notification(self, message: str, channel: str = None):
        """Send a notification to Slack"""
        try:
            if not self.slack_client:
                return
            
            target_channel = channel or await self.sdk.get_config("default_channel", "#general")
            
            response = await self.slack_client.send_message(target_channel, message)
            
            if response.get("ok"):
                self.logger.debug(f"Sent Slack notification to {target_channel}")
            else:
                self.logger.error(f"Failed to send Slack notification: {response.get('error')}")
                await self.sdk.track_error("notification_failed", response.get('error', 'unknown'))
            
        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {e}")
            await self.sdk.track_error("notification_error", str(e))
    
    async def _sync_channels(self):
        """Sync Slack channels"""
        try:
            if not self.slack_client:
                return
            
            channels = await self.slack_client.list_channels()
            
            # Store channel information for use in configuration
            channel_names = [f"#{channel['name']}" for channel in channels.get('channels', [])]
            self.logger.info(f"Found {len(channel_names)} Slack channels")
            
        except Exception as e:
            self.logger.error(f"Failed to sync Slack channels: {e}")
    
    async def _sync_recent_messages(self):
        """Sync recent messages from configured channels"""
        # This would implement message syncing if needed
        pass
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    # RPC methods that other plugins can call
    async def send_custom_message(self, channel: str, message: str) -> bool:
        """Send a custom message to Slack (callable by other plugins)"""
        try:
            if not await self.sdk.check_permission("slack.send_message"):
                return False
            
            await self._send_notification(message, channel)
            await self.sdk.track_feature_usage("custom_message_api")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send custom message: {e}")
            return False
    
    async def get_channel_list(self) -> List[str]:
        """Get list of available Slack channels"""
        try:
            if not self.slack_client:
                return []
            
            channels = await self.slack_client.list_channels()
            return [f"#{channel['name']}" for channel in channels.get('channels', [])]
            
        except Exception as e:
            self.logger.error(f"Failed to get channel list: {e}")
            return []


class SlackClient:
    """Slack API client wrapper"""
    
    def __init__(self, bot_token: str, sdk):
        self.bot_token = bot_token
        self.sdk = sdk
        self.base_url = "https://slack.com/api"
        
    async def _make_request(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make an authenticated request to Slack API"""
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            if data:
                async with session.post(url, json=data, headers=headers) as response:
                    return await response.json()
            else:
                async with session.get(url, headers=headers) as response:
                    return await response.json()
    
    async def test_auth(self) -> Dict[str, Any]:
        """Test authentication with Slack"""
        return await self._make_request("auth.test")
    
    async def send_message(self, channel: str, text: str) -> Dict[str, Any]:
        """Send a message to a Slack channel"""
        data = {
            "channel": channel,
            "text": text
        }
        return await self._make_request("chat.postMessage", data)
    
    async def list_channels(self) -> Dict[str, Any]:
        """List Slack channels"""
        return await self._make_request("conversations.list")
    
    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Get information about a specific channel"""
        return await self._make_request(f"conversations.info?channel={channel_id}")


# Plugin entry point
Plugin = SlackIntegrationPlugin