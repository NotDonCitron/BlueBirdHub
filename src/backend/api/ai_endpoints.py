"""
AI API endpoints for OrdnungsHub
Provides AI text analysis, summarization, and content categorization
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

class TextAnalysisRequest(BaseModel):
    text: str
    analysis_type: Optional[str] = "general"

class TextSummarizationRequest(BaseModel):
    text: str
    max_length: Optional[int] = 200
    
class ContentCategorizationRequest(BaseModel):
    text: str
    context: Optional[str] = None

@router.post("/text/analyze")
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze text for various properties like sentiment, topics, entities
    """
    try:
        # Mock AI analysis for now - replace with actual AI service
        analysis = {
            "sentiment": {
                "score": 0.7,
                "label": "positive",
                "confidence": 0.85
            },
            "topics": [
                {"topic": "technology", "confidence": 0.9},
                {"topic": "organization", "confidence": 0.7}
            ],
            "entities": [
                {"text": "file", "type": "object", "confidence": 0.8},
                {"text": "system", "type": "concept", "confidence": 0.9}
            ],
            "language": "en",
            "readability": {
                "score": 7.5,
                "level": "intermediate"
            },
            "key_phrases": [
                "file organization",
                "system management",
                "data processing"
            ]
        }
        
        return {
            "success": True,
            "text": request.text,
            "analysis_type": request.analysis_type,
            "analysis": analysis,
            "processing_time": "0.45s"
        }
        
    except Exception as e:
        logger.error(f"Text analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/text/summarize")
async def summarize_text(request: TextSummarizationRequest):
    """
    Generate a summary of the provided text
    """
    try:
        # Mock summarization - replace with actual AI service
        summary = "This text discusses file organization and system management, focusing on efficient data processing and workspace optimization."
        
        # Truncate to max_length if specified
        if request.max_length and len(summary) > request.max_length:
            summary = summary[:request.max_length-3] + "..."
        
        return {
            "success": True,
            "original_text": request.text,
            "summary": summary,
            "compression_ratio": round(len(summary) / len(request.text), 2),
            "original_length": len(request.text),
            "summary_length": len(summary),
            "processing_time": "0.62s"
        }
        
    except Exception as e:
        logger.error(f"Text summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@router.post("/content/categorize")
async def categorize_content(request: ContentCategorizationRequest):
    """
    Categorize content into predefined categories
    """
    try:
        # Mock categorization - replace with actual AI service
        # Analyze text content to determine category
        text_lower = request.text.lower()
        
        categories = []
        confidence_scores = {}
        
        # Simple keyword-based categorization for demo
        if any(word in text_lower for word in ["document", "pdf", "report", "paper"]):
            categories.append("Documents")
            confidence_scores["Documents"] = 0.9
            
        if any(word in text_lower for word in ["image", "photo", "picture", "visual"]):
            categories.append("Images")
            confidence_scores["Images"] = 0.85
            
        if any(word in text_lower for word in ["project", "task", "work", "development"]):
            categories.append("Projects")
            confidence_scores["Projects"] = 0.8
            
        if any(word in text_lower for word in ["video", "audio", "media", "music"]):
            categories.append("Media")
            confidence_scores["Media"] = 0.75
            
        if any(word in text_lower for word in ["data", "database", "csv", "json"]):
            categories.append("Data")
            confidence_scores["Data"] = 0.9
            
        # Default category if nothing matches
        if not categories:
            categories = ["General"]
            confidence_scores["General"] = 0.6
        
        # Get primary category (highest confidence)
        primary_category = max(confidence_scores.items(), key=lambda x: x[1])
        
        return {
            "success": True,
            "text": request.text,
            "context": request.context,
            "primary_category": {
                "name": primary_category[0],
                "confidence": primary_category[1]
            },
            "all_categories": [
                {
                    "name": cat,
                    "confidence": confidence_scores[cat]
                } for cat in categories
            ],
            "tags": [
                "ai-categorized",
                "auto-generated",
                primary_category[0].lower()
            ],
            "processing_time": "0.23s"
        }
        
    except Exception as e:
        logger.error(f"Content categorization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Categorization failed: {str(e)}")

@router.get("/models/status")
async def get_ai_models_status():
    """
    Get the status of available AI models and services
    """
    try:
        return {
            "success": True,
            "models": {
                "text_analysis": {
                    "name": "mock-analyzer-v1",
                    "status": "available",
                    "version": "1.0.0",
                    "capabilities": ["sentiment", "topics", "entities", "language_detection"]
                },
                "text_summarization": {
                    "name": "mock-summarizer-v1", 
                    "status": "available",
                    "version": "1.0.0",
                    "capabilities": ["extractive", "abstractive", "multi_language"]
                },
                "content_categorization": {
                    "name": "mock-categorizer-v1",
                    "status": "available", 
                    "version": "1.0.0",
                    "capabilities": ["file_types", "content_analysis", "auto_tagging"]
                }
            },
            "overall_status": "healthy",
            "last_updated": "2025-06-28T02:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"AI models status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/capabilities")
async def get_ai_capabilities():
    """
    Get a list of all available AI capabilities and endpoints
    """
    try:
        return {
            "success": True,
            "capabilities": {
                "text_processing": {
                    "endpoints": [
                        "/ai/text/analyze",
                        "/ai/text/summarize"
                    ],
                    "description": "Text analysis and summarization services"
                },
                "content_management": {
                    "endpoints": [
                        "/ai/content/categorize"
                    ],
                    "description": "Automatic content categorization and tagging"
                },
                "system": {
                    "endpoints": [
                        "/ai/models/status",
                        "/ai/capabilities"
                    ],
                    "description": "AI system status and capability information"
                }
            },
            "total_endpoints": 5,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"AI capabilities check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Capabilities check failed: {str(e)}") 