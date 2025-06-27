"""
Voice Command Schemas
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class VoiceProfileCreate(BaseModel):
    language_preference: str = Field(default="en", description="Preferred language")
    accent_model: str = Field(default="default", description="Accent model to use")
    voice_shortcuts: Dict[str, str] = Field(default_factory=dict, description="Voice command shortcuts")
    wake_word_sensitivity: float = Field(default=0.7, ge=0, le=1, description="Wake word detection sensitivity")
    noise_cancellation_level: float = Field(default=0.5, ge=0, le=1, description="Noise cancellation strength")
    confirmation_required: bool = Field(default=True, description="Require confirmation for commands")
    voice_feedback_enabled: bool = Field(default=True, description="Enable voice feedback")
    custom_commands: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Custom voice commands")

class VoiceProfileResponse(VoiceProfileCreate):
    user_id: str

class VoiceSettingsUpdate(BaseModel):
    language_preference: Optional[str] = None
    accent_model: Optional[str] = None
    voice_shortcuts: Optional[Dict[str, str]] = None
    wake_word_sensitivity: Optional[float] = Field(None, ge=0, le=1)
    noise_cancellation_level: Optional[float] = Field(None, ge=0, le=1)
    confirmation_required: Optional[bool] = None
    voice_feedback_enabled: Optional[bool] = None
    custom_commands: Optional[Dict[str, Dict[str, Any]]] = None

class VoiceCommandResponse(BaseModel):
    type: str
    text: str
    confidence: float
    parameters: Dict[str, Any]
    timestamp: datetime
    language: str

class VoiceCommandHistoryResponse(VoiceCommandResponse):
    id: int
    status: str

class VoiceAnalyticsResponse(BaseModel):
    total_commands: int
    command_types: Dict[str, int]
    success_rate: float
    average_confidence: float
    most_used_command: str
    languages_used: List[str]

class VoiceStreamRequest(BaseModel):
    audio_chunk: str = Field(..., description="Base64 encoded audio chunk")
    language: str = Field(default="en", description="Language code")
    session_id: Optional[str] = Field(None, description="Voice session ID")

class VoiceStreamResponse(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime

class CustomCommandCreate(BaseModel):
    name: str = Field(..., description="Command name")
    pattern: str = Field(..., description="Voice pattern to match")
    action: Dict[str, Any] = Field(..., description="Action to perform")
    description: Optional[str] = Field(None, description="Command description")

class VoiceFeedbackSettings(BaseModel):
    rate: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech rate")
    pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="Voice pitch")
    volume: float = Field(default=1.0, ge=0, le=1, description="Voice volume")
    voice: str = Field(default="default", description="Voice to use for feedback")