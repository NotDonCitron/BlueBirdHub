"""
Voice Command API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, File, UploadFile
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import base64

from ..database.database import get_db
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..services.voice_recognition_service import (
    voice_recognition_service, 
    VoiceProfile,
    VoiceCommand,
    VoiceCommandType
)
from ..schemas.voice import (
    VoiceProfileCreate,
    VoiceProfileResponse,
    VoiceCommandResponse,
    VoiceCommandHistoryResponse,
    VoiceAnalyticsResponse,
    VoiceSettingsUpdate
)

router = APIRouter(prefix="/api/voice", tags=["voice"])

@router.post("/profile", response_model=VoiceProfileResponse)
async def create_voice_profile(
    profile_data: VoiceProfileCreate,
    current_user: User = Depends(get_current_user)
):
    """Create or update voice profile for current user"""
    try:
        profile = await voice_recognition_service.create_voice_profile(
            str(current_user.id),
            profile_data.dict()
        )
        
        return VoiceProfileResponse(
            user_id=profile.user_id,
            language_preference=profile.language_preference,
            accent_model=profile.accent_model,
            voice_shortcuts=profile.voice_shortcuts,
            wake_word_sensitivity=profile.wake_word_sensitivity,
            noise_cancellation_level=profile.noise_cancellation_level,
            confirmation_required=profile.confirmation_required,
            voice_feedback_enabled=profile.voice_feedback_enabled,
            custom_commands=profile.custom_commands
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile", response_model=VoiceProfileResponse)
async def get_voice_profile(
    current_user: User = Depends(get_current_user)
):
    """Get voice profile for current user"""
    profile = voice_recognition_service.voice_profiles.get(str(current_user.id))
    
    if not profile:
        # Return default profile
        return VoiceProfileResponse(
            user_id=str(current_user.id),
            language_preference="en",
            accent_model="default",
            voice_shortcuts={},
            wake_word_sensitivity=0.7,
            noise_cancellation_level=0.5,
            confirmation_required=True,
            voice_feedback_enabled=True,
            custom_commands={}
        )
    
    return VoiceProfileResponse(
        user_id=profile.user_id,
        language_preference=profile.language_preference,
        accent_model=profile.accent_model,
        voice_shortcuts=profile.voice_shortcuts,
        wake_word_sensitivity=profile.wake_word_sensitivity,
        noise_cancellation_level=profile.noise_cancellation_level,
        confirmation_required=profile.confirmation_required,
        voice_feedback_enabled=profile.voice_feedback_enabled,
        custom_commands=profile.custom_commands
    )

@router.put("/profile", response_model=VoiceProfileResponse)
async def update_voice_profile(
    settings: VoiceSettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update voice settings for current user"""
    try:
        profile_data = settings.dict(exclude_unset=True)
        profile = await voice_recognition_service.create_voice_profile(
            str(current_user.id),
            profile_data
        )
        
        return VoiceProfileResponse(
            user_id=profile.user_id,
            language_preference=profile.language_preference,
            accent_model=profile.accent_model,
            voice_shortcuts=profile.voice_shortcuts,
            wake_word_sensitivity=profile.wake_word_sensitivity,
            noise_cancellation_level=profile.noise_cancellation_level,
            confirmation_required=profile.confirmation_required,
            voice_feedback_enabled=profile.voice_feedback_enabled,
            custom_commands=profile.custom_commands
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-audio")
async def process_audio(
    audio_file: UploadFile = File(...),
    language: str = "en",
    current_user: User = Depends(get_current_user)
):
    """Process audio file for voice commands"""
    try:
        # Read audio data
        audio_data = await audio_file.read()
        
        # Process audio
        command = await voice_recognition_service.process_audio_stream(
            str(current_user.id),
            audio_data,
            language
        )
        
        if command:
            return VoiceCommandResponse(
                type=command.type.value,
                text=command.text,
                confidence=command.confidence,
                parameters=command.parameters,
                timestamp=command.timestamp,
                language=command.language
            )
        else:
            return {"message": "No command detected"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-text")
async def process_text_command(
    text: str,
    language: str = "en",
    current_user: User = Depends(get_current_user)
):
    """Process text as voice command"""
    try:
        command = await voice_recognition_service._parse_command(
            text,
            str(current_user.id),
            language
        )
        
        if command.type != VoiceCommandType.UNKNOWN:
            voice_recognition_service.command_queue.put(command)
        
        return VoiceCommandResponse(
            type=command.type.value,
            text=command.text,
            confidence=command.confidence,
            parameters=command.parameters,
            timestamp=command.timestamp,
            language=command.language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[VoiceCommandHistoryResponse])
async def get_command_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get voice command history for current user"""
    try:
        commands = await voice_recognition_service.get_command_history(
            str(current_user.id),
            limit
        )
        
        return [
            VoiceCommandHistoryResponse(
                id=i,
                type=cmd.type.value,
                text=cmd.text,
                confidence=cmd.confidence,
                parameters=cmd.parameters,
                timestamp=cmd.timestamp,
                language=cmd.language,
                status="completed"  # Simulated status
            )
            for i, cmd in enumerate(commands)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics", response_model=VoiceAnalyticsResponse)
async def get_voice_analytics(
    current_user: User = Depends(get_current_user)
):
    """Get voice command analytics for current user"""
    try:
        analytics = await voice_recognition_service.get_command_analytics(
            str(current_user.id)
        )
        
        return VoiceAnalyticsResponse(
            total_commands=analytics["total_commands"],
            command_types=analytics["command_types"],
            success_rate=analytics["success_rate"],
            average_confidence=analytics["average_confidence"],
            most_used_command=analytics.get("most_used_command", ""),
            languages_used=analytics.get("languages_used", ["en"])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/commands")
async def get_available_commands(
    current_user: User = Depends(get_current_user)
):
    """Get list of available voice commands"""
    commands = {
        "wake_words": voice_recognition_service.grammar.WAKE_WORDS,
        "command_types": {
            cmd_type.value: {
                "description": cmd_type.value.replace("_", " ").title(),
                "examples": []
            }
            for cmd_type in VoiceCommandType
            if cmd_type != VoiceCommandType.UNKNOWN
        },
        "shortcuts": {},
        "custom_commands": {}
    }
    
    # Add examples for each command type
    command_examples = {
        VoiceCommandType.CREATE_TASK: [
            "Create a task to review Q4 reports",
            "Add new task for meeting preparation",
            "Remind me to call the client tomorrow"
        ],
        VoiceCommandType.UPDATE_TASK: [
            "Update task review reports to high priority",
            "Change task meeting prep deadline to Friday"
        ],
        VoiceCommandType.DELETE_TASK: [
            "Delete task old meeting notes",
            "Mark review task as complete"
        ],
        VoiceCommandType.SEARCH_TASK: [
            "Show me all high priority tasks",
            "Find tasks due this week",
            "Search tasks about client meeting"
        ],
        VoiceCommandType.NAVIGATE: [
            "Go to dashboard",
            "Open task manager",
            "Navigate to settings"
        ],
        VoiceCommandType.SET_PRIORITY: [
            "Set priority to high",
            "Make it urgent priority"
        ],
        VoiceCommandType.SET_DEADLINE: [
            "Set deadline tomorrow",
            "Due date next Friday",
            "Schedule for end of month"
        ]
    }
    
    for cmd_type, examples in command_examples.items():
        if cmd_type.value in commands["command_types"]:
            commands["command_types"][cmd_type.value]["examples"] = examples
    
    # Add user's custom shortcuts and commands
    profile = voice_recognition_service.voice_profiles.get(str(current_user.id))
    if profile:
        commands["shortcuts"] = profile.voice_shortcuts
        commands["custom_commands"] = profile.custom_commands
    
    return commands

@router.websocket("/stream")
async def voice_stream_websocket(
    websocket: WebSocket,
    token: str
):
    """WebSocket endpoint for real-time voice streaming"""
    await websocket.accept()
    
    try:
        # Authenticate user
        # In production, validate token and get user
        user_id = "test_user"  # Placeholder
        
        # Initialize session
        session_id = f"voice_session_{user_id}_{datetime.utcnow().timestamp()}"
        voice_recognition_service.active_sessions[session_id] = {
            "user_id": user_id,
            "websocket": websocket,
            "start_time": datetime.utcnow(),
            "language": "en"
        }
        
        # Send initial response
        await websocket.send_json({
            "type": "session_started",
            "session_id": session_id,
            "message": "Voice session started"
        })
        
        # Handle incoming audio streams
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "audio_chunk":
                # Process audio chunk
                audio_data = base64.b64decode(data["audio"])
                language = data.get("language", "en")
                
                command = await voice_recognition_service.process_audio_stream(
                    user_id,
                    audio_data,
                    language
                )
                
                if command:
                    await websocket.send_json({
                        "type": "command_detected",
                        "command": {
                            "type": command.type.value,
                            "text": command.text,
                            "confidence": command.confidence,
                            "parameters": command.parameters
                        }
                    })
            
            elif data["type"] == "end_session":
                break
            
            elif data["type"] == "update_language":
                session = voice_recognition_service.active_sessions.get(session_id)
                if session:
                    session["language"] = data.get("language", "en")
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        # Clean up session
        if session_id in voice_recognition_service.active_sessions:
            del voice_recognition_service.active_sessions[session_id]
        
        try:
            await websocket.close()
        except:
            pass

@router.post("/custom-command")
async def add_custom_command(
    name: str,
    pattern: str,
    action: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Add custom voice command for user"""
    try:
        profile = voice_recognition_service.voice_profiles.get(str(current_user.id))
        
        if not profile:
            # Create default profile
            profile = await voice_recognition_service.create_voice_profile(
                str(current_user.id),
                {}
            )
        
        # Add custom command
        profile.custom_commands[name] = {
            "pattern": pattern,
            "action": action,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "message": f"Custom command '{name}' added successfully",
            "command": profile.custom_commands[name]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/custom-command/{name}")
async def delete_custom_command(
    name: str,
    current_user: User = Depends(get_current_user)
):
    """Delete custom voice command"""
    try:
        profile = voice_recognition_service.voice_profiles.get(str(current_user.id))
        
        if not profile or name not in profile.custom_commands:
            raise HTTPException(status_code=404, detail="Custom command not found")
        
        del profile.custom_commands[name]
        
        return {"message": f"Custom command '{name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))