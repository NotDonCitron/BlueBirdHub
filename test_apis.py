#!/usr/bin/env python3
"""
Test-Script für alle API-Integrationen
Führe aus mit: python test_apis.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.api_integrations import api_manager

def test_all_apis():
    print("🔧 OrdnungsHub API Test Suite")
    print("=" * 50)
    
    # 1. Check API Keys
    print("\n📋 API Keys Status:")
    for key, value in api_manager.keys.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: {'Loaded' if value else 'Missing'}")
    
    # 2. Test Cohere
    if api_manager.keys['cohere']:
        print("\n🧠 Testing Cohere Summarization...")
        test_text = """
        OrdnungsHub ist eine KI-gestützte Desktop-Anwendung, die Nutzern hilft, 
        ihren digitalen Arbeitsbereich effizient zu organisieren. Die App kombiniert 
        lokale KI-Verarbeitung mit intelligenten Dateiverwaltungs- und 
        Systemoptimierungstools. Mit Features wie automatischer Kategorisierung, 
        Duplikat-Erkennung und Smart Search macht OrdnungsHub Ordnung halten einfach.
        """
        result = api_manager.summarize_with_cohere(test_text, 'short')
        if result['success']:
            print("  ✅ Summary:", result['summary'])
        else:
            print("  ❌ Error:", result['error'])
    
    # 3. Test Hugging Face
    if api_manager.keys['huggingface']:
        print("\n🤖 Testing Hugging Face Classification...")
        test_doc = "Hiermit kündige ich meinen Vertrag zum nächstmöglichen Zeitpunkt."
        result = api_manager.classify_document(test_doc)
        if 'labels' in result:
            print("  ✅ Classification:", result['labels'][0])
            print("  📊 Confidence:", f"{result['scores'][0]:.2%}")
        else:
            print("  ❌ Error:", result.get('error', 'Unknown error'))
    
    # 4. Test Brave Search
    if api_manager.keys['brave_search']:
        print("\n🔍 Testing Brave Search...")
        result = api_manager.search_web("Python file organization tools")
        if 'web' in result and 'results' in result['web']:
            print(f"  ✅ Found {len(result['web']['results'])} results")
            if result['web']['results']:
                print(f"  📌 Top result: {result['web']['results'][0]['title']}")
        else:
            print("  ❌ Error:", result.get('error', 'No results'))
    
    # 5. Test OpenWeather
    if api_manager.keys['openweather']:
        print("\n☀️ Testing OpenWeather...")
        result = api_manager.get_weather("Berlin")
        if 'main' in result:
            print(f"  ✅ Weather in Berlin: {result['weather'][0]['description']}")
            print(f"  🌡️ Temperature: {result['main']['temp']}°C")
        else:
            print("  ❌ Error:", result.get('message', 'Unknown error'))
    
    print("\n" + "=" * 50)
    print("✨ Test Suite Complete!")

if __name__ == "__main__":
    test_all_apis()
