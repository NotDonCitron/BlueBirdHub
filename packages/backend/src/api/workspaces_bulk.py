"""
Bulk operations and advanced AI content assignment endpoints for workspaces
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from loguru import logger

from database.database import get_db
from models.workspace import Workspace
from services.ai_service import ai_service
from api.workspaces_enhanced import (
    get_workspace_template_context,
    calculate_enhanced_compatibility
)

router = APIRouter(prefix="/workspaces", tags=["workspaces-bulk"])


@router.post("/bulk-assign-content")
async def bulk_assign_content(
    content_items: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """Analyze multiple content items and suggest optimal workspace assignments"""
    try:
        # Get all available workspaces
        workspaces = db.query(Workspace).filter(Workspace.is_active == True).all()
        
        if not workspaces:
            raise HTTPException(status_code=404, detail="No active workspaces found")
        
        results = []
        
        for content in content_items:
            content_text = content.get("text", "") or content.get("description", "")
            content_type = content.get("type", "general")
            content_tags = content.get("tags", [])
            
            if not content_text:
                results.append({
                    "content_id": content.get("id", "unknown"),
                    "error": "Content text is required for analysis",
                    "recommendations": []
                })
                continue
            
            # Analyze content
            content_analysis = await ai_service.analyze_text(content_text)
            
            # Score against all workspaces
            workspace_scores = []
            
            for workspace in workspaces:
                workspace_context = f"{workspace.name} - {workspace.description or ''} - Theme: {workspace.theme}"
                workspace_analysis = await ai_service.analyze_text(workspace_context)
                template_context = await get_workspace_template_context(workspace, db)
                
                compatibility_factors = await calculate_enhanced_compatibility(
                    content_analysis=content_analysis,
                    workspace_analysis=workspace_analysis,
                    template_context=template_context,
                    content_type=content_type,
                    content_tags=content_tags,
                    workspace=workspace
                )
                
                workspace_scores.append({
                    "workspace_id": workspace.id,
                    "workspace_name": workspace.name,
                    "workspace_theme": workspace.theme,
                    "compatibility_score": compatibility_factors["total_score"],
                    "recommendation": compatibility_factors["recommendation"],
                    "reasoning": compatibility_factors["detailed_reasoning"]
                })
            
            # Sort by compatibility score
            workspace_scores.sort(key=lambda x: x["compatibility_score"], reverse=True)
            
            results.append({
                "content_id": content.get("id", "unknown"),
                "content_analysis": content_analysis,
                "recommendations": workspace_scores[:3],  # Top 3 recommendations
                "best_match": workspace_scores[0] if workspace_scores else None
            })
        
        return {
            "total_content_items": len(content_items),
            "results": results,
            "summary": {
                "processed": len([r for r in results if "error" not in r]),
                "errors": len([r for r in results if "error" in r])
            }
        }
        
    except Exception as e:
        logger.error(f"Error in bulk content assignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to process bulk content assignment")


@router.post("/optimize-all")
async def optimize_all_workspaces(db: Session = Depends(get_db)):
    """AI-powered optimization suggestions for all user workspaces"""
    try:
        workspaces = db.query(Workspace).filter(Workspace.is_active == True).all()
        
        optimization_results = []
        
        for workspace in workspaces:
            # Analyze workspace for optimization opportunities
            workspace_context = f"{workspace.name} - {workspace.description or ''} - Theme: {workspace.theme}"
            analysis = await ai_service.analyze_text(workspace_context)
            template_context = await get_workspace_template_context(workspace, db)
            
            # Generate optimization suggestions
            optimizations = []
            
            # Theme optimization
            if workspace.theme == "default":
                suggested_theme = "professional"  # Default suggestion
                category = analysis.get("category", "general")
                theme_map = {
                    "work": "professional",
                    "personal": "minimal",
                    "education": "light",
                    "creative": "colorful",
                    "finance": "dark"
                }
                suggested_theme = theme_map.get(category, "professional")
                
                optimizations.append({
                    "type": "theme",
                    "current": workspace.theme,
                    "suggested": suggested_theme,
                    "reason": f"Based on detected category: {category}",
                    "impact": "medium",
                    "confidence": 0.8
                })
            
            # Layout optimization based on content type
            if not workspace.layout_config or not workspace.layout_config.get("widgets"):
                default_widgets = template_context["content_types"][:4]  # Top 4 widget types
                optimizations.append({
                    "type": "layout",
                    "current": "empty",
                    "suggested": default_widgets,
                    "reason": "Add recommended widgets for workspace type",
                    "impact": "high",
                    "confidence": 0.9
                })
            
            # Ambient sound optimization
            if not workspace.ambient_sound or workspace.ambient_sound == "none":
                sound_suggestions = {
                    "work": "office_ambience",
                    "personal": "nature_sounds",
                    "study": "study_music",
                    "creative": "creativity_boost",
                    "focus": "white_noise",
                    "wellness": "meditation_sounds"
                }
                template_type = template_context.get("type", "work")
                suggested_sound = sound_suggestions.get(template_type, "nature_sounds")
                
                optimizations.append({
                    "type": "ambient_sound",
                    "current": workspace.ambient_sound or "none",
                    "suggested": suggested_sound,
                    "reason": "Enhance focus with appropriate ambient sound",
                    "impact": "low",
                    "confidence": 0.7
                })
            
            optimization_results.append({
                "workspace_id": workspace.id,
                "workspace_name": workspace.name,
                "current_theme": workspace.theme,
                "analysis": analysis,
                "optimizations": optimizations,
                "optimization_score": len(optimizations) * 0.3  # Simple score based on number of optimizations
            })
        
        # Sort by optimization potential
        optimization_results.sort(key=lambda x: x["optimization_score"], reverse=True)
        
        return {
            "total_workspaces": len(workspaces),
            "optimization_results": optimization_results,
            "summary": {
                "workspaces_needing_optimization": len([r for r in optimization_results if r["optimization_score"] > 0]),
                "total_optimizations": sum(len(r["optimizations"]) for r in optimization_results),
                "avg_optimization_score": sum(r["optimization_score"] for r in optimization_results) / len(optimization_results) if optimization_results else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error optimizing workspaces: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize workspaces")


@router.get("/content-insights")
async def get_content_insights(
    workspace_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get AI-powered insights about content distribution and workspace usage patterns"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import and_, func as sql_func
        from models.task import Task
        
        # Date range for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query workspace usage patterns
        if workspace_id:
            workspaces = db.query(Workspace).filter(Workspace.id == workspace_id).all()
        else:
            workspaces = db.query(Workspace).filter(Workspace.is_active == True).all()
        
        insights = []
        
        for workspace in workspaces:
            # Get task statistics
            total_tasks = db.query(Task).filter(
                and_(Task.workspace_id == workspace.id, Task.created_at >= start_date)
            ).count()
            
            completed_tasks = db.query(Task).filter(
                and_(
                    Task.workspace_id == workspace.id,
                    Task.completed_at >= start_date,
                    Task.completed_at.isnot(None)
                )
            ).count()
            
            # Calculate productivity metrics
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            productivity_score = min(100, completion_rate + 20)  # Adjusted score
            
            # AI analysis of workspace content patterns
            workspace_analysis = await ai_service.analyze_text(
                f"Workspace: {workspace.name}. Description: {workspace.description or 'No description'}. "
                f"Tasks: {total_tasks}, Completed: {completed_tasks}, Theme: {workspace.theme}"
            )
            
            # Generate insights
            workspace_insights = {
                "workspace_id": workspace.id,
                "workspace_name": workspace.name,
                "analysis_period": f"{days} days",
                "metrics": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "completion_rate": round(completion_rate, 1),
                    "productivity_score": round(productivity_score, 1)
                },
                "ai_insights": {
                    "content_category": workspace_analysis.get("category", "general"),
                    "productivity_level": "high" if completion_rate > 70 else "medium" if completion_rate > 40 else "low",
                    "optimization_potential": "low" if completion_rate > 80 else "medium" if completion_rate > 50 else "high",
                    "theme_effectiveness": "good" if workspace.theme != "default" else "needs_improvement"
                },
                "recommendations": []
            }
            
            # Generate specific recommendations
            if completion_rate < 50:
                workspace_insights["recommendations"].append({
                    "type": "productivity",
                    "suggestion": "Consider breaking down large tasks into smaller, manageable pieces",
                    "priority": "high"
                })
            
            if workspace.theme == "default":
                workspace_insights["recommendations"].append({
                    "type": "theme",
                    "suggestion": "Customize workspace theme to match your work style",
                    "priority": "medium"
                })
            
            if not workspace.ambient_sound:
                workspace_insights["recommendations"].append({
                    "type": "ambient_sound",
                    "suggestion": "Add ambient sounds to improve focus and productivity",
                    "priority": "low"
                })
            
            insights.append(workspace_insights)
        
        # Overall summary
        total_workspaces = len(insights)
        avg_completion_rate = sum(i["metrics"]["completion_rate"] for i in insights) / total_workspaces if total_workspaces > 0 else 0
        high_performers = len([i for i in insights if i["metrics"]["completion_rate"] > 70])
        
        return {
            "analysis_period": f"{days} days",
            "workspace_insights": insights,
            "summary": {
                "total_workspaces_analyzed": total_workspaces,
                "average_completion_rate": round(avg_completion_rate, 1),
                "high_performing_workspaces": high_performers,
                "workspaces_needing_attention": len([i for i in insights if i["metrics"]["completion_rate"] < 40])
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating content insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate content insights")