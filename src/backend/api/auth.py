"""
Authentication API endpoints for Schwab OAuth flow.

Provides endpoints to initiate and manage Schwab API authentication.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/schwab/authenticate")
async def start_schwab_authentication(request: Request) -> Dict[str, Any]:
    """
    Start Schwab OAuth authentication flow.
    
    This will initiate the OAuth flow which requires browser interaction.
    The user will need to visit the OAuth URL and complete authentication.
    
    Returns:
        Dict with authentication status and instructions
    """
    try:
        logger.info("Starting Schwab authentication flow")
        
        data_service = request.app.state.data_service
        if not data_service.schwab_client:
            raise HTTPException(
                status_code=500,
                detail="Schwab client not initialized"
            )
        
        # Access the underlying TradeAssistSchwabClient through the wrapper
        underlying_client = data_service.schwab_client._client
        if not underlying_client:
            raise HTTPException(
                status_code=500,
                detail="Underlying Schwab client not initialized"
            )
        
        # Start the manual authentication flow
        await underlying_client.authenticate_manual()
        
        return {
            "status": "success",
            "message": "Schwab authentication completed successfully",
            "next_steps": "Authentication tokens have been saved. You can now start streaming market data."
        }
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/schwab/status")
async def get_authentication_status(request: Request) -> Dict[str, Any]:
    """
    Get current Schwab API authentication status.
    
    Returns:
        Dict with authentication and connection status
    """
    try:
        data_service = request.app.state.data_service
        if not data_service.schwab_client:
            return {
                "authenticated": False,
                "connected": False,
                "status": "client_not_initialized"
            }
        
        # Access the underlying TradeAssistSchwabClient through the wrapper
        underlying_client = data_service.schwab_client._client
        if not underlying_client:
            return {
                "authenticated": False,
                "connected": False,
                "status": "underlying_client_not_initialized"
            }
        
        # Get health status from the underlying client
        health = underlying_client.get_health_status()
        
        return {
            "authenticated": health.get("authenticated", False),
            "connected": health.get("client_ready", False),
            "status": health.get("status", "unknown"),
            "details": health
        }
        
    except Exception as e:
        logger.error(f"Failed to get auth status: {e}")
        return {
            "authenticated": False,
            "connected": False,
            "status": "error",
            "error": str(e)
        }


@router.post("/schwab/reconnect")
async def reconnect_schwab(request: Request) -> Dict[str, Any]:
    """
    Attempt to reconnect to Schwab API using existing tokens.
    
    Returns:
        Dict with reconnection status
    """
    try:
        logger.info("Attempting to reconnect to Schwab API")
        
        data_service = request.app.state.data_service
        if not data_service.schwab_client:
            raise HTTPException(
                status_code=500,
                detail="Schwab client not initialized"
            )
        
        # Try to restart streaming which will use existing tokens
        symbols = ["ES", "NQ", "YM", "CL", "GC", "SPX", "NDX", "RUT", "VIX", "TICK", "ADD", "TRIN"]
        success = await data_service.schwab_client.start_streaming(symbols)
        
        if success:
            return {
                "status": "success",
                "message": "Successfully reconnected to Schwab API",
                "streaming": True
            }
        else:
            return {
                "status": "failed",
                "message": "Failed to reconnect. May need to re-authenticate.",
                "streaming": False
            }
        
    except Exception as e:
        logger.error(f"Reconnection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Reconnection failed: {str(e)}"
        )