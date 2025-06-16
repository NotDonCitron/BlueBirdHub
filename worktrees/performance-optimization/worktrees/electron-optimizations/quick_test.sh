#!/bin/bash

echo "=== Quick Test Summary ==="

# Test Backend Health
echo "Testing backend connection..."
cd "/Users/pascalhintermaier/Documents/neue UI /ordnungshub"

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Python virtual environment activated"
    
    # Test one simple backend test
    echo "Running simple backend test..."
    python -c "
from fastapi.testclient import TestClient
from src.backend.main import app

client = TestClient(app)
response = client.get('/')
print(f'✓ Backend API responding: {response.status_code}')
print(f'  Response: {response.json()}')
"
else
    echo "✗ Virtual environment not found"
fi

# Test Frontend builds
echo
echo "Testing frontend build..."
npm run build 2>/dev/null && echo "✓ Frontend builds successfully" || echo "✗ Frontend build failed"

# Test linting on key files
echo
echo "Testing key file syntax..."
npx tsc --noEmit 2>/dev/null && echo "✓ TypeScript compilation successful" || echo "✗ TypeScript errors found"

echo
echo "=== Summary ==="
echo "Basic checks completed. For full test suite run: ./run_all_tests.sh"