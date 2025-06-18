#!/bin/bash

# OrdnungsHub Quick Start - Neue sichere Architektur
# Verwendung: ./quick-start-new.sh

echo "🚀 OrdnungsHub - Neue sichere API-Architektur"
echo "============================================="

# 1. Umgebung prüfen
echo "🔍 Prüfe Umgebung..."
if [ ! -f ".env" ]; then
    echo "❌ .env Datei fehlt!"
    echo "Kopiere .env.example zu .env und konfiguriere die Werte."
    exit 1
fi

# 2. Environment-Variablen laden
source .env
echo "✅ Environment geladen:"
echo "   API_URL: $REACT_APP_API_URL"
echo "   FALLBACK_URL: $REACT_APP_FALLBACK_API_URL"

# 3. Ports bereinigen
echo "🧹 Bereinige Ports..."
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true  
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

# 4. Dependencies prüfen
echo "📦 Prüfe Dependencies..."
if [ ! -d "node_modules" ]; then
    echo "Installiere Node.js Dependencies..."
    npm install
fi

if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installiere Python Dependencies..."
    pip3 install -r requirements.txt
fi

# 5. Services starten
echo "🚀 Starte Services..."

# FastAPI Backend
echo "📡 Starte FastAPI Backend (Port 8000)..."
python3 src/backend/main.py &
FASTAPI_PID=$!

# Mock Backend mit neuen Automation-Endpunkten
echo "🎭 Starte Mock Backend (Port 8001)..."
python3 mock_backend.py &
MOCK_PID=$!

# Warte auf Backends
echo "⏳ Warte auf Backend-Start..."
sleep 5

# 6. Teste neue API-Architektur
echo "🔍 Teste neue API-Architektur..."
python3 test-api-cors.py

if [ $? -eq 0 ]; then
    echo "✅ API-Tests bestanden!"
else
    echo "❌ API-Tests fehlgeschlagen!"
    exit 1
fi

# 7. Frontend starten
echo "🎨 Starte Frontend (Port 3001)..."
npm run dev:react &
FRONTEND_PID=$!

echo ""
echo "🎉 OrdnungsHub gestartet mit neuer sicherer Architektur!"
echo "============================================="
echo "📱 Frontend:     http://localhost:3001"
echo "📡 FastAPI:      http://localhost:8000"  
echo "🎭 Mock Backend: http://localhost:8001"
echo ""
echo "🛡️ Schutzmaßnahmen aktiv:"
echo "   ✅ Frontend-Self-Call-Prevention"
echo "   ✅ Automatische Backend-Auswahl"
echo "   ✅ Request-Monitoring (Development)"
echo "   ✅ CORS-Probleme behoben"
echo ""
echo "🔧 Debug-Tools (Browser-Konsole):"
echo "   - window.apiManager"
echo "   - window.debugApi"
echo "   - window.requestInterceptor"
echo ""
echo "⏹️  Drücke Ctrl+C zum Beenden"

# Cleanup-Funktion
cleanup() {
    echo ""
    echo "🛑 Stoppe alle Services..."
    kill $FASTAPI_PID $MOCK_PID $FRONTEND_PID 2>/dev/null
    echo "✅ Alle Services gestoppt"
    exit 0
}

trap cleanup SIGINT
wait
