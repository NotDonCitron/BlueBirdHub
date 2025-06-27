"""
Example Plugins for BlueBirdHub

This module contains example implementations of various plugin types
to demonstrate the capabilities of the BlueBirdHub plugin system.
"""

from .slack_integration import SlackIntegrationPlugin, create_slack_plugin_manifest
from .github_integration import GitHubIntegrationPlugin, create_github_plugin_manifest  
from .ai_task_assistant import AITaskAssistantPlugin, create_ai_assistant_plugin_manifest

__all__ = [
    'SlackIntegrationPlugin',
    'create_slack_plugin_manifest',
    'GitHubIntegrationPlugin', 
    'create_github_plugin_manifest',
    'AITaskAssistantPlugin',
    'create_ai_assistant_plugin_manifest'
]