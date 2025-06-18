# api_integrations.py
# Einfache API-Integrationen für OrdnungsHub

import os
import json
import requests
from dotenv import load_dotenv

# Lade Environment Variables
load_dotenv()

class APIManager:
    """Verwaltet alle API-Integrationen"""
    
    def __init__(self):
        self.keys = {
            'cohere': os.getenv('COHERE_API_KEY'),
            'huggingface': os.getenv('HUGGINGFACE_API_KEY'),
            'tinypng': os.getenv('TINYPNG_API_KEY'),
            'openweather': os.getenv('OPENWEATHER_API_KEY'),
            'brave_search': os.getenv('BRAVE_SEARCH_API_KEY')
        }
    
    def summarize_with_cohere(self, text, length='medium'):
        """Text-Zusammenfassung mit Cohere"""
        try:
            import cohere
            co = cohere.Client(self.keys['cohere'])
            response = co.summarize(
                text=text,
                length=length,
                format='bullets'
            )
            return {'success': True, 'summary': response.summary}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def classify_document(self, text):
        """Dokument-Klassifizierung mit Hugging Face"""
        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {self.keys['huggingface']}"}
        
        payload = {
            "inputs": text,
            "parameters": {
                "candidate_labels": [
                    "Rechnung", "Vertrag", "Brief", 
                    "Bericht", "Notiz", "Anleitung"
                ]
            }
        }
        
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def search_web(self, query):
        """Web-Suche mit Brave Search API"""
        headers = {
            "X-Subscription-Token": self.keys['brave_search']
        }
        
        params = {
            "q": query,
            "count": 5
        }
        
        try:
            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params
            )
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_weather(self, city):
        """Wetter-Info mit OpenWeather"""
        params = {
            "q": city,
            "appid": self.keys['openweather'],
            "units": "metric",
            "lang": "de"
        }
        
        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params=params
            )
            return response.json()
        except Exception as e:
            return {'error': str(e)}

# Globale Instanz
api_manager = APIManager()

# Test-Funktion
if __name__ == "__main__":
    # Teste ob Keys geladen wurden
    print("Geladene API Keys:")
    for key, value in api_manager.keys.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {'Geladen' if value else 'Fehlt'}")
