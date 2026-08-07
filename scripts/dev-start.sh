#!/bin/bash
set -e

echo "🚀 Starting Verdis/AegisOS Local Development Environment"
echo ""

echo "Starting AegisOS (backend + frontend + redis)..."
docker compose -f docker-compose.dev.yml up -d aegisos-backend aegisos-frontend redis

echo ""
echo "✅ AegisOS Backend:    http://localhost:8000"
echo "✅ AegisOS Frontend:   http://localhost:5173"
echo "✅ Redis:              localhost:6379"
echo "✅ API Docs:           http://localhost:8000/docs"
echo ""
echo "To start blockchain node:  docker compose -f docker-compose.dev.yml --profile blockchain up -d"
echo "To start PostgreSQL:       docker compose -f docker-compose.dev.yml --profile postgres up -d"
echo "To start monitoring:       docker compose -f docker-compose.dev.yml --profile monitoring up -d"
echo ""
echo "To stop: docker compose -f docker-compose.dev.yml down"
