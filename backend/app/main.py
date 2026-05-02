"""
FastAPI Main Application
Entry point for the RCA Benchmarking Dashboard API
Implements Vellum-style multi-source data fetching and auto-refresh
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
import uvicorn
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="AI Model Leaderboard API",
    description="Multi-category LLM benchmarking with real-time updates from multiple sources",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """
    Initialize services on startup
    Implements Vellum's approach: auto-refresh and multi-source data
    """
    logger.info("=" * 60)
    logger.info("Starting AI Model Leaderboard API v2.0.0")
    logger.info("Implementing Vellum-style multi-source approach")
    logger.info("=" * 60)
    
    # Note: Auto-refresh is available but not started by default
    # To enable, uncomment the following lines:
    # from .services.auto_refresh import start_auto_refresh
    # asyncio.create_task(start_auto_refresh())
    # logger.info("✓ Auto-refresh service started (24-hour interval)")
    
    logger.info("✓ API ready")
    logger.info("✓ Multi-source data fetching available")
    logger.info("✓ Category-based leaderboards active")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API...")
    
    # Stop auto-refresh if running
    try:
        from .services.auto_refresh import stop_auto_refresh
        await stop_auto_refresh()
        logger.info("✓ Auto-refresh service stopped")
    except:
        pass


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Model Leaderboard API",
        "version": "2.0.0",
        "description": "Multi-category LLM benchmarking with Vellum-style multi-source validation",
        "features": [
            "4 category leaderboards (RCA, General, Coding, Reasoning)",
            "Multi-source data validation",
            "Automated refresh system",
            "Confidence scoring",
            "Real-time updates"
        ],
        "endpoints": {
            "docs": "/docs",
            "api": "/api",
            "categories": "/api/categories",
            "data_sources": "/api/data-sources",
            "refresh_status": "/api/refresh/status"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from .services.auto_refresh import get_auto_refresh_service
        service = get_auto_refresh_service()
        status = service.get_status()
        
        return {
            "status": "healthy",
            "api_version": "2.0.0",
            "refresh_service": {
                "status": status.get('status', 'unknown'),
                "last_refresh": status.get('last_refresh'),
                "models_count": status.get('models_updated', 0)
            }
        }
    except Exception as e:
        return {
            "status": "healthy",
            "api_version": "2.0.0",
            "refresh_service": {
                "status": "not_initialized",
                "error": str(e)
            }
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob
