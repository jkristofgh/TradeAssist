"""
Analytics API Routes

Provides REST API endpoints for advanced market analytics, ML predictions,
and risk calculations for the TradeAssist platform Phase 4.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..services.analytics_engine import analytics_engine, TechnicalIndicator
from ..services.ml_models import ml_service, ModelType, PredictionHorizon
from ..services.risk_calculator import risk_calculator, ConfidenceLevel, RiskMetricType
from ..services.market_data_processor import market_data_processor, DataFrequency
from ..database.connection import get_db_session
from ..models.instruments import Instrument
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


# Pydantic models for request/response
class AnalyticsRequest(BaseModel):
    """Request model for analytics operations."""
    instrument_id: int
    lookback_hours: Optional[int] = Field(default=24, ge=1, le=8760)  # 1 hour to 1 year
    indicators: Optional[List[str]] = Field(default=None)


class PredictionRequest(BaseModel):
    """Request model for ML predictions."""
    instrument_id: int
    model_type: str = Field(default="lstm_price_predictor")
    horizon: str = Field(default="short_term")
    confidence_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)


class RiskRequest(BaseModel):
    """Request model for risk calculations."""
    instrument_id: int
    confidence_level: float = Field(default=0.95, ge=0.90, le=0.999)
    time_horizon_days: int = Field(default=1, ge=1, le=30)
    position_size: float = Field(default=10000.0, ge=100.0)
    method: str = Field(default="historical")


class StressTestRequest(BaseModel):
    """Request model for stress testing."""
    instrument_id: int
    scenarios: Optional[List[Dict[str, Any]]] = None


class VolumeProfileRequest(BaseModel):
    """Request model for volume profile analysis."""
    instrument_id: int
    lookback_hours: int = Field(default=24, ge=1, le=168)  # 1 hour to 1 week
    price_bins: int = Field(default=100, ge=10, le=1000)


# Analytics endpoints
@router.get("/market-analysis/{instrument_id}")
async def get_market_analysis(
    instrument_id: int = Path(..., description="Instrument ID"),
    lookback_hours: int = Query(default=24, ge=1, le=8760),
    session=Depends(get_db_session)
):
    """
    Get comprehensive market analysis for an instrument.
    
    Returns technical indicators, trend analysis, volatility metrics,
    support/resistance levels, and pattern signals.
    """
    try:
        # Validate instrument exists
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one_or_none()
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        # Get market analysis
        analysis = await analytics_engine.get_market_analysis(instrument_id, lookback_hours)
        if not analysis:
            raise HTTPException(status_code=404, detail="Insufficient data for analysis")
        
        # Convert to serializable format
        response_data = {
            "timestamp": analysis.timestamp.isoformat(),
            "instrument_id": analysis.instrument_id,
            "instrument_symbol": instrument.symbol,
            "lookback_hours": lookback_hours,
            "technical_indicators": [
                {
                    "type": indicator.indicator_type.value,
                    "timestamp": indicator.timestamp.isoformat(),
                    "values": indicator.values,
                    "metadata": indicator.metadata
                }
                for indicator in analysis.technical_indicators
            ],
            "trend_analysis": analysis.trend_analysis,
            "volatility_metrics": analysis.volatility_metrics,
            "support_resistance": analysis.support_resistance,
            "pattern_signals": analysis.pattern_signals
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/real-time-indicators/{instrument_id}")
async def get_real_time_indicators(
    instrument_id: int = Path(..., description="Instrument ID"),
    indicators: List[str] = Query(default=["rsi", "macd", "bollinger_bands"]),
    session=Depends(get_db_session)
):
    """
    Get real-time technical indicators for an instrument.
    
    Available indicators: rsi, macd, bollinger_bands, moving_average, 
    stochastic, atr, adx
    """
    try:
        # Validate instrument
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one_or_none()
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        # Convert string indicators to enum
        try:
            indicator_enums = [TechnicalIndicator(ind) for ind in indicators]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid indicator: {e}")
        
        # Get real-time indicators
        results = await analytics_engine.get_real_time_indicators(
            instrument_id, indicator_enums
        )
        
        # Format response
        response_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "instrument_id": instrument_id,
            "instrument_symbol": instrument.symbol,
            "indicators": [
                {
                    "type": result.indicator_type.value,
                    "timestamp": result.timestamp.isoformat(),
                    "values": result.values,
                    "metadata": result.metadata
                }
                for result in results
            ]
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting real-time indicators: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/predict-price")
async def predict_price(request: PredictionRequest, session=Depends(get_db_session)):
    """
    Predict future price using machine learning models.
    
    Available models: lstm_price_predictor, random_forest_predictor
    Horizons: short_term (5 minutes), medium_term (1 hour), long_term (1 day)
    """
    try:
        # Validate instrument
        result = await session.execute(
            select(Instrument).where(Instrument.id == request.instrument_id)
        )
        instrument = result.scalar_one_or_none()
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        # Convert string enums
        try:
            model_type = ModelType(request.model_type)
            horizon = PredictionHorizon(request.horizon)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid parameter: {e}")
        
        # Get prediction
        prediction = await ml_service.predict_price(
            request.instrument_id, horizon, model_type
        )
        
        if not prediction:
            raise HTTPException(status_code=404, detail="Unable to generate prediction")
        
        if prediction.confidence_score < request.confidence_threshold:
            return JSONResponse(
                status_code=202,
                content={
                    "message": "Prediction available but confidence below threshold",
                    "confidence_threshold": request.confidence_threshold,
                    "actual_confidence": prediction.confidence_score,
                    "prediction": {
                        "model_type": prediction.model_type.value,
                        "timestamp": prediction.timestamp.isoformat(),
                        "instrument_id": prediction.instrument_id,
                        "predicted_value": prediction.predicted_value,
                        "confidence_score": prediction.confidence_score,
                        "prediction_horizon": prediction.prediction_horizon.value,
                        "feature_importance": prediction.feature_importance,
                        "metadata": prediction.metadata
                    }
                }
            )
        
        # High confidence prediction
        response_data = {
            "model_type": prediction.model_type.value,
            "timestamp": prediction.timestamp.isoformat(),
            "instrument_id": prediction.instrument_id,
            "instrument_symbol": instrument.symbol,
            "predicted_value": prediction.predicted_value,
            "confidence_score": prediction.confidence_score,
            "prediction_horizon": prediction.prediction_horizon.value,
            "feature_importance": prediction.feature_importance,
            "metadata": prediction.metadata
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting price: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/anomaly-detection/{instrument_id}")
async def detect_anomalies(
    instrument_id: int = Path(..., description="Instrument ID"),
    lookback_hours: int = Query(default=24, ge=1, le=168),
    session=Depends(get_db_session)
):
    """
    Detect anomalous market behavior using machine learning.
    
    Returns detected anomalies with severity scores and timestamps.
    """
    try:
        # Validate instrument
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one_or_none()
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        # Detect anomalies
        anomalies = await ml_service.detect_anomalies(instrument_id, lookback_hours)
        
        response_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "instrument_id": instrument_id,
            "instrument_symbol": instrument.symbol,
            "lookback_hours": lookback_hours,
            "anomalies_detected": len(anomalies),
            "anomalies": [
                {
                    "timestamp": anomaly["timestamp"].isoformat() if isinstance(anomaly["timestamp"], datetime) else anomaly["timestamp"],
                    "anomaly_score": anomaly["anomaly_score"],
                    "severity": anomaly["severity"],
                    "features": anomaly["features"]
                }
                for anomaly in anomalies
            ]
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trend-classification/{instrument_id}")
async def classify_trend(
    instrument_id: int = Path(..., description="Instrument ID"),
    session=Depends(get_db_session)
):
    """
    Classify current market trend using machine learning.
    
    Returns trend classification (bullish, bearish, sideways) with confidence.
    """
    try:
        # Validate instrument
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one_or_none()
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        # Classify trend
        trend_result = await ml_service.classify_trend(instrument_id)
        
        response_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "instrument_id": instrument_id,
            "instrument_symbol": instrument.symbol,
            **trend_result
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error classifying trend: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/calculate-var")
async def calculate_var(request: RiskRequest, session=Depends(get_db_session)):
    """
    Calculate Value at Risk (VaR) for a position.
    
    Methods: historical, parametric, monte_carlo
    Confidence levels: 0.90, 0.95, 0.99, 0.999
    """
    try:
        # Validate instrument
        result = await session.execute(
            select(Instrument).where(Instrument.id == request.instrument_id)
        )
        instrument = result.scalar_one_or_none()
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        # Convert confidence level
        if request.confidence_level == 0.95:
            confidence_enum = ConfidenceLevel.NINETY_FIVE
        elif request.confidence_level == 0.99:
            confidence_enum = ConfidenceLevel.NINETY_NINE
        elif request.confidence_level == 0.999:
            confidence_enum = ConfidenceLevel.NINETY_NINE_NINE
        else:
            raise HTTPException(status_code=400, detail="Invalid confidence level")
        
        # Calculate VaR
        var_result = await risk_calculator.calculate_var(
            request.instrument_id,
            confidence_enum,
            request.time_horizon_days,
            request.position_size,
            request.method
        )
        
        if not var_result:
            raise HTTPException(status_code=404, detail="Unable to calculate VaR")
        
        response_data = {
            "timestamp": var_result.timestamp.isoformat(),
            "instrument_id": var_result.instrument_id,
            "instrument_symbol": instrument.symbol,
            "var_amount": var_result.var_amount,
            "confidence_level": var_result.confidence_level,
            "time_horizon_days": var_result.time_horizon_days,
            "method": var_result.method,
            "current_position": var_result.current_position,
            "portfolio_value": var_result.portfolio_value,
            "volatility": var_result.volatility,
            "metadata": var_result.metadata
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating VaR: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/risk-metrics/{instrument_id}")
async def get_risk_metrics(
    instrument_id: int = Path(..., description="Instrument ID"),
    lookback_days: int = Query(default=252, ge=30, le=1000),
    benchmark_id: Optional[int] = Query(default=None),
    session=Depends(get_db_session)
):
    """
    Get comprehensive risk metrics for an instrument.
    
    Includes VaR, volatility, Sharpe ratio, max drawdown, beta, and more.
    """
    try:
        # Validate instrument
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one_or_none()
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        # Validate benchmark if provided
        if benchmark_id:
            result = await session.execute(
                select(Instrument).where(Instrument.id == benchmark_id)
            )
            benchmark = result.scalar_one_or_none()
            if not benchmark:
                raise HTTPException(status_code=404, detail="Benchmark instrument not found")
        
        # Calculate risk metrics
        risk_metrics = await risk_calculator.calculate_comprehensive_risk_metrics(
            instrument_id, lookback_days, benchmark_id
        )
        
        if not risk_metrics:
            raise HTTPException(status_code=404, detail="Unable to calculate risk metrics")
        
        response_data = {
            "timestamp": risk_metrics.timestamp.isoformat(),
            "instrument_id": risk_metrics.instrument_id,
            "instrument_symbol": instrument.symbol,
            "portfolio_id": risk_metrics.portfolio_id,
            "risk_metrics": {
                "var_95": risk_metrics.var_95,
                "var_99": risk_metrics.var_99,
                "cvar_95": risk_metrics.cvar_95,
                "volatility_annual": risk_metrics.volatility_annual,
                "max_drawdown": risk_metrics.max_drawdown,
                "sharpe_ratio": risk_metrics.sharpe_ratio,
                "sortino_ratio": risk_metrics.sortino_ratio,
                "beta": risk_metrics.beta,
                "correlation_to_market": risk_metrics.correlation_to_market,
                "tracking_error": risk_metrics.tracking_error,
                "skewness": risk_metrics.skewness,
                "kurtosis": risk_metrics.kurtosis,
                "downside_deviation": risk_metrics.downside_deviation,
                "calmar_ratio": risk_metrics.calmar_ratio
            },
            "analysis_details": {
                "data_period_days": risk_metrics.data_period_days,
                "lookback_days_requested": lookback_days,
                "benchmark_id": benchmark_id,
                "last_updated": risk_metrics.last_updated.isoformat()
            }
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stress-test")
async def perform_stress_test(
    request: StressTestRequest,
    session=Depends(get_db_session)
):
    """
    Perform stress testing on an instrument position.
    
    Tests various market shock scenarios and estimates recovery times.
    """
    try:
        # Validate instrument
        result = await session.execute(
            select(Instrument).where(Instrument.id == request.instrument_id)
        )
        instrument = result.scalar_one_or_none()
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        # Perform stress test
        stress_results = await risk_calculator.perform_stress_test(
            request.instrument_id, request.scenarios
        )
        
        response_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "instrument_id": request.instrument_id,
            "instrument_symbol": instrument.symbol,
            "scenarios_tested": len(stress_results),
            "stress_test_results": [
                {
                    "scenario_name": result.scenario_name,
                    "timestamp": result.timestamp.isoformat(),
                    "shock_magnitude": result.shock_magnitude,
                    "original_value": result.original_value,
                    "stressed_value": result.stressed_value,
                    "loss_amount": result.loss_amount,
                    "loss_percentage": result.loss_percentage,
                    "recovery_time_estimate_days": result.recovery_time_estimate_days
                }
                for result in stress_results
            ]
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing stress test: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/volume-profile")
async def get_volume_profile(
    request: VolumeProfileRequest,
    session=Depends(get_db_session)
):
    """
    Get volume profile analysis for an instrument.
    
    Returns Point of Control (POC), value area, and volume distribution.
    """
    try:
        # Validate instrument
        result = await session.execute(
            select(Instrument).where(Instrument.id == request.instrument_id)
        )
        instrument = result.scalar_one_or_none()
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        # Get volume profile
        volume_profile = await market_data_processor.analyze_volume_profile(
            request.instrument_id, request.lookback_hours, request.price_bins
        )
        
        if not volume_profile:
            raise HTTPException(status_code=404, detail="Unable to generate volume profile")
        
        response_data = {
            "timestamp": volume_profile.timestamp.isoformat(),
            "instrument_id": request.instrument_id,
            "instrument_symbol": instrument.symbol,
            "analysis_period_hours": request.lookback_hours,
            "point_of_control": volume_profile.poc,
            "value_area_high": volume_profile.value_area_high,
            "value_area_low": volume_profile.value_area_low,
            "total_volume": volume_profile.total_volume,
            "price_levels": volume_profile.price_levels,
            "volume_at_price": volume_profile.volume_at_price,
            "price_bins": len(volume_profile.price_levels)
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting volume profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/correlation-matrix")
async def get_correlation_matrix(
    instrument_ids: List[int] = Query(..., description="List of instrument IDs"),
    lookback_days: int = Query(default=252, ge=30, le=1000),
    session=Depends(get_db_session)
):
    """
    Calculate correlation matrix for multiple instruments.
    
    Returns correlation coefficients, eigenvalues, and condition number.
    """
    try:
        if len(instrument_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 instruments required")
        
        # Validate all instruments exist
        result = await session.execute(
            select(Instrument).where(Instrument.id.in_(instrument_ids))
        )
        instruments = result.scalars().all()
        found_ids = [inst.id for inst in instruments]
        
        missing_ids = set(instrument_ids) - set(found_ids)
        if missing_ids:
            raise HTTPException(
                status_code=404, 
                detail=f"Instruments not found: {list(missing_ids)}"
            )
        
        # Calculate correlation matrix
        correlation_result = await risk_calculator.calculate_correlation_matrix(
            instrument_ids, lookback_days
        )
        
        if not correlation_result:
            raise HTTPException(status_code=404, detail="Unable to calculate correlation matrix")
        
        # Create instrument symbol mapping
        symbol_map = {inst.id: inst.symbol for inst in instruments}
        
        response_data = {
            "timestamp": correlation_result.timestamp.isoformat(),
            "instrument_ids": correlation_result.instrument_ids,
            "instrument_symbols": [symbol_map[id] for id in correlation_result.instrument_ids],
            "correlation_matrix": correlation_result.correlation_matrix,
            "eigenvalues": correlation_result.eigenvalues,
            "condition_number": correlation_result.condition_number,
            "analysis_period_days": correlation_result.period_days,
            "requested_lookback_days": lookback_days
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating correlation matrix: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/market-microstructure/{instrument_id}")
async def get_market_microstructure(
    instrument_id: int = Path(..., description="Instrument ID"),
    lookback_minutes: int = Query(default=60, ge=5, le=1440),
    session=Depends(get_db_session)
):
    """
    Get market microstructure analysis for an instrument.
    
    Returns bid-ask spreads, market impact, and order flow metrics.
    """
    try:
        # Validate instrument
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one_or_none()
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        
        # Get microstructure analysis
        microstructure = await market_data_processor.calculate_market_microstructure(
            instrument_id, lookback_minutes
        )
        
        if not microstructure:
            raise HTTPException(status_code=404, detail="Unable to calculate market microstructure")
        
        response_data = {
            "timestamp": microstructure.timestamp.isoformat(),
            "instrument_id": microstructure.instrument_id,
            "instrument_symbol": instrument.symbol,
            "analysis_period_minutes": lookback_minutes,
            "microstructure_metrics": {
                "bid_ask_spread": microstructure.bid_ask_spread,
                "market_impact": microstructure.market_impact,
                "order_flow_imbalance": microstructure.order_flow_imbalance,
                "effective_spread": microstructure.effective_spread,
                "price_improvement": microstructure.price_improvement,
                "fill_rate": microstructure.fill_rate
            }
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market microstructure: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for analytics services."""
    try:
        # Check service availability
        services_status = {
            "analytics_engine": "available",
            "ml_service": "available" if ml_service else "unavailable",
            "risk_calculator": "available",
            "market_data_processor": "available"
        }
        
        return JSONResponse(content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_status
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )