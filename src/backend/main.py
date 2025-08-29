"""
TradeAssist FastAPI Application Entry Point.

This is the main application file that initializes the FastAPI service
with WebSocket support, API routes, and background task management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .api.instruments import router as instruments_router
from .api.rules import router as rules_router
from .api.alerts import router as alerts_router
from .api.analytics import router as analytics_router
from .config import settings
from .database.connection import init_database, close_database
from .services.data_ingestion import DataIngestionService
from .services.alert_engine import AlertEngine
from .services.notification import NotificationService
from .services.analytics_engine import analytics_engine
from .services.ml_models import ml_service
from .services.market_data_processor import market_data_processor
from .websocket.realtime import router as websocket_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application,
    including database initialization and background service management.
    """
    logger.info("Starting TradeAssist application")
    
    # Initialize database
    await init_database()
    
    # Initialize notification service
    notification_service = NotificationService()
    await notification_service.initialize()
    
    # Initialize Phase 4 analytics services
    await market_data_processor.initialize()
    await ml_service.initialize_models()
    
    # Start alert engine
    alert_engine = AlertEngine()
    alert_engine.notification_service = notification_service
    await alert_engine.start()
    
    # Start background data ingestion service
    data_service = DataIngestionService()
    data_service.set_alert_engine(alert_engine)
    await data_service.start()
    
    # Store service instances for access during shutdown
    app.state.data_service = data_service
    app.state.alert_engine = alert_engine
    app.state.notification_service = notification_service
    
    logger.info("TradeAssist application started successfully")
    
    yield
    
    # Shutdown processes
    logger.info("Shutting down TradeAssist application")
    
    # Stop data ingestion service
    await app.state.data_service.stop()
    
    # Stop alert engine
    await app.state.alert_engine.stop()
    
    # Cleanup notification service
    await app.state.notification_service.cleanup()
    
    # Close database connections
    await close_database()
    
    logger.info("TradeAssist application shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance.
    """
    app = FastAPI(
        title="TradeAssist API",
        description="Real-time trading alerts and market data streaming",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Configure CORS for frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(instruments_router, prefix="/api", tags=["instruments"])
    app.include_router(rules_router, prefix="/api", tags=["rules"])
    app.include_router(alerts_router, prefix="/api", tags=["alerts"])
    app.include_router(analytics_router, tags=["analytics"])
    
    # Include WebSocket router
    app.include_router(websocket_router, prefix="/ws")
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )