#!/bin/bash
set -e

echo "Initializing ClaimFlow development environment..."

# Install dependencies
echo "Installing backend dependencies..."
cd backend && uv sync && cd ..

echo "Installing frontend dependencies..."
cd frontend && npm ci && cd ..

# Start services
echo "Starting backend (FastAPI on :8000)..."
cd backend && uv run uvicorn src.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

echo "Starting frontend (Vite on :5173)..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for services to be ready
echo "Waiting for services to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend healthy"
    break
  fi
  echo "Waiting for backend... ($i/30)"
  sleep 2
done

for i in {1..30}; do
  if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✓ Frontend ready"
    break
  fi
  echo "Waiting for frontend... ($i/30)"
  sleep 2
done

echo ""
echo "✓ ClaimFlow development environment ready!"
echo "  Backend: http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop services"

# Keep script running
wait $BACKEND_PID $FRONTEND_PID
