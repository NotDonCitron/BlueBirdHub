"""
Lightweight Local AI Service for OrdnungsHub
Provides basic text processing capabilities without heavy dependencies
"""

import re
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from loguru import logger

class LocalAIService:
    """
    Lightweight AI service for text processing and analysis
    Uses rule-based methods and simple algorithms for privacy-focused processing
    """
    
    def __init__(self):
        # Scale thread pool based on CPU cores
        cpu_count = os.cpu_count() or 1
        # Use 2x CPU cores for I/O bound tasks, with min 2, max 8
        max_workers = min(max(cpu_count * 2, 2), 8)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._initialize_patterns()
        logger.info(f"AI Service initialized with {max_workers} thread pool workers ({cpu_count} CPU cores detected)")
        
    def _initialize_patterns(self):
        """Initialize regex patterns for text analysis"""
        # Email pattern
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Phone pattern - improved to match more formats
        self.phone_pattern = re.compile(r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}')
        
        # URL pattern - improved to not capture trailing punctuation
        self.url_pattern = re.compile(r'https?://(?:[a-zA-Z0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+(?:/[a-zA-Z0-9-._~:/?#[\]@!$&\'()*+,;=]*)?')
        
        # Priority keywords
        self.priority_keywords = {
            'urgent': ['urgent', 'asap', 'immediately', 'critical', 'emergency'],
            'high': ['important', 'high', 'priority', 'deadline', 'due'],
            'medium': ['normal', 'regular', 'standard'],
            'low': ['low', 'later', 'whenever', 'optional']
        }
        
        # Category keywords
        self.category_keywords = {
            'work': ['work', 'job', 'office', 'meeting', 'project', 'business', 'client'],
            'personal': ['personal', 'family', 'home', 'hobby', 'health', 'doctor'],
            'finance': ['money', 'bank', 'payment', 'bill', 'finance', 'budget', 'tax'],
            'shopping': ['buy', 'purchase', 'shop', 'store', 'order', 'delivery'],
            'travel': ['travel', 'trip', 'flight', 'hotel', 'vacation', 'visit'],
            'education': ['learn', 'study', 'course', 'school', 'university', 'book']
        }

    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text and extract insights
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        loop = asyncio.get_event_loop()
        
        # Run analysis in thread pool to avoid blocking
        result = await loop.run_in_executor(
            self.executor, 
            self._analyze_text_sync, 
            text
        )
        
        return result
    
    def _analyze_text_sync(self, text: str) -> Dict[str, Any]:
        """Synchronous text analysis"""
        if not text or not text.strip():
            return {}
            
        text_lower = text.lower()
        
        return {
            'entities': self._extract_entities(text),
            'sentiment': self._analyze_sentiment(text_lower),
            'priority': self._suggest_priority(text_lower),
            'category': self._suggest_category(text_lower),
            'keywords': self._extract_keywords(text_lower),
            'word_count': len(text.split()),
            'character_count': len(text),
            'language': 'en'  # Default to English
        }
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities like emails, phones, URLs"""
        entities = {
            'emails': self.email_pattern.findall(text),
            'phones': self.phone_pattern.findall(text),
            'urls': self.url_pattern.findall(text)
        }
        
        # Clean up phone numbers
        entities['phones'] = [phone.strip() for phone in entities['phones'] if phone.strip()]
        
        # Clean up URLs - remove trailing punctuation
        cleaned_urls = []
        for url in entities['urls']:
            # Remove trailing punctuation
            while url and url[-1] in '!?.,;:':
                url = url[:-1]
            if url:
                cleaned_urls.append(url)
        entities['urls'] = cleaned_urls
        
        return entities
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Simple rule-based sentiment analysis"""
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'enjoy', 'happy', 'excited', 'perfect'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike',
            'sad', 'angry', 'frustrated', 'disappointed', 'problem', 'issue'
        ]
        
        words = text.split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            return {'score': 0.0, 'label': 'neutral'}
        
        score = (positive_count - negative_count) / total_sentiment_words
        
        if score > 0.1:
            label = 'positive'
        elif score < -0.1:
            label = 'negative'
        else:
            label = 'neutral'
            
        return {'score': score, 'label': label}
    
    def _suggest_priority(self, text: str) -> str:
        """Suggest task priority based on keywords"""
        for priority, keywords in self.priority_keywords.items():
            if any(keyword in text for keyword in keywords):
                return priority
        return 'medium'  # Default priority
    
    def _suggest_category(self, text: str) -> str:
        """Suggest category based on keywords"""
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return 'general'  # Default category
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction - remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
            'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Extract words that are longer than 3 characters and not stop words
        words = re.findall(r'\b\w{4,}\b', text.lower())
        keywords = [word for word in words if word not in stop_words]
        
        # Return unique keywords, limited to top 10
        return list(dict.fromkeys(keywords))[:10]

    async def suggest_tags(self, text: str) -> List[str]:
        """Suggest tags for content based on analysis"""
        analysis = await self.analyze_text(text)
        
        tags = []
        
        # Add category as tag
        if analysis.get('category') != 'general':
            tags.append(analysis['category'])
        
        # Add priority as tag if not medium
        if analysis.get('priority') != 'medium':
            tags.append(f"priority-{analysis['priority']}")
        
        # Add sentiment as tag if not neutral
        sentiment = analysis.get('sentiment', {})
        if sentiment.get('label') != 'neutral':
            tags.append(f"sentiment-{sentiment['label']}")
        
        # Add top keywords as tags
        keywords = analysis.get('keywords', [])[:3]
        tags.extend(keywords)
        
        return tags

    async def categorize_file(self, filename: str, content_preview: str = "") -> Dict[str, Any]:
        """Categorize file based on name and content"""
        result = {
            'category': 'document',
            'subcategory': 'general',
            'tags': [],
            'priority': 'medium'
        }
        
        filename_lower = filename.lower()
        
        # File type based categorization
        if any(ext in filename_lower for ext in ['.jpg', '.png', '.gif', '.svg', '.bmp']):
            result['category'] = 'image'
        elif any(ext in filename_lower for ext in ['.mp4', '.avi', '.mov', '.wmv']):
            result['category'] = 'video'
        elif any(ext in filename_lower for ext in ['.mp3', '.wav', '.flac', '.aac']):
            result['category'] = 'audio'
        elif any(ext in filename_lower for ext in ['.pdf', '.doc', '.docx', '.txt']):
            result['category'] = 'document'
        elif any(ext in filename_lower for ext in ['.zip', '.rar', '.7z', '.tar']):
            result['category'] = 'archive'
        elif any(ext in filename_lower for ext in ['.py', '.js', '.html', '.css', '.cpp']):
            result['category'] = 'code'
        
        # Content-based analysis if available
        if content_preview:
            analysis = await self.analyze_text(content_preview)
            result['subcategory'] = analysis.get('category', 'general')
            result['tags'] = await self.suggest_tags(content_preview)
            result['priority'] = analysis.get('priority', 'medium')
        
        return result

    async def generate_suggestions(self, task_description: str) -> List[str]:
        """Generate task suggestions based on description"""
        if not task_description or not task_description.strip():
            return []
        
        # Analyze the task description
        analysis = await self.analyze_text(task_description)
        
        suggestions = []
        
        # Add category-based suggestions
        category = analysis.get('category', 'general')
        if category == 'work':
            suggestions.extend([
                "Schedule a meeting to discuss requirements",
                "Create a project timeline",
                "Assign team members to specific tasks",
                "Set up progress tracking system"
            ])
        elif category == 'personal':
            suggestions.extend([
                "Set a reminder for this task",
                "Break down into smaller steps",
                "Schedule time in calendar",
                "Prepare necessary materials"
            ])
        elif category == 'finance':
            suggestions.extend([
                "Review budget constraints",
                "Compare different options",
                "Consult with financial advisor",
                "Keep receipts and documentation"
            ])
        else:
            suggestions.extend([
                "Research best practices",
                "Create a checklist",
                "Set realistic deadlines",
                "Identify potential obstacles"
            ])
        
        # Add priority-based suggestions
        priority = analysis.get('priority', 'medium')
        if priority == 'urgent' or priority == 'high':
            suggestions.extend([
                "Start immediately",
                "Allocate dedicated time",
                "Minimize distractions"
            ])
        elif priority == 'low':
            suggestions.extend([
                "Schedule for later",
                "Consider delegating",
                "Combine with similar tasks"
            ])
        
        # Add keyword-based suggestions
        keywords = analysis.get('keywords', [])
        if any(word in keywords for word in ['meeting', 'call', 'contact']):
            suggestions.append("Prepare agenda and talking points")
        if any(word in keywords for word in ['document', 'report', 'write']):
            suggestions.append("Create outline before writing")
        if any(word in keywords for word in ['buy', 'purchase', 'order']):
            suggestions.append("Compare prices and reviews")
        
        # Return unique suggestions, limited to 8
        return list(dict.fromkeys(suggestions))[:8]

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'service': 'LocalAIService',
            'status': 'operational',
            'thread_pool_workers': self.executor._max_workers,
            'cpu_cores': os.cpu_count(),
            'capabilities': [
                'text_analysis',
                'entity_extraction', 
                'sentiment_analysis',
                'priority_suggestion',
                'category_suggestion',
                'keyword_extraction',
                'tag_suggestion',
                'file_categorization',
                'task_suggestions'
            ],
            'models': 'rule-based',
            'privacy': 'fully_local',
            'performance': 'optimized_for_cpu_cores'
        }

# Global service instance
ai_service = LocalAIService()