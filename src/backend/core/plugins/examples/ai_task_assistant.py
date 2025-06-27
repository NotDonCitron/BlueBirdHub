"""
Example AI Task Assistant Plugin

Demonstrates AI enhancement plugin that provides intelligent task suggestions,
auto-completion, and smart organization features.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..sdk import BaseAIPlugin, PluginBuilder, ConfigType
from ..base import PluginType, PluginMetadata


# Plugin configuration
def create_ai_assistant_plugin_manifest():
    """Create the plugin manifest for AI Task Assistant"""
    builder = PluginBuilder("ai-task-assistant", "AI Task Assistant")
    builder.version("1.0.0")
    builder.description("AI-powered task management and productivity assistant")
    builder.author("BlueBirdHub Team", "team@bluebirdhub.com")
    builder.type(PluginType.AI_ENHANCEMENT)
    builder.entry_point("AITaskAssistantPlugin")
    builder.module_path("ai_task_assistant")
    builder.category("productivity")
    builder.tags("ai", "tasks", "productivity", "automation", "smart-suggestions")
    builder.homepage("https://github.com/bluebirdhub/plugins/ai-assistant")
    
    # Configuration
    builder.add_config(
        "openai_api_key",
        ConfigType.STRING,
        "OpenAI API Key for GPT integration",
        secret=True
    )
    
    builder.add_config(
        "ai_model",
        ConfigType.STRING,
        "AI model to use",
        default_value="gpt-3.5-turbo",
        choices=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    )
    
    builder.add_config(
        "enable_auto_suggestions",
        ConfigType.BOOLEAN,
        "Enable automatic task suggestions",
        default_value=True
    )
    
    builder.add_config(
        "enable_smart_scheduling",
        ConfigType.BOOLEAN,
        "Enable AI-powered task scheduling",
        default_value=True
    )
    
    builder.add_config(
        "suggestion_frequency_hours",
        ConfigType.INTEGER,
        "How often to generate suggestions (hours)",
        default_value=24,
        min_value=1,
        max_value=168
    )
    
    builder.add_config(
        "max_suggestions_per_session",
        ConfigType.INTEGER,
        "Maximum suggestions per session",
        default_value=5,
        min_value=1,
        max_value=20
    )
    
    # Permissions
    builder.add_permission("net.http", "HTTP requests to AI APIs", "network", "execute", required=True)
    builder.add_permission("workspace.read", "Read workspace data for analysis", "workspace", "read", required=True)
    builder.add_permission("workspace.write", "Create suggested tasks", "workspace", "write")
    builder.add_permission("user.read", "Read user preferences", "user", "read")
    
    return builder.build()


class AITaskAssistantPlugin(BaseAIPlugin):
    """AI Task Assistant plugin implementation"""
    
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.ai_client = None
        self.suggestion_task = None
        self.last_suggestion_time = None
        
    async def initialize(self) -> bool:
        """Initialize the AI Task Assistant plugin"""
        try:
            await super().initialize()
            
            # Setup AI client
            api_key = await self.sdk.get_config("openai_api_key")
            model = await self.sdk.get_config("ai_model", "gpt-3.5-turbo")
            
            if api_key:
                self.ai_client = AIClient(api_key, model, self.sdk)
            else:
                self.logger.warning("No AI API key configured, some features will be limited")
            
            # Register event handlers
            await self._setup_event_handlers()
            
            self.logger.info("AI Task Assistant initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Task Assistant: {e}")
            return False
    
    async def activate(self) -> bool:
        """Activate the AI Task Assistant plugin"""
        try:
            await super().activate()
            
            # Start suggestion engine
            if await self.sdk.get_config("enable_auto_suggestions", True):
                await self._start_suggestion_engine()
            
            self.logger.info("AI Task Assistant activated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate AI Task Assistant: {e}")
            return False
    
    async def deactivate(self) -> bool:
        """Deactivate the AI Task Assistant plugin"""
        try:
            # Stop suggestion engine
            if self.suggestion_task:
                self.suggestion_task.cancel()
                try:
                    await self.suggestion_task
                except asyncio.CancelledError:
                    pass
            
            await super().deactivate()
            self.logger.info("AI Task Assistant deactivated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate AI Task Assistant: {e}")
            return False
    
    async def process(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Process data with AI enhancement"""
        try:
            processing_type = context.get("type", "general")
            
            if processing_type == "task_analysis":
                return await self._analyze_task(input_data, context)
            elif processing_type == "suggestion_generation":
                return await self._generate_suggestions(input_data, context)
            elif processing_type == "smart_scheduling":
                return await self._suggest_schedule(input_data, context)
            elif processing_type == "task_completion":
                return await self._predict_completion_time(input_data, context)
            else:
                return await self._general_processing(input_data, context)
                
        except Exception as e:
            self.logger.error(f"AI processing failed: {e}")
            await self.sdk.track_error("ai_processing", str(e))
            return None
    
    def get_capabilities(self) -> List[str]:
        """Get AI capabilities provided by this plugin"""
        return [
            "task_analysis",
            "suggestion_generation", 
            "smart_scheduling",
            "completion_prediction",
            "priority_optimization",
            "dependency_detection",
            "workload_balancing"
        ]
    
    async def _setup_event_handlers(self):
        """Setup event handlers"""
        self.sdk.add_event_handler("task.created", self._handle_task_created)
        self.sdk.add_event_handler("task.updated", self._handle_task_updated)
        self.sdk.add_event_handler("task.completed", self._handle_task_completed)
        self.sdk.add_event_handler("workspace.created", self._handle_workspace_created)
    
    async def _start_suggestion_engine(self):
        """Start the automatic suggestion engine"""
        frequency_hours = await self.sdk.get_config("suggestion_frequency_hours", 24)
        
        async def suggestion_loop():
            while True:
                try:
                    await asyncio.sleep(frequency_hours * 3600)  # Convert to seconds
                    await self._generate_periodic_suggestions()
                    await self.sdk.track_feature_usage("periodic_suggestions")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Suggestion engine error: {e}")
                    await self.sdk.track_error("suggestion_engine", str(e))
        
        self.suggestion_task = asyncio.create_task(suggestion_loop())
    
    async def _handle_task_created(self, event):
        """Handle task created event"""
        try:
            task_data = event.data
            
            # Analyze new task for optimization
            analysis = await self._analyze_task(task_data, {"type": "new_task"})
            
            if analysis:
                # Suggest improvements
                suggestions = analysis.get("suggestions", [])
                if suggestions:
                    await self.sdk.emit_event("ai.task_suggestions", {
                        "task_id": task_data.get("id"),
                        "suggestions": suggestions
                    })
            
            # Check for dependencies
            dependencies = await self._detect_dependencies(task_data)
            if dependencies:
                await self.sdk.emit_event("ai.dependencies_detected", {
                    "task_id": task_data.get("id"),
                    "dependencies": dependencies
                })
            
            await self.sdk.track_feature_usage("task_analysis")
            
        except Exception as e:
            self.logger.error(f"Failed to handle task created event: {e}")
    
    async def _handle_task_updated(self, event):
        """Handle task updated event"""
        try:
            task_data = event.data
            
            # Re-analyze task for smart scheduling
            if await self.sdk.get_config("enable_smart_scheduling", True):
                schedule_suggestion = await self._suggest_schedule(task_data, {})
                if schedule_suggestion:
                    await self.sdk.emit_event("ai.schedule_suggestion", {
                        "task_id": task_data.get("id"),
                        "suggestion": schedule_suggestion
                    })
            
            await self.sdk.track_feature_usage("task_update_analysis")
            
        except Exception as e:
            self.logger.error(f"Failed to handle task updated event: {e}")
    
    async def _handle_task_completed(self, event):
        """Handle task completed event"""
        try:
            task_data = event.data
            
            # Learn from completion for future predictions
            await self._learn_from_completion(task_data)
            
            # Generate follow-up suggestions
            follow_ups = await self._generate_follow_up_tasks(task_data)
            if follow_ups:
                await self.sdk.emit_event("ai.follow_up_suggestions", {
                    "completed_task_id": task_data.get("id"),
                    "suggestions": follow_ups
                })
            
            await self.sdk.track_feature_usage("completion_learning")
            
        except Exception as e:
            self.logger.error(f"Failed to handle task completed event: {e}")
    
    async def _handle_workspace_created(self, event):
        """Handle workspace created event"""
        try:
            workspace_data = event.data
            
            # Generate initial task suggestions for new workspace
            suggestions = await self._generate_workspace_starter_tasks(workspace_data)
            if suggestions:
                await self.sdk.emit_event("ai.workspace_suggestions", {
                    "workspace_id": workspace_data.get("id"),
                    "suggestions": suggestions
                })
            
            await self.sdk.track_feature_usage("workspace_setup_suggestions")
            
        except Exception as e:
            self.logger.error(f"Failed to handle workspace created event: {e}")
    
    async def _analyze_task(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze a task and provide insights"""
        try:
            if not self.ai_client:
                return self._basic_task_analysis(task_data)
            
            # Prepare task context
            task_context = {
                "title": task_data.get("title", ""),
                "description": task_data.get("description", ""),
                "priority": task_data.get("priority", "medium"),
                "due_date": task_data.get("due_date"),
                "estimated_hours": task_data.get("estimated_hours"),
                "tags": task_data.get("tags", [])
            }
            
            # Get AI analysis
            analysis = await self.ai_client.analyze_task(task_context)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Task analysis failed: {e}")
            return None
    
    async def _generate_suggestions(self, input_data: Any, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate task suggestions"""
        try:
            if not self.ai_client:
                return self._basic_suggestions(input_data)
            
            max_suggestions = await self.sdk.get_config("max_suggestions_per_session", 5)
            
            suggestions = await self.ai_client.generate_suggestions(input_data, max_suggestions)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Suggestion generation failed: {e}")
            return []
    
    async def _suggest_schedule(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Suggest optimal scheduling for a task"""
        try:
            if not self.ai_client:
                return self._basic_scheduling(task_data)
            
            # Get user's existing tasks and calendar
            existing_tasks = await self._get_user_tasks(context.get("user_id"))
            
            schedule_context = {
                "task": task_data,
                "existing_tasks": existing_tasks,
                "preferences": context.get("user_preferences", {})
            }
            
            schedule = await self.ai_client.suggest_schedule(schedule_context)
            
            return schedule
            
        except Exception as e:
            self.logger.error(f"Schedule suggestion failed: {e}")
            return None
    
    async def _predict_completion_time(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Optional[float]:
        """Predict task completion time"""
        try:
            if not self.ai_client:
                return self._basic_time_estimation(task_data)
            
            # Get historical data for similar tasks
            similar_tasks = await self._find_similar_tasks(task_data)
            
            prediction_context = {
                "task": task_data,
                "similar_tasks": similar_tasks,
                "user_performance": context.get("user_performance", {})
            }
            
            estimated_time = await self.ai_client.predict_completion_time(prediction_context)
            
            return estimated_time
            
        except Exception as e:
            self.logger.error(f"Completion time prediction failed: {e}")
            return None
    
    async def _general_processing(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """General AI processing"""
        try:
            # Fallback processing for any other AI requests
            return {"status": "processed", "data": input_data}
            
        except Exception as e:
            self.logger.error(f"General AI processing failed: {e}")
            return None
    
    async def _generate_periodic_suggestions(self):
        """Generate periodic task suggestions"""
        try:
            # Get user workspaces and current tasks
            workspaces = await self._get_user_workspaces()
            
            for workspace in workspaces:
                suggestions = await self._generate_workspace_suggestions(workspace)
                
                if suggestions:
                    await self.sdk.emit_event("ai.periodic_suggestions", {
                        "workspace_id": workspace.get("id"),
                        "suggestions": suggestions,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            self.last_suggestion_time = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Periodic suggestion generation failed: {e}")
    
    async def _detect_dependencies(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect potential task dependencies"""
        try:
            if not self.ai_client:
                return []
            
            # Get related tasks
            related_tasks = await self._find_related_tasks(task_data)
            
            dependencies = await self.ai_client.detect_dependencies(task_data, related_tasks)
            
            return dependencies
            
        except Exception as e:
            self.logger.error(f"Dependency detection failed: {e}")
            return []
    
    async def _learn_from_completion(self, task_data: Dict[str, Any]):
        """Learn from task completion for future predictions"""
        try:
            # Store completion data for machine learning
            completion_data = {
                "task_id": task_data.get("id"),
                "actual_duration": task_data.get("actual_duration"),
                "estimated_duration": task_data.get("estimated_duration"),
                "completion_quality": task_data.get("completion_quality"),
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # In a real implementation, this would feed into a learning model
            await self.sdk.record_metric("completion_learning", 1, {"task_type": task_data.get("type", "unknown")})
            
        except Exception as e:
            self.logger.error(f"Learning from completion failed: {e}")
    
    # Fallback methods for when AI client is not available
    def _basic_task_analysis(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Basic task analysis without AI"""
        analysis = {
            "complexity": "medium",
            "estimated_time": 2.0,
            "suggestions": [],
            "priority_score": 0.5
        }
        
        # Simple heuristics
        title = task_data.get("title", "").lower()
        description = task_data.get("description", "").lower()
        
        if any(word in title + description for word in ["urgent", "asap", "critical"]):
            analysis["priority_score"] = 0.9
            analysis["suggestions"].append("Consider higher priority due to urgency keywords")
        
        if any(word in title + description for word in ["research", "analysis", "review"]):
            analysis["complexity"] = "high"
            analysis["estimated_time"] = 4.0
        
        return analysis
    
    def _basic_suggestions(self, input_data: Any) -> List[Dict[str, Any]]:
        """Basic suggestions without AI"""
        return [
            {
                "title": "Review project status",
                "description": "Check progress on current projects",
                "priority": "medium",
                "estimated_time": 1.0
            },
            {
                "title": "Plan next week",
                "description": "Set goals and priorities for upcoming week",
                "priority": "low",
                "estimated_time": 0.5
            }
        ]
    
    def _basic_scheduling(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Basic scheduling without AI"""
        # Simple scheduling logic
        estimated_time = task_data.get("estimated_hours", 2.0)
        due_date = task_data.get("due_date")
        
        if due_date:
            suggested_start = datetime.fromisoformat(due_date) - timedelta(hours=estimated_time * 1.5)
        else:
            suggested_start = datetime.utcnow() + timedelta(days=1)
        
        return {
            "suggested_start_time": suggested_start.isoformat(),
            "suggested_duration_hours": estimated_time,
            "confidence": 0.6
        }
    
    def _basic_time_estimation(self, task_data: Dict[str, Any]) -> float:
        """Basic time estimation without AI"""
        # Simple estimation based on keywords
        title = task_data.get("title", "").lower()
        description = task_data.get("description", "").lower()
        
        base_time = 2.0  # Default 2 hours
        
        if any(word in title + description for word in ["quick", "simple", "easy"]):
            return base_time * 0.5
        elif any(word in title + description for word in ["complex", "detailed", "comprehensive"]):
            return base_time * 2.0
        
        return base_time
    
    # Helper methods
    async def _get_user_tasks(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get user's existing tasks"""
        # This would integrate with the task management system
        return []
    
    async def _get_user_workspaces(self) -> List[Dict[str, Any]]:
        """Get user's workspaces"""
        # This would integrate with the workspace system
        return []
    
    async def _find_similar_tasks(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar tasks for learning"""
        # This would implement similarity matching
        return []
    
    async def _find_related_tasks(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find related tasks for dependency detection"""
        # This would implement relation detection
        return []
    
    # RPC methods for other plugins
    async def analyze_task_intelligence(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task with AI (callable by other plugins)"""
        return await self._analyze_task(task_data, {"type": "api_request"})
    
    async def get_task_suggestions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get task suggestions (callable by other plugins)"""
        return await self._generate_suggestions(context, {"type": "api_request"})


class AIClient:
    """AI client for interacting with language models"""
    
    def __init__(self, api_key: str, model: str, sdk):
        self.api_key = api_key
        self.model = model
        self.sdk = sdk
        
    async def analyze_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task using AI"""
        # This would implement actual AI API calls
        # For demo purposes, return mock analysis
        return {
            "complexity": "medium",
            "estimated_time": 3.0,
            "suggestions": [
                "Break down into smaller subtasks",
                "Add more specific acceptance criteria"
            ],
            "priority_score": 0.7,
            "confidence": 0.85
        }
    
    async def generate_suggestions(self, context: Any, max_suggestions: int) -> List[Dict[str, Any]]:
        """Generate task suggestions using AI"""
        # Mock suggestions for demo
        return [
            {
                "title": "Code review session",
                "description": "Review recent code changes with team",
                "priority": "high",
                "estimated_time": 2.0,
                "confidence": 0.8
            },
            {
                "title": "Update documentation",
                "description": "Update project documentation with recent changes",
                "priority": "medium", 
                "estimated_time": 1.5,
                "confidence": 0.7
            }
        ]
    
    async def suggest_schedule(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest optimal schedule using AI"""
        # Mock scheduling for demo
        return {
            "suggested_start_time": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            "suggested_duration_hours": 2.5,
            "optimal_time_blocks": ["09:00-11:30", "14:00-16:30"],
            "confidence": 0.75
        }
    
    async def predict_completion_time(self, context: Dict[str, Any]) -> float:
        """Predict task completion time using AI"""
        # Mock prediction for demo
        return 2.5
    
    async def detect_dependencies(self, task_data: Dict[str, Any], related_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect task dependencies using AI"""
        # Mock dependency detection for demo
        return [
            {
                "task_id": "related_task_1",
                "dependency_type": "blocks",
                "confidence": 0.8,
                "reason": "Requires output from this task"
            }
        ]


# Plugin entry point
Plugin = AITaskAssistantPlugin