"""
Test cases for AI Service functionality
"""

import pytest
import asyncio
import sys
import os

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.backend.services.ai_service import ai_service

class TestAIService:
    """Test AI Service functionality"""
    
    def test_service_status(self):
        """Test AI service status"""
        status = ai_service.get_status()
        
        assert status['service'] == 'LocalAIService'
        assert status['status'] == 'operational'
        assert 'text_analysis' in status['capabilities']
        assert status['privacy'] == 'fully_local'

    @pytest.mark.asyncio
    async def test_text_analysis_basic(self):
        """Test basic text analysis"""
        text = "This is an urgent task that needs to be completed immediately for work"
        
        result = await ai_service.analyze_text(text)
        
        assert 'priority' in result
        assert 'category' in result
        assert 'sentiment' in result
        assert 'keywords' in result
        assert result['word_count'] > 0
        assert result['character_count'] > 0

    @pytest.mark.asyncio
    async def test_priority_detection(self):
        """Test priority detection from text"""
        urgent_text = "This is an urgent task that needs immediate attention"
        normal_text = "This is a regular task to be done sometime"
        
        urgent_result = await ai_service.analyze_text(urgent_text)
        normal_result = await ai_service.analyze_text(normal_text)
        
        assert urgent_result['priority'] == 'urgent'
        assert normal_result['priority'] in ['medium', 'low']

    @pytest.mark.asyncio
    async def test_category_detection(self):
        """Test category detection from text"""
        work_text = "Schedule a meeting with the client for the project"
        personal_text = "Visit the doctor for a health checkup"
        
        work_result = await ai_service.analyze_text(work_text)
        personal_result = await ai_service.analyze_text(personal_text)
        
        assert work_result['category'] == 'work'
        assert personal_result['category'] == 'personal'

    @pytest.mark.asyncio
    async def test_entity_extraction(self):
        """Test entity extraction (emails, phones, URLs)"""
        text = "Contact me at john@example.com or call +1-555-123-4567. Check https://example.com"
        
        result = await ai_service.analyze_text(text)
        entities = result['entities']
        
        assert len(entities['emails']) > 0
        assert len(entities['phones']) > 0
        assert len(entities['urls']) > 0
        assert 'john@example.com' in entities['emails']

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self):
        """Test sentiment analysis"""
        positive_text = "I love this amazing project and I'm very excited about it"
        negative_text = "This is terrible and I hate working on this awful task"
        neutral_text = "The task is scheduled for next week"
        
        positive_result = await ai_service.analyze_text(positive_text)
        negative_result = await ai_service.analyze_text(negative_text)
        neutral_result = await ai_service.analyze_text(neutral_text)
        
        assert positive_result['sentiment']['label'] == 'positive'
        assert negative_result['sentiment']['label'] == 'negative'
        assert neutral_result['sentiment']['label'] == 'neutral'

    @pytest.mark.asyncio
    async def test_keyword_extraction(self):
        """Test keyword extraction"""
        text = "Machine learning and artificial intelligence are transforming technology"
        
        result = await ai_service.analyze_text(text)
        keywords = result['keywords']
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Should extract meaningful words, not stop words
        assert 'machine' in keywords or 'learning' in keywords

    @pytest.mark.asyncio
    async def test_tag_suggestion(self):
        """Test tag suggestion"""
        text = "Urgent work meeting with high priority client about important project"
        
        tags = await ai_service.suggest_tags(text)
        
        assert isinstance(tags, list)
        assert len(tags) > 0
        # Should include category and priority tags
        assert any('work' in tag or 'priority' in tag for tag in tags)

    @pytest.mark.asyncio
    async def test_file_categorization(self):
        """Test file categorization"""
        # Test different file types
        image_result = await ai_service.categorize_file("photo.jpg", "")
        code_result = await ai_service.categorize_file("script.py", "")
        doc_result = await ai_service.categorize_file("report.pdf", "Important business document")
        
        assert image_result['category'] == 'image'
        assert code_result['category'] == 'code'
        assert doc_result['category'] == 'document'
        assert doc_result['subcategory'] == 'work'  # Based on content

    @pytest.mark.asyncio
    async def test_empty_text_handling(self):
        """Test handling of empty or invalid text"""
        empty_result = await ai_service.analyze_text("")
        whitespace_result = await ai_service.analyze_text("   ")
        
        assert empty_result == {}
        assert whitespace_result == {}

    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """Test concurrent text processing"""
        texts = [
            "This is urgent work task",
            "Personal doctor appointment",
            "Buy groceries for dinner",
            "Important client meeting"
        ]
        
        # Process multiple texts concurrently
        tasks = [ai_service.analyze_text(text) for text in texts]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 4
        assert all('category' in result for result in results)
        assert all('priority' in result for result in results)