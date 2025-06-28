"""
Gemini AI Service for BlueBirdHub
Provides AI-powered file analysis, content categorization, and smart organization
"""

import os
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from loguru import logger
from pathlib import Path
import mimetypes
import hashlib

class GeminiAIService:
    """AI service using Google's Gemini API for file analysis and content understanding"""
    
    def __init__(self, api_key: str = "AIzaSyC6x1AXciljkMov3F1P7LRcdMdZTRe5Tt4"):
        self.api_key = api_key
        self.model = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Gemini client"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI service: {e}")
            self.model = None
    
    async def analyze_file_content(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Analyze file content and extract meaningful insights
        """
        try:
            if not self.model:
                return self._get_fallback_analysis(file_path, file_type)
            
            # Read file content based on type
            content = await self._extract_file_content(file_path, file_type)
            if not content:
                return self._get_fallback_analysis(file_path, file_type)
            
            # Prepare analysis prompt
            prompt = f"""
            Analyze this file content and provide structured insights:
            
            File Type: {file_type}
            Content: {content[:4000]}  # Limit content to avoid token limits
            
            Please provide:
            1. A brief summary (2-3 sentences)
            2. Key topics/themes (up to 5)
            3. Suggested category (choose from: Documents, Images, Code, Data, Media, Archives, Other)
            4. Important keywords/tags (up to 8)
            5. Complexity level (Basic, Intermediate, Advanced)
            6. Suggested workspace type (Development, Design, Business, Personal, Research)
            
            Format your response as JSON with these fields:
            {{
                "summary": "...",
                "topics": ["...", "..."],
                "category": "...",
                "tags": ["...", "..."],
                "complexity": "...",
                "suggested_workspace": "...",
                "confidence": 0.85
            }}
            """
            
            # Generate AI analysis
            response = self.model.generate_content(prompt)
            
            # Parse response
            import json
            try:
                analysis = json.loads(response.text)
                analysis["ai_generated"] = True
                analysis["model"] = "gemini-pro"
                return analysis
            except json.JSONDecodeError:
                # Fallback to text parsing if JSON fails
                return self._parse_text_response(response.text, file_type)
                
        except Exception as e:
            logger.error(f"Error analyzing file with Gemini AI: {e}")
            return self._get_fallback_analysis(file_path, file_type)
    
    async def generate_smart_tags(self, content: str, context: Optional[str] = None) -> List[str]:
        """
        Generate intelligent tags based on content
        """
        try:
            if not self.model:
                return self._get_fallback_tags(content)
            
            prompt = f"""
            Generate relevant, specific tags for this content:
            
            Content: {content[:2000]}
            Context: {context or "General file"}
            
            Rules:
            - Maximum 8 tags
            - Use specific, descriptive terms
            - Include technical terms when relevant
            - Focus on searchable keywords
            - Avoid generic terms
            
            Return only a comma-separated list of tags.
            """
            
            response = self.model.generate_content(prompt)
            tags = [tag.strip() for tag in response.text.split(',')]
            return tags[:8]  # Limit to 8 tags
            
        except Exception as e:
            logger.error(f"Error generating tags with Gemini AI: {e}")
            return self._get_fallback_tags(content)
    
    async def suggest_workspace_assignment(self, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest optimal workspace based on file characteristics
        """
        try:
            if not self.model:
                return self._get_fallback_workspace_suggestion(file_metadata)
            
            prompt = f"""
            Suggest the best workspace for this file:
            
            File Name: {file_metadata.get('name', 'Unknown')}
            File Type: {file_metadata.get('file_type', 'Unknown')}
            Category: {file_metadata.get('category', 'Unknown')}
            Tags: {', '.join(file_metadata.get('tags', []))}
            
            Available workspace types:
            - Development (code, technical docs, APIs)
            - Design (graphics, mockups, assets)
            - Business (documents, presentations, reports)
            - Personal (personal files, notes)
            - Research (papers, studies, data)
            
            Provide:
            1. Primary workspace recommendation
            2. Confidence level (0-1)
            3. Reasoning (brief)
            4. Alternative workspace if applicable
            
            Format as JSON:
            {{
                "primary_workspace": "...",
                "confidence": 0.85,
                "reasoning": "...",
                "alternative": "..."
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            import json
            try:
                suggestion = json.loads(response.text)
                return suggestion
            except json.JSONDecodeError:
                return self._get_fallback_workspace_suggestion(file_metadata)
                
        except Exception as e:
            logger.error(f"Error suggesting workspace with Gemini AI: {e}")
            return self._get_fallback_workspace_suggestion(file_metadata)
    
    async def _extract_file_content(self, file_path: str, file_type: str) -> str:
        """Extract text content from various file types"""
        try:
            path = Path(file_path)
            if not path.exists():
                return ""
            
            # Text files
            if file_type.startswith('text/') or file_type in ['application/json', 'application/xml']:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            # Code files
            code_extensions = {'.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.go', '.rs', '.php'}
            if path.suffix.lower() in code_extensions:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            # For other files, return basic metadata
            return f"File: {path.name}, Size: {path.stat().st_size} bytes, Type: {file_type}"
            
        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {e}")
            return ""
    
    def _get_fallback_analysis(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Provide basic analysis when AI is unavailable"""
        path = Path(file_path)
        
        # Basic categorization based on file type
        category_map = {
            'image/': 'Images',
            'video/': 'Media',
            'audio/': 'Media',
            'text/': 'Documents',
            'application/pdf': 'Documents',
            'application/msword': 'Documents',
            'application/zip': 'Archives',
            'application/x-zip': 'Archives',
        }
        
        category = 'Other'
        for pattern, cat in category_map.items():
            if file_type.startswith(pattern) or file_type == pattern:
                category = cat
                break
        
        return {
            "summary": f"File: {path.name}",
            "topics": [path.suffix.replace('.', '').upper() if path.suffix else 'FILE'],
            "category": category,
            "tags": [path.suffix.replace('.', '') if path.suffix else 'file', category.lower()],
            "complexity": "Basic",
            "suggested_workspace": "Personal",
            "confidence": 0.5,
            "ai_generated": False,
            "model": "fallback"
        }
    
    def _get_fallback_tags(self, content: str) -> List[str]:
        """Generate basic tags when AI is unavailable"""
        # Simple keyword extraction
        words = content.lower().split()
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        return list(set(keywords[:8]))  # Return unique keywords
    
    def _get_fallback_workspace_suggestion(self, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Provide basic workspace suggestion when AI is unavailable"""
        file_type = file_metadata.get('file_type', '')
        
        if 'image' in file_type or 'design' in file_metadata.get('name', '').lower():
            workspace = 'Design'
        elif any(ext in file_metadata.get('name', '') for ext in ['.py', '.js', '.html', '.css', '.java']):
            workspace = 'Development'
        elif 'pdf' in file_type or 'document' in file_type:
            workspace = 'Business'
        else:
            workspace = 'Personal'
        
        return {
            "primary_workspace": workspace,
            "confidence": 0.6,
            "reasoning": f"Based on file type: {file_type}",
            "alternative": "Personal"
        }
    
    def _parse_text_response(self, response_text: str, file_type: str) -> Dict[str, Any]:
        """Parse AI response when JSON parsing fails"""
        # Basic text parsing fallback
        return {
            "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
            "topics": ["AI Analysis"],
            "category": "Other",
            "tags": ["analyzed"],
            "complexity": "Basic",
            "suggested_workspace": "Personal",
            "confidence": 0.7,
            "ai_generated": True,
            "model": "gemini-pro-text"
        }

# Global service instance
gemini_service = GeminiAIService() 