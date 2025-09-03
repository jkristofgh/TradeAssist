"""
Test API endpoint for broadcasting market data via WebSocket.
Used to verify UI refresh mechanism during development.
"""

import random
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..websocket.realtime import get_websocket_manager

router = APIRouter()


class TestMarketDataRequest(BaseModel):
    """Request model for test market data."""
    instrument_id: int
    symbol: str
    base_price: float = 100.0


@router.post("/test-market-data")
async def broadcast_test_market_data(request: TestMarketDataRequest):
    """
    Broadcast test market data for a specific instrument.
    
    Args:
        request: Test market data request containing instrument details
        
    Returns:
        Success message with broadcast count
    """
    try:
        manager = get_websocket_manager()
        
        # Generate realistic market data
        price_variation = random.uniform(-0.05, 0.05)  # ±5% variation
        current_price = request.base_price * (1 + price_variation)
        volume = random.randint(100, 10000)
        bid = current_price - 0.01
        ask = current_price + 0.01
        
        # Broadcast tick update
        broadcast_count = await manager.broadcast_tick_update(
            instrument_id=request.instrument_id,
            symbol=request.symbol,
            price=current_price,
            volume=volume,
            bid=bid,
            ask=ask,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return {
            "success": True,
            "message": f"Test market data broadcast for {request.symbol}",
            "data": {
                "instrumentId": request.instrument_id,
                "symbol": request.symbol,
                "price": current_price,
                "volume": volume,
                "bid": bid,
                "ask": ask,
                "broadcastCount": broadcast_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to broadcast test data: {str(e)}")


@router.post("/test-market-data/multiple")
async def broadcast_multiple_test_data():
    """
    Broadcast test market data for multiple instruments.
    Useful for testing UI with various instruments at once.
    
    Returns:
        Success message with details for each broadcast
    """
    try:
        manager = get_websocket_manager()
        
        # Test data for common instruments
        test_instruments = [
            {"id": 1, "symbol": "/ES", "base_price": 4500.0},
            {"id": 2, "symbol": "SPY", "base_price": 450.0},
            {"id": 3, "symbol": "/NQ", "base_price": 15000.0},
            {"id": 4, "symbol": "QQQ", "base_price": 380.0},
            {"id": 5, "symbol": "/YM", "base_price": 35000.0}
        ]
        
        results = []
        
        for instrument in test_instruments:
            # Generate realistic market data
            price_variation = random.uniform(-0.02, 0.02)  # ±2% variation
            current_price = instrument["base_price"] * (1 + price_variation)
            volume = random.randint(500, 5000)
            bid = current_price - (current_price * 0.001)  # 0.1% spread
            ask = current_price + (current_price * 0.001)
            
            # Broadcast tick update
            broadcast_count = await manager.broadcast_tick_update(
                instrument_id=instrument["id"],
                symbol=instrument["symbol"],
                price=current_price,
                volume=volume,
                bid=bid,
                ask=ask,
                timestamp=datetime.utcnow().isoformat()
            )
            
            results.append({
                "instrumentId": instrument["id"],
                "symbol": instrument["symbol"],
                "price": round(current_price, 2),
                "volume": volume,
                "bid": round(bid, 2),
                "ask": round(ask, 2),
                "broadcastCount": broadcast_count
            })
        
        return {
            "success": True,
            "message": f"Broadcast test data for {len(test_instruments)} instruments",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to broadcast multiple test data: {str(e)}")


@router.get("/websocket-status")
async def get_websocket_status():
    """
    Get current WebSocket connection status.
    
    Returns:
        WebSocket manager status and active connections
    """
    try:
        manager = get_websocket_manager()
        
        return {
            "success": True,
            "status": {
                "activeConnections": len(manager.active_connections),
                "connectionIds": list(manager.active_connections.keys()),
                "subscriptions": {
                    client_id: list(subs) 
                    for client_id, subs in manager.client_subscriptions.items()
                },
                "performanceMetrics": manager.performance_metrics
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get WebSocket status: {str(e)}")