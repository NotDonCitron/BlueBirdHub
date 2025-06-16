from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TextAnalysisRequest(BaseModel):
    """Request model for text analysis."""
    text: str

class TextAnalysisResponse(BaseModel):
    """Response model for text analysis."""
    entities: Dict[str, List[str]]
    sentiment: Dict[str, Any]
    priority: str
    category: str
    keywords: List[str]
    word_count: int
    character_count: int
    language: str

class FileCategorizationRequest(BaseModel):
    """Request model for file categorization."""
    filename: str
    content_preview: Optional[str] = ""

class FileCategorizationResponse(BaseModel):
    """Response model for file categorization."""
    category: str
    subcategory: str
    tags: List[str]
    priority: str

class TaskPriorityRequest(BaseModel):
    """Request model for task priority suggestion."""
    title: str
    description: Optional[str] = ""

class TaskPriorityResponse(BaseModel):
    """Response model for task priority suggestion."""
    priority: str
    reasoning: str
    confidence: float

class TagSuggestionRequest(BaseModel):
    """Request model for tag suggestions."""
    text: str
    
class TagSuggestionResponse(BaseModel):
    """Response model for tag suggestions."""
    tags: List[str]

class EntityExtractionResponse(BaseModel):
    """Response model for entity extraction."""
    entities: Dict[str, List[str]]
    count: int

class SentimentAnalysisResponse(BaseModel):
    """Response model for sentiment analysis."""
    sentiment: str
    score: float
    confidence: float