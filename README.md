# 🚀 OrdnungsHub - AI-Powered System Organizer

> **Eine intelligente Desktop-Anwendung für Workspace-Management, Task-Organisation und Dokumentenverwaltung mit KI-Integration.**

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Node](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)

## ✨ Features

### 🎯 **Core Funktionalitäten**
- **Workspace Management** - Organisiere Projekte in strukturierten Arbeitsbereichen
- **Task Management** - Intelligente Aufgabenverwaltung mit KI-Unterstützung
- **File Management** - Dokumentenverwaltung mit automatischer Kategorisierung
- **AI Integration** - Unterstützung für multiple AI-Provider (OpenAI, Anthropic, Google)

### 🔧 **Technische Features**
- **Cross-Platform** - Desktop-App für Windows, macOS und Linux
- **Real-time Updates** - Live-Synchronisation zwischen Frontend und Backend
- **Performance Optimized** - Webpack-Bundle-Optimierung und Lazy Loading
- **Comprehensive Testing** - Unit-, Integration- und E2E-Tests
- **Authentication** - Sichere Benutzerauthentifizierung

### 🎨 **User Experience**
- **Modern UI** - React-basierte Benutzeroberfläche mit TypeScript
- **Responsive Design** - Optimiert für verschiedene Bildschirmgrößen
- **Dark/Light Theme** - Anpassbare Benutzeroberfläche
- **Keyboard Shortcuts** - Effiziente Navigation

## 🛠️ Tech Stack

### **Frontend**
- **React 19** mit TypeScript
- **Electron** für Desktop-Integration
- **Webpack 5** für Module-Bundling
- **CSS3** mit modernen Features

### **Backend**
- **Python 3.10+** mit FastAPI
- **SQLAlchemy** für Datenbankmanagement
- **Alembic** für Datenbankmigrationen
- **Pydantic** für Datenvalidierung

### **Development Tools**
- **Jest** für Unit-Testing
- **Playwright** für E2E-Testing
- **ESLint** für Code-Qualität
- **Docker** für Containerisierung

## 🚀 Quick Start

### **Voraussetzungen**
```bash
node >= 18.0.0
python >= 3.10
npm oder yarn
```

### **Installation**
```bash
# Repository klonen
git clone https://github.com/NotDonCitron/BlueBirdHub.git
cd BlueBirdHub

# Dependencies installieren
npm install
pip install -r requirements.txt

# Entwicklungsserver starten
npm run dev
```

### **Verfügbare Scripts**
```bash
npm run dev          # Startet Backend, Frontend und Electron
npm run dev:backend  # Nur Backend starten
npm run dev:react    # Nur React-Frontend starten
npm run build        # Production Build erstellen
npm run test         # Tests ausführen
```

## 📁 Projektstruktur

```
OrdnungsHub/
├── src/
│   ├── backend/          # Python FastAPI Backend
│   │   ├── api/         # API Endpoints
│   │   ├── models/      # Datenbankmodelle
│   │   ├── services/    # Business Logic
│   │   └── database/    # Datenbankonfiguration
│   └── frontend/        # React Frontend
│       ├── react/       # React-Komponenten
│       ├── styles/      # CSS-Dateien
│       └── utils/       # Utility-Funktionen
├── tests/               # Test-Dateien
├── docs/                # Dokumentation
└── deploy/              # Deployment-Skripte
```

## 🔧 Konfiguration

### **Umgebungsvariablen**
Erstelle eine `.env`-Datei im Projektroot:

```env
# Database
DATABASE_URL=sqlite:///./ordnungshub.db

# API Keys (optional)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Security
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
```

## 🧪 Testing

```bash
# Alle Tests ausführen
npm run test

# Nur Unit-Tests
npm run test:unit

# Nur Integration-Tests
npm run test:integration

# E2E-Tests
npm run test:e2e

# Test-Coverage
npm run test:coverage
```

## 📦 Deployment

### **Production Build**
```bash
npm run build:prod
```

### **Docker**
```bash
docker-compose up -d
```

### **Electron App**
```bash
npm run build:electron
```

## 🤝 Contributing

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/amazing-feature`)
3. Committe deine Änderungen (`git commit -m 'Add amazing feature'`)
4. Push zum Branch (`git push origin feature/amazing-feature`)
5. Öffne eine Pull Request

## 📝 Changelog

### v0.1.0 (2025-01-22)
- ✅ Initial Release
- ✅ Basic Workspace Management
- ✅ Task Management mit AI-Integration
- ✅ File Upload und Management
- ✅ Authentication System
- ✅ Performance Optimierungen
- ✅ Comprehensive Test Suite

## 📄 License

Dieses Projekt ist unter der MIT License lizenziert - siehe [LICENSE](LICENSE) für Details.

## 🙏 Acknowledgments

- React Team für das fantastische Framework
- FastAPI für das schnelle Backend-Framework
- Electron für die Desktop-Integration
- Alle Open-Source-Contributors

## 📞 Support

Bei Fragen oder Problemen:
- 📧 **Email**: support@ordnungshub.dev
- 🐛 **Issues**: [GitHub Issues](https://github.com/NotDonCitron/BlueBirdHub/issues)
- 📖 **Docs**: [Documentation](https://github.com/NotDonCitron/BlueBirdHub/docs)

---

**Entwickelt mit ❤️ für effiziente Workspace-Organisation**