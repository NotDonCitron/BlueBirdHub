# API Keys Configuration für OrdnungsHub

## ✅ Du hast bereits diese Keys:
- Cohere
- Hugging Face  
- A21 Studio
- Notion API
- JSON API (vermutlich JSONbin.io?)
- OpenWeather

## 🔧 So richtest du sie ein:

### 1. Erstelle/Update deine .env Datei:
```bash
# AI Services
COHERE_API_KEY="dein-cohere-key-hier"
HUGGINGFACE_API_KEY="dein-huggingface-key-hier"
A21_API_KEY="dein-a21-studio-key-hier"

# Productivity APIs
NOTION_API_KEY="dein-notion-key-hier"
JSONBIN_API_KEY="dein-jsonbin-key-hier"

# Utility APIs
OPENWEATHER_API_KEY="dein-openweather-key-hier"

# Weitere empfohlene kostenlose APIs:
TINYPNG_API_KEY=""  # https://tinypng.com/developers
FILESTACK_API_KEY=""  # https://www.filestack.com/
EMAILJS_PUBLIC_KEY=""  # https://www.emailjs.com/
EMAILJS_SERVICE_ID=""
EMAILJS_TEMPLATE_ID=""
```

### 2. Backend Integration (Python):
```python
# In ultra_simple_backend.py oder config.py
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys laden
API_KEYS = {
    'cohere': os.getenv('COHERE_API_KEY'),
    'huggingface': os.getenv('HUGGINGFACE_API_KEY'),
    'a21': os.getenv('A21_API_KEY'),
    'notion': os.getenv('NOTION_API_KEY'),
    'openweather': os.getenv('OPENWEATHER_API_KEY')
}
```

### 3. Beispiel-Integrationen:

#### Cohere für Text-Zusammenfassung:
```python
import cohere

co = cohere.Client(API_KEYS['cohere'])

async def summarize_document(text: str):
    response = co.summarize(
        text=text,
        length='medium',
        format='bullets'
    )
    return response.summary
```

#### Hugging Face für Datei-Klassifizierung:
```python
import requests

def classify_document(text: str):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    headers = {"Authorization": f"Bearer {API_KEYS['huggingface']}"}
    
    payload = {
        "inputs": text,
        "parameters": {"candidate_labels": ["Rechnung", "Vertrag", "Brief", "Bericht"]}
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()
```

#### Notion Integration für Task-Management:
```python
from notion_client import Client

notion = Client(auth=API_KEYS['notion'])

async def create_task(title: str, description: str):
    # Deine Notion Database ID hier
    database_id = "DEINE_DATABASE_ID"
    
    notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Name": {"title": [{"text": {"content": title}}]},
            "Description": {"rich_text": [{"text": {"content": description}}]}
        }
    )
```

## 📝 Fehlt noch:

### Empfohlene zusätzliche Keys (alle kostenlos):
1. **TinyPNG** - Für Bild-Optimierung
2. **Filestack** - Für erweiterte Uploads  
3. **EmailJS** - Für Email-Benachrichtigungen
4. **Supabase** - Als Backend-Alternative (Auth + DB)

### MCP Server API Keys:
Für einige MCP Server brauchst du auch Keys:
- Brave Search API (für search-mcp)
- Wenn du Claude/OpenAI MCP nutzen willst

## 🚀 Nächste Schritte:

1. **Stoppe den laufenden Prozess** (Ctrl+C)
2. **Füge deine API Keys zur .env hinzu**
3. **Starte neu mit:** `npm run dev`
4. **Teste die erste API-Integration!**
