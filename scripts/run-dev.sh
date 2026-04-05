#!/bin/bash

set -e

cleanup() {
    echo -e "\nShutting down services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
    wait $FRONTEND_PID 2>/dev/null || true
    echo "Done."
    exit 0
}

trap cleanup SIGINT SIGTERM

cd "$(dirname "$0")/../infra/backend"
echo "Starting backend..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd "$(dirname "$0")/../infra/frontend"
echo "Starting frontend..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Both services are running:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both services."

wait $BACKEND_PID $FRONTEND_PID
