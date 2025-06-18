"""
AI API endpoints for OrdnungsHub
Provides AI-powered analysis and suggestions
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from loguru import logger

from services.ai_service import ai_service
from services.enhanced_ai_service import enhanced_ai_service
# from src.backend.services.file_scanner import file_scanner

router = APIRouter(prefix="/ai", tags=["ai"])

# Request/Response Models
class TextAnalysisRequest(BaseModel):
    text: str
    
class TextAnalysisResponse(BaseModel):
    entities: Dict[str, List[str]]
    sentiment: Dict[str, Any]
    priority: str
    category: str
    keywords: List[str]
    word_count: int
    character_count: int
    language: str

class TagSuggestionRequest(BaseModel):
    text: str
    
class TagSuggestionResponse(BaseModel):
    tags: List[str]

class FileCategorizeRequest(BaseModel):
    filename: str
    content_preview: Optional[str] = ""
    
class FileCategorizeResponse(BaseModel):
    category: str
    subcategory: str
    tags: List[str]
    priority: str

class AIStatusResponse(BaseModel):
    service: str
    status: str
    capabilities: List[str]
    models: str
    privacy: str

@router.get("/status", response_model=AIStatusResponse)
async def get_ai_status():
    """Get AI service status and capabilities"""
    try:
        status = ai_service.get_status()
        return AIStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI service status")

@router.post("/analyze-text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze text and extract insights including:
    - Named entities (emails, phones, URLs)
    - Sentiment analysis
    - Priority suggestion
    - Category suggestion
    - Keywords
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        analysis = await ai_service.analyze_text(request.text)
        
        # Handle empty analysis result
        if not analysis:
            raise HTTPException(status_code=400, detail="Text content is too short to analyze")
        
        return TextAnalysisResponse(**analysis)
    
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 errors)
        raise
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze text: {str(e)}")

@router.post("/suggest-tags", response_model=TagSuggestionResponse)
async def suggest_tags(request: TagSuggestionRequest):
    """
    Suggest relevant tags for content based on text analysis
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        tags = await ai_service.suggest_tags(request.text)
        
        return TagSuggestionResponse(tags=tags)
    
    except Exception as e:
        logger.error(f"Error suggesting tags: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to suggest tags: {str(e)}")

@router.post("/categorize-file", response_model=FileCategorizeResponse)
async def categorize_file(request: FileCategorizeRequest):
    """
    Categorize file based on filename and optional content preview
    """
    try:
        if not request.filename.strip():
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        result = await ai_service.categorize_file(
            request.filename, 
            request.content_preview or ""
        )
        
        return FileCategorizeResponse(**result)
    
    except Exception as e:
        logger.error(f"Error categorizing file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to categorize file: {str(e)}")

@router.post("/suggest-priority")
async def suggest_task_priority(request: TextAnalysisRequest):
    """
    Suggest task priority based on text content
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        analysis = await ai_service.analyze_text(request.text)
        
        return {
            "priority": analysis.get("priority", "medium"),
            "reasoning": f"Based on content analysis and keyword detection",
            "confidence": 0.7  # Static confidence for rule-based system
        }
    
    except Exception as e:
        logger.error(f"Error suggesting priority: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to suggest priority: {str(e)}")

@router.post("/extract-entities")
async def extract_entities(request: TextAnalysisRequest):
    """
    Extract named entities from text (emails, phones, URLs)
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        analysis = await ai_service.analyze_text(request.text)
        
        return {
            "entities": analysis.get("entities", {}),
            "count": sum(len(entities) for entities in analysis.get("entities", {}).values())
        }
    
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract entities: {str(e)}")

@router.post("/analyze-sentiment")
async def analyze_sentiment(request: TextAnalysisRequest):
    """
    Analyze sentiment of text content
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        analysis = await ai_service.analyze_text(request.text)
        sentiment = analysis.get("sentiment", {})
        
        return {
            "sentiment": sentiment.get("label", "neutral"),
            "score": sentiment.get("score", 0.0),
            "confidence": abs(sentiment.get("score", 0.0))
        }
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze sentiment: {str(e)}")

# Enhanced AI Endpoints

@router.get("/enhanced/status")
async def get_enhanced_ai_status():
    """Get enhanced AI service status with ML model information"""
    try:
        status = enhanced_ai_service.get_enhanced_status()
        return status
    except Exception as e:
        logger.error(f"Error getting enhanced AI status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get enhanced AI service status")

@router.post("/enhanced/analyze-text")
async def enhanced_analyze_text(request: TextAnalysisRequest):
    """Enhanced text analysis with ML predictions"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        analysis = await enhanced_ai_service.enhanced_analyze_text(request.text)
        return analysis
    except Exception as e:
        logger.error(f"Error in enhanced text analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced analysis failed: {str(e)}")

@router.post("/enhanced/categorize-file")
async def enhanced_categorize_file(request: FileCategorizeRequest):
    """Enhanced file categorization with ML and metadata analysis"""
    try:
        if not request.filename.strip():
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        result = await enhanced_ai_service.smart_categorize_file(
            filename=request.filename,
            content_preview=request.content_preview or ""
        )
        return result
    except Exception as e:
        logger.error(f"Error in enhanced file categorization: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced categorization failed: {str(e)}")

class SimilarityRequest(BaseModel):
    target_text: str
    file_database: List[Dict[str, Any]]
    limit: Optional[int] = 5

@router.post("/find-similar")
async def find_similar_files(request: SimilarityRequest):
    """Find files similar to the target text"""
    try:
        if not request.target_text.strip():
            raise HTTPException(status_code=400, detail="Target text cannot be empty")
        
        similar_files = await enhanced_ai_service.find_similar_files(
            target_text=request.target_text,
            file_database=request.file_database,
            limit=request.limit
        )
        return {"similar_files": similar_files}
    except Exception as e:
        logger.error(f"Error finding similar files: {e}")
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")

class OrganizationRequest(BaseModel):
    files: List[Dict[str, Any]]

@router.post("/suggest-organization")
async def suggest_workspace_organization(request: OrganizationRequest):
    """Suggest workspace organization based on file clustering"""
    try:
        if not request.files:
            raise HTTPException(status_code=400, detail="File list cannot be empty")
        
        organization = await enhanced_ai_service.suggest_workspace_organization(request.files)
        return organization
    except Exception as e:
        logger.error(f"Error suggesting organization: {e}")
        raise HTTPException(status_code=500, detail=f"Organization suggestion failed: {str(e)}")

class LearningRequest(BaseModel):
    text: str
    user_category: str
    user_priority: str

@router.post("/learn")
async def learn_from_user_actions(request: LearningRequest):
    """Learn from user corrections to improve AI accuracy"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        await enhanced_ai_service.learn_from_user_actions(
            text=request.text,
            user_category=request.user_category,
            user_priority=request.user_priority
        )
        return {"message": "Learning data recorded successfully"}
    except Exception as e:
        logger.error(f"Error in learning: {e}")
        raise HTTPException(status_code=500, detail=f"Learning failed: {str(e)}")

# File Scanner Endpoints

class ScanRequest(BaseModel):
    directory_path: str
    user_id: int
    recursive: Optional[bool] = True

# @router.post("/scan-directory")
# async def scan_directory(request: ScanRequest):
#     """Scan directory and automatically categorize files"""
#     try:
#         if not request.directory_path.strip():
#             raise HTTPException(status_code=400, detail="Directory path cannot be empty")
#         
#         if file_scanner.scanning:
#             raise HTTPException(status_code=409, detail="Scanner is already running")
#         
#         result = await file_scanner.scan_directory(
#             directory_path=request.directory_path,
#             user_id=request.user_id,
#             recursive=request.recursive
#         )
#         return result
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logger.error(f"Error scanning directory: {e}")
#         raise HTTPException(status_code=500, detail=f"Directory scan failed: {str(e)}")

# @router.get("/scan-status")
# async def get_scan_status():
#     """Get current file scan status"""
#     try:
#         status = file_scanner.get_scan_status()
#         return status
#     except Exception as e:
#         logger.error(f"Error getting scan status: {e}")
#         raise HTTPException(status_code=500, detail="Failed to get scan status")

class QuickScanRequest(BaseModel):
    user_id: int
    since_hours: Optional[int] = 24

# @router.post("/quick-scan")
# async def quick_scan_updates(request: QuickScanRequest):
#     """Quick scan for recently modified files"""
#     try:
#         result = await file_scanner.quick_scan_updates(
#             user_id=request.user_id,
#             since_hours=request.since_hours
#         )
#         return result
#     except Exception as e:
#         logger.error(f"Error in quick scan: {e}")
#         raise HTTPException(status_code=500, detail=f"Quick scan failed: {str(e)}")

class CleanupRequest(BaseModel):
    user_id: int

# @router.post("/cleanup-missing")
# async def cleanup_missing_files(request: CleanupRequest):
#     """Remove database entries for files that no longer exist"""
#     try:
#         result = await file_scanner.cleanup_missing_files(request.user_id)
#         return result
#     except Exception as e:
#         logger.error(f"Error in cleanup: {e}")
#         raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Workspace Suggestion Endpoints

class WorkspaceSuggestionRequest(BaseModel):
    task_title: str
    task_description: str
    existing_workspaces: Optional[List[Dict[str, Any]]] = []

class WorkspaceSuggestionResponse(BaseModel):
    suggestions: List[Dict[str, Any]]
    reasoning: str

@router.post("/suggest-workspaces", response_model=WorkspaceSuggestionResponse)
async def suggest_workspaces(request: WorkspaceSuggestionRequest):
    """
    Generate AI-powered workspace suggestions based on task content
    """
    try:
        if not request.task_title.strip():
            raise HTTPException(status_code=400, detail="Task title cannot be empty")
        
        # Combine task title and description for analysis
        full_text = f"{request.task_title}. {request.task_description or ''}"
        
        # Analyze the task content
        analysis = await ai_service.analyze_text(full_text)
        
        # Extract keywords and category for workspace suggestions
        keywords = analysis.get("keywords", [])
        category = analysis.get("category", "general")
        
        # Generate workspace suggestions based on analysis
        suggestions = []
        
        # Technology-based suggestions
        tech_keywords = ["python", "javascript", "react", "api", "database", "frontend", "backend", "docker", "ci/cd"]
        found_tech = [kw for kw in keywords if any(tech in kw.lower() for tech in tech_keywords)]
        
        if found_tech:
            suggestions.append({
                "name": f"{category.title()} Development",
                "description": f"Workspace for {', '.join(found_tech[:3])} development tasks",
                "color": "#3b82f6",
                "theme": "modern_light",
                "icon": "💻",
                "reasoning": f"Detected technology keywords: {', '.join(found_tech[:3])}"
            })
        
        # Project-based suggestions
        if "project" in request.task_title.lower() or "feature" in request.task_title.lower():
            suggestions.append({
                "name": f"{request.task_title.split()[0]} Project",
                "description": f"Dedicated workspace for {request.task_title.lower()} related tasks",
                "color": "#10b981",
                "theme": "modern_light",
                "icon": "🚀",
                "reasoning": "Detected project-oriented task structure"
            })
        
        # Domain-specific suggestions based on category
        category_map = {
            "development": {"name": "Development Hub", "icon": "⚡", "color": "#8b5cf6"},
            "documentation": {"name": "Documentation Center", "icon": "📚", "color": "#f59e0b"},
            "testing": {"name": "Quality Assurance", "icon": "🧪", "color": "#ef4444"},
            "design": {"name": "Design Studio", "icon": "🎨", "color": "#ec4899"},
            "planning": {"name": "Strategy & Planning", "icon": "📋", "color": "#6366f1"}
        }
        
        if category in category_map:
            cat_info = category_map[category]
            suggestions.append({
                "name": cat_info["name"],
                "description": f"Centralized workspace for all {category} activities",
                "color": cat_info["color"],
                "theme": "modern_light",
                "icon": cat_info["icon"],
                "reasoning": f"Task categorized as {category}-related"
            })
        
        # Generic fallback suggestion
        if not suggestions:
            suggestions.append({
                "name": "General Tasks",
                "description": "Multi-purpose workspace for various tasks",
                "color": "#6b7280",
                "theme": "modern_light",
                "icon": "📁",
                "reasoning": "Default workspace for general task management"
            })
        
        # Limit to top 3 suggestions
        suggestions = suggestions[:3]
        
        reasoning = f"Generated {len(suggestions)} workspace suggestions based on task content analysis. "
        reasoning += f"Key factors: category ({category}), keywords ({', '.join(keywords[:3])})"
        
        return WorkspaceSuggestionResponse(
            suggestions=suggestions,
            reasoning=reasoning
        )
        
    except Exception as e:
        logger.error(f"Error suggesting workspaces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to suggest workspaces: {str(e)}")