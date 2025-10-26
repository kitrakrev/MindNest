"""
Chat Simulator FastAPI Service
A service for simulating conversations among multiple personas with LLM integration.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import uvicorn

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from api.routes import personas, chat, simulation
from core.config import settings
from core.queue_manager import MessageQueueManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    # Initialize database
    from database.connection import init_db
    await init_db()
    
    # Initialize message queue manager
    app.state.queue_manager = MessageQueueManager()
    yield
    # Cleanup
    await app.state.queue_manager.shutdown()


app = FastAPI(
    title="Chat Simulator API",
    description="Simulate conversations among multiple personas with LLM integration",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api.routes import groups, global_agent, admin, views

app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(groups.router, prefix="/api/groups", tags=["Groups"])
app.include_router(personas.router, prefix="/api/personas", tags=["Personas"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["Simulation"])
app.include_router(global_agent.router, prefix="/api/global-agent", tags=["Global Agent"])
app.include_router(views.router, prefix="/api/views", tags=["Views"])


@app.get("/", include_in_schema=False)
async def root():
    """Serve the web UI."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "status": "healthy",
        "service": "Chat Simulator API",
        "version": "1.0.0",
        "message": "UI not found. API endpoints available at /docs"
    }


@app.get("/robot", include_in_schema=False)
async def robot_controller():
    """Serve the robot controller UI."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    robot_path = os.path.join(static_dir, "robot.html")
    if os.path.exists(robot_path):
        return FileResponse(robot_path)
    return {"error": "Robot controller UI not found"}


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "queue_status": "active"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )


# Configure logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

