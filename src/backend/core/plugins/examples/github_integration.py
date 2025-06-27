"""
Example GitHub Integration Plugin

Demonstrates integration with GitHub for issue tracking and repository management.
"""

import asyncio
import aiohttp
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..sdk import BaseIntegrationPlugin, PluginBuilder, ConfigType
from ..base import PluginType, PluginMetadata


# Plugin configuration
def create_github_plugin_manifest():
    """Create the plugin manifest for GitHub integration"""
    builder = PluginBuilder("github-integration", "GitHub Integration")
    builder.version("1.0.0")
    builder.description("Integration with GitHub for issue tracking and repository management")
    builder.author("BlueBirdHub Team", "team@bluebirdhub.com")
    builder.type(PluginType.INTEGRATION)
    builder.entry_point("GitHubIntegrationPlugin")
    builder.module_path("github_integration")
    builder.category("development")
    builder.tags("github", "issues", "repositories", "version-control")
    builder.homepage("https://github.com/bluebirdhub/plugins/github")
    
    # Configuration
    builder.add_config(
        "access_token",
        ConfigType.STRING,
        "GitHub Personal Access Token",
        required=True,
        secret=True
    )
    
    builder.add_config(
        "default_owner",
        ConfigType.STRING,
        "Default repository owner/organization",
        required=True
    )
    
    builder.add_config(
        "default_repo",
        ConfigType.STRING,
        "Default repository name"
    )
    
    builder.add_config(
        "sync_interval_minutes",
        ConfigType.INTEGER,
        "Sync interval in minutes",
        default_value=15,
        min_value=5,
        max_value=1440
    )
    
    builder.add_config(
        "create_issues_from_tasks",
        ConfigType.BOOLEAN,
        "Automatically create GitHub issues from BlueBirdHub tasks",
        default_value=True
    )
    
    builder.add_config(
        "sync_labels",
        ConfigType.ARRAY,
        "Labels to sync from GitHub",
        default_value=["bug", "enhancement", "question"]
    )
    
    # Permissions
    builder.add_permission("net.http", "HTTP requests to GitHub API", "network", "execute", required=True)
    builder.add_permission("workspace.write", "Create tasks from GitHub issues", "workspace", "write")
    builder.add_permission("api.write", "Create webhooks", "api", "write")
    
    return builder.build()


class GitHubIntegrationPlugin(BaseIntegrationPlugin):
    """GitHub integration plugin implementation"""
    
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.github_client = None
        self.access_token = None
        self.sync_task = None
        self.webhook_endpoints = []
        
    async def initialize(self) -> bool:
        """Initialize the GitHub plugin"""
        try:
            await super().initialize()
            
            # Get configuration
            self.access_token = await self.sdk.get_config("access_token")
            if not self.access_token:
                self.logger.error("GitHub access token not configured")
                return False
            
            # Setup GitHub client
            self.github_client = GitHubClient(self.access_token, self.sdk)
            
            # Register event handlers
            await self._setup_event_handlers()
            
            self.logger.info("GitHub integration initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GitHub integration: {e}")
            return False
    
    async def activate(self) -> bool:
        """Activate the GitHub plugin"""
        try:
            await super().activate()
            
            # Test GitHub connection
            if not await self.authenticate():
                return False
            
            # Start periodic sync
            await self._start_sync_task()
            
            # Setup webhooks
            await self._setup_webhooks()
            
            self.logger.info("GitHub integration activated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate GitHub integration: {e}")
            return False
    
    async def deactivate(self) -> bool:
        """Deactivate the GitHub plugin"""
        try:
            # Stop sync task
            if self.sync_task:
                self.sync_task.cancel()
                try:
                    await self.sync_task
                except asyncio.CancelledError:
                    pass
            
            # Remove webhooks
            await self._cleanup_webhooks()
            
            await super().deactivate()
            self.logger.info("GitHub integration deactivated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate GitHub integration: {e}")
            return False
    
    async def authenticate(self) -> bool:
        """Authenticate with GitHub API"""
        try:
            if not self.github_client:
                return False
                
            # Test API connection
            user_info = await self.github_client.get_authenticated_user()
            if user_info:
                self.logger.info(f"Authenticated with GitHub as {user_info.get('login')}")
                return True
            else:
                self.logger.error("GitHub authentication failed")
                return False
                
        except Exception as e:
            self.logger.error(f"GitHub authentication error: {e}")
            return False
    
    async def sync_data(self) -> bool:
        """Sync data with GitHub"""
        try:
            default_owner = await self.sdk.get_config("default_owner")
            default_repo = await self.sdk.get_config("default_repo")
            
            if not default_owner:
                self.logger.warning("No default owner configured, skipping sync")
                return True
            
            # Sync issues
            if default_repo:
                await self._sync_issues(default_owner, default_repo)
            
            # Sync repositories
            await self._sync_repositories(default_owner)
            
            self.logger.info("GitHub data sync completed")
            return True
            
        except Exception as e:
            self.logger.error(f"GitHub data sync failed: {e}")
            return False
    
    async def _setup_event_handlers(self):
        """Setup BlueBirdHub event handlers"""
        self.sdk.add_event_handler("task.created", self._handle_task_created)
        self.sdk.add_event_handler("task.updated", self._handle_task_updated)
        self.sdk.add_event_handler("task.completed", self._handle_task_completed)
    
    async def _start_sync_task(self):
        """Start periodic sync task"""
        sync_interval = await self.sdk.get_config("sync_interval_minutes", 15)
        
        async def sync_loop():
            while True:
                try:
                    await asyncio.sleep(sync_interval * 60)  # Convert to seconds
                    await self.sync_data()
                    await self.sdk.track_feature_usage("periodic_sync")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Sync task error: {e}")
                    await self.sdk.track_error("sync_task", str(e))
        
        self.sync_task = asyncio.create_task(sync_loop())
    
    async def _setup_webhooks(self):
        """Setup GitHub webhooks"""
        try:
            default_owner = await self.sdk.get_config("default_owner")
            default_repo = await self.sdk.get_config("default_repo")
            
            if not default_owner or not default_repo:
                return
            
            # This would setup actual webhooks with GitHub
            # For demo purposes, we'll just log the intent
            self.logger.info(f"Setting up webhooks for {default_owner}/{default_repo}")
            
            # In a real implementation, you would:
            # 1. Create webhook endpoint in BlueBirdHub
            # 2. Register webhook with GitHub API
            # 3. Store webhook ID for later cleanup
            
        except Exception as e:
            self.logger.error(f"Failed to setup webhooks: {e}")
    
    async def _cleanup_webhooks(self):
        """Remove GitHub webhooks"""
        for endpoint in self.webhook_endpoints:
            # Remove webhook from GitHub
            pass
    
    async def _handle_task_created(self, event):
        """Handle task created event"""
        try:
            create_issues = await self.sdk.get_config("create_issues_from_tasks", True)
            if not create_issues:
                return
            
            task_data = event.data
            
            # Create GitHub issue
            default_owner = await self.sdk.get_config("default_owner")
            default_repo = await self.sdk.get_config("default_repo")
            
            if default_owner and default_repo:
                issue = await self._create_github_issue(
                    default_owner, default_repo, task_data
                )
                
                if issue:
                    # Update task with GitHub issue link
                    await self.sdk.emit_event("task.updated", {
                        "task_id": task_data.get("id"),
                        "github_issue_url": issue.get("html_url"),
                        "github_issue_number": issue.get("number")
                    })
                    
                    await self.sdk.track_feature_usage("task_to_issue_creation")
            
        except Exception as e:
            self.logger.error(f"Failed to handle task created event: {e}")
            await self.sdk.track_error("task_handling", str(e))
    
    async def _handle_task_updated(self, event):
        """Handle task updated event"""
        try:
            task_data = event.data
            
            # If task has GitHub issue, update it
            if task_data.get("github_issue_number"):
                await self._update_github_issue(task_data)
                await self.sdk.track_feature_usage("task_to_issue_update")
            
        except Exception as e:
            self.logger.error(f"Failed to handle task updated event: {e}")
            await self.sdk.track_error("task_handling", str(e))
    
    async def _handle_task_completed(self, event):
        """Handle task completed event"""
        try:
            task_data = event.data
            
            # If task has GitHub issue, close it
            if task_data.get("github_issue_number"):
                await self._close_github_issue(task_data)
                await self.sdk.track_feature_usage("task_completion_issue_close")
            
        except Exception as e:
            self.logger.error(f"Failed to handle task completed event: {e}")
            await self.sdk.track_error("task_handling", str(e))
    
    async def _sync_issues(self, owner: str, repo: str):
        """Sync GitHub issues to BlueBirdHub tasks"""
        try:
            if not self.github_client:
                return
            
            issues = await self.github_client.list_issues(owner, repo)
            sync_labels = await self.sdk.get_config("sync_labels", [])
            
            for issue in issues:
                # Check if issue has sync labels
                issue_labels = [label["name"] for label in issue.get("labels", [])]
                
                if not sync_labels or any(label in sync_labels for label in issue_labels):
                    await self._create_task_from_issue(issue)
            
            self.logger.info(f"Synced {len(issues)} issues from {owner}/{repo}")
            
        except Exception as e:
            self.logger.error(f"Failed to sync issues: {e}")
    
    async def _sync_repositories(self, owner: str):
        """Sync repository information"""
        try:
            if not self.github_client:
                return
            
            repos = await self.github_client.list_repositories(owner)
            
            # Store repository information for configuration
            repo_names = [repo["name"] for repo in repos]
            self.logger.info(f"Found {len(repo_names)} repositories for {owner}")
            
        except Exception as e:
            self.logger.error(f"Failed to sync repositories: {e}")
    
    async def _create_github_issue(self, owner: str, repo: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a GitHub issue from task data"""
        try:
            if not self.github_client:
                return None
            
            issue_data = {
                "title": task_data.get("title", "Untitled Task"),
                "body": task_data.get("description", ""),
                "labels": ["bluebirdhub-task"]
            }
            
            # Add priority label
            if task_data.get("priority"):
                priority_label = f"priority-{task_data['priority'].lower()}"
                issue_data["labels"].append(priority_label)
            
            issue = await self.github_client.create_issue(owner, repo, issue_data)
            
            if issue:
                self.logger.info(f"Created GitHub issue #{issue['number']} for task {task_data.get('id')}")
            
            return issue
            
        except Exception as e:
            self.logger.error(f"Failed to create GitHub issue: {e}")
            return None
    
    async def _update_github_issue(self, task_data: Dict[str, Any]):
        """Update GitHub issue from task data"""
        try:
            # Implementation would update the GitHub issue
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to update GitHub issue: {e}")
    
    async def _close_github_issue(self, task_data: Dict[str, Any]):
        """Close GitHub issue when task is completed"""
        try:
            # Implementation would close the GitHub issue
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to close GitHub issue: {e}")
    
    async def _create_task_from_issue(self, issue: Dict[str, Any]):
        """Create BlueBirdHub task from GitHub issue"""
        try:
            task_data = {
                "title": issue.get("title"),
                "description": issue.get("body", ""),
                "github_issue_number": issue.get("number"),
                "github_issue_url": issue.get("html_url"),
                "created_by": self.metadata.id,
                "source": "github"
            }
            
            # Extract priority from labels
            for label in issue.get("labels", []):
                if label["name"].startswith("priority-"):
                    task_data["priority"] = label["name"].replace("priority-", "").upper()
                    break
            
            # Emit task creation event
            await self.sdk.emit_event("task.created", task_data)
            
        except Exception as e:
            self.logger.error(f"Failed to create task from issue: {e}")
    
    # RPC methods for other plugins
    async def create_issue(self, owner: str, repo: str, title: str, body: str = "", labels: List[str] = None) -> Optional[Dict[str, Any]]:
        """Create a GitHub issue (callable by other plugins)"""
        try:
            if not await self.sdk.check_permission("github.create_issue"):
                return None
            
            issue_data = {
                "title": title,
                "body": body,
                "labels": labels or []
            }
            
            issue = await self.github_client.create_issue(owner, repo, issue_data)
            await self.sdk.track_feature_usage("api_issue_creation")
            return issue
            
        except Exception as e:
            self.logger.error(f"Failed to create issue via API: {e}")
            return None
    
    async def get_repositories(self, owner: str) -> List[Dict[str, Any]]:
        """Get list of repositories (callable by other plugins)"""
        try:
            if not self.github_client:
                return []
            
            repos = await self.github_client.list_repositories(owner)
            await self.sdk.track_feature_usage("api_repo_list")
            return repos
            
        except Exception as e:
            self.logger.error(f"Failed to get repositories via API: {e}")
            return []


class GitHubClient:
    """GitHub API client wrapper"""
    
    def __init__(self, access_token: str, sdk):
        self.access_token = access_token
        self.sdk = sdk
        self.base_url = "https://api.github.com"
        
    async def _make_request(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make an authenticated request to GitHub API"""
        headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BlueBirdHub-GitHub-Plugin/1.0"
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            self.sdk.logger.error(f"GitHub API error: {response.status}")
                            return None
                elif method == "POST":
                    async with session.post(url, json=data, headers=headers) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            self.sdk.logger.error(f"GitHub API error: {response.status}")
                            return None
                elif method == "PATCH":
                    async with session.patch(url, json=data, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            self.sdk.logger.error(f"GitHub API error: {response.status}")
                            return None
                            
        except Exception as e:
            self.sdk.logger.error(f"GitHub API request failed: {e}")
            return None
    
    async def get_authenticated_user(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user information"""
        return await self._make_request("user")
    
    async def list_repositories(self, owner: str) -> List[Dict[str, Any]]:
        """List repositories for an owner"""
        result = await self._make_request(f"users/{owner}/repos")
        return result if result else []
    
    async def list_issues(self, owner: str, repo: str, state: str = "open") -> List[Dict[str, Any]]:
        """List issues for a repository"""
        result = await self._make_request(f"repos/{owner}/{repo}/issues?state={state}")
        return result if result else []
    
    async def create_issue(self, owner: str, repo: str, issue_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new issue"""
        return await self._make_request(f"repos/{owner}/{repo}/issues", "POST", issue_data)
    
    async def update_issue(self, owner: str, repo: str, issue_number: int, issue_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing issue"""
        return await self._make_request(f"repos/{owner}/{repo}/issues/{issue_number}", "PATCH", issue_data)
    
    async def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific issue"""
        return await self._make_request(f"repos/{owner}/{repo}/issues/{issue_number}")


# Plugin entry point
Plugin = GitHubIntegrationPlugin