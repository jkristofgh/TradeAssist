"""
TradeAssist FastAPI Application Entry Point.

This is the main application file that initializes the FastAPI service
with WebSocket support, API routes, and background task management.
"""

import asyncio
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
from .api.auth import router as auth_router
from .api.historical_data import router as historical_data_router, set_historical_data_service
from .config import settings
from .database.connection import init_database, close_database
from .services.data_ingestion import DataIngestionService
from .services.alert_engine import AlertEngine
from .services.notification import NotificationService
from .services.analytics_engine import analytics_engine
from .services.ml_models import ml_service
from .services.market_data_processor import market_data_processor
from .services.historical_data_service import HistoricalDataService
from .websocket.realtime import router as websocket_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application,
    including database initialization and background service management.
    """
    # Configure production logging first
    from .logging_config import configure_production_logging
    configure_production_logging()
    
    logger.info("Starting TradeAssist application", version="1.0.0", phase="4_production")
    
    # Initialize database
    await init_database()
    
    # Initialize notification service
    notification_service = NotificationService()
    await notification_service.initialize()
    
    # Initialize Phase 4 analytics services
    await market_data_processor.initialize()
    await ml_service.initialize_models()
    
    # Initialize historical data service
    historical_data_service = HistoricalDataService()
    await historical_data_service.start()
    
    # Register historical data service with API
    set_historical_data_service(historical_data_service)
    
    # Initialize Phase 4 performance monitoring services
    from .services.performance_monitoring_service import get_performance_monitoring_service
    from .services.partition_manager_service import get_partition_manager_service
    
    # Initialize services  
    data_ingestion = DataIngestionService()
    alert_engine = AlertEngine()
    performance_monitoring = get_performance_monitoring_service()
    partition_manager = get_partition_manager_service()
    
    # Start services in order
    logger.info("Starting core services")
    
    # Try to start data ingestion, but don't fail if streaming fails
    try:
        await data_ingestion.start()
        logger.info("Data ingestion service started successfully")
    except Exception as e:
        logger.warning(f"Data ingestion service failed to start (streaming issue): {e}")
        logger.info("Continuing without real-time streaming - historical data will still work")
    
    await alert_engine.start()
    
    # Start Phase 4 performance services
    logger.info("Starting Phase 4 performance monitoring services")
    await partition_manager.start_partition_management()
    await performance_monitoring.start_monitoring()
    
    # Start API standardization performance monitoring (Phase 3)
    from .services.api_performance_monitor import start_performance_monitoring
    await start_performance_monitoring()
    logger.info("API standardization performance monitoring started")
    
    logger.info("TradeAssist application started successfully")
    
    try:
        yield  # App is running
    finally:
        # Shutdown sequence
        logger.info("Shutting down TradeAssist application")
        
        # Stop services in reverse order
        # Stop API standardization performance monitoring
        from .services.api_performance_monitor import stop_performance_monitoring
        await stop_performance_monitoring()
        
        await performance_monitoring.stop_monitoring()
        await partition_manager.stop_partition_management()
        await analytics_engine.stop()
        await alert_engine.stop()
        await data_ingestion.stop()
        await historical_data_service.stop()
        
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
    
    # Set up enhanced OpenAPI documentation (Phase 3)
    from .api.common.openapi_generator import setup_enhanced_openapi
    setup_enhanced_openapi(app)
    
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
    app.include_router(auth_router, prefix="/api", tags=["authentication"])
    app.include_router(historical_data_router, tags=["historical-data"])
    
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