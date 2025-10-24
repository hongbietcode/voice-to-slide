#!/bin/bash

echo "🔍 Checking Voice-to-Slide Services..."
echo "======================================="
echo ""

# Check Docker containers
echo "📦 Docker Containers:"
docker compose ps
echo ""

# Check if services are healthy
echo "🏥 Health Checks:"

# Check database
if docker compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL: Healthy"
else
    echo "❌ PostgreSQL: Not ready"
fi

# Check Redis
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: Healthy"
else
    echo "❌ Redis: Not ready"
fi

# Check API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API: Healthy (http://localhost:8000)"
else
    echo "❌ API: Not ready"
fi

# Check Frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend: Healthy (http://localhost:3000)"
else
    echo "❌ Frontend: Not ready"
fi

echo ""
echo "📊 Service URLs:"
echo "   Frontend:  http://localhost:3000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   API Health: http://localhost:8000/health"
echo ""
echo "📝 View logs: docker compose logs -f [service-name]"
echo "   Services: api, db, redis, worker-transcription, worker-analysis, worker-generation, frontend"
