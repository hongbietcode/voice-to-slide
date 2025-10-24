# Voice-to-Slide Web UI - Design & Implementation Plan

**Document Version:** 1.0
**Date:** October 25, 2025
**Status:** Design Phase

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [System Architecture](#system-architecture)
5. [Database Design](#database-design)
6. [API Design](#api-design)
7. [Frontend Design](#frontend-design)
8. [Background Job Processing](#background-job-processing)
9. [File Storage Strategy](#file-storage-strategy)
10. [Security Considerations](#security-considerations)
11. [Deployment Architecture](#deployment-architecture)
12. [Implementation Roadmap](#implementation-roadmap)
13. [Cost Analysis](#cost-analysis)

---

## 1. Executive Summary

### Current State
Voice-to-Slide is a Python CLI application that converts audio recordings into PowerPoint presentations using:
- Audio transcription (Soniox API)
- AI structure analysis (Claude Tool Use)
- Interactive feedback loop (optional)
- HTML generation with themes (Claude Messages API)
- Browser rendering (Playwright)
- PPTX assembly (python-pptx)

### Goal
Transform the CLI application into a modern web application with:
- User-friendly web interface
- Real-time progress updates
- Multi-user support
- Cloud-based deployment
- Enhanced user experience with preview capabilities

### Key Requirements
1. **Preserve Core Logic**: Keep all existing modules unchanged
2. **Async Processing**: Handle long-running operations (5-10 minutes)
3. **Real-time Updates**: WebSocket-based progress tracking
4. **Multi-user Support**: Session isolation and concurrent processing
5. **Scalability**: Handle 10-100 concurrent users initially
6. **Professional UI**: Modern, responsive design with preview capabilities

---

## 2. Architecture Overview

### Architecture Pattern: **Microservices-Lite with Monolithic Core**

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                       │
│  React/Vue.js SPA + WebSocket Client + File Upload         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│         FastAPI REST API + WebSocket Server                  │
└─────────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Business Logic Layer   │  │   Background Job Layer   │
│  (Existing Core Modules) │  │   Redis + Celery/RQ      │
│  - Transcriber           │  │   - Job Queue            │
│  - Orchestrator          │  │   - Task Workers         │
│  - HTML Generator        │  │   - Progress Tracking    │
│  - Image Fetcher         │  │                          │
│  - Structure Editor      │  │                          │
└──────────────────────────┘  └──────────────────────────┘
                 │                         │
                 └────────────┬────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Persistence Layer                         │
│  PostgreSQL (metadata) + File Storage (S3/local)            │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Separation of Concerns**
   - Frontend: User interface and interaction
   - API Layer: Request handling, validation, routing
   - Business Logic: Existing core modules (unchanged)
   - Background Jobs: Long-running async operations
   - Persistence: Data storage and retrieval

2. **Minimal Refactoring**
   - Keep all existing `voice_to_slide/*` modules as-is
   - Create new `api/` and `frontend/` directories
   - Wrap existing logic with API layer

3. **Progressive Enhancement**
   - Phase 1: Basic API + simple UI
   - Phase 2: Interactive feedback loop
   - Phase 3: Advanced features (collaboration, templates, etc.)

---

## 3. Technology Stack

### Backend Stack

#### Primary Framework: **FastAPI**
**Rationale:**
- ✅ Native async/await support (Python 3.8+)
- ✅ Built-in WebSocket support
- ✅ Automatic OpenAPI documentation
- ✅ High performance (comparable to Node.js)
- ✅ Easy integration with existing Python modules
- ✅ Excellent type hints and validation (Pydantic)

**Alternative Considered:** Flask + Flask-SocketIO
- ❌ Less performant for async operations
- ❌ More complex WebSocket setup
- ✅ More mature ecosystem

**Decision:** FastAPI for better async support and WebSocket integration

#### Job Queue: **Celery + Redis**
**Rationale:**
- ✅ Industry standard for Python background jobs
- ✅ Robust task management (retry, timeout, chaining)
- ✅ Built-in progress tracking
- ✅ Distributed worker support (horizontal scaling)
- ✅ Integration with FastAPI via `celery-fastapi`

**Alternative Considered:** Python-RQ
- ✅ Simpler setup
- ❌ Less feature-rich (no retries, canvas, chaining)
- ❌ Not designed for long-running tasks

**Decision:** Celery for production-grade features

#### Database: **PostgreSQL + SQLAlchemy**
**Rationale:**
- ✅ Reliable, production-ready
- ✅ JSON support for storing structure data
- ✅ Full-text search for transcriptions
- ✅ SQLAlchemy 2.0 async support
- ✅ Easy migration path (Alembic)

**Alternative Considered:** MongoDB
- ❌ Overkill for structured data
- ❌ Less mature Python async support

**Decision:** PostgreSQL for reliability and SQL features

#### Cache/Message Broker: **Redis**
**Rationale:**
- ✅ Required for Celery
- ✅ Session storage
- ✅ Rate limiting
- ✅ WebSocket pub/sub for real-time updates

#### File Storage: **Local Filesystem (Phase 1) → S3 (Phase 2)**
**Rationale:**
- Phase 1: Local storage for MVP (simpler deployment)
- Phase 2: S3 for scalability and CDN delivery

---

### Frontend Stack

#### Framework: **React 18 + TypeScript**
**Rationale:**
- ✅ Component-based architecture
- ✅ Large ecosystem (libraries for file upload, drag-drop, etc.)
- ✅ Strong TypeScript support
- ✅ Excellent WebSocket libraries (socket.io-client, react-use-websocket)
- ✅ Wide talent pool

**Alternative Considered:** Vue.js 3
- ✅ Simpler learning curve
- ❌ Smaller ecosystem

**Decision:** React for ecosystem and developer availability

#### UI Framework: **Tailwind CSS + shadcn/ui**
**Rationale:**
- ✅ Utility-first CSS (fast prototyping)
- ✅ shadcn/ui provides accessible, customizable components
- ✅ Modern, professional look
- ✅ Responsive by default

**Alternative Considered:** Material UI
- ❌ Heavier bundle size
- ❌ Less customizable without theme overrides

**Decision:** Tailwind + shadcn for flexibility and performance

#### State Management: **Zustand**
**Rationale:**
- ✅ Lightweight (1KB)
- ✅ Simple API (no boilerplate)
- ✅ TypeScript-first
- ✅ Sufficient for moderate complexity

**Alternative Considered:** Redux Toolkit
- ❌ More boilerplate
- ❌ Overkill for this project

**Decision:** Zustand for simplicity

#### File Upload: **react-dropzone + tus (resumable uploads)**
**Rationale:**
- ✅ Drag-and-drop support
- ✅ Resumable uploads for large audio files (tus protocol)
- ✅ Progress tracking

#### Real-time Communication: **Socket.IO (client + server)**
**Rationale:**
- ✅ Automatic reconnection
- ✅ Fallback to polling if WebSocket unavailable
- ✅ Room-based broadcasting (per-user updates)
- ✅ FastAPI integration via `python-socketio`

---

### DevOps & Infrastructure

#### Containerization: **Docker + Docker Compose**
**Rationale:**
- ✅ Consistent development/production environments
- ✅ Easy local setup for contributors
- ✅ Playwright Chromium isolation

#### CI/CD: **GitHub Actions**
**Rationale:**
- ✅ Free for public repos
- ✅ Native GitHub integration
- ✅ Easy testing and deployment automation

#### Deployment Options:
1. **Phase 1 (MVP):** Single VPS (DigitalOcean, Hetzner)
   - Docker Compose with all services
   - Nginx reverse proxy
   - ~$20-40/month for 4GB RAM + 2 vCPU

2. **Phase 2 (Scale):** Kubernetes or managed services
   - API: Cloud Run / ECS Fargate (auto-scaling)
   - Workers: Celery on EC2/Compute Engine
   - Database: Managed PostgreSQL (RDS/Cloud SQL)
   - Storage: S3/GCS
   - ~$100-300/month depending on usage

---

## 4. System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER BROWSER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Upload Page  │  │ Progress Page│  │ Result Page  │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│         │                  │                  │                      │
│         │ HTTP POST        │ WebSocket        │ HTTP GET            │
│         │ (audio file)     │ (progress)       │ (download)          │
└─────────┴──────────────────┴──────────────────┴──────────────────────┘
                    │                  │                  │
┌───────────────────┴──────────────────┴──────────────────┴────────────┐
│                        FASTAPI SERVER (API LAYER)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  REST API    │  │  WebSocket   │  │ Static Files │               │
│  │  Endpoints   │  │  Handler     │  │  Serving     │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│         │                  │                                          │
│         ▼                  ▼                                          │
│  ┌──────────────────────────────────────────────────┐               │
│  │           Session Manager & Job Tracker          │               │
│  └──────────────────────────────────────────────────┘               │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│    CELERY WORKERS        │  │    REDIS                 │
│  ┌────────────────────┐  │  │  - Job Queue            │
│  │ Transcription Task │  │  │  - Session Storage      │
│  ├────────────────────┤  │  │  - Progress Cache       │
│  │ Analysis Task      │  │  │  - WebSocket Pub/Sub    │
│  ├────────────────────┤  │  └──────────────────────────┘
│  │ Generation Task    │  │
│  └────────────────────┘  │
│         │                │
│         ▼                │
│  ┌────────────────────┐  │
│  │ Core Modules       │  │
│  │ (voice_to_slide/*) │  │
│  └────────────────────┘  │
└──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────┐
│              PERSISTENCE LAYER                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ PostgreSQL │  │ File System│  │ S3 Storage │    │
│  │ (metadata) │  │ (temp)     │  │ (permanent)│    │
│  └────────────┘  └────────────┘  └────────────┘    │
└──────────────────────────────────────────────────────┘
```

### Data Flow - Generation Process

```
1. User uploads audio file
   → POST /api/generate
   → Save file to temp storage
   → Create job in database
   → Enqueue Celery task
   → Return job_id

2. Celery worker starts
   → Update status: "transcribing"
   → Call AudioTranscriber.transcribe()
   → Emit progress via WebSocket (10%)
   → Save transcription to DB

3. Structure analysis
   → Update status: "analyzing"
   → Call PresentationOrchestrator.analyze_and_structure()
   → Emit progress via WebSocket (30%)
   → Save structure to DB

4. User feedback loop (if interactive mode)
   → Frontend displays structure preview
   → User submits feedback
   → POST /api/edit-structure
   → Call StructureEditor.edit_structure()
   → Return updated structure
   → Repeat until user confirms

5. PPTX generation
   → User confirms (or auto-confirm if non-interactive)
   → POST /api/confirm-generation
   → Enqueue generation task
   → Update status: "generating"

6. Generation task
   → Fetch images (40%)
   → Generate HTML slides (60%)
   → Render HTML to PNG (80%)
   → Assemble PPTX (90%)
   → Upload to storage (95%)
   → Update status: "completed"
   → Emit completion via WebSocket (100%)

7. User downloads result
   → GET /api/download/{job_id}
   → Stream PPTX file
   → Optional: Delete temp files after 24h
```

---

## 5. Database Design

### Schema Design (PostgreSQL)

#### Table: `users` (Phase 2 - Authentication)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `jobs`
```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE, -- NULL for anonymous users

    -- Job metadata
    status VARCHAR(50) NOT NULL, -- pending, transcribing, analyzing, editing, generating, completed, failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Input data
    audio_filename VARCHAR(255) NOT NULL,
    audio_file_path VARCHAR(500) NOT NULL,
    audio_file_size_mb DECIMAL(10, 2),
    audio_duration_seconds INTEGER,

    -- Configuration
    theme VARCHAR(100) DEFAULT 'Modern Professional',
    include_images BOOLEAN DEFAULT TRUE,
    interactive_mode BOOLEAN DEFAULT FALSE,

    -- Processing results
    transcription_text TEXT,
    transcription_json JSONB, -- Full transcription with timestamps
    structure JSONB, -- Presentation structure
    image_data JSONB, -- Array of image metadata

    -- Output files
    html_files JSONB, -- Array of HTML file paths
    image_files JSONB, -- Array of PNG file paths
    pptx_file_path VARCHAR(500),
    pptx_file_size_mb DECIMAL(10, 2),

    -- Progress tracking
    progress_percentage INTEGER DEFAULT 0,
    current_step VARCHAR(100),
    error_message TEXT,

    -- Statistics
    total_slides INTEGER,
    images_fetched INTEGER,
    processing_time_seconds INTEGER,

    -- Indexes
    INDEX idx_jobs_status (status),
    INDEX idx_jobs_user_id (user_id),
    INDEX idx_jobs_created_at (created_at)
);
```

#### Table: `feedback_sessions` (for interactive mode)
```sql
CREATE TABLE feedback_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,

    -- Session data
    session_started_at TIMESTAMP DEFAULT NOW(),
    session_ended_at TIMESTAMP,
    feedback_count INTEGER DEFAULT 0,

    -- Structure history
    initial_structure JSONB NOT NULL,
    final_structure JSONB,

    INDEX idx_feedback_job_id (job_id)
);
```

#### Table: `feedback_edits`
```sql
CREATE TABLE feedback_edits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES feedback_sessions(id) ON DELETE CASCADE,

    -- Edit details
    edit_number INTEGER NOT NULL,
    user_feedback TEXT NOT NULL,
    previous_structure JSONB NOT NULL,
    updated_structure JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    -- AI usage tracking
    prompt_tokens_used INTEGER,
    cache_read_tokens INTEGER,
    cache_creation_tokens INTEGER,

    INDEX idx_feedback_session_id (session_id)
);
```

#### Table: `api_usage` (cost tracking)
```sql
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,

    -- API details
    api_provider VARCHAR(50) NOT NULL, -- soniox, anthropic, unsplash
    api_operation VARCHAR(100) NOT NULL, -- transcribe, analyze, generate_html, fetch_images
    created_at TIMESTAMP DEFAULT NOW(),

    -- Usage metrics
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 4),
    duration_seconds INTEGER,

    INDEX idx_api_usage_job_id (job_id),
    INDEX idx_api_usage_provider (api_provider)
);
```

---

## 6. API Design

### REST API Endpoints

#### Base URL: `/api/v1`

---

### 6.1 Job Management

#### `POST /api/v1/generate`
**Description:** Start a new presentation generation job

**Request:**
```json
Content-Type: multipart/form-data

{
  "audio_file": <file>, // Required: Audio file (mp3, wav, m4a)
  "theme": "Modern Professional", // Optional: Default "Modern Professional"
  "include_images": true, // Optional: Default true
  "interactive_mode": false, // Optional: Default false
  "save_transcription": true // Optional: Default true
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "message": "Job created successfully",
  "estimated_time_seconds": 300
}
```

**Errors:**
- `400 Bad Request`: Invalid file format, file too large (>100MB)
- `413 Payload Too Large`: File exceeds size limit
- `500 Internal Server Error`: Server error

---

#### `GET /api/v1/jobs/{job_id}`
**Description:** Get job status and metadata

**Response (200 OK):**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "analyzing", // pending, transcribing, analyzing, editing, generating, completed, failed
  "progress_percentage": 30,
  "current_step": "Analyzing presentation structure",
  "created_at": "2025-10-25T12:00:00Z",
  "updated_at": "2025-10-25T12:02:30Z",

  // Available after transcription
  "transcription_preview": "First 500 characters of transcription...",

  // Available after analysis
  "structure": {
    "title": "Presentation Title",
    "slides": [...]
  },

  // Available after completion
  "pptx_file_url": "/api/v1/download/123e4567-e89b-12d3-a456-426614174000",
  "total_slides": 9,
  "images_fetched": 8,
  "processing_time_seconds": 287,

  // Error details (if failed)
  "error_message": "Transcription failed: API timeout"
}
```

**Errors:**
- `404 Not Found`: Job ID not found

---

#### `DELETE /api/v1/jobs/{job_id}`
**Description:** Cancel a running job or delete completed job data

**Response (200 OK):**
```json
{
  "message": "Job cancelled successfully"
}
```

**Errors:**
- `404 Not Found`: Job ID not found
- `409 Conflict`: Job already completed (cannot cancel)

---

### 6.2 Interactive Feedback Loop

#### `POST /api/v1/jobs/{job_id}/edit-structure`
**Description:** Submit feedback to edit presentation structure (interactive mode only)

**Request:**
```json
{
  "feedback": "Change slide 2 title to 'Introduction to AI' and add a bullet point about machine learning"
}
```

**Response (200 OK):**
```json
{
  "updated_structure": {
    "title": "Presentation Title",
    "slides": [...]
  },
  "edit_number": 3,
  "message": "Structure updated successfully"
}
```

**Errors:**
- `400 Bad Request`: Job not in interactive mode or not in editing phase
- `404 Not Found`: Job ID not found

---

#### `POST /api/v1/jobs/{job_id}/confirm-generation`
**Description:** Confirm structure and start PPTX generation (interactive mode only)

**Response (202 Accepted):**
```json
{
  "message": "PPTX generation started",
  "status": "generating"
}
```

**Errors:**
- `400 Bad Request`: Job not in editing phase
- `404 Not Found`: Job ID not found

---

### 6.3 File Operations

#### `GET /api/v1/download/{job_id}`
**Description:** Download the generated PPTX file

**Response (200 OK):**
```
Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation
Content-Disposition: attachment; filename="presentation.pptx"

<binary PPTX data>
```

**Errors:**
- `404 Not Found`: Job not found or PPTX not ready
- `410 Gone`: File expired (after 24h)

---

#### `GET /api/v1/download/{job_id}/transcription`
**Description:** Download transcription JSON

**Response (200 OK):**
```json
{
  "text": "Full transcription text...",
  "words": [
    {"text": "Hello", "start_time": 0.0, "end_time": 0.5},
    ...
  ],
  "audio_file": "recording.mp3",
  "file_size_mb": 5.2
}
```

---

#### `GET /api/v1/preview/{job_id}/slide/{slide_number}`
**Description:** Preview individual slide as PNG image

**Response (200 OK):**
```
Content-Type: image/png

<binary PNG data>
```

---

### 6.4 Configuration

#### `GET /api/v1/themes`
**Description:** List available themes

**Response (200 OK):**
```json
{
  "themes": [
    {
      "name": "Modern Professional",
      "description": "Clean design with blue accents",
      "preview_url": "/api/v1/theme-previews/modern-professional.png"
    },
    {
      "name": "Dark Mode",
      "description": "Dark background with neon highlights",
      "preview_url": "/api/v1/theme-previews/dark-mode.png"
    },
    ...
  ]
}
```

---

#### `POST /api/v1/check-config`
**Description:** Verify API keys and configuration (admin endpoint)

**Response (200 OK):**
```json
{
  "soniox_configured": true,
  "anthropic_configured": true,
  "unsplash_configured": true,
  "playwright_installed": true
}
```

---

### 6.5 WebSocket Events

#### Connection: `ws://api.example.com/ws/{job_id}`

**Client → Server:**
```json
{
  "type": "subscribe",
  "job_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Server → Client (Progress Updates):**
```json
{
  "type": "progress",
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "transcribing",
  "progress_percentage": 15,
  "current_step": "Transcribing audio...",
  "timestamp": "2025-10-25T12:01:30Z"
}
```

**Server → Client (Structure Ready - Interactive Mode):**
```json
{
  "type": "structure_ready",
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "structure": {
    "title": "Presentation Title",
    "slides": [...]
  },
  "message": "Structure analysis complete. You can now provide feedback or confirm to generate."
}
```

**Server → Client (Completion):**
```json
{
  "type": "completed",
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "pptx_file_url": "/api/v1/download/123e4567-e89b-12d3-a456-426614174000",
  "total_slides": 9,
  "processing_time_seconds": 287
}
```

**Server → Client (Error):**
```json
{
  "type": "error",
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "error_message": "Transcription failed: API timeout",
  "error_code": "TRANSCRIPTION_TIMEOUT"
}
```

---

## 7. Frontend Design

### 7.1 User Flows

#### Flow 1: Quick Generation (Non-Interactive)

```
┌─────────────────┐
│  Upload Page    │
│  - Drop audio   │
│  - Select theme │
│  - Options      │
└────────┬────────┘
         │ Click "Generate"
         ▼
┌─────────────────┐
│ Progress Page   │
│  - Progress bar │
│  - Current step │
│  - Logs         │
└────────┬────────┘
         │ Wait (auto-redirect)
         ▼
┌─────────────────┐
│  Result Page    │
│  - Slide preview│
│  - Download btn │
│  - Share link   │
└─────────────────┘
```

#### Flow 2: Interactive Generation

```
┌─────────────────┐
│  Upload Page    │
│  - Drop audio   │
│  - [✓] Interactive │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Progress Page   │
│ (Transcription) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Editor Page    │
│  - Structure    │
│  - Feedback box │
│  - Preview      │
└────────┬────────┘
         │ User edits
         │ (loop: feedback → updated preview)
         │
         │ Click "Generate PPTX"
         ▼
┌─────────────────┐
│ Progress Page   │
│ (Generation)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Result Page    │
└─────────────────┘
```

---

### 7.2 Page Designs

#### Page 1: Upload Page (`/`)

**Layout:**
```
╔════════════════════════════════════════════════╗
║  Voice-to-Slide Generator              [About]║
╠════════════════════════════════════════════════╣
║                                                ║
║   ┌──────────────────────────────────────┐   ║
║   │  🎤 Drop audio file here             │   ║
║   │     or click to browse               │   ║
║   │                                      │   ║
║   │  Supported: MP3, WAV, M4A (max 100MB)│   ║
║   └──────────────────────────────────────┘   ║
║                                                ║
║   ┌─ Configuration ──────────────────────┐   ║
║   │                                      │   ║
║   │  Theme:  [Modern Professional ▼]    │   ║
║   │                                      │   ║
║   │  [✓] Include images from Unsplash   │   ║
║   │  [✓] Save transcription             │   ║
║   │  [ ] Interactive mode (edit before  │   ║
║   │      generating)                     │   ║
║   │                                      │   ║
║   │       [Generate Presentation]        │   ║
║   └──────────────────────────────────────┘   ║
║                                                ║
║   💡 Tips:                                    ║
║   • Clear audio improves transcription       ║
║   • Processing takes 5-10 minutes            ║
║   • Interactive mode lets you edit structure ║
╚════════════════════════════════════════════════╝
```

**Key Components:**
- File dropzone (react-dropzone)
- Theme selector dropdown
- Checkbox options
- Submit button (disabled until file uploaded)

---

#### Page 2: Progress Page (`/job/{job_id}`)

**Layout:**
```
╔════════════════════════════════════════════════╗
║  Generating Presentation...            [Cancel]║
╠════════════════════════════════════════════════╣
║                                                ║
║   ████████████████░░░░░░░░░░  60%            ║
║                                                ║
║   Current Step:                               ║
║   🎨 Generating HTML slides...                ║
║                                                ║
║   ┌─ Progress Timeline ───────────────────┐  ║
║   │ ✓ Audio uploaded (0:00)              │  ║
║   │ ✓ Transcription complete (2:15)      │  ║
║   │ ✓ Structure analyzed (2:45)          │  ║
║   │ ● Generating slides... (3:10)        │  ║
║   │ ○ Rendering images                   │  ║
║   │ ○ Assembling PPTX                    │  ║
║   └──────────────────────────────────────┘  ║
║                                                ║
║   📊 Details:                                 ║
║   • Audio: recording.mp3 (5.2 MB)            ║
║   • Theme: Modern Professional                ║
║   • Estimated time: 2 minutes remaining       ║
║                                                ║
╚════════════════════════════════════════════════╝
```

**Key Components:**
- Progress bar (animated)
- Real-time status updates (WebSocket)
- Timeline with completed/current/pending steps
- Cancel button

---

#### Page 3: Editor Page (`/job/{job_id}/edit`) - Interactive Mode Only

**Layout:**
```
╔════════════════════════════════════════════════╗
║  Edit Presentation Structure       [Generate] ║
╠════════════════════════════════════════════════╣
║  ┌─ Structure Preview ───┐  ┌─ Feedback ───┐ ║
║  │                        │  │               │ ║
║  │ Title: AI in 2025     │  │ 💬 Provide    │ ║
║  │                        │  │ feedback to   │ ║
║  │ Slide 1: Introduction │  │ edit:         │ ║
║  │  • Point 1            │  │               │ ║
║  │  • Point 2            │  │ [Text area]   │ ║
║  │  Image: "AI tech"     │  │               │ ║
║  │                        │  │               │ ║
║  │ Slide 2: Applications │  │               │ ║
║  │  • Healthcare         │  │               │ ║
║  │  • Finance            │  │               │ ║
║  │  Image: "hospital"    │  │  [Submit]     │ ║
║  │                        │  │               │ ║
║  │ Slide 3: Challenges   │  │ Examples:     │ ║
║  │  • Ethics             │  │ • "Add slide" │ ║
║  │  • Bias               │  │ • "Change     │ ║
║  │  Image: "balance"     │  │    title"     │ ║
║  │                        │  │ • "Remove     │ ║
║  │ ...                    │  │    slide 3"   │ ║
║  │                        │  │               │ ║
║  └────────────────────────┘  └───────────────┘ ║
╚════════════════════════════════════════════════╝
```

**Key Components:**
- Structure preview (collapsible sections)
- Feedback textarea with examples
- Submit button (triggers AI editing)
- Generate PPTX button (confirms structure)

---

#### Page 4: Result Page (`/job/{job_id}/result`)

**Layout:**
```
╔════════════════════════════════════════════════╗
║  ✅ Presentation Ready!                  [Home]║
╠════════════════════════════════════════════════╣
║                                                ║
║   📄 presentation_20251025.pptx (15.3 MB)     ║
║                                                ║
║   ┌──────────────────────────────────────┐   ║
║   │  [⬇ Download PPTX]  [📋 Copy Link]  │   ║
║   └──────────────────────────────────────┘   ║
║                                                ║
║   ┌─ Slide Preview ──────────────────────┐   ║
║   │  [< Prev]  Slide 1/9  [Next >]       │   ║
║   │                                      │   ║
║   │  ┌────────────────────────────────┐ │   ║
║   │  │  [Slide image thumbnail]       │ │   ║
║   │  │                                │ │   ║
║   │  └────────────────────────────────┘ │   ║
║   └──────────────────────────────────────┘   ║
║                                                ║
║   📊 Statistics:                              ║
║   • Total slides: 9                           ║
║   • Images: 8/8 fetched                       ║
║   • Processing time: 4 minutes 47 seconds     ║
║                                                ║
║   💾 Also Available:                          ║
║   • [Download Transcription (JSON)]           ║
║                                                ║
╚════════════════════════════════════════════════╝
```

**Key Components:**
- Download button
- Copy shareable link button
- Slide preview carousel
- Statistics summary
- Optional transcription download

---

### 7.3 Component Hierarchy

```
App
├── Layout
│   ├── Header
│   │   ├── Logo
│   │   └── Navigation
│   └── Footer
│
├── Pages
│   ├── UploadPage
│   │   ├── FileDropzone
│   │   ├── ConfigurationForm
│   │   │   ├── ThemeSelector
│   │   │   ├── CheckboxOptions
│   │   │   └── SubmitButton
│   │   └── TipsSection
│   │
│   ├── ProgressPage
│   │   ├── ProgressBar
│   │   ├── StatusDisplay
│   │   ├── Timeline
│   │   └── CancelButton
│   │
│   ├── EditorPage (interactive mode)
│   │   ├── StructurePreview
│   │   │   └── SlideCard (repeated)
│   │   ├── FeedbackPanel
│   │   │   ├── FeedbackTextarea
│   │   │   ├── SubmitButton
│   │   │   └── ExamplesSection
│   │   └── ConfirmButton
│   │
│   └── ResultPage
│       ├── DownloadSection
│       ├── SlidePreview
│       │   └── ImageCarousel
│       ├── StatisticsSection
│       └── AdditionalDownloads
│
└── Shared Components
    ├── Modal
    ├── Spinner
    ├── Alert
    └── WebSocketProvider
```

---

### 7.4 State Management (Zustand)

```typescript
// stores/jobStore.ts
interface JobStore {
  // Current job state
  currentJob: Job | null;
  jobStatus: JobStatus;
  progressPercentage: number;
  currentStep: string;

  // Structure editing (interactive mode)
  structure: PresentationStructure | null;
  isEditing: boolean;
  feedbackHistory: FeedbackEdit[];

  // Actions
  setCurrentJob: (job: Job) => void;
  updateProgress: (percentage: number, step: string) => void;
  updateStructure: (structure: PresentationStructure) => void;
  addFeedback: (feedback: FeedbackEdit) => void;
  resetJob: () => void;
}

// stores/configStore.ts
interface ConfigStore {
  // Configuration
  theme: string;
  includeImages: boolean;
  saveTranscription: boolean;
  interactiveMode: boolean;

  // Available options
  availableThemes: Theme[];

  // Actions
  setTheme: (theme: string) => void;
  toggleImages: () => void;
  toggleInteractive: () => void;
  loadThemes: () => Promise<void>;
}

// stores/wsStore.ts
interface WebSocketStore {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  connect: (jobId: string) => void;
  disconnect: () => void;
}
```

---

### 7.5 Key Libraries

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.2",
    "socket.io-client": "^4.7.2",
    "react-dropzone": "^14.2.3",
    "react-use-websocket": "^4.5.0",
    "@tanstack/react-query": "^5.14.2",
    "tailwindcss": "^3.3.6",
    "@radix-ui/react-*": "^1.0.0", // shadcn/ui primitives
    "lucide-react": "^0.294.0", // Icons
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "typescript": "^5.3.3",
    "vite": "^5.0.7",
    "@vitejs/plugin-react": "^4.2.1"
  }
}
```

---

## 8. Background Job Processing

### 8.1 Celery Task Structure

```python
# api/tasks/generation_tasks.py

from celery import Task, chain, group
from voice_to_slide import (
    AudioTranscriber,
    PresentationOrchestrator,
    ImageFetcher,
    HTMLSlideGenerator,
    HTMLToImageConverter,
    HTMLToPPTXConverter,
)

@celery_app.task(bind=True, max_retries=3)
def transcribe_audio_task(self, job_id: str, audio_path: str):
    """Step 1: Transcribe audio"""
    try:
        # Update job status
        update_job_status(job_id, "transcribing", 10)
        emit_progress(job_id, "transcribing", 10, "Transcribing audio...")

        # Call existing module
        transcriber = AudioTranscriber(api_key=os.getenv("SONIOX_API_KEY"))
        result = transcriber.transcribe(audio_path)

        # Save to database
        save_transcription(job_id, result)

        # Update progress
        update_job_status(job_id, "analyzing", 25)
        emit_progress(job_id, "analyzing", 25, "Transcription complete")

        return {"job_id": job_id, "transcription": result}

    except Exception as e:
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        else:
            # Mark as failed
            update_job_status(job_id, "failed", error=str(e))
            emit_error(job_id, str(e))
            raise


@celery_app.task(bind=True)
def analyze_structure_task(self, job_id: str, transcription_text: str, use_images: bool):
    """Step 2: Analyze structure using Claude Tool Use"""
    try:
        update_job_status(job_id, "analyzing", 30)
        emit_progress(job_id, "analyzing", 30, "Analyzing content structure...")

        # Call existing module
        orchestrator = PresentationOrchestrator(
            api_key=os.getenv("CONTENT_ANTHROPIC_API_KEY")
        )
        result = orchestrator.analyze_and_structure(transcription_text, use_images)

        # Save structure to database
        save_structure(job_id, result["structure"])

        # Check if interactive mode
        job = get_job(job_id)
        if job.interactive_mode:
            # Emit structure_ready event
            update_job_status(job_id, "editing", 35)
            emit_structure_ready(job_id, result["structure"])
            # Wait for user confirmation (task pauses here)
            return {"job_id": job_id, "awaiting_confirmation": True}
        else:
            # Auto-confirm, proceed to generation
            update_job_status(job_id, "generating", 40)
            return {"job_id": job_id, "structure": result["structure"]}

    except Exception as e:
        update_job_status(job_id, "failed", error=str(e))
        emit_error(job_id, str(e))
        raise


@celery_app.task(bind=True)
def generate_presentation_task(self, job_id: str):
    """Step 3: Generate PPTX (after confirmation)"""
    try:
        job = get_job(job_id)
        structure = job.structure

        # Sub-step 1: Fetch images
        update_job_status(job_id, "generating", 45)
        emit_progress(job_id, "generating", 45, "Fetching images...")

        if job.include_images:
            fetcher = ImageFetcher(api_key=os.getenv("UNSPLASH_ACCESS_KEY"))
            image_queries = [slide.get("image_theme") for slide in structure["slides"]]
            image_data = fetcher.get_image_urls_for_presentation(image_queries)
            save_image_data(job_id, image_data)
        else:
            image_data = []

        # Sub-step 2: Generate HTML
        update_job_status(job_id, "generating", 60)
        emit_progress(job_id, "generating", 60, "Generating HTML slides...")

        generator = HTMLSlideGenerator(
            api_key=os.getenv("CONTENT_ANTHROPIC_API_KEY"),
            workspace_dir=f"/tmp/jobs/{job_id}"
        )
        html_files = generator.generate_slides_html(
            structure=structure,
            image_data=image_data,
            theme=job.theme,
            output_dir=f"/tmp/jobs/{job_id}/slides"
        )

        # Sub-step 3: Render to PNG
        update_job_status(job_id, "generating", 80)
        emit_progress(job_id, "generating", 80, "Rendering slides to images...")

        # (HTMLToPPTXConverter calls HTMLToImageConverter internally)

        # Sub-step 4: Assemble PPTX
        update_job_status(job_id, "generating", 90)
        emit_progress(job_id, "generating", 90, "Assembling PowerPoint...")

        output_path = f"/tmp/jobs/{job_id}/output.pptx"
        converter = HTMLToPPTXConverter()
        converter.convert_html_files_to_pptx(
            html_files=html_files,
            output_path=output_path,
            image_dir=f"/tmp/jobs/{job_id}/slide_images"
        )

        # Upload to storage (S3 in Phase 2)
        final_path = upload_file_to_storage(output_path, job_id)

        # Update job as completed
        update_job_status(job_id, "completed", 100)
        save_pptx_path(job_id, final_path)
        emit_completed(job_id, final_path)

        return {"job_id": job_id, "pptx_path": final_path}

    except Exception as e:
        update_job_status(job_id, "failed", error=str(e))
        emit_error(job_id, str(e))
        raise


# Task chain for non-interactive mode
def start_generation_pipeline(job_id: str, audio_path: str, use_images: bool):
    """Chain tasks together"""
    chain(
        transcribe_audio_task.s(job_id, audio_path),
        analyze_structure_task.s(job_id, use_images),
        generate_presentation_task.s(job_id)
    ).apply_async()
```

---

### 8.2 Celery Configuration

```python
# api/celery_config.py

from celery import Celery
from kombu import Exchange, Queue

celery_app = Celery("voice_to_slide")

celery_app.config_from_object({
    # Broker (Redis)
    "broker_url": "redis://localhost:6379/0",
    "result_backend": "redis://localhost:6379/0",

    # Task settings
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "UTC",
    "enable_utc": True,

    # Retry settings
    "task_acks_late": True,
    "task_reject_on_worker_lost": True,
    "task_time_limit": 3600,  # 1 hour max per task
    "task_soft_time_limit": 3300,  # 55 minutes soft limit

    # Queue settings
    "task_routes": {
        "api.tasks.generation_tasks.transcribe_audio_task": {"queue": "transcription"},
        "api.tasks.generation_tasks.analyze_structure_task": {"queue": "analysis"},
        "api.tasks.generation_tasks.generate_presentation_task": {"queue": "generation"},
    },

    # Concurrency
    "worker_prefetch_multiplier": 1,  # One task at a time per worker
    "worker_max_tasks_per_child": 10,  # Restart worker after 10 tasks (prevent memory leaks)
})
```

---

### 8.3 Worker Deployment

```bash
# Start workers for different queues

# Transcription queue (CPU-bound, 2 workers)
celery -A api.celery_config worker \
  --queue=transcription \
  --concurrency=2 \
  --loglevel=info \
  --logfile=/var/log/celery/transcription.log

# Analysis queue (API-bound, 4 workers)
celery -A api.celery_config worker \
  --queue=analysis \
  --concurrency=4 \
  --loglevel=info \
  --logfile=/var/log/celery/analysis.log

# Generation queue (Resource-intensive, 1 worker with Playwright)
celery -A api.celery_config worker \
  --queue=generation \
  --concurrency=1 \
  --loglevel=info \
  --logfile=/var/log/celery/generation.log
```

---

## 9. File Storage Strategy

### 9.1 Phase 1: Local Filesystem

```
/var/app/storage/
├── uploads/              # Uploaded audio files
│   └── {job_id}/
│       └── audio.mp3
│
├── workspace/            # Temporary processing files
│   └── {job_id}/
│       ├── slides/       # HTML files
│       │   ├── slide_00.html
│       │   ├── slide_01.html
│       │   └── ...
│       ├── slide_images/ # Rendered PNG files
│       │   ├── slide_00.png
│       │   └── ...
│       └── structure.json
│
└── outputs/              # Final PPTX files
    └── {job_id}/
        └── presentation.pptx
```

**Cleanup Policy:**
- Delete `workspace/{job_id}` after successful PPTX generation
- Delete `uploads/{job_id}` after 24 hours
- Delete `outputs/{job_id}` after 7 days (or when user downloads)

---

### 9.2 Phase 2: S3/Cloud Storage

```
s3://voice-to-slide-prod/
├── uploads/              # Temporary audio files
│   └── {job_id}/audio.mp3
│
├── outputs/              # Final PPTX files (permanent)
│   └── {job_id}/presentation.pptx
│
└── thumbnails/           # Slide preview images
    └── {job_id}/
        ├── slide_00.png
        └── ...
```

**Benefits:**
- Scalable storage
- CDN delivery for downloads
- Automatic expiration policies (S3 lifecycle rules)
- Multi-region redundancy

**Implementation:**
```python
# api/storage/s3_storage.py

import boto3
from botocore.exceptions import ClientError

class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv("S3_BUCKET_NAME")

    def upload_file(self, file_path: str, key: str) -> str:
        """Upload file to S3 and return public URL"""
        try:
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                key,
                ExtraArgs={"ContentType": self._get_content_type(file_path)}
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
        except ClientError as e:
            raise Exception(f"S3 upload failed: {e}")

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate temporary download URL"""
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': key},
            ExpiresIn=expiration
        )

    def delete_file(self, key: str):
        """Delete file from S3"""
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
```

---

## 10. Security Considerations

### 10.1 Input Validation

**Audio File Upload:**
- Maximum file size: 100MB
- Allowed formats: `.mp3`, `.wav`, `.m4a`, `.ogg`
- Virus scanning (ClamAV in production)
- Content-Type verification

**User Input:**
- Sanitize feedback text (prevent XSS)
- Validate theme names against whitelist
- Rate limiting: 5 requests per minute per IP

---

### 10.2 API Authentication (Phase 2)

**JWT-based authentication:**
```python
# api/auth/jwt.py

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv("JWT_SECRET"),
            algorithms=["HS256"]
        )
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Protected endpoint
@app.post("/api/v1/generate")
async def generate_presentation(
    file: UploadFile,
    user_id: str = Depends(verify_token)
):
    # Only authenticated users can generate
    ...
```

---

### 10.3 API Key Management

**Environment variables stored in:**
- Development: `.env` file
- Production: Kubernetes Secrets / AWS Secrets Manager

**Never expose:**
- Soniox API key
- Anthropic API key
- Unsplash API key
- Database credentials

**Client-side security:**
- No API keys in frontend code
- All API calls proxied through backend

---

### 10.4 File Access Control

**Prevent unauthorized access:**
- Generate unique, unpredictable job IDs (UUID v4)
- Check job ownership before serving files
- Use presigned URLs for temporary access

```python
@app.get("/api/v1/download/{job_id}")
async def download_pptx(job_id: str, user_id: str = Depends(verify_token)):
    job = get_job(job_id)

    # Check ownership (Phase 2)
    if job.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check expiration
    if job.expired:
        raise HTTPException(status_code=410, detail="File expired")

    return FileResponse(job.pptx_file_path)
```

---

## 11. Deployment Architecture

### 11.1 Development Environment (Docker Compose)

```yaml
# docker-compose.yml

version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: voice_to_slide
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis (Celery broker + cache)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # FastAPI Backend
  api:
    build:
      context: .
      dockerfile: api/Dockerfile
    env_file: .env
    volumes:
      - ./src:/app/src
      - ./storage:/app/storage
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker (Transcription)
  worker-transcription:
    build:
      context: .
      dockerfile: api/Dockerfile
    env_file: .env
    volumes:
      - ./storage:/app/storage
    depends_on:
      - db
      - redis
    command: celery -A api.celery_config worker --queue=transcription --concurrency=2 --loglevel=info

  # Celery Worker (Generation - with Playwright)
  worker-generation:
    build:
      context: .
      dockerfile: api/Dockerfile.playwright
    env_file: .env
    volumes:
      - ./storage:/app/storage
    depends_on:
      - db
      - redis
    command: celery -A api.celery_config worker --queue=generation --concurrency=1 --loglevel=info

  # Frontend (Vite dev server)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend/src:/app/src
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    command: npm run dev

volumes:
  postgres_data:
```

---

### 11.2 Production Deployment (VPS - Phase 1)

**Server Requirements:**
- 4GB RAM minimum (8GB recommended)
- 2 vCPU minimum (4 vCPU recommended)
- 50GB SSD storage
- Ubuntu 22.04 LTS

**Stack:**
```
Internet
   │
   ▼
┌─────────────────┐
│  Nginx (80/443) │  ← Reverse proxy + SSL (Let's Encrypt)
└─────────────────┘
   │
   ├──────────────────┐
   │                  │
   ▼                  ▼
┌─────────────┐  ┌─────────────┐
│ FastAPI     │  │ React SPA   │
│ (8000)      │  │ (static)    │
└─────────────┘  └─────────────┘
   │
   ├──────────────────┐
   │                  │
   ▼                  ▼
┌─────────────┐  ┌─────────────┐
│ PostgreSQL  │  │ Redis       │
│ (5432)      │  │ (6379)      │
└─────────────┘  └─────────────┘
   │
   ▼
┌─────────────────────────────┐
│ Celery Workers (background) │
│  - Transcription (×2)       │
│  - Generation (×1)          │
└─────────────────────────────┘
```

**Nginx Configuration:**
```nginx
# /etc/nginx/sites-available/voice-to-slide

upstream api_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name voice-to-slide.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name voice-to-slide.example.com;

    ssl_certificate /etc/letsencrypt/live/voice-to-slide.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/voice-to-slide.example.com/privkey.pem;

    # Frontend (React SPA)
    location / {
        root /var/www/voice-to-slide/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Large file upload support
        client_max_body_size 100M;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;  # 24 hours
    }
}
```

---

### 11.3 Production Deployment (Kubernetes - Phase 2)

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: voice-to-slide/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-generation
spec:
  replicas: 2
  selector:
    matchLabels:
      app: worker-generation
  template:
    metadata:
      labels:
        app: worker-generation
    spec:
      containers:
      - name: worker
        image: voice-to-slide/worker-playwright:latest
        command: ["celery", "-A", "api.celery_config", "worker", "--queue=generation"]
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

---

## 12. Implementation Roadmap

### Phase 1: MVP (4-6 weeks)

#### Week 1-2: Backend Foundation
- [ ] Set up FastAPI project structure
- [ ] Implement database models (SQLAlchemy)
- [ ] Create REST API endpoints (generate, status, download)
- [ ] Set up Celery + Redis for background jobs
- [ ] Wrap existing modules in Celery tasks
- [ ] Implement WebSocket server for progress updates
- [ ] Write unit tests for API endpoints

**Deliverables:**
- Working API that accepts audio files
- Background job processing with progress tracking
- Database storing job metadata

---

#### Week 3-4: Frontend Foundation
- [ ] Set up React + TypeScript + Vite project
- [ ] Implement Upload Page with file dropzone
- [ ] Implement Progress Page with WebSocket integration
- [ ] Implement Result Page with download functionality
- [ ] Create shared components (Header, Footer, Spinner, etc.)
- [ ] Set up Zustand state management
- [ ] Integrate with backend API

**Deliverables:**
- Working web UI for basic generation flow
- Real-time progress updates
- File download capability

---

#### Week 5: Integration & Testing
- [ ] End-to-end testing of full pipeline
- [ ] Error handling and retry logic
- [ ] File cleanup automation
- [ ] Performance testing (10 concurrent users)
- [ ] Bug fixes and polish

**Deliverables:**
- Stable MVP ready for internal testing

---

#### Week 6: Deployment & Documentation
- [ ] Create Docker Compose setup
- [ ] Write deployment documentation
- [ ] Deploy to VPS (staging environment)
- [ ] User acceptance testing
- [ ] Fix critical bugs

**Deliverables:**
- Deployed MVP on staging server
- Documentation for setup and usage

---

### Phase 2: Interactive Mode & Enhancements (3-4 weeks)

#### Week 7-8: Interactive Feedback Loop
- [ ] Implement Editor Page UI
- [ ] Add `/api/v1/jobs/{job_id}/edit-structure` endpoint
- [ ] Integrate `StructureEditor` with API
- [ ] Add feedback history tracking
- [ ] Implement confirmation flow
- [ ] Test prompt caching performance

**Deliverables:**
- Interactive mode fully functional
- Cost savings from prompt caching

---

#### Week 9: UI/UX Enhancements
- [ ] Add slide preview carousel
- [ ] Implement theme preview images
- [ ] Add transcription viewer
- [ ] Improve error messages and user feedback
- [ ] Add loading skeletons and animations
- [ ] Responsive design for mobile

**Deliverables:**
- Professional, polished UI
- Better user experience

---

#### Week 10: Optimization & Monitoring
- [ ] Add logging and monitoring (Sentry, Datadog)
- [ ] Optimize Playwright rendering (parallel batch processing)
- [ ] Implement rate limiting
- [ ] Add analytics tracking
- [ ] Performance optimization

**Deliverables:**
- Production-ready system with monitoring
- Optimized performance

---

### Phase 3: Advanced Features (4-6 weeks)

#### Week 11-12: User Authentication
- [ ] Implement JWT authentication
- [ ] Add user registration/login pages
- [ ] Create user dashboard (job history)
- [ ] Add user profile management
- [ ] Implement API key management UI

**Deliverables:**
- Multi-user support with authentication
- User dashboard

---

#### Week 13-14: Cloud Storage & CDN
- [ ] Migrate to S3 for file storage
- [ ] Implement presigned URLs for downloads
- [ ] Set up CloudFront CDN
- [ ] Add lifecycle policies for automatic cleanup
- [ ] Migrate existing files

**Deliverables:**
- Scalable cloud storage
- Faster file delivery via CDN

---

#### Week 15-16: Collaboration & Sharing
- [ ] Add shareable links for presentations
- [ ] Implement public/private visibility toggle
- [ ] Add commenting on slides
- [ ] Enable multiple users editing same structure
- [ ] Real-time collaboration via WebSocket

**Deliverables:**
- Collaboration features
- Shareable presentations

---

### Phase 4: Enterprise Features (Optional)

- [ ] Custom branding (logos, colors)
- [ ] Template library
- [ ] Batch processing (multiple audio files)
- [ ] API access for third-party integrations
- [ ] Webhooks for job completion notifications
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Voice cloning for narration

---

## 13. Cost Analysis

### 13.1 Infrastructure Costs

#### Phase 1 (MVP - VPS)
| Item | Provider | Specs | Monthly Cost |
|------|----------|-------|--------------|
| VPS | Hetzner | 4GB RAM, 2 vCPU, 80GB SSD | $10 |
| Domain | Namecheap | .com domain | $1 |
| SSL | Let's Encrypt | Free SSL certificate | $0 |
| **Total** | | | **$11/month** |

#### Phase 2 (Cloud - AWS)
| Item | Service | Specs | Monthly Cost |
|------|---------|-------|--------------|
| API | ECS Fargate | 3 tasks, 0.5 vCPU, 1GB RAM | $40 |
| Workers | EC2 | t3.medium (2 instances) | $60 |
| Database | RDS PostgreSQL | db.t3.small | $30 |
| Cache | ElastiCache Redis | cache.t3.micro | $15 |
| Storage | S3 | 100GB + requests | $5 |
| CDN | CloudFront | 500GB transfer | $50 |
| Load Balancer | ALB | 1 ALB | $20 |
| **Total** | | | **$220/month** |

---

### 13.2 API Usage Costs (per 100 presentations)

| API | Operation | Cost per 100 |
|-----|-----------|--------------|
| Soniox | Transcription (avg 5 min audio) | $5-10 |
| Anthropic | Structure analysis (5K tokens × 100) | $2 |
| Anthropic | HTML generation (15K tokens × 100) | $6 |
| Anthropic | Interactive editing (5 feedbacks avg) | $2 |
| Unsplash | Image URLs (free tier) | $0 |
| **Total** | | **$15-20 per 100 presentations** |

**Per presentation:** $0.15-0.20

---

### 13.3 Break-even Analysis

**Assumptions:**
- Infrastructure: $220/month (Phase 2)
- API costs: $0.18 per presentation
- Target pricing: $5 per presentation (for users)

**Break-even:**
- Fixed costs: $220/month
- Profit per presentation: $5 - $0.18 = $4.82
- Break-even presentations: 220 / 4.82 = **46 presentations/month**

**Revenue Projections:**
- 100 presentations/month: $500 revenue - $238 costs = **$262 profit**
- 500 presentations/month: $2,500 revenue - $310 costs = **$2,190 profit**
- 1,000 presentations/month: $5,000 revenue - $400 costs = **$4,600 profit**

---

## 14. Risk Analysis & Mitigation

### 14.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Playwright crashes | High | Medium | Restart worker, implement health checks |
| API rate limits (Unsplash) | Medium | Medium | Implement caching, fallback images |
| Large file uploads fail | Medium | Medium | Implement resumable uploads (tus) |
| Database scaling issues | High | Low | Use connection pooling, read replicas |
| WebSocket disconnections | Low | High | Auto-reconnect, fallback to polling |

---

### 14.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Low user adoption | High | Medium | Beta testing, user feedback, marketing |
| API cost overruns | Medium | Low | Set usage quotas, monitor costs |
| Competition | Medium | High | Focus on quality, unique features |
| API provider changes | High | Low | Abstract API calls, multi-provider support |

---

## 15. Success Metrics (KPIs)

### 15.1 Technical Metrics
- **Uptime:** > 99.5%
- **API response time:** < 200ms (p95)
- **Job completion rate:** > 95%
- **Average processing time:** < 5 minutes
- **Error rate:** < 2%

### 15.2 Business Metrics
- **Monthly active users (MAU):** Track growth
- **Presentations generated per month:** Track usage
- **User retention rate:** > 40% (30-day)
- **Net Promoter Score (NPS):** > 50
- **API cost per presentation:** < $0.20

---

## 16. Next Steps

### Immediate Actions (Week 1)
1. **Set up development environment:**
   - Create `api/` directory for backend
   - Create `frontend/` directory for React app
   - Set up Docker Compose for local development

2. **Database design:**
   - Finalize schema
   - Create migration scripts (Alembic)

3. **API endpoint specification:**
   - Write OpenAPI spec
   - Set up FastAPI project structure

4. **Frontend scaffolding:**
   - Initialize React + TypeScript project
   - Set up Tailwind CSS + shadcn/ui
   - Create basic routing structure

### Review & Approval
- [ ] Review architecture decisions
- [ ] Confirm technology stack choices
- [ ] Approve implementation timeline
- [ ] Assign development resources

---

## Appendix

### A. Technology Alternatives Considered

| Category | Chosen | Alternatives | Reason |
|----------|--------|--------------|--------|
| Backend Framework | FastAPI | Flask, Django | Async support, WebSocket |
| Job Queue | Celery | Python-RQ, Dramatiq | Production-grade features |
| Database | PostgreSQL | MySQL, MongoDB | JSON support, reliability |
| Frontend | React | Vue.js, Svelte | Ecosystem, talent pool |
| UI Framework | Tailwind + shadcn | Material UI, Chakra | Customization, performance |
| State Management | Zustand | Redux, MobX | Simplicity, low boilerplate |

---

### B. File Structure (Proposed)

```
voice-to-slide/
├── src/voice_to_slide/       # Existing core modules (unchanged)
│   ├── main.py
│   ├── transcriber.py
│   ├── presentation_orchestrator.py
│   ├── structure_editor.py
│   ├── image_fetcher.py
│   ├── html_generator.py
│   ├── html_to_image.py
│   ├── html_to_pptx.py
│   ├── slide_builder.py
│   ├── themes.md
│   └── utils.py
│
├── api/                       # NEW: Backend API layer
│   ├── main.py               # FastAPI app
│   ├── routers/              # API endpoints
│   │   ├── generate.py
│   │   ├── jobs.py
│   │   ├── download.py
│   │   └── config.py
│   ├── models/               # Database models (SQLAlchemy)
│   │   ├── job.py
│   │   ├── feedback.py
│   │   └── user.py
│   ├── tasks/                # Celery tasks
│   │   ├── generation_tasks.py
│   │   └── cleanup_tasks.py
│   ├── schemas/              # Pydantic schemas
│   │   ├── job_schema.py
│   │   └── structure_schema.py
│   ├── services/             # Business logic wrappers
│   │   ├── job_service.py
│   │   └── storage_service.py
│   ├── websocket/            # WebSocket handlers
│   │   └── progress_handler.py
│   ├── celery_config.py      # Celery configuration
│   ├── database.py           # Database setup
│   └── Dockerfile
│
├── frontend/                  # NEW: React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── UploadPage.tsx
│   │   │   ├── ProgressPage.tsx
│   │   │   ├── EditorPage.tsx
│   │   │   └── ResultPage.tsx
│   │   ├── components/
│   │   │   ├── FileDropzone.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── StructurePreview.tsx
│   │   │   └── SlideCarousel.tsx
│   │   ├── stores/
│   │   │   ├── jobStore.ts
│   │   │   ├── configStore.ts
│   │   │   └── wsStore.ts
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   └── useJobStatus.ts
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── docker-compose.yml         # Development environment
├── .env.example               # Environment variables template
├── README.md                  # Updated with web UI instructions
├── WEB_UI_DESIGN_PLAN.md      # This document
└── pyproject.toml             # Updated dependencies
```

---

### C. Environment Variables (Updated)

```bash
# Existing variables (from CLI)
SONIOX_API_KEY=...
CONTENT_ANTHROPIC_API_KEY=...
UNSPLASH_ACCESS_KEY=...
CONTENT_MODEL=claude-haiku-4-5-20251001
CONTENT_ANTHROPIC_BASE_URL=...

# NEW: Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/voice_to_slide

# NEW: Redis
REDIS_URL=redis://localhost:6379/0

# NEW: File Storage (Phase 1)
STORAGE_DIR=/var/app/storage

# NEW: File Storage (Phase 2)
S3_BUCKET_NAME=voice-to-slide-prod
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# NEW: Authentication (Phase 2)
JWT_SECRET=your-secret-key-here
JWT_EXPIRATION_HOURS=24

# NEW: Application Settings
ALLOWED_ORIGINS=http://localhost:3000,https://voice-to-slide.example.com
MAX_UPLOAD_SIZE_MB=100
FILE_RETENTION_DAYS=7
LOG_LEVEL=INFO
```

---

### D. Testing Strategy

#### Unit Tests
- Test individual API endpoints
- Test Celery task logic (mocked external APIs)
- Test database models and queries
- Test frontend components (React Testing Library)

#### Integration Tests
- Test full API flow (upload → process → download)
- Test WebSocket communication
- Test background job processing

#### End-to-End Tests
- Test complete user journey (Playwright/Cypress)
- Test interactive feedback loop
- Test file upload and download

#### Performance Tests
- Load testing with 10-100 concurrent users (Locust)
- Stress testing with large audio files
- Database query performance

---

## Conclusion

This design plan provides a comprehensive roadmap for converting the Voice-to-Slide CLI application into a modern web application. The architecture preserves the existing core logic while adding a scalable API layer and user-friendly frontend.

**Key Highlights:**
- ✅ Minimal refactoring of existing modules
- ✅ Modern tech stack (FastAPI, React, Celery)
- ✅ Scalable architecture (VPS → Cloud)
- ✅ Real-time progress updates (WebSocket)
- ✅ Interactive feedback loop preserved
- ✅ Cost-effective deployment strategy
- ✅ Clear implementation roadmap (12-16 weeks)

**Next Steps:**
1. Review and approve architecture
2. Set up development environment
3. Begin Phase 1 implementation

**Questions for Stakeholders:**
1. Do you want to prioritize authentication (Phase 2) or launch with anonymous users?
2. Do you prefer AWS, Google Cloud, or other cloud provider for Phase 2?
3. Should we implement a freemium pricing model or subscription-based?
4. Any specific UI/UX preferences or branding guidelines?

---

**Document End**
