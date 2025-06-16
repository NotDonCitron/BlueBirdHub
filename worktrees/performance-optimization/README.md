# OrdnungsHub - AI-Powered System Organizer

OrdnungsHub is an AI-powered desktop application designed to help users organize their digital workspace efficiently. It combines local AI processing with intelligent file management and system optimization tools.

## Project Structure

```
ordnungshub/
├── src/
│   ├── backend/        # Python FastAPI backend
│   ├── frontend/       # Electron frontend
│   ├── core/          # Core application logic
│   └── utils/         # Utility functions
├── tests/             # Test files
├── docs/              # Documentation
├── resources/         # Static resources
└── logs/              # Application logs
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm

### Backend Setup
1. Create and activate Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup
1. Install Node.js dependencies:
   ```bash
   npm install
   ```

## Running the Application

### Development Mode
Run both backend and frontend in development mode:
```bash
npm run dev
```

Or run them separately:
- Backend: `npm run dev:backend`
- Frontend: `npm run dev:frontend`

### Production Mode
```bash
npm start
```

## Testing

### Python Tests
```bash
pytest
```

### JavaScript Tests
```bash
npm test
```

## Architecture

- **Backend**: FastAPI (Python) - Handles AI processing, file management, and system operations
- **Frontend**: Electron + HTML/CSS/JS - Provides the desktop application interface
- **IPC**: Inter-process communication between Electron and Python backend
- **Database**: SQLite for local data storage (to be implemented)
- **AI**: Local transformer models for intelligent features (to be implemented)

## Development Status

Currently implemented:
- ✅ Basic project structure
- ✅ FastAPI backend with health check endpoint
- ✅ Electron frontend with IPC communication
- ✅ Basic UI with connection status
- ✅ Development environment setup

Next steps:
- 🔄 Database layer implementation
- 🔄 UI framework integration (React)
- 🔄 Local AI model integration
- 🔄 Core features implementation

## License

MIT License - See LICENSE file for details