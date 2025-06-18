"""
Enhanced AI-powered content assignment functions for workspaces
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from models.workspace import Workspace
from services.ai_service import ai_service


async def get_workspace_template_context(workspace: Workspace, db: Session) -> Dict[str, Any]:
    """Get template context for workspace to understand its intended purpose"""
    template_mapping = {
        "professional": "work",
        "minimal": "focus",
        "light": "study",
        "colorful": "creative",
        "dark": "focus"
    }
    
    likely_template = template_mapping.get(workspace.theme, "general")
    
    templates = {
        "work": {
            "focus_areas": ["productivity", "business", "tasks", "meetings", "deadlines"],
            "content_types": ["documents", "spreadsheets", "presentations", "emails"],
            "priority_keywords": ["urgent", "deadline", "meeting", "project", "client"]
        },
        "personal": {
            "focus_areas": ["life", "family", "health", "hobbies", "personal growth"],
            "content_types": ["photos", "notes", "reminders", "personal documents"],
            "priority_keywords": ["important", "remember", "appointment", "birthday"]
        },
        "study": {
            "focus_areas": ["learning", "research", "education", "knowledge", "skills"],
            "content_types": ["notes", "pdfs", "research papers", "flashcards"],
            "priority_keywords": ["exam", "assignment", "deadline", "study", "learn"]
        },
        "creative": {
            "focus_areas": ["art", "design", "creativity", "inspiration", "projects"],
            "content_types": ["images", "videos", "designs", "ideas", "sketches"],
            "priority_keywords": ["inspiration", "idea", "draft", "concept", "creative"]
        },
        "focus": {
            "focus_areas": ["deep work", "concentration", "important tasks", "minimal distractions"],
            "content_types": ["essential documents", "core tasks", "priority items"],
            "priority_keywords": ["critical", "important", "focus", "priority", "essential"]
        },
        "wellness": {
            "focus_areas": ["health", "fitness", "mental wellness", "self-care", "mindfulness"],
            "content_types": ["health records", "workout plans", "meditation guides"],
            "priority_keywords": ["health", "wellness", "exercise", "meditation", "self-care"]
        }
    }
    
    return templates.get(likely_template, templates["work"])


async def calculate_enhanced_compatibility(
    content_analysis: Dict[str, Any],
    workspace_analysis: Dict[str, Any],
    template_context: Dict[str, Any],
    content_type: str,
    content_tags: List[str],
    workspace: Workspace
) -> Dict[str, Any]:
    """Calculate multi-factor compatibility score with detailed reasoning"""
    
    factors = {
        "category_match": 0.0,
        "priority_match": 0.0,
        "content_type_match": 0.0,
        "keyword_match": 0.0,
        "theme_alignment": 0.0,
        "tag_relevance": 0.0
    }
    
    reasoning_parts = []
    
    # 1. Category matching (30% weight)
    content_category = content_analysis.get("category", "general")
    workspace_category = workspace_analysis.get("category", "general")
    
    if content_category == workspace_category:
        factors["category_match"] = 0.9
        reasoning_parts.append(f"Strong category match: {content_category}")
    elif content_category in ["general"] or workspace_category in ["general"]:
        factors["category_match"] = 0.6
        reasoning_parts.append(f"General category compatibility")
    else:
        factors["category_match"] = 0.3
        reasoning_parts.append(f"Category mismatch: {content_category} vs {workspace_category}")
    
    # 2. Priority matching (20% weight)
    content_priority = content_analysis.get("priority", "medium")
    if "urgent" in workspace.name.lower() and content_priority == "urgent":
        factors["priority_match"] = 0.9
        reasoning_parts.append("Priority alignment: urgent content for urgent workspace")
    elif "focus" in workspace.theme and content_priority in ["high", "urgent"]:
        factors["priority_match"] = 0.8
        reasoning_parts.append("High priority content fits focus workspace")
    else:
        factors["priority_match"] = 0.5
    
    # 3. Content type matching (15% weight)
    if content_type in template_context["content_types"]:
        factors["content_type_match"] = 0.8
        reasoning_parts.append(f"Content type '{content_type}' matches workspace purpose")
    else:
        factors["content_type_match"] = 0.4
    
    # 4. Keyword matching (15% weight)
    content_text = (content_analysis.get("text", "") or content_analysis.get("description", "")).lower()
    keyword_matches = sum(1 for keyword in template_context["priority_keywords"] 
                         if keyword in content_text)
    if keyword_matches > 0:
        factors["keyword_match"] = min(0.9, 0.3 * keyword_matches)
        reasoning_parts.append(f"Found {keyword_matches} relevant keywords")
    else:
        factors["keyword_match"] = 0.2
    
    # 5. Theme alignment (10% weight)
    theme_content_mapping = {
        "professional": ["business", "work", "corporate", "meeting", "client", "project"],
        "minimal": ["simple", "clean", "essential", "focus", "important"],
        "dark": ["late", "night", "intensive", "deep", "urgent"],
        "colorful": ["creative", "fun", "vibrant", "artistic", "design"],
        "light": ["study", "learning", "bright", "clear", "research"]
    }
    
    theme_keywords = theme_content_mapping.get(workspace.theme, [])
    theme_matches = sum(1 for keyword in theme_keywords if keyword in content_text)
    if theme_matches > 0:
        factors["theme_alignment"] = min(0.8, 0.3 * theme_matches)
        reasoning_parts.append(f"Theme alignment: {theme_matches} matching keywords")
    else:
        factors["theme_alignment"] = 0.3
    
    # 6. Tag relevance (10% weight)
    workspace_focus_areas = template_context["focus_areas"]
    tag_matches = sum(1 for tag in content_tags 
                     if any(area in tag.lower() for area in workspace_focus_areas))
    if tag_matches > 0:
        factors["tag_relevance"] = min(0.9, 0.3 * tag_matches)
        reasoning_parts.append(f"Tags align with workspace focus areas")
    else:
        factors["tag_relevance"] = 0.3
    
    # Calculate weighted total score
    weights = {
        "category_match": 0.30,
        "priority_match": 0.20,
        "content_type_match": 0.15,
        "keyword_match": 0.15,
        "theme_alignment": 0.10,
        "tag_relevance": 0.10
    }
    
    total_score = sum(factors[factor] * weights[factor] for factor in factors)
    
    # Generate recommendation
    if total_score >= 0.75:
        recommendation = "highly_recommended"
        rec_text = "Highly recommended - excellent fit"
    elif total_score >= 0.60:
        recommendation = "recommended"
        rec_text = "Recommended - good compatibility"
    elif total_score >= 0.45:
        recommendation = "consider"
        rec_text = "Consider - moderate compatibility"
    else:
        recommendation = "not_recommended"
        rec_text = "Not recommended - poor fit"
    
    return {
        "factors": factors,
        "weights": weights,
        "total_score": round(total_score, 3),
        "recommendation": recommendation,
        "recommendation_text": rec_text,
        "detailed_reasoning": "; ".join(reasoning_parts)
    }


async def generate_organization_suggestions(
    content: Dict[str, Any],
    workspace: Workspace,
    compatibility_factors: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate AI-powered suggestions for organizing content within the workspace"""
    suggestions = []
    
    content_type = content.get("type", "general")
    score = compatibility_factors["total_score"]
    
    # Widget placement suggestions
    if content_type == "task":
        suggestions.append({
            "type": "widget_placement",
            "suggestion": "Add to Tasks widget in top-left quadrant",
            "reason": "Tasks are most effective when prominently displayed",
            "confidence": 0.9
        })
    elif content_type == "note":
        suggestions.append({
            "type": "widget_placement",
            "suggestion": "Place in Notes widget with quick access pin",
            "reason": "Notes benefit from easy access and visibility",
            "confidence": 0.8
        })
    elif content_type == "file":
        suggestions.append({
            "type": "widget_placement",
            "suggestion": "Organize in Files widget with auto-categorization",
            "reason": "Files should be categorized for efficient retrieval",
            "confidence": 0.85
        })
    
    # Workflow integration suggestions
    if score > 0.7:
        suggestions.append({
            "type": "workflow_integration",
            "suggestion": "Set up automated processing for similar content",
            "reason": "High compatibility suggests this content type fits well",
            "confidence": 0.9
        })
    
    # Priority and urgency suggestions
    if "urgent" in content.get("text", "").lower():
        suggestions.append({
            "type": "priority_handling",
            "suggestion": "Pin to top of workspace and set reminder",
            "reason": "Urgent content needs immediate visibility",
            "confidence": 0.95
        })
    
    # Theme-specific suggestions
    if workspace.theme == "focus":
        suggestions.append({
            "type": "distraction_minimization",
            "suggestion": "Hide non-essential widgets while working on this content",
            "reason": "Focus theme benefits from minimal distractions",
            "confidence": 0.8
        })
    elif workspace.theme == "colorful":
        suggestions.append({
            "type": "visual_enhancement",
            "suggestion": "Add color coding and visual tags",
            "reason": "Creative workspace benefits from visual organization",
            "confidence": 0.7
        })
    
    return suggestions


async def suggest_alternative_workspaces(
    db: Session, 
    content_analysis: Dict[str, Any], 
    current_workspace_id: int
) -> List[Dict[str, Any]]:
    """Suggest alternative workspaces that might be better fits"""
    
    # Get all workspaces except current one
    workspaces = db.query(Workspace).filter(Workspace.id != current_workspace_id).all()
    
    alternatives = []
    content_category = content_analysis.get("category", "general")
    
    for workspace in workspaces[:5]:  # Limit to top 5 alternatives
        workspace_context = f"{workspace.name} - {workspace.description or ''}"
        workspace_analysis = await ai_service.analyze_text(workspace_context)
        workspace_category = workspace_analysis.get("category", "general")
        
        # Simple compatibility check
        if content_category == workspace_category:
            compatibility = 0.9
        elif content_category in ["general"] or workspace_category in ["general"]:
            compatibility = 0.6
        else:
            compatibility = 0.3
        
        if compatibility > 0.5:
            alternatives.append({
                "workspace_id": workspace.id,
                "workspace_name": workspace.name,
                "compatibility_score": compatibility,
                "reason": f"Better category match: {workspace_category}"
            })
    
    # Sort by compatibility score
    alternatives.sort(key=lambda x: x["compatibility_score"], reverse=True)
    
    return alternatives[:3]  # Return top 3 alternatives