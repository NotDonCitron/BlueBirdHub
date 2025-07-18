"""
Workspace API endpoints for OrdnungsHub
Provides workspace management and AI-powered organization
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from loguru import logger

from database.database import get_db
from models.workspace import Workspace, WorkspaceTheme
from schemas.workspace import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    WorkspaceStateUpdate, WorkspaceThemeCreate
)
from crud.crud_workspace import workspace as crud_workspace
from services.ai_service import ai_service
from api.workspaces_enhanced import (
    get_workspace_template_context,
    calculate_enhanced_compatibility,
    generate_organization_suggestions,
    suggest_alternative_workspaces
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get("/templates")
async def get_workspace_templates():
    """Get available workspace templates with enhanced information"""
    try:
        templates = {
            "work": {
                "name": "work",
                "display_name": "Professional",
                "description": "Optimized for productivity and business tasks",
                "theme": "professional",
                "color": "#2563eb",
                "icon": "💼",
                "default_widgets": ["calendar", "tasks", "notes", "quick_actions"],
                "ambient_sound": "office_ambience",
                "features": ["Task management", "Calendar integration", "Note taking", "Professional appearance"],
                "recommended_for": ["Business professionals", "Project managers", "Remote workers"]
            },
            "personal": {
                "name": "personal",
                "display_name": "Personal",
                "description": "For daily life and personal organization",
                "theme": "minimal",
                "color": "#059669",
                "icon": "🏠",
                "default_widgets": ["calendar", "notes", "weather", "quick_actions"],
                "ambient_sound": "nature_sounds",
                "features": ["Personal scheduling", "Weather updates", "Daily planning", "Clean interface"],
                "recommended_for": ["Home organization", "Personal productivity", "Life management"]
            },
            "study": {
                "name": "study",
                "display_name": "Study",
                "description": "Focused environment for learning and research",
                "theme": "light",
                "color": "#7c3aed",
                "icon": "📚",
                "default_widgets": ["notes", "timer", "calendar", "files"],
                "ambient_sound": "study_music",
                "features": ["Pomodoro timer", "Note organization", "File management", "Focus-enhancing design"],
                "recommended_for": ["Students", "Researchers", "Lifelong learners"]
            },
            "creative": {
                "name": "creative",
                "display_name": "Creative",
                "description": "Inspiring space for creative work and projects",
                "theme": "colorful",
                "color": "#ea580c",
                "icon": "🎨",
                "default_widgets": ["files", "notes", "gallery", "music"],
                "ambient_sound": "creativity_boost",
                "features": ["Visual inspiration", "Media management", "Color-rich interface", "Creative tools"],
                "recommended_for": ["Artists", "Designers", "Content creators"]
            },
            "focus": {
                "name": "focus",
                "display_name": "Deep Focus",
                "description": "Distraction-free environment for concentrated work",
                "theme": "minimal",
                "color": "#1f2937",
                "icon": "🎯",
                "default_widgets": ["timer", "notes", "tasks"],
                "ambient_sound": "white_noise",
                "features": ["Minimal distractions", "Focus timer", "Essential tools only", "Dark theme"],
                "recommended_for": ["Deep work sessions", "Writing", "Programming"]
            },
            "wellness": {
                "name": "wellness",
                "display_name": "Wellness & Health",
                "description": "Supportive environment for health and wellness tracking",
                "theme": "light",
                "color": "#10b981",
                "icon": "🌿",
                "default_widgets": ["calendar", "notes", "weather", "timer"],
                "ambient_sound": "meditation_sounds",
                "features": ["Health tracking", "Meditation timer", "Wellness reminders", "Calming colors"],
                "recommended_for": ["Health enthusiasts", "Wellness coaches", "Self-care focus"]
            }
        }
        
        return {
            "templates": templates,
            "total": len(templates),
            "categories": ["productivity", "personal", "creative", "focus", "health"]
        }
        
    except Exception as e:
        logger.error(f"Error fetching workspace templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workspace templates")

@router.get("/themes")
async def get_available_themes(db: Session = Depends(get_db)):
    """Get all available workspace themes"""
    try:
        # Built-in themes
        builtin_themes = {
            "professional": {
                "name": "professional",
                "display_name": "Professional",
                "description": "Clean, business-focused design",
                "primary_color": "#2563eb",
                "secondary_color": "#1e40af",
                "accent_color": "#3b82f6",
                "background_color": "#ffffff",
                "text_color": "#1f2937",
                "is_dark_mode": False,
                "is_system": True
            },
            "minimal": {
                "name": "minimal",
                "display_name": "Minimal",
                "description": "Simple, distraction-free interface",
                "primary_color": "#6b7280",
                "secondary_color": "#4b5563",
                "accent_color": "#9ca3af",
                "background_color": "#f9fafb",
                "text_color": "#111827",
                "is_dark_mode": False,
                "is_system": True
            },
            "dark": {
                "name": "dark",
                "display_name": "Dark",
                "description": "Easy on the eyes for long work sessions",
                "primary_color": "#1f2937",
                "secondary_color": "#111827",
                "accent_color": "#3b82f6",
                "background_color": "#030712",
                "text_color": "#f9fafb",
                "is_dark_mode": True,
                "is_system": True
            },
            "colorful": {
                "name": "colorful",
                "display_name": "Colorful",
                "description": "Vibrant and inspiring design",
                "primary_color": "#ea580c",
                "secondary_color": "#dc2626",
                "accent_color": "#f59e0b",
                "background_color": "#fffbeb",
                "text_color": "#1f2937",
                "is_dark_mode": False,
                "is_system": True
            },
            "light": {
                "name": "light",
                "display_name": "Light",
                "description": "Bright and airy workspace",
                "primary_color": "#7c3aed",
                "secondary_color": "#6d28d9",
                "accent_color": "#8b5cf6",
                "background_color": "#ffffff",
                "text_color": "#374151",
                "is_dark_mode": False,
                "is_system": True
            }
        }
        
        # Get custom themes from database
        custom_themes = db.query(WorkspaceTheme).filter(WorkspaceTheme.is_system == False).all()
        
        return {
            "builtin_themes": builtin_themes,
            "custom_themes": [
                {
                    "name": theme.name,
                    "display_name": theme.display_name,
                    "description": theme.description,
                    "primary_color": theme.primary_color,
                    "secondary_color": theme.secondary_color,
                    "accent_color": theme.accent_color,
                    "background_color": theme.background_color,
                    "text_color": theme.text_color,
                    "is_dark_mode": theme.is_dark_mode,
                    "is_system": theme.is_system
                } for theme in custom_themes
            ],
            "total_themes": len(builtin_themes) + len(custom_themes)
        }
        
    except Exception as e:
        logger.error(f"Error fetching themes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch themes")

@router.get("/", response_model=List[WorkspaceResponse])
async def get_workspaces(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all workspaces for a user"""
    try:
        # Try to get workspaces from database
        try:
            workspaces = crud_workspace.get_multi_by_user(
                db, user_id=user_id or 1, skip=skip, limit=limit
            )
            if workspaces:
                return workspaces
        except Exception as db_error:
            logger.warning(f"Database workspace fetch failed: {db_error}")
        
        # Return mock workspaces if database is empty or fails
        mock_workspaces = [
            {
                "id": 1,
                "name": "Development",
                "description": "Software development and coding projects",
                "theme": "professional", 
                "color": "#3b82f6",
                "user_id": 1,
                "created_at": "2024-06-08T10:00:00Z",
                "updated_at": "2024-06-08T10:00:00Z",
                "is_active": True,
                "layout_config": {},
                "ambient_sound": "office_ambience"
            },
            {
                "id": 2,
                "name": "Design",
                "description": "UI/UX design and creative projects",
                "theme": "colorful",
                "color": "#10b981", 
                "user_id": 1,
                "created_at": "2024-06-08T11:00:00Z",
                "updated_at": "2024-06-08T11:00:00Z",
                "is_active": True,
                "layout_config": {},
                "ambient_sound": "creativity_boost"
            },
            {
                "id": 3,
                "name": "Research",
                "description": "Research and documentation workspace",
                "theme": "light",
                "color": "#7c3aed",
                "user_id": 1,
                "created_at": "2024-06-08T12:00:00Z",
                "updated_at": "2024-06-08T12:00:00Z", 
                "is_active": True,
                "layout_config": {},
                "ambient_sound": "study_music"
            }
        ]
        
        return mock_workspaces
    except Exception as e:
        logger.error(f"Error fetching workspaces: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workspaces")

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: int, db: Session = Depends(get_db)):
    """Get a specific workspace by ID"""
    try:
        workspace = crud_workspace.get(db, id=workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return workspace
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workspace")

@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    workspace: WorkspaceCreate,
    db: Session = Depends(get_db)
):
    """Create a new workspace"""
    try:
        # Use AI to suggest initial settings if description provided
        ai_suggestions = {}
        if workspace.description:
            analysis = await ai_service.analyze_text(workspace.description)
            ai_suggestions = {
                "suggested_category": analysis.get("category", "general"),
                "suggested_tags": await ai_service.suggest_tags(workspace.description)
            }
        
        # Create workspace with AI suggestions
        workspace_data = workspace.model_dump()
        if (not workspace_data.get("theme") or workspace_data.get("theme") == "default") and ai_suggestions.get("suggested_category"):
            # Map AI category to theme
            category_theme_map = {
                "work": "professional",
                "personal": "minimal",
                "finance": "dark",
                "education": "light"
            }
            workspace_data["theme"] = category_theme_map.get(
                ai_suggestions["suggested_category"], "default"
            )
        
        db_workspace = crud_workspace.create(db, obj_in=WorkspaceCreate(**workspace_data))
        
        # Log AI suggestions for user feedback
        if ai_suggestions:
            logger.info(f"AI suggestions for workspace {db_workspace.id}: {ai_suggestions}")
        
        return db_workspace
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workspace")

@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    workspace_update: WorkspaceUpdate,
    db: Session = Depends(get_db)
):
    """Update a workspace"""
    try:
        workspace = crud_workspace.get(db, id=workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        updated_workspace = crud_workspace.update(
            db, db_obj=workspace, obj_in=workspace_update
        )
        return updated_workspace
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update workspace")

@router.delete("/{workspace_id}")
async def delete_workspace(workspace_id: int, db: Session = Depends(get_db)):
    """Delete a workspace"""
    try:
        workspace = crud_workspace.get(db, id=workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        crud_workspace.remove(db, id=workspace_id)
        return {"message": "Workspace deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete workspace")

@router.post("/{workspace_id}/switch")
async def switch_workspace(
    workspace_id: int,
    db: Session = Depends(get_db)
):
    """Switch to a specific workspace"""
    try:
        workspace = crud_workspace.get(db, id=workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Mark workspace as active (set last_accessed)
        crud_workspace.mark_as_accessed(db, workspace_id=workspace_id)
        
        # Return workspace state for UI restoration
        return {
            "workspace": workspace,
            "state": workspace.layout_config or {},
            "message": f"Switched to workspace: {workspace.name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching to workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to switch workspace")

@router.put("/{workspace_id}/state")
async def update_workspace_state(
    workspace_id: int,
    state_update: WorkspaceStateUpdate,
    db: Session = Depends(get_db)
):
    """Update workspace state (for state preservation)"""
    try:
        workspace = crud_workspace.get(db, id=workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Update workspace state
        updated_workspace = crud_workspace.update_state(
            db, workspace_id=workspace_id, state=state_update.state
        )
        
        return {
            "workspace_id": workspace_id,
            "state": updated_workspace.layout_config,
            "message": "Workspace state updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workspace state {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update workspace state")

@router.get("/{workspace_id}/state")
async def get_workspace_state(workspace_id: int, db: Session = Depends(get_db)):
    """Get workspace state for restoration"""
    try:
        workspace = crud_workspace.get(db, id=workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        return {
            "workspace_id": workspace_id,
            "state": workspace.layout_config or {},
            "last_accessed_at": workspace.last_accessed_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workspace state {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workspace state")

@router.post("/{workspace_id}/assign-content")
async def assign_content_to_workspace(
    workspace_id: int,
    content: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Use AI to suggest content assignment to workspace with enhanced analysis"""
    try:
        workspace = crud_workspace.get(db, id=workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Analyze content with AI
        content_text = content.get("text", "") or content.get("description", "")
        content_type = content.get("type", "general")  # file, task, note, etc.
        content_tags = content.get("tags", [])
        
        if not content_text:
            raise HTTPException(status_code=400, detail="Content text is required for analysis")
        
        analysis = await ai_service.analyze_text(content_text)
        
        # Enhanced workspace analysis
        workspace_context = f"{workspace.name} - {workspace.description or ''} - Theme: {workspace.theme}"
        workspace_analysis = await ai_service.analyze_text(workspace_context)
        
        # Get workspace template data for context
        template_context = await get_workspace_template_context(workspace, db)
        
        # Multi-factor compatibility scoring
        compatibility_factors = await calculate_enhanced_compatibility(
            content_analysis=analysis,
            workspace_analysis=workspace_analysis,
            template_context=template_context,
            content_type=content_type,
            content_tags=content_tags,
            workspace=workspace
        )
        
        # Generate AI-powered organizational suggestions
        org_suggestions = await generate_organization_suggestions(
            content=content,
            workspace=workspace,
            compatibility_factors=compatibility_factors
        )
        
        return {
            "workspace_id": workspace_id,
            "workspace_name": workspace.name,
            "content_analysis": analysis,
            "compatibility_factors": compatibility_factors,
            "overall_compatibility": compatibility_factors["total_score"],
            "recommendation": compatibility_factors["recommendation"],
            "reasoning": compatibility_factors["detailed_reasoning"],
            "organization_suggestions": org_suggestions,
            "alternative_workspaces": await suggest_alternative_workspaces(
                db, analysis, workspace_id
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing content for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze content assignment")

@router.get("/{workspace_id}/suggestions")
async def get_workspace_suggestions(workspace_id: int, db: Session = Depends(get_db)):
    """Get AI suggestions for workspace optimization"""
    try:
        workspace = crud_workspace.get(db, id=workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Analyze workspace usage and provide suggestions
        suggestions = []
        
        # Theme suggestions based on name/description
        if workspace.description:
            analysis = await ai_service.analyze_text(workspace.description)
            category = analysis.get("category", "general")
            
            theme_suggestions = {
                "work": ["professional", "dark", "minimal"],
                "personal": ["light", "colorful", "minimal"],
                "finance": ["dark", "professional"],
                "education": ["light", "colorful"]
            }
            
            if category in theme_suggestions:
                suggestions.append({
                    "type": "theme",
                    "suggestion": theme_suggestions[category][0],
                    "reason": f"Based on {category} category detection"
                })
        
        # Layout suggestions based on workspace size/usage
        suggestions.append({
            "type": "layout",
            "suggestion": "Add quick actions widget",
            "reason": "Improve workflow efficiency"
        })
        
        return {
            "workspace_id": workspace_id,
            "suggestions": suggestions,
            "generated_at": "now"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating suggestions for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate workspace suggestions")

@router.post("/create-from-template")
async def create_workspace_from_template(
    template_name: str,
    workspace_name: str,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Create workspace from predefined template"""
    try:
        templates = {
            "work": {
                "theme": "professional",
                "description": "Professional workspace for work tasks and projects",
                "default_widgets": ["calendar", "tasks", "notes", "quick_actions"],
                "color_scheme": "blue",
                "ambient_sound": "office_ambience"
            },
            "personal": {
                "theme": "minimal",
                "description": "Personal workspace for daily life organization",
                "default_widgets": ["calendar", "notes", "weather", "quick_actions"],
                "color_scheme": "green",
                "ambient_sound": "nature_sounds"
            },
            "study": {
                "theme": "light",
                "description": "Study workspace for learning and education",
                "default_widgets": ["notes", "timer", "calendar", "files"],
                "color_scheme": "purple",
                "ambient_sound": "study_music"
            },
            "creative": {
                "theme": "colorful",
                "description": "Creative workspace for projects and inspiration",
                "default_widgets": ["files", "notes", "gallery", "music"],
                "color_scheme": "orange",
                "ambient_sound": "creativity_boost"
            },
            "focus": {
                "theme": "minimal",
                "description": "Distraction-free environment for concentrated work",
                "default_widgets": ["timer", "notes", "tasks"],
                "color_scheme": "dark",
                "ambient_sound": "white_noise"
            },
            "wellness": {
                "theme": "light",
                "description": "Supportive environment for health and wellness tracking",
                "default_widgets": ["calendar", "notes", "weather", "timer"],
                "color_scheme": "green",
                "ambient_sound": "meditation_sounds"
            }
        }
        
        if template_name not in templates:
            raise HTTPException(status_code=400, detail=f"Template '{template_name}' not found")
        
        template = templates[template_name]
        
        # Create workspace with template settings
        workspace_data = WorkspaceCreate(
            name=workspace_name,
            description=template["description"],
            theme=template["theme"],
            user_id=user_id or 1,
            ambient_sound=template.get("ambient_sound", "none"),
            layout_config={
                "widgets": template["default_widgets"],
                "color_scheme": template["color_scheme"],
                "created_from_template": template_name
            }
        )
        
        workspace = crud_workspace.create(db, obj_in=workspace_data)
        
        return {
            "workspace": workspace,
            "template_used": template_name,
            "message": f"Workspace '{workspace_name}' created from {template_name} template"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workspace from template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workspace from template")

@router.get("/{workspace_id}/analytics")
async def get_workspace_analytics(workspace_id: int, db: Session = Depends(get_db)):
    """Get analytics and usage statistics for a workspace"""
    try:
        workspace = crud_workspace.get(db, id=workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Calculate usage statistics
        from datetime import datetime, timedelta
        from sqlalchemy import and_, func as sql_func
        
        # Get task statistics for this workspace
        from models.task import Task
        
        # Task completion rate in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        total_tasks = db.query(Task).filter(
            and_(Task.workspace_id == workspace_id, Task.created_at >= thirty_days_ago)
        ).count()
        
        completed_tasks = db.query(Task).filter(
            and_(
                Task.workspace_id == workspace_id,
                Task.completed_at >= thirty_days_ago,
                Task.completed_at.isnot(None)
            )
        ).count()
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate time spent (simulated - would come from actual usage tracking)
        time_spent_hours = max(1, total_tasks * 0.5)  # Rough estimate
        
        # Generate productivity insights using AI
        analysis = await ai_service.analyze_text(
            f"Workspace: {workspace.name}. Description: {workspace.description or 'No description'}. "
            f"Tasks completed: {completed_tasks}/{total_tasks}. Theme: {workspace.theme}."
        )
        
        return {
            "workspace_id": workspace_id,
            "workspace_name": workspace.name,
            "analytics_period": "last_30_days",
            "usage_stats": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": round(completion_rate, 1),
                "estimated_time_spent_hours": round(time_spent_hours, 1),
                "last_accessed": workspace.last_accessed_at
            },
            "ai_insights": {
                "productivity_score": min(100, completion_rate + 20),  # Adjusted score
                "suggested_improvements": [
                    "Consider adding more visual widgets if completion rate is low",
                    "Try ambient sounds to improve focus",
                    "Regular workspace switching can boost productivity"
                ] if completion_rate < 70 else [
                    "Great productivity! Keep up the excellent work",
                    "Consider mentoring others on workspace organization"
                ],
                "category": analysis.get("category", "general"),
                "sentiment": analysis.get("sentiment", {}).get("label", "neutral")
            },
            "recommendations": [
                {
                    "type": "widget",
                    "suggestion": "Add a calendar widget for better time management",
                    "reason": "Low task completion rate suggests scheduling issues"
                } if completion_rate < 50 else {
                    "type": "optimization",
                    "suggestion": "Workspace is well-optimized",
                    "reason": "High productivity metrics indicate good setup"
                }
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating workspace analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate workspace analytics")

@router.post("/{workspace_id}/ambient-sound")
async def update_ambient_sound(
    workspace_id: int,
    sound_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update ambient sound settings for a workspace"""
    try:
        workspace = crud_workspace.get(db, id=workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Available ambient sounds
        available_sounds = {
            "none": "No ambient sound",
            "office_ambience": "Office ambience",
            "nature_sounds": "Nature sounds",
            "study_music": "Study music",
            "creativity_boost": "Creativity boost",
            "white_noise": "White noise",
            "meditation_sounds": "Meditation sounds",
            "rain": "Rain sounds",
            "forest": "Forest sounds",
            "ocean": "Ocean waves",
            "cafe": "Cafe ambience"
        }
        
        ambient_sound = sound_data.get("ambient_sound", "none")
        
        if ambient_sound not in available_sounds:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid ambient sound. Available options: {list(available_sounds.keys())}"
            )
        
        # Update workspace
        updated_workspace = crud_workspace.update(
            db, db_obj=workspace, obj_in={"ambient_sound": ambient_sound}
        )
        
        return {
            "workspace_id": workspace_id,
            "ambient_sound": ambient_sound,
            "sound_name": available_sounds[ambient_sound],
            "message": f"Ambient sound updated to '{available_sounds[ambient_sound]}'",
            "available_sounds": available_sounds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ambient sound: {e}")
        raise HTTPException(status_code=500, detail="Failed to update ambient sound")

@router.get("/workspace-files")
async def get_workspace_files(
    workspace_id: Optional[int] = None,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Get files for workspace(s) - compatible with frontend expectations
    """
    try:
        from crud.crud_file import file_metadata as crud_file
        
        if workspace_id:
            # Get files for specific workspace
            try:
                files = crud_file.get_by_workspace(db, workspace_id=workspace_id, skip=0, limit=100)
            except AttributeError:
                # Fallback if method doesn't exist
                files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=100)
                files = [f for f in files if f.workspace_id == workspace_id]
        else:
            # Get all files for user
            files = crud_file.get_by_user(db, user_id=user_id, skip=0, limit=100)
        
        # Convert to expected format
        results = []
        for file in files:
            results.append({
                "id": str(file.id),
                "name": file.name,
                "type": file.file_type or "unknown",
                "size": f"{file.size or 0} bytes",
                "modified": file.updated_at.isoformat() if file.updated_at else "",
                "tags": [],
                "category": file.user_category or file.ai_category or "Other",
                "priority": file.priority or "normal",
                "workspace_id": file.workspace_id or 1,
                "workspace_name": "Default",
                "folder": file.folder_path or ""
            })
        
        return {
            "success": True,
            "files": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Error loading workspace files: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "files": [],
            "total": 0
        }

@router.get("/{workspace_id}/detail")
async def get_workspace_detail(workspace_id: int, db: Session = Depends(get_db)):
    """
    Get comprehensive workspace details including tasks, files, and analytics
    """
    try:
        # Get workspace basic info
        workspace = crud_workspace.get(db, id=workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Get tasks for this workspace
        from crud.crud_task import task as crud_task
        from models.task import Task
        from sqlalchemy import and_, func as sql_func
        
        try:
            tasks = crud_task.get_by_workspace(db, workspace_id=workspace_id, skip=0, limit=100)
        except AttributeError:
            # Fallback if method doesn't exist
            tasks = db.query(Task).filter(Task.workspace_id == workspace_id).all()
        
        # Get files for this workspace
        from crud.crud_file import file_metadata as crud_file
        
        try:
            files = crud_file.get_by_workspace(db, workspace_id=workspace_id, skip=0, limit=100)
        except AttributeError:
            # Fallback if method doesn't exist
            from models.file_metadata import FileMetadata
            files = db.query(FileMetadata).filter(FileMetadata.workspace_id == workspace_id).all()
        
        # Calculate workspace statistics
        from datetime import datetime, timedelta
        
        # Task statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'completed' or t.status == 'done'])
        in_progress_tasks = len([t for t in tasks if t.status == 'in-progress'])
        pending_tasks = len([t for t in tasks if t.status == 'pending'])
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # File statistics
        total_files = len(files)
        file_types = {}
        total_size = 0
        
        for file in files:
            file_type = file.file_type or 'unknown'
            file_types[file_type] = file_types.get(file_type, 0) + 1
            total_size += file.size or 0
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_tasks = [t for t in tasks if t.created_at and t.created_at >= seven_days_ago]
        recent_files = [f for f in files if f.created_at and f.created_at >= seven_days_ago]
        
        # AI-powered workspace insights
        workspace_context = f"""
        Workspace: {workspace.name}
        Description: {workspace.description or 'No description'}
        Theme: {workspace.theme}
        Total tasks: {total_tasks}
        Completed tasks: {completed_tasks}
        Completion rate: {completion_rate:.1f}%
        Total files: {total_files}
        File types: {', '.join(file_types.keys()) if file_types else 'None'}
        """
        
        try:
            analysis = await ai_service.analyze_text(workspace_context)
            ai_insights = {
                "productivity_score": min(100, completion_rate + 20),
                "category": analysis.get("category", "general"),
                "sentiment": analysis.get("sentiment", {}).get("label", "neutral"),
                "keywords": analysis.get("keywords", []),
                "suggestions": []
            }
            
            # Generate AI suggestions
            if completion_rate < 50:
                ai_insights["suggestions"].append("Consider reorganizing tasks by priority")
            if total_files > 20 and len(file_types) > 5:
                ai_insights["suggestions"].append("Files could benefit from better organization")
            if in_progress_tasks > completed_tasks:
                ai_insights["suggestions"].append("Focus on completing existing tasks")
            
        except Exception as ai_error:
            logger.warning(f"AI analysis failed: {ai_error}")
            ai_insights = {
                "productivity_score": 50,
                "category": "general",
                "sentiment": "neutral",
                "keywords": [],
                "suggestions": ["AI analysis temporarily unavailable"]
            }
        
        # Format tasks for frontend
        task_data = []
        for task in tasks[:10]:  # Limit to 10 most recent
            task_data.append({
                "id": str(task.id),
                "title": task.title,
                "description": task.description or "",
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at.isoformat() if task.created_at else "",
                "updated_at": task.updated_at.isoformat() if task.updated_at else "",
                "due_date": task.due_date.isoformat() if hasattr(task, 'due_date') and task.due_date else None
            })
        
        # Format files for frontend
        file_data = []
        for file in files[:10]:  # Limit to 10 most recent
            file_data.append({
                "id": str(file.id),
                "name": file.name,
                "type": file.file_type or "unknown",
                "size": file.size or 0,
                "size_formatted": f"{(file.size or 0) / 1024:.1f} KB" if file.size else "0 KB",
                "created_at": file.created_at.isoformat() if file.created_at else "",
                "updated_at": file.updated_at.isoformat() if file.updated_at else "",
                "category": file.user_category or file.ai_category or "Other",
                "priority": file.priority or "normal"
            })
        
        return {
            "workspace": {
                "id": workspace.id,
                "name": workspace.name,
                "description": workspace.description,
                "theme": workspace.theme,
                "color": workspace.color,
                "created_at": workspace.created_at.isoformat() if workspace.created_at else "",
                "updated_at": workspace.updated_at.isoformat() if workspace.updated_at else "",
                "last_accessed_at": workspace.last_accessed_at.isoformat() if workspace.last_accessed_at else "",
                "layout_config": workspace.layout_config or {}
            },
            "statistics": {
                "tasks": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "in_progress": in_progress_tasks,
                    "pending": pending_tasks,
                    "completion_rate": round(completion_rate, 1)
                },
                "files": {
                    "total": total_files,
                    "total_size": total_size,
                    "total_size_formatted": f"{total_size / (1024*1024):.1f} MB" if total_size > 0 else "0 MB",
                    "types": file_types
                },
                "activity": {
                    "recent_tasks": len(recent_tasks),
                    "recent_files": len(recent_files),
                    "last_activity": max(
                        [t.updated_at for t in tasks if t.updated_at] + 
                        [f.updated_at for f in files if f.updated_at] + 
                        [datetime.min]
                    ).isoformat() if (tasks or files) else None
                }
            },
            "tasks": task_data,
            "files": file_data,
            "ai_insights": ai_insights,
            "recommendations": [
                {
                    "type": "productivity",
                    "title": "High Productivity" if completion_rate > 70 else "Room for Improvement",
                    "description": "Great work!" if completion_rate > 70 else "Consider prioritizing task completion",
                    "priority": "low" if completion_rate > 70 else "medium"
                },
                {
                    "type": "organization",
                    "title": "File Organization",
                    "description": "Files are well organized" if len(file_types) <= 3 else "Consider organizing files by type",
                    "priority": "low" if len(file_types) <= 3 else "medium"
                }
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workspace detail {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch workspace detail: {str(e)}")
