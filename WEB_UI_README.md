# Voice-to-Slide Web UI - Setup Guide

This guide explains how to set up and run the Voice-to-Slide web application.

## Architecture Overview

The web application consists of:
- **Backend**: FastAPI with Celery workers for background processing
- **Frontend**: React 18 + TypeScript with Vite
- **Database**: PostgreSQL for metadata storage
- **Cache/Queue**: Redis for Celery and WebSocket pub/sub
- **Real-time Updates**: WebSocket for progress tracking

## Prerequisites

- Python 3.11+ with `uv` package manager installed
- Node.js 20+ and npm
- Docker and Docker Compose (recommended)
- PostgreSQL 16 (if running without Docker)
- Redis 7 (if running without Docker)

## Quick Start with Docker Compose (Recommended)

### 1. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required API keys
SONIOX_API_KEY=your_soniox_api_key_here
CONTENT_ANTHROPIC_API_KEY=your_anthropic_api_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here

# Database and Redis URLs (already configured for Docker)
DATABASE_URL=postgresql://postgres:postgres@db:5432/voice_to_slide
REDIS_URL=redis://redis:6379/0
```

### 2. Start All Services

```bash
# Start all services (database, redis, API, workers, frontend)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Manual Setup (Without Docker)

If you prefer to run services locally without Docker:

### 1. Start PostgreSQL and Redis

```bash
# Start PostgreSQL (adjust for your OS)
brew services start postgresql@16  # macOS
sudo systemctl start postgresql    # Linux

# Start Redis
brew services start redis           # macOS
sudo systemctl start redis          # Linux
```

### 2. Create Database

```bash
psql postgres
CREATE DATABASE voice_to_slide;
\q
```

### 3. Install Python Dependencies

```bash
# Install uv if not already installed
pip install uv

# Install all dependencies
uv sync
```

### 4. Initialize Database Tables

```bash
# Run FastAPI to create tables on startup
uv run uvicorn api.main:app --reload
```

### 5. Start Celery Workers

Open separate terminals for each worker:

```bash
# Terminal 1: Transcription worker
uv run celery -A api.celery_config worker --queue=transcription --concurrency=2 --loglevel=info

# Terminal 2: Analysis worker
uv run celery -A api.celery_config worker --queue=analysis --concurrency=4 --loglevel=info

# Terminal 3: Generation worker (requires Playwright)
uv run playwright install chromium
uv run celery -A api.celery_config worker --queue=generation --concurrency=1 --loglevel=info
```

### 6. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 7. Start API Server

```bash
# In project root
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
voice-to-slide/
├── api/                      # Backend FastAPI application
│   ├── routers/              # API endpoints
│   ├── models/               # Database models
│   ├── schemas/              # Pydantic schemas
│   ├── tasks/                # Celery tasks
│   ├── services/             # Business logic
│   ├── websocket/            # WebSocket handlers
│   ├── main.py               # FastAPI app
│   ├── database.py           # Database config
│   └── celery_config.py      # Celery config
│
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── pages/            # Page components
│   │   ├── components/       # Reusable components
│   │   ├── stores/           # Zustand state management
│   │   ├── hooks/            # Custom React hooks
│   │   ├── api/              # API client
│   │   └── types/            # TypeScript types
│   ├── package.json
│   └── vite.config.ts
│
├── src/voice_to_slide/       # Core modules (unchanged)
├── storage/                  # File storage (created automatically)
│   ├── uploads/              # Uploaded audio files
│   ├── workspace/            # Temporary working files
│   └── outputs/              # Generated PPTX files
│
├── docker-compose.yml        # Docker Compose configuration
├── .env.example              # Environment variables template
└── WEB_UI_DESIGN_PLAN.md     # Complete design documentation
```

## API Endpoints

### Generation

- `POST /api/v1/generate` - Upload audio and start generation
- `GET /api/v1/jobs/{job_id}` - Get job status
- `DELETE /api/v1/jobs/{job_id}` - Cancel/delete job

### Interactive Mode

- `POST /api/v1/jobs/{job_id}/edit-structure` - Submit feedback
- `POST /api/v1/jobs/{job_id}/confirm-generation` - Confirm and start PPTX generation

### Download

- `GET /api/v1/download/{job_id}` - Download PPTX
- `GET /api/v1/download/{job_id}/transcription` - Download transcription JSON
- `GET /api/v1/preview/{job_id}/slide/{slide_number}` - Preview slide image

### Configuration

- `GET /api/v1/themes` - List available themes
- `POST /api/v1/check-config` - Check API configuration

### WebSocket

- `WS /ws/{job_id}` - Real-time progress updates

## User Flows

### 1. Quick Generation (Non-Interactive)

1. Upload audio file on homepage
2. Select theme and options
3. Click "Generate Presentation"
4. View real-time progress
5. Download PPTX when complete

### 2. Interactive Generation

1. Upload audio file with "Interactive mode" enabled
2. Wait for structure analysis
3. Review generated structure
4. Provide feedback to edit structure (e.g., "Change slide 2 title to...")
5. Repeat editing as needed
6. Click "Confirm & Generate PPTX"
7. Download final presentation

## Development

### Backend Development

```bash
# Run API with auto-reload
uv run uvicorn api.main:app --reload

# Run tests (when available)
uv run pytest

# Format code
uv run black api/
uv run ruff check api/
```

### Frontend Development

```bash
cd frontend

# Start dev server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint
```

### Database Migrations (Future)

```bash
# Install Alembic
uv add alembic

# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head
```

## Troubleshooting

### "Connection refused" errors

- Ensure PostgreSQL and Redis are running
- Check `DATABASE_URL` and `REDIS_URL` in `.env`
- For Docker: ensure services are started (`docker-compose ps`)

### Celery workers not processing jobs

- Check worker logs: `docker-compose logs worker-transcription`
- Ensure Redis is accessible
- Verify API keys in `.env`

### Frontend can't connect to backend

- Ensure API is running on port 8000
- Check CORS settings in `api/main.py`
- Verify `VITE_API_URL` and `VITE_WS_URL` in frontend

### Playwright browser not found

```bash
# Install Chromium
uv run playwright install chromium

# Or in Docker, rebuild the generation worker
docker-compose build worker-generation
```

### Database tables not created

```bash
# Manually initialize database
uv run python -c "from api.database import init_db; init_db()"
```

## Production Deployment

See `WEB_UI_DESIGN_PLAN.md` for detailed production deployment instructions, including:

- VPS deployment with Nginx
- Kubernetes deployment
- S3 storage integration
- Monitoring and logging setup

## Key Features

- ✅ Drag-and-drop file upload
- ✅ Real-time progress updates via WebSocket
- ✅ Interactive structure editing with AI
- ✅ 5 professional themes
- ✅ Image fetching from Unsplash
- ✅ Multi-user support with session isolation
- ✅ PPTX download with preview
- ✅ Transcription export

## Cost Estimates

**Per presentation (9 slides):**
- Transcription: ~$0.01-0.05
- Structure analysis: ~$0.01-0.02
- HTML generation: ~$0.02-0.03
- Interactive editing (5 feedbacks): ~$0.004
- **Total: ~$0.04-0.10**

**Infrastructure (Phase 1 - VPS):**
- ~$11/month

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Review the design plan: `WEB_UI_DESIGN_PLAN.md`
3. Open an issue on GitHub

## Next Steps

1. ✅ Basic API and frontend setup complete
2. 🚧 TODO: Add authentication (Phase 2)
3. 🚧 TODO: Migrate to S3 storage (Phase 2)
4. 🚧 TODO: Add slide preview carousel
5. 🚧 TODO: Implement rate limiting
6. 🚧 TODO: Add monitoring and analytics

## License

Same as main project
