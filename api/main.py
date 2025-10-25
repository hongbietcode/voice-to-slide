"""FastAPI main application."""

import os
import json
import asyncio
import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.database import init_db
from api.routers import generate, jobs, download, config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    init_db()  # Initialize database tables
    yield
    # Shutdown
    pass


# Create FastAPI app
app = FastAPI(
    title="Voice-to-Slide API",
    description="API for converting voice recordings to PowerPoint presentations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generate.router)
app.include_router(jobs.router)
app.include_router(download.router)
app.include_router(config.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Voice-to-Slide API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for each job."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        """Connect a WebSocket client for a job."""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def send_message(self, job_id: str, message: dict):
        """Send message to all connected clients for a job."""
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass  # Connection closed, will be removed on disconnect


manager = ConnectionManager()


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time progress updates.

    Clients connect to /ws/{job_id} and receive progress updates.
    """
    await manager.connect(job_id, websocket)

    # Create Redis pubsub client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = aioredis.from_url(redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()

    # Subscribe to job channel
    channel = f"job:{job_id}"
    await pubsub.subscribe(channel)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "message": "Connected to job updates"
        })

        # Listen for Redis messages and forward to WebSocket
        async def listen_redis():
            """Listen to Redis pub/sub and forward messages."""
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await manager.send_message(job_id, data)

        # Listen for Redis messages
        redis_task = asyncio.create_task(listen_redis())

        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for messages from client (ping/pong or subscription)
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                break

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Cleanup
        manager.disconnect(job_id, websocket)
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await redis_client.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
