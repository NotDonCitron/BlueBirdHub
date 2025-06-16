# 🚀 OrdnungsHub Development Guide

## Schnell starten (empfohlen):

```bash
# Alles auf einmal starten:
./dev.sh

# Oder einzeln:
npm run dev:test        # Test-Backend (funktioniert immer)
npm run dev:react       # Frontend

# Vollständiges Backend (wenn es funktioniert):
npm run dev:backend     # Vollständiges Backend
```

## 🛠️ Development Best Practices

### 1. Immer Test-Backend zuerst
```bash
# Test ob alles funktioniert:
python3 test_backend.py

# Backend läuft? Test mit:
curl http://127.0.0.1:8001/
```

### 2. Feature Development Workflow
```bash
# 1. Test-Backend starten
python3 test_backend.py &

# 2. Frontend starten
npm run dev:react

# 3. Feature implementieren
# 4. Sofort testen im Browser
# 5. Erst wenn Frontend funktioniert → Backend integrieren
```

### 3. Debugging vermeiden

#### ❌ Vermeiden:
- Große Änderungen ohne Tests
- Komplexe Imports ohne Fallbacks
- Backend und Frontend gleichzeitig ändern

#### ✅ Besser:
- Kleine Schritte mit Tests
- Test-Backend für Frontend Development
- Ein System nach dem anderen ändern

### 4. File Structure für Features

```
feature/
├── test_endpoint.py      # Mock Backend zuerst
├── Component.tsx         # Frontend implementieren
├── Component.test.tsx    # Tests schreiben
└── real_backend.py       # Echtes Backend zuletzt
```

## 🔧 Tools & Commands

### Backend Testing:
```bash
# Schneller Test-Backend (funktioniert immer):
python3 test_backend.py

# Echter Backend (kann Probleme haben):
cd src/backend && PYTHONPATH=../.. uvicorn main:app --reload --port 8001
```

### Frontend Testing:
```bash
# Development Server:
npm run dev:react

# Test ob API Calls funktionieren:
curl http://127.0.0.1:8001/api/dashboard/stats
```

### Quick Debugging:
```bash
# Alle Prozesse killen:
pkill -f uvicorn && pkill -f webpack

# Neu starten:
./dev.sh
```

## 🎯 Troubleshooting

### Problem: Backend startet nicht
**Lösung:** Test-Backend verwenden
```bash
python3 test_backend.py
```

### Problem: Frontend kann Backend nicht erreichen
**Lösung:** URL prüfen
```bash
# In ApiContext.tsx:
const url = `http://127.0.0.1:8001${endpoint}`;  // ✅
const url = `http://localhost:8001${endpoint}`;  // ❌
```

### Problem: Import Errors
**Lösung:** Fallbacks verwenden
```python
try:
    from typing import AsyncGenerator
except ImportError:
    # Fallback für ältere Python Versionen
    pass
```

## 🚀 Production Deployment

### 1. Frontend Build:
```bash
npm run build:react
```

### 2. Backend mit echten Features:
```bash
# Alle Features aktiviert:
cd src/backend && uvicorn main:app --host 0.0.0.0 --port 8001
```

## 📝 Development Checklist

- [ ] Test-Backend funktioniert
- [ ] Frontend lädt ohne Errors
- [ ] API Calls funktionieren
- [ ] Drag & Drop Feature getestet
- [ ] Neue Features in Test-Backend mocken
- [ ] Schritt für Schritt implementieren
- [ ] Echtes Backend erst am Ende integrieren

## 🎉 Ready to Code!

Mit diesem Setup sollte das Debugging drastisch reduziert werden. Der Test-Backend funktioniert immer und das Frontend kann unabhängig entwickelt werden!