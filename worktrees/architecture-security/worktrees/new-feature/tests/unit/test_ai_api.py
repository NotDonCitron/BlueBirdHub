"""
Test cases for AI API endpoints
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.backend.main import app

client = TestClient(app)

class TestAIAPI:
    """Test AI API endpoints"""
    
    def test_ai_status_endpoint(self):
        """Test AI status endpoint"""
        response = client.get("/ai/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data['service'] == 'LocalAIService'
        assert data['status'] == 'operational'
        assert 'capabilities' in data
        assert 'text_analysis' in data['capabilities']

    def test_analyze_text_endpoint(self):
        """Test text analysis endpoint"""
        test_data = {
            "text": "This is an urgent work task that needs immediate attention"
        }
        
        response = client.post("/ai/analyze-text", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 'priority' in data
        assert 'category' in data
        assert 'sentiment' in data
        assert 'keywords' in data
        assert data['word_count'] > 0

    def test_analyze_text_empty(self):
        """Test text analysis with empty text"""
        test_data = {"text": ""}
        
        response = client.post("/ai/analyze-text", json=test_data)
        assert response.status_code == 400

    def test_suggest_tags_endpoint(self):
        """Test tag suggestion endpoint"""
        test_data = {
            "text": "Urgent meeting with client about important project deadline"
        }
        
        response = client.post("/ai/suggest-tags", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 'tags' in data
        assert isinstance(data['tags'], list)

    def test_categorize_file_endpoint(self):
        """Test file categorization endpoint"""
        test_data = {
            "filename": "important_document.pdf",
            "content_preview": "This is a work-related business document"
        }
        
        response = client.post("/ai/categorize-file", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 'category' in data
        assert 'subcategory' in data
        assert 'tags' in data
        assert data['category'] == 'document'

    def test_suggest_priority_endpoint(self):
        """Test priority suggestion endpoint"""
        test_data = {
            "text": "This is an urgent task that needs immediate attention"
        }
        
        response = client.post("/ai/suggest-priority", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 'priority' in data
        assert 'reasoning' in data
        assert 'confidence' in data
        assert data['priority'] in ['low', 'medium', 'high', 'urgent']

    def test_extract_entities_endpoint(self):
        """Test entity extraction endpoint"""
        test_data = {
            "text": "Contact John at john@example.com or call +1-555-123-4567"
        }
        
        response = client.post("/ai/extract-entities", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 'entities' in data
        assert 'count' in data
        assert 'emails' in data['entities']

    def test_analyze_sentiment_endpoint(self):
        """Test sentiment analysis endpoint"""
        test_data = {
            "text": "I love this amazing project and I'm very excited about it"
        }
        
        response = client.post("/ai/analyze-sentiment", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 'sentiment' in data
        assert 'score' in data
        assert 'confidence' in data
        assert data['sentiment'] in ['positive', 'negative', 'neutral']

    def test_invalid_request_format(self):
        """Test invalid request format handling"""
        # Missing required fields
        response = client.post("/ai/analyze-text", json={})
        assert response.status_code == 422  # Unprocessable Entity

    def test_file_categorization_image(self):
        """Test image file categorization"""
        test_data = {
            "filename": "vacation_photo.jpg",
            "content_preview": ""
        }
        
        response = client.post("/ai/categorize-file", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data['category'] == 'image'

    def test_file_categorization_code(self):
        """Test code file categorization"""
        test_data = {
            "filename": "main.py",
            "content_preview": "import os\nprint('Hello World')"
        }
        
        response = client.post("/ai/categorize-file", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data['category'] == 'code'