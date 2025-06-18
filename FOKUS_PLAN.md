# 🚀 FOKUS-PLAN: OrdnungsHub wieder auf Kurs

## 🎯 JETZT SOFORT (nächste 15 Min):

### 1. Status-Check & Aufräumen
```bash
cd C:\Users\pasca\CascadeProjects\nnewcoededui

# Alte Logs löschen für frischen Start
del *.log

# Git-Status prüfen
git status --short

# Welche Python-Version?
python --version

# Node-Version?
node --version
```

### 2. Minimal-Funktionstest
```bash
# Backend einzeln testen
python ultra_simple_backend.py

# Wenn das klappt, Frontend:
npm run dev
```

## 🔧 ERWEITERTE MCP-SERVER für OrdnungsHub

### Installiere diese Power-Kombination:

1. **@modelcontextprotocol/server-filesystem**
   ```bash
   npm install -g @modelcontextprotocol/server-filesystem
   ```
   - Perfekt für: Batch-Dateioperationen in OrdnungsHub

2. **@modelcontextprotocol/server-sqlite**
   ```bash
   npm install -g @modelcontextprotocol/server-sqlite
   ```
   - Perfekt für: Lokale Datenbank ohne externes Setup

3. **@modelcontextprotocol/server-brave-search**
   ```bash
   npm install -g @modelcontextprotocol/server-brave-search
   ```
   - Kostenlose Web-Suche API!

4. **Custom File-Organizer MCP** (erstellen wir gemeinsam!)

## 🎁 KOSTENLOSE APIs für OrdnungsHub

### Sofort einsetzbar (ohne Kreditkarte):

1. **TinyPNG API** (500 Komprimierungen/Monat gratis)
   ```python
   # Für Bild-Organisation in OrdnungsHub
   import tinify
   tinify.key = "YOUR_API_KEY"  # https://tinypng.com/developers
   ```

2. **Abstract API Suite** (Mehrere kostenlose Tiers)
   - Email Validation: 100/Monat
   - IP Geolocation: 1000/Monat
   - Website Screenshot: 100/Monat
   ```python
   # Perfekt für Metadaten-Anreicherung
   ```

3. **Filestack** (100 Uploads/Monat, 1GB Bandwidth)
   ```javascript
   // Für erweiterte Datei-Uploads
   const client = filestack.init('YOUR_API_KEY');
   ```

4. **EmailJS** (200 Emails/Monat gratis)
   ```javascript
   // Für Benachrichtigungen ohne Backend
   emailjs.send('service_id', 'template_id', params);
   ```

5. **Supabase** (Kostenlose Postgres DB + Auth)
   ```python
   # Alternative zu SQLite für Cloud-Features
   from supabase import create_client
   ```

## 🤖 CLAUDE CODE POWER-WORKFLOWS

### Workflow 1: "Fix-It-Mode"
```bash
# In Claude Code eingeben:
"Analysiere C:\Users\pasca\CascadeProjects\nnewcoededui\src
Finde alle TODO-Kommentare und unvollständigen Funktionen.
Erstelle eine priorisierte Fix-Liste."
```

### Workflow 2: "Test-Generator"
```bash
# Claude Code Prompt:
"Schreibe Tests für src/backend/api/routes.py
Nutze pytest und erstelle mindestens 5 sinnvolle Tests
mit Mock-Daten für Datei-Operationen."
```

### Workflow 3: "API-Integration"
```bash
# Claude Code Prompt:
"Integriere TinyPNG API in src/utils/image_processor.py
Erstelle eine Funktion compress_image(path) mit Error-Handling
und Progress-Callback."
```

## 🎮 ROO CODE OPTIMALE KONFIGURATION

### .claude/config.json für OrdnungsHub:
```json
{
  "mcpServers": {
    "ordnungshub-fs": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "C:\\Users\\pasca\\CascadeProjects\\nnewcoededui"]
    },
    "ordnungshub-git": {
      "command": "node",
      "args": ["mcp-servers/git-mcp-server/index.js"]
    },
    "ordnungshub-search": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-brave-search"]
    },
    "ordnungshub-db": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-sqlite", "ordnungshub.db"]
    }
  }
}
```

### .roomodes für kontextabhängige Befehle:
```
# Debugging Mode
debug: "Aktiviere Debug-Modus. Zeige mir alle Fehler in den letzten Logs und schlage Fixes vor."

# Refactor Mode  
refactor: "Analysiere den Code und schlage Verbesserungen vor. Fokus auf Clean Code und Performance."

# Test Mode
test: "Erstelle oder verbessere Tests für die aktuelle Datei."

# Doc Mode
doc: "Erstelle oder aktualisiere die Dokumentation."
```

## 🏆 QUICK WINS (Sofort spürbare Erfolge)

### Win 1: Backend Health-Check (5 Min)
```python
# Füge zu ultra_simple_backend.py hinzu:
@app.get("/health")
async def health_check():
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0"
    }
```

### Win 2: Frontend-Verbindung testen (5 Min)
```javascript
// In src/frontend/App.js oder main.js:
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(data => console.log('✅ Backend connected:', data))
  .catch(e => console.error('❌ Backend error:', e));
```

### Win 3: Erste Datei-Organisation (10 Min)
```python
# Neue Datei: src/backend/organizer.py
import os
from pathlib import Path
from typing import List, Dict

def analyze_folder(path: str) -> Dict:
    """Analysiert einen Ordner und gibt Statistiken zurück"""
    files = list(Path(path).glob('**/*'))
    return {
        "total_files": len([f for f in files if f.is_file()]),
        "total_folders": len([f for f in files if f.is_dir()]),
        "file_types": {}  # TODO: Implementieren
    }
```

## 🚨 NOTFALL-KOMMANDOS

### Wenn gar nichts geht:
```bash
# Nuclear Option - Alles neu
cd C:\Users\pasca\CascadeProjects\nnewcoededui
rmdir /s /q node_modules
rmdir /s /q .venv
npm cache clean --force
npm install
python -m venv .venv
.venv\Scripts\activate
pip install fastapi uvicorn
```

### Mini-Backend zum Testen:
```python
# test_backend.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"msg": "OrdnungsHub lebt!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 📈 FORTSCHRITTS-TRACKER

Hake ab was funktioniert:
- [ ] Python & Node installiert
- [ ] Git repository sauber (`git status`)
- [ ] Backend startet ohne Fehler
- [ ] Frontend lädt im Browser
- [ ] Health-Endpoint antwortet
- [ ] Erste API-Route funktioniert
- [ ] Ein Test läuft grün
- [ ] MCP-Server verbunden

---

**🎯 NÄCHSTER SCHRITT:** 
Führe den Status-Check aus (erste 15 Min) und sag mir was dabei rauskommt. 
Dann können wir gezielt das erste Problem lösen!

**Du schaffst das! Ein funktionierender Endpoint ist der erste Schritt zum Erfolg! 💪**
