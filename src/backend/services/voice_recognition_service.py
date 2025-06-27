"""
Voice Recognition Service for BlueBirdHub
Handles voice recognition, wake word detection, and command processing
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import deque
import threading
import queue

from ..models.user import User
from ..models.task import Task
from ..models.workspace import Workspace
from ..crud.crud_task import CRUDTask
from ..crud.crud_workspace import CRUDWorkspace
from ..database.database import get_db
from ..services.ai_service import ai_service
from .websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)

class VoiceCommandType(Enum):
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    SEARCH_TASK = "search_task"
    NAVIGATE = "navigate"
    DICTATE = "dictate"
    CREATE_WORKSPACE = "create_workspace"
    SWITCH_WORKSPACE = "switch_workspace"
    SET_PRIORITY = "set_priority"
    SET_DEADLINE = "set_deadline"
    ASSIGN_TASK = "assign_task"
    VOICE_FEEDBACK = "voice_feedback"
    HELP = "help"
    CANCEL = "cancel"
    CONFIRM = "confirm"
    UNKNOWN = "unknown"

@dataclass
class VoiceCommand:
    type: VoiceCommandType
    text: str
    confidence: float
    parameters: Dict[str, Any]
    timestamp: datetime
    user_id: str
    language: str = "en"
    context: Optional[Dict[str, Any]] = None

@dataclass
class VoiceProfile:
    user_id: str
    language_preference: str
    accent_model: str
    voice_shortcuts: Dict[str, str]
    wake_word_sensitivity: float
    noise_cancellation_level: float
    confirmation_required: bool
    voice_feedback_enabled: bool
    custom_commands: Dict[str, Dict[str, Any]]

class VoiceGrammar:
    """Defines voice command grammar patterns"""
    
    WAKE_WORDS = ["hey bluebird", "okay bluebird", "bluebird", "hey blue bird"]
    
    COMMAND_PATTERNS = {
        VoiceCommandType.CREATE_TASK: [
            r"create (?:a )?task (?:to |for |about )?(.+)",
            r"add (?:a )?(?:new )?task (?:to |for |about )?(.+)",
            r"new task (?:to |for |about )?(.+)",
            r"remind me to (.+)",
            r"schedule (?:a )?task (?:to |for )?(.+)"
        ],
        VoiceCommandType.UPDATE_TASK: [
            r"update task (.+) (?:to|with) (.+)",
            r"change task (.+) (?:to|with) (.+)",
            r"modify task (.+) (?:to|with) (.+)",
            r"edit task (.+) (?:to|with) (.+)"
        ],
        VoiceCommandType.DELETE_TASK: [
            r"delete task (.+)",
            r"remove task (.+)",
            r"cancel task (.+)",
            r"complete task (.+)",
            r"mark (.+) as (?:done|complete|finished)"
        ],
        VoiceCommandType.SEARCH_TASK: [
            r"(?:search|find|show|list) (?:tasks? )?(?:for |about |with )?(.+)",
            r"what tasks? (?:do I have |are there )?(?:for |about |with )?(.+)?",
            r"show (?:me )?(?:all )?(?:my )?tasks?"
        ],
        VoiceCommandType.SET_PRIORITY: [
            r"set priority (?:to |as )?(.+)",
            r"make (?:it |this )?(.+) priority",
            r"priority (.+)"
        ],
        VoiceCommandType.SET_DEADLINE: [
            r"(?:set |add )?deadline (.+)",
            r"due (?:date |by |on )?(.+)",
            r"schedule (?:for |on )?(.+)"
        ],
        VoiceCommandType.NAVIGATE: [
            r"(?:go to|open|show|navigate to) (.+)",
            r"take me to (.+)",
            r"switch to (.+)"
        ],
        VoiceCommandType.HELP: [
            r"help",
            r"what can (?:I|you) (?:do|say)",
            r"show (?:me )?commands",
            r"voice commands"
        ]
    }
    
    PRIORITY_KEYWORDS = {
        "urgent": "urgent",
        "high": "high",
        "medium": "medium",
        "normal": "medium",
        "low": "low",
        "critical": "urgent",
        "important": "high"
    }
    
    NAVIGATION_KEYWORDS = {
        "dashboard": "/dashboard",
        "tasks": "/tasks",
        "workspaces": "/workspaces",
        "files": "/files",
        "settings": "/settings",
        "profile": "/profile",
        "calendar": "/calendar",
        "search": "/search"
    }

class VoiceRecognitionService:
    """Main voice recognition service"""
    
    def __init__(self):
        self.ai_service = ai_service
        self.websocket_manager = ConnectionManager()
        self.grammar = VoiceGrammar()
        self.voice_profiles: Dict[str, VoiceProfile] = {}
        self.command_history: deque = deque(maxlen=100)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.wake_word_detected = False
        self.listening_timeout = 30  # seconds
        self.confirmation_timeout = 10  # seconds
        self.noise_threshold = 0.3
        self.command_queue = queue.Queue()
        self.processing_thread = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize voice recognition service"""
        try:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._process_commands)
            self.processing_thread.start()
            logger.info("Voice recognition service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize voice recognition: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown voice recognition service"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        logger.info("Voice recognition service shutdown")
    
    def _process_commands(self):
        """Process voice commands from queue"""
        while self.is_running:
            try:
                command = self.command_queue.get(timeout=1)
                asyncio.run(self._execute_command(command))
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing command: {e}")
    
    async def process_audio_stream(self, user_id: str, audio_data: bytes, 
                                 language: str = "en") -> Optional[VoiceCommand]:
        """Process audio stream for voice commands"""
        try:
            # Simulate audio processing (in production, use actual speech recognition)
            # This would integrate with Web Speech API or third-party services
            
            # Apply noise cancellation
            processed_audio = await self._apply_noise_cancellation(audio_data)
            
            # Detect wake word
            if not self.wake_word_detected:
                if await self._detect_wake_word(processed_audio):
                    self.wake_word_detected = True
                    await self._send_feedback(user_id, "listening", 
                                           {"message": "I'm listening..."})
                    return None
            
            # Convert audio to text (simulated)
            text = await self._speech_to_text(processed_audio, language)
            if not text:
                return None
            
            # Parse command
            command = await self._parse_command(text, user_id, language)
            
            # Add to history
            self.command_history.append(command)
            
            # Process command
            if command.type != VoiceCommandType.UNKNOWN:
                self.command_queue.put(command)
                
            return command
            
        except Exception as e:
            logger.error(f"Error processing audio stream: {e}")
            return None
    
    async def _detect_wake_word(self, audio_data: bytes) -> bool:
        """Detect wake word in audio"""
        # Simulated wake word detection
        # In production, use actual wake word detection models
        return False  # Placeholder
    
    async def _apply_noise_cancellation(self, audio_data: bytes) -> bytes:
        """Apply noise cancellation to audio"""
        # Simulated noise cancellation
        # In production, use actual audio processing libraries
        return audio_data
    
    async def _speech_to_text(self, audio_data: bytes, language: str) -> Optional[str]:
        """Convert speech to text"""
        # Simulated speech-to-text
        # In production, integrate with Web Speech API or services like:
        # - Google Cloud Speech-to-Text
        # - Azure Speech Services
        # - AWS Transcribe
        # - OpenAI Whisper
        return None  # Placeholder
    
    async def _parse_command(self, text: str, user_id: str, language: str) -> VoiceCommand:
        """Parse text into voice command"""
        text_lower = text.lower().strip()
        
        # Check each command type
        for cmd_type, patterns in self.grammar.COMMAND_PATTERNS.items():
            for pattern in patterns:
                match = re.match(pattern, text_lower)
                if match:
                    parameters = await self._extract_parameters(
                        cmd_type, match.groups(), text_lower
                    )
                    
                    return VoiceCommand(
                        type=cmd_type,
                        text=text,
                        confidence=0.9,  # Simulated confidence
                        parameters=parameters,
                        timestamp=datetime.utcnow(),
                        user_id=user_id,
                        language=language
                    )
        
        # If no pattern matches, use AI to understand intent
        intent = await self._analyze_intent_with_ai(text, user_id)
        
        return VoiceCommand(
            type=intent.get("type", VoiceCommandType.UNKNOWN),
            text=text,
            confidence=intent.get("confidence", 0.5),
            parameters=intent.get("parameters", {}),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            language=language
        )
    
    async def _extract_parameters(self, cmd_type: VoiceCommandType, 
                                groups: Tuple[str, ...], text: str) -> Dict[str, Any]:
        """Extract parameters from command"""
        parameters = {}
        
        if cmd_type == VoiceCommandType.CREATE_TASK:
            if groups:
                task_text = groups[0]
                parameters["title"] = task_text
                
                # Extract priority
                for keyword, priority in self.grammar.PRIORITY_KEYWORDS.items():
                    if keyword in text:
                        parameters["priority"] = priority
                        break
                
                # Extract deadline using AI
                deadline_info = await self._extract_deadline_from_text(task_text)
                if deadline_info:
                    parameters["deadline"] = deadline_info
                    
        elif cmd_type == VoiceCommandType.SET_PRIORITY:
            if groups:
                priority_text = groups[0]
                parameters["priority"] = self.grammar.PRIORITY_KEYWORDS.get(
                    priority_text, "medium"
                )
                
        elif cmd_type == VoiceCommandType.NAVIGATE:
            if groups:
                destination = groups[0]
                parameters["destination"] = self.grammar.NAVIGATION_KEYWORDS.get(
                    destination, f"/{destination}"
                )
        
        return parameters
    
    async def _analyze_intent_with_ai(self, text: str, user_id: str) -> Dict[str, Any]:
        """Use AI to analyze command intent"""
        try:
            prompt = f"""
            Analyze this voice command and determine the intent:
            Text: "{text}"
            
            Identify:
            1. Command type (create_task, update_task, search_task, navigate, etc.)
            2. Relevant parameters (task title, priority, deadline, etc.)
            3. Confidence level (0-1)
            
            Return as JSON.
            """
            
            response = await self.ai_service.generate_completion(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error analyzing intent with AI: {e}")
            return {"type": VoiceCommandType.UNKNOWN, "confidence": 0}
    
    async def _extract_deadline_from_text(self, text: str) -> Optional[str]:
        """Extract deadline information from text using AI"""
        try:
            prompt = f"""
            Extract deadline information from this text:
            "{text}"
            
            Look for time expressions like:
            - tomorrow, next week, next month
            - by Friday, by end of month
            - in 3 days, in 2 weeks
            - specific dates
            
            Return the deadline as ISO format date or null if none found.
            """
            
            response = await self.ai_service.generate_completion(prompt)
            return response if response != "null" else None
        except Exception as e:
            logger.error(f"Error extracting deadline: {e}")
            return None
    
    async def _execute_command(self, command: VoiceCommand):
        """Execute voice command"""
        try:
            # Get user profile
            profile = self.voice_profiles.get(command.user_id)
            
            # Check if confirmation required
            if profile and profile.confirmation_required:
                confirmed = await self._request_confirmation(command)
                if not confirmed:
                    await self._send_feedback(
                        command.user_id, "cancelled", 
                        {"message": "Command cancelled"}
                    )
                    return
            
            # Execute based on command type
            if command.type == VoiceCommandType.CREATE_TASK:
                await self._create_task(command)
            elif command.type == VoiceCommandType.UPDATE_TASK:
                await self._update_task(command)
            elif command.type == VoiceCommandType.DELETE_TASK:
                await self._delete_task(command)
            elif command.type == VoiceCommandType.SEARCH_TASK:
                await self._search_tasks(command)
            elif command.type == VoiceCommandType.NAVIGATE:
                await self._navigate(command)
            elif command.type == VoiceCommandType.HELP:
                await self._show_help(command)
            
            # Send success feedback
            if profile and profile.voice_feedback_enabled:
                await self._send_voice_feedback(command, "success")
                
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            await self._send_feedback(
                command.user_id, "error", 
                {"message": f"Error: {str(e)}"}
            )
    
    async def _create_task(self, command: VoiceCommand):
        """Create task from voice command"""
        async with get_db() as db:
            crud_task = CRUDTask(Task)
            
            task_data = {
                "title": command.parameters.get("title", "New Task"),
                "description": f"Created by voice command: {command.text}",
                "priority": command.parameters.get("priority", "medium"),
                "status": "pending",
                "user_id": command.user_id,
                "workspace_id": command.parameters.get("workspace_id"),
                "deadline": command.parameters.get("deadline")
            }
            
            task = await crud_task.create(db, obj_in=task_data)
            
            await self._send_feedback(
                command.user_id, "task_created", 
                {
                    "task_id": task.id,
                    "title": task.title,
                    "message": f"Task '{task.title}' created successfully"
                }
            )
    
    async def _request_confirmation(self, command: VoiceCommand) -> bool:
        """Request user confirmation for command"""
        await self._send_feedback(
            command.user_id, "confirmation_required",
            {
                "command": command.text,
                "type": command.type.value,
                "message": f"Do you want to {command.type.value.replace('_', ' ')}?"
            }
        )
        
        # Wait for confirmation (simulated)
        # In production, wait for actual user response
        return True
    
    async def _send_feedback(self, user_id: str, event_type: str, data: Dict[str, Any]):
        """Send feedback to user via WebSocket"""
        await self.websocket_manager.send_to_user(
            user_id,
            {
                "type": f"voice_{event_type}",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _send_voice_feedback(self, command: VoiceCommand, status: str):
        """Send voice feedback using text-to-speech"""
        feedback_messages = {
            "success": f"Command executed successfully",
            "error": f"Sorry, I couldn't process that command",
            "cancelled": f"Command cancelled",
            "listening": f"I'm listening"
        }
        
        message = feedback_messages.get(status, "Command processed")
        
        await self._send_feedback(
            command.user_id, "voice_feedback",
            {
                "message": message,
                "speak": True,
                "voice_settings": {
                    "rate": 1.0,
                    "pitch": 1.0,
                    "volume": 1.0
                }
            }
        )
    
    async def create_voice_profile(self, user_id: str, profile_data: Dict[str, Any]) -> VoiceProfile:
        """Create or update voice profile for user"""
        profile = VoiceProfile(
            user_id=user_id,
            language_preference=profile_data.get("language", "en"),
            accent_model=profile_data.get("accent", "default"),
            voice_shortcuts=profile_data.get("shortcuts", {}),
            wake_word_sensitivity=profile_data.get("wake_word_sensitivity", 0.7),
            noise_cancellation_level=profile_data.get("noise_cancellation", 0.5),
            confirmation_required=profile_data.get("confirmation_required", True),
            voice_feedback_enabled=profile_data.get("voice_feedback", True),
            custom_commands=profile_data.get("custom_commands", {})
        )
        
        self.voice_profiles[user_id] = profile
        return profile
    
    async def get_command_history(self, user_id: str, limit: int = 50) -> List[VoiceCommand]:
        """Get voice command history for user"""
        user_commands = [
            cmd for cmd in self.command_history 
            if cmd.user_id == user_id
        ]
        return user_commands[-limit:]
    
    async def get_command_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get voice command analytics for user"""
        user_commands = await self.get_command_history(user_id, limit=1000)
        
        if not user_commands:
            return {
                "total_commands": 0,
                "command_types": {},
                "success_rate": 0,
                "average_confidence": 0
            }
        
        command_types = {}
        total_confidence = 0
        
        for cmd in user_commands:
            cmd_type = cmd.type.value
            command_types[cmd_type] = command_types.get(cmd_type, 0) + 1
            total_confidence += cmd.confidence
        
        return {
            "total_commands": len(user_commands),
            "command_types": command_types,
            "success_rate": 0.95,  # Simulated
            "average_confidence": total_confidence / len(user_commands),
            "most_used_command": max(command_types, key=command_types.get),
            "languages_used": list(set(cmd.language for cmd in user_commands))
        }

# Global instance
voice_recognition_service = VoiceRecognitionService()