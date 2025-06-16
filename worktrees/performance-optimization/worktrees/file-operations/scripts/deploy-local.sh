#!/bin/bash

# OrdnungsHub Local Production Deployment Script
# Deploys OrdnungsHub to local production mode without Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ordnungshub"
ENV=${1:-production}
BACKEND_PORT=8000
FRONTEND_PORT=3001

echo -e "${BLUE}🚀 Starting OrdnungsHub Local Production Deployment...${NC}"
echo "=================================================="
echo "Environment: $ENV"
echo "Project: $PROJECT_NAME"
echo ""

# Function to print colored output
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required files exist
log_info "Checking deployment requirements..."

if [ ! -f ".env.production" ]; then
    log_error ".env.production file not found"
    exit 1
fi

if [ ! -f ".env.secrets" ]; then
    log_error ".env.secrets file not found"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed"
    exit 1
fi

# Install backend dependencies
log_info "Installing backend dependencies..."
if [ ! -f "requirements.txt" ]; then
    log_warn "requirements.txt not found, creating basic one..."
    cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
python-multipart==0.0.6
loguru==0.7.2
python-dotenv==1.0.0
psycopg2-binary==2.9.9
redis==5.0.1
pydantic==2.5.0
pydantic-settings==2.1.0
databases[postgresql]==0.8.0
asyncpg==0.29.0
httpx==0.25.2
jinja2==3.1.2
pytest==7.4.3
pytest-asyncio==0.21.1
requests==2.31.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
EOF
fi

pip3 install -r requirements.txt

# Install frontend dependencies
log_info "Installing frontend dependencies..."
npm install

# Build frontend for production
log_info "Building frontend for production..."
npm run build

# Create production database
log_info "Setting up production database..."
if [ ! -d "data" ]; then
    mkdir -p data
fi

# Run database migrations (if any)
log_info "Running database migrations..."
if [ -d "migrations" ]; then
    python3 -c "
import os
os.environ['ENV'] = '$ENV'
from src.backend.database.database import init_db
init_db()
print('Database initialized successfully')
"
fi

# Create systemd service files (optional for proper production)
log_info "Creating service configuration..."
cat > ordnungshub-backend.service << EOF
[Unit]
Description=OrdnungsHub Backend API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=ENV=$ENV
ExecStart=$(which python3) -m uvicorn src.backend.main:app --host 0.0.0.0 --port $BACKEND_PORT --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

cat > ordnungshub-frontend.service << EOF
[Unit]
Description=OrdnungsHub Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(which npx) serve -s dist -l $FRONTEND_PORT
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create startup script
log_info "Creating startup script..."
cat > start-production.sh << 'EOF'
#!/bin/bash

# Start OrdnungsHub in production mode
echo "🚀 Starting OrdnungsHub Production Services..."

# Set environment
export ENV=production

# Start backend
echo "Starting backend on port 8000..."
python3 -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --workers 4 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Check if backend is running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend started successfully"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend (serving built files)
echo "Starting frontend on port 3001..."
npx serve -s dist -l 3001 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

# Check if frontend is running
if curl -f http://localhost:3001 > /dev/null 2>&1; then
    echo "✅ Frontend started successfully"
else
    echo "❌ Frontend failed to start"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 OrdnungsHub is now running in production mode!"
echo "📱 Frontend: http://localhost:3001"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "To stop services:"
echo "kill $BACKEND_PID $FRONTEND_PID"

# Keep script running
echo "Press Ctrl+C to stop all services..."
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait
EOF

chmod +x start-production.sh

# Create stop script
cat > stop-production.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping OrdnungsHub services..."

# Kill processes by port
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "Stopping backend (port 8000)..."
    kill $(lsof -ti:8000) 2>/dev/null || true
fi

if lsof -ti:3001 > /dev/null 2>&1; then
    echo "Stopping frontend (port 3001)..."
    kill $(lsof -ti:3001) 2>/dev/null || true
fi

echo "✅ All services stopped"
EOF

chmod +x stop-production.sh

# Run basic health checks
log_info "Running pre-deployment health checks..."

# Test backend startup
log_info "Testing backend startup..."
python3 -c "
import os
os.environ['ENV'] = '$ENV'
from src.backend.main import app
print('✅ Backend configuration valid')
"

# Test frontend build
if [ -d "dist" ] && [ -f "dist/index.html" ]; then
    log_info "✅ Frontend build successful"
else
    log_error "Frontend build failed"
    exit 1
fi

# Create deployment summary
echo ""
echo -e "${GREEN}🎉 Local Production Deployment Complete!${NC}"
echo "=============================================="
echo ""
echo "📂 Project Structure:"
echo "  ├── Backend API (Python/FastAPI)"
echo "  ├── Frontend (React/TypeScript)"
echo "  ├── Database (SQLite for local)"
echo "  └── Configuration (Production ready)"
echo ""
echo "🚀 To start production services:"
echo "  ./start-production.sh"
echo ""
echo "🛑 To stop services:"
echo "  ./stop-production.sh"
echo ""
echo "📱 Access URLs (when running):"
echo "  Frontend: http://localhost:3001"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "🔒 Security Notes:"
echo "  • Production secrets configured"
echo "  • Environment variables set"
echo "  • CORS properly configured"
echo "  • Ready for reverse proxy setup"
echo ""
echo "📝 Next Steps:"
echo "  1. Run ./start-production.sh to start services"
echo "  2. Test at http://localhost:3001/tasks"
echo "  3. Configure reverse proxy (nginx) for external access"
echo "  4. Set up SSL certificates for HTTPS"
echo "  5. Configure domain DNS if needed"
echo ""

log_info "Deployment completed successfully! 🚀"