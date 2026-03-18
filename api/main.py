"""
FastAPI application for Fridge Bot API.

Provides REST API for:
- User management
- Fridge operations
- Product catalog
- Notifications
- Scanning
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database.session import init_db, close_db
from .routers import users, fridge, products, notifications, scan, recipes, shopping

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting API server...")
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_db()
        logger.info("Database connection established")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down API server...")
        await close_db()
        logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="Fridge Bot API",
    description="REST API for Fridge Telegram Bot",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(fridge.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(scan.router, prefix="/api/v1")
app.include_router(recipes.router, prefix="/api/v1")
app.include_router(shopping.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "fridge-bot-api",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Fridge Bot API",
        "docs": "/docs",
        "health": "/health"
    }


# WebApp for scanner
WEBAPP_DIR = Path(__file__).parent.parent / "webapp"


@app.get("/webapp")
async def webapp_index():
    """Serve WebApp index."""
    index_file = WEBAPP_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"error": "WebApp not found"}


@app.get("/webapp/{file_path:path}")
async def webapp_static(file_path: str):
    """Serve WebApp static files."""
    file = WEBAPP_DIR / file_path
    if file.exists() and file.is_file():
        return FileResponse(file)
    return {"error": "File not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
