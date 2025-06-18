# OrdnungsHub Recovery & Development Plan

## 🚀 Sofortmaßnahmen (Quick Wins)

### 1. Environment Setup
```bash
# Backend starten
cd C:\Users\pasca\CascadeProjects\nnewcoededui
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Frontend Dependencies
npm install
```

### 2. Basis-Funktionalität testen
```bash
# Backend Test
python ultra_simple_backend.py

# In neuem Terminal: Frontend
npm run dev:react
```

## 📋 Strukturierter Arbeitsplan

### Woche 1: Stabilisierung
- [ ] Alle Dependencies updaten
- [ ] Fehlerhafte Imports fixen
- [ ] Test-Suite zum Laufen bringen
- [ ] CI/CD Pipeline reparieren

### Woche 2: MCP-Integration
- [ ] MCP-Server konfigurieren
- [ ] Claude Code Integration
- [ ] API-Keys einrichten
- [ ] Erste Automatisierungen

### Woche 3: Feature-Entwicklung
- [ ] Kern-Features identifizieren
- [ ] UI/UX verbessern
- [ ] API-Endpoints optimieren
- [ ] Dokumentation aktualisieren

## 🛠️ Tool-Stack für effektives Arbeiten

### Claude Code / Roo Code Setup

1. **MCP-Server Konfiguration**
   ```json
   {
     "mcpServers": {
       "filesystem": {
         "command": "npx",
         "args": ["@modelcontextprotocol/server-filesystem", "C:\\Users\\pasca\\CascadeProjects"]
       },
       "search": {
         "command": "npx",
         "args": ["@modelcontextprotocol/server-search"]
       },
       "fetch": {
         "command": "npx",
         "args": ["@modelcontextprotocol/server-fetch"]
       },
       "memory": {
         "command": "npx",
         "args": ["@modelcontextprotocol/server-memory"]
       }
     }
   }
   ```

2. **Kostenlose API Integration**
   ```env
   # Füge zu .env hinzu:
   HUGGINGFACE_API_KEY=hf_xxxxx  # Kostenlos nach Registrierung
   COHERE_API_KEY=xxx            # 1000 Calls/Monat kostenlos
   DEEPL_AUTH_KEY=xxx            # 500k Zeichen/Monat kostenlos
   ```

3. **Roo Code Rules Optimierung**
   - Erstelle spezifische Rules für jeden Arbeitsbereich
   - Nutze `.roomodes` für kontextabhängige Befehle
   - Implementiere Automatisierungen für repetitive Tasks

## 🎯 Konkrete nächste Schritte

### Schritt 1: Projekt-Bereinigung
```bash
# Alte Logs aufräumen
rm *.log

# Git-Status prüfen
git status

# Branches aufräumen
git branch -a
```

### Schritt 2: Dependencies aktualisieren
```bash
# Python
pip install --upgrade -r requirements.txt

# Node
npm update
npm audit fix
```

### Schritt 3: Erste Tests
- Starte Backend: `python ultra_simple_backend.py`
- Starte Frontend: `npm run dev`
- Öffne: http://localhost:3002

## 💡 Pro-Tipps für effektives Arbeiten

1. **Nutze Claude Code's Stärken:**
   - Lass Claude Code repetitive Refactorings machen
   - Nutze es für Test-Generierung
   - Dokumentation automatisch erstellen lassen

2. **MCP-Server Workflows:**
   - Git-MCP für Versionskontrolle
   - Filesystem-MCP für Batch-Operationen
   - Memory-MCP für Kontext über Sessions

3. **Debugging-Strategie:**
   - Console-Monitor nutzen: `npm run dev:monitor`
   - Logs strukturiert analysieren
   - Fehler isoliert in kleinen Tests reproduzieren

## 🔄 Tägliche Routine

1. **Morgens:**
   - Git pull & Status check
   - Dependencies prüfen
   - Test-Suite laufen lassen

2. **Während der Arbeit:**
   - Feature-Branch erstellen
   - Kleine, atomare Commits
   - Tests parallel schreiben

3. **Abends:**
   - Code Review mit Claude Code
   - Dokumentation updaten
   - Backup erstellen

## 🚨 Troubleshooting

### Häufige Probleme & Lösungen:

1. **"Module not found" Fehler:**
   ```bash
   npm install
   pip install -r requirements.txt
   ```

2. **CORS-Probleme:**
   - Prüfe `.env` CORS_ORIGINS
   - Backend auf richtiger Port?

3. **Electron startet nicht:**
   ```bash
   npm run dev:react  # Erst Frontend
   npm run dev:electron  # Dann Electron
   ```

## 📚 Wichtige Ressourcen

- [MCP Servers Directory](https://github.com/modelcontextprotocol/servers)
- [Claude Code Dokumentation](https://docs.anthropic.com)
- [Kostenlose APIs Liste](https://github.com/public-apis/public-apis)

---

**Nächster konkreter Schritt:** 
Lass uns mit der Projekt-Bereinigung anfangen. Soll ich dir helfen, die aktuelle Git-Situation zu analysieren und aufzuräumen?
