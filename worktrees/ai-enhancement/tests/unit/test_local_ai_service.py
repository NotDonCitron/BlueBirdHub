import pytest
import asyncio
from src.backend.services.ai_service import LocalAIService

@pytest.fixture
def ai_service():
    """Create AI service instance for testing."""
    return LocalAIService()

class TestLocalAIService:
    """Test cases for LocalAIService."""
    
    @pytest.mark.asyncio
    async def test_analyze_text_basic(self, ai_service):
        """Test basic text analysis."""
        text = "This is an urgent email to john@example.com about the meeting tomorrow."
        result = await ai_service.analyze_text(text)
        
        assert 'entities' in result
        assert 'sentiment' in result
        assert 'priority' in result
        assert 'category' in result
        assert 'keywords' in result
        
        # Check entity extraction
        assert 'john@example.com' in result['entities']['emails']
        
        # Check priority detection
        assert result['priority'] == 'urgent'
        
        # Check word count
        assert result['word_count'] == 11
    
    @pytest.mark.asyncio
    async def test_analyze_text_empty(self, ai_service):
        """Test analysis with empty text."""
        result = await ai_service.analyze_text("")
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_extract_entities(self, ai_service):
        """Test entity extraction."""
        text = """
        Contact me at test@example.com or call +1-555-123-4567.
        Visit our website at https://example.com
        """
        result = await ai_service.analyze_text(text)
        
        entities = result['entities']
        assert 'test@example.com' in entities['emails']
        assert any('+1-555-123-4567' in phone for phone in entities['phones'])
        assert 'https://example.com' in entities['urls']
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, ai_service):
        """Test sentiment analysis."""
        # Positive sentiment
        positive_text = "This is absolutely fantastic! I love it!"
        positive_result = await ai_service.analyze_text(positive_text)
        assert positive_result['sentiment']['label'] == 'positive'
        assert positive_result['sentiment']['score'] > 0
        
        # Negative sentiment
        negative_text = "This is terrible. I hate this awful experience."
        negative_result = await ai_service.analyze_text(negative_text)
        assert negative_result['sentiment']['label'] == 'negative'
        assert negative_result['sentiment']['score'] < 0
        
        # Neutral sentiment
        neutral_text = "The meeting is scheduled for tomorrow at 3 PM."
        neutral_result = await ai_service.analyze_text(neutral_text)
        assert neutral_result['sentiment']['label'] == 'neutral'
    
    @pytest.mark.asyncio
    async def test_priority_suggestion(self, ai_service):
        """Test priority suggestion."""
        # Test urgent priority
        urgent_text = "URGENT: Critical issue needs immediate attention!"
        urgent_result = await ai_service.analyze_text(urgent_text)
        assert urgent_result['priority'] == 'urgent'
        
        # Test high priority
        high_text = "Important deadline approaching for the project."
        high_result = await ai_service.analyze_text(high_text)
        assert high_result['priority'] == 'high'
        
        # Test default priority
        normal_text = "Regular status update for the team."
        normal_result = await ai_service.analyze_text(normal_text)
        assert normal_result['priority'] == 'medium'
    
    @pytest.mark.asyncio
    async def test_category_suggestion(self, ai_service):
        """Test category suggestion."""
        # Work category
        work_text = "Meeting with client about the project proposal."
        work_result = await ai_service.analyze_text(work_text)
        assert work_result['category'] == 'work'
        
        # Finance category
        finance_text = "Need to pay the monthly bills and check bank balance."
        finance_result = await ai_service.analyze_text(finance_text)
        assert finance_result['category'] == 'finance'
        
        # Travel category
        travel_text = "Book flight and hotel for vacation next month."
        travel_result = await ai_service.analyze_text(travel_text)
        assert travel_result['category'] == 'travel'
    
    @pytest.mark.asyncio
    async def test_keyword_extraction(self, ai_service):
        """Test keyword extraction."""
        text = "The artificial intelligence project requires machine learning expertise."
        result = await ai_service.analyze_text(text)
        
        keywords = result['keywords']
        assert 'artificial' in keywords
        assert 'intelligence' in keywords
        assert 'project' in keywords
        assert 'machine' in keywords
        assert 'learning' in keywords
        assert 'expertise' in keywords
        
        # Should not include stop words
        assert 'the' not in keywords
        assert 'is' not in keywords
    
    @pytest.mark.asyncio
    async def test_suggest_tags(self, ai_service):
        """Test tag suggestion."""
        text = "Urgent work meeting about the financial report."
        tags = await ai_service.suggest_tags(text)
        
        assert 'work' in tags
        assert 'priority-urgent' in tags
        assert any('financial' in tag or 'report' in tag or 'meeting' in tag for tag in tags)
    
    @pytest.mark.asyncio
    async def test_categorize_file(self, ai_service):
        """Test file categorization."""
        # Image file
        image_result = await ai_service.categorize_file("vacation_photo.jpg")
        assert image_result['category'] == 'image'
        
        # Document file with content
        doc_result = await ai_service.categorize_file(
            "project_report.pdf",
            "This is the quarterly financial report for the project."
        )
        assert doc_result['category'] == 'document'
        assert doc_result['subcategory'] in ['work', 'finance']
        
        # Code file
        code_result = await ai_service.categorize_file("main.py")
        assert code_result['category'] == 'code'
    
    def test_get_status(self, ai_service):
        """Test service status."""
        status = ai_service.get_status()
        
        assert status['service'] == 'LocalAIService'
        assert status['status'] == 'operational'
        assert 'text_analysis' in status['capabilities']
        assert status['models'] == 'rule-based'
        assert status['privacy'] == 'fully_local'

class TestAIServiceEdgeCases:
    """Test edge cases for AI service."""
    
    @pytest.mark.asyncio
    async def test_long_text_analysis(self, ai_service):
        """Test analysis with very long text."""
        long_text = " ".join(["This is a test sentence."] * 1000)
        result = await ai_service.analyze_text(long_text)
        
        assert result['word_count'] == 5000
        assert result['character_count'] == len(long_text)
    
    @pytest.mark.asyncio
    async def test_special_characters(self, ai_service):
        """Test handling of special characters."""
        text = "Email: test@example.com!!! Phone: +1(555)123-4567??? URL: https://example.com!!!"
        result = await ai_service.analyze_text(text)
        
        assert 'test@example.com' in result['entities']['emails']
        assert any('555' in phone for phone in result['entities']['phones'])
        assert 'https://example.com' in result['entities']['urls']
    
    @pytest.mark.asyncio
    async def test_mixed_case_keywords(self, ai_service):
        """Test keyword detection with mixed case."""
        text = "URGENT Meeting about Important PROJECT deadline"
        result = await ai_service.analyze_text(text)
        
        assert result['priority'] == 'urgent'
        assert result['category'] == 'work'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])