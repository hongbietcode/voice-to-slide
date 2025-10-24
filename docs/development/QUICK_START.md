# Voice-to-Slide Web UI - Quick Start Guide

## Current Status

🚀 **Web UI Implementation Complete!**

The Voice-to-Slide application now has a full web interface with:
- FastAPI backend with REST API
- React frontend with real-time progress
- Celery background workers for async processing
- PostgreSQL database for job tracking
- WebSocket for real-time updates

## Services Being Built

Docker is currently building and starting the following services:

1. **PostgreSQL** (port 5432) - Database for job metadata
2. **Redis** (port 6379) - Message broker and cache
3. **FastAPI API** (port 8000) - REST API server
4. **Celery Worker - Transcription** - Handles audio transcription
5. **Celery Worker - Analysis** - Handles AI structure analysis
6. **Celery Worker - Generation** - Handles PPTX generation (includes Playwright)
7. **React Frontend** (port 3000) - Web UI

## Build Time

**Expected build time:** 5-10 minutes (first time)
- Most time spent installing Playwright with Chromium browser (~200MB download)
- Subsequent starts will be much faster (cached layers)

## Once Build Completes

### 1. Check Services Status

```bash
./check-services.sh
```

Or manually:

```bash
docker compose ps
docker compose logs -f api
```

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

### 3. Test the Application

#### Basic Flow:
1. Open http://localhost:3000
2. Drag and drop an audio file (or click to browse)
3. Select theme (optional)
4. Click "Generate Presentation"
5. Watch real-time progress
6. Download PPTX when complete

#### Interactive Mode:
1. Enable "Interactive mode" checkbox before upload
2. After structure analysis, you'll be redirected to editor
3. Provide feedback like "Change slide 2 title to 'AI Overview'"
4. Click "Submit Feedback" to update structure
5. Repeat as needed
6. Click "Confirm & Generate PPTX" when satisfied

## Common Commands

```bash
# View all container logs
docker compose logs -f

# View specific service logs
docker compose logs -f api
docker compose logs -f worker-generation
docker compose logs -f frontend

# Restart a service
docker compose restart api

# Stop all services
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v

# Rebuild a specific service
docker compose up -d --build api
```

## Troubleshooting

### Build Issues

If build fails:

```bash
# Clean everything and start fresh
docker compose down -v
docker system prune -a
docker compose up -d --build
```

### Services Not Starting

```bash
# Check logs for errors
docker compose logs api
docker compose logs worker-generation

# Common issues:
# - Database not ready: Wait 30 seconds and restart
# - Redis connection failed: Check redis logs
```

### API Not Responding

```bash
# Check if API is running
curl http://localhost:8000/health

# View API logs
docker compose logs -f api

# Restart API
docker compose restart api
```

### Frontend Not Loading

```bash
# Check frontend logs
docker compose logs -f frontend

# Frontend takes ~30 seconds to start (Vite dev server)
# Wait for: "Local: http://localhost:3000/"
```

## Development Workflow

### Backend Changes

```bash
# API code changes auto-reload
# Just edit files in api/ or src/voice_to_slide/

# View logs to see reload
docker compose logs -f api
```

### Frontend Changes

```bash
# Frontend auto-reloads with hot module replacement
# Just edit files in frontend/src/

# View logs
docker compose logs -f frontend
```

### Database Changes

```bash
# Access PostgreSQL
docker compose exec db psql -U postgres -d voice_to_slide

# View jobs
SELECT id, status, progress_percentage FROM jobs;

# Exit psql
\q
```

### Redis Commands

```bash
# Access Redis CLI
docker compose exec redis redis-cli

# View keys
KEYS *

# Get job channel messages
SUBSCRIBE job:*

# Exit redis-cli
exit
```

## Next Steps

Once the application is running:

1. **Test basic generation** with a short audio file
2. **Test interactive mode** to try AI-powered editing
3. **Explore API docs** at http://localhost:8000/docs
4. **Review logs** to understand the pipeline flow
5. **Customize themes** by editing `src/voice_to_slide/themes.md`

## Documentation

- **Design Plan**: `WEB_UI_DESIGN_PLAN.md` (97 pages, complete architecture)
- **Setup Guide**: `WEB_UI_README.md` (comprehensive setup instructions)
- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md` (what was built)
- **Original CLI Docs**: `CLAUDE.md`, `README.md`

## Support

If you encounter issues:

1. Check logs: `docker compose logs -f`
2. Verify API keys in `.env`
3. Ensure ports 3000, 5432, 6379, 8000 are not in use
4. Try clean rebuild: `docker compose down -v && docker compose up -d --build`

## Success Indicators

✅ All 7 containers show as "Up" in `docker compose ps`
✅ API health check returns 200: `curl http://localhost:8000/health`
✅ Frontend loads at http://localhost:3000
✅ Database is accessible: `docker compose exec db pg_isready`
✅ Redis responds: `docker compose exec redis redis-cli ping`

## What's Running

```
┌─────────────┐
│   Browser   │ ← User interacts here
└─────────────┘
       ↓
┌─────────────┐
│  Frontend   │ ← React app (port 3000)
│  (Vite)     │
└─────────────┘
       ↓
┌─────────────┐
│  FastAPI    │ ← API server (port 8000)
│  + WebSocket│
└─────────────┘
       ↓
┌─────────────────────────────────┐
│  Celery Workers (3 queues)      │
│  - Transcription (×2 workers)   │
│  - Analysis (×4 workers)        │
│  - Generation (×1 worker)       │
└─────────────────────────────────┘
       ↓
┌──────────────┬──────────────┐
│  PostgreSQL  │    Redis     │
│  (metadata)  │ (queue+cache)│
└──────────────┴──────────────┘
```

---

**Current build status**: Building... (check `docker compose ps`)
**Estimated completion**: 5-10 minutes from start
**Next command**: `./check-services.sh` (once build completes)
