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

# Import standardized API components
from .common.exceptions import StandardAPIError, ValidationError, SystemError
from .common.responses import AnalyticsResponseBuilder
from .common.validators import (
    validate_instrument_exists, 
    validate_lookback_hours, 
    validate_confidence_level
)
from .common.configuration import TechnicalIndicatorConfig, ValidationConfig

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
@validate_instrument_exists
@validate_lookback_hours(min_hours=1, max_hours=8760)
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
    start_time = datetime.utcnow()
    response_builder = AnalyticsResponseBuilder()
    
    try:
        # Get instrument (validation decorator already confirmed it exists)
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one()
        
        # Get market analysis
        analysis = await analytics_engine.get_market_analysis(instrument_id, lookback_hours)
        if not analysis:
            raise ValidationError(
                error_code="ANALYTICS_001",
                message="Insufficient data for market analysis",
                details={"instrument_id": instrument_id, "lookback_hours": lookback_hours}
            )
        
        # Prepare response data
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
        
        # Calculate performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        data_points = len(analysis.technical_indicators)
        
        # Build standardized response
        return response_builder.success(response_data) \
            .with_performance_metrics(processing_time, data_points) \
            .with_confidence_score(getattr(analysis, 'confidence_score', 1.0)) \
            .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        logger.error(f"Error getting market analysis: {e}")
        raise SystemError(
            error_code="ANALYTICS_002", 
            message="Failed to process market analysis request",
            details={"instrument_id": instrument_id, "error": str(e)}
        )


@router.get("/real-time-indicators/{instrument_id}")
@validate_instrument_exists
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
    start_time = datetime.utcnow()
    response_builder = AnalyticsResponseBuilder()
    
    try:
        # Get instrument (validation decorator already confirmed it exists)
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one()
        
        # Convert string indicators to enum
        try:
            indicator_enums = [TechnicalIndicator(ind) for ind in indicators]
        except ValueError as e:
            raise ValidationError(
                error_code="ANALYTICS_003",
                message=f"Invalid technical indicator: {e}",
                details={"invalid_indicators": indicators, "available_indicators": [ti.value for ti in TechnicalIndicator]}
            )
        
        # Get real-time indicators
        results = await analytics_engine.get_real_time_indicators(
            instrument_id, indicator_enums
        )
        
        # Prepare response data
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
        
        # Calculate performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        data_points = len(results)
        
        # Build standardized response
        return response_builder.success(response_data) \
            .with_performance_metrics(processing_time, data_points) \
            .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        logger.error(f"Error getting real-time indicators: {e}")
        raise SystemError(
            error_code="ANALYTICS_004", 
            message="Failed to retrieve real-time indicators",
            details={"instrument_id": instrument_id, "error": str(e)}
        )


@router.post("/predict-price")
@validate_instrument_exists
@validate_confidence_level(allowed=[0.7, 0.8, 0.9, 0.95, 0.99])
async def predict_price(request: PredictionRequest, session=Depends(get_db_session)):
    """
    Predict future price using machine learning models.
    
    Available models: lstm_price_predictor, random_forest_predictor
    Horizons: short_term (5 minutes), medium_term (1 hour), long_term (1 day)
    """
    start_time = datetime.utcnow()
    response_builder = AnalyticsResponseBuilder()
    
    try:
        # Get instrument (validation decorator already confirmed it exists)
        result = await session.execute(
            select(Instrument).where(Instrument.id == request.instrument_id)
        )
        instrument = result.scalar_one()
        
        # Convert string enums with validation
        try:
            model_type = ModelType(request.model_type)
            horizon = PredictionHorizon(request.horizon)
        except ValueError as e:
            raise ValidationError(
                error_code="ANALYTICS_005",
                message=f"Invalid prediction parameter: {e}",
                details={
                    "provided_model_type": request.model_type,
                    "provided_horizon": request.horizon,
                    "available_models": [mt.value for mt in ModelType],
                    "available_horizons": [ph.value for ph in PredictionHorizon]
                }
            )
        
        # Get prediction
        prediction = await ml_service.predict_price(
            request.instrument_id, horizon, model_type
        )
        
        if not prediction:
            raise ValidationError(
                error_code="ANALYTICS_006",
                message="Unable to generate price prediction",
                details={"instrument_id": request.instrument_id, "reason": "insufficient_data"}
            )
        
        # Prepare response data
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
        
        # Check confidence threshold
        if prediction.confidence_score < request.confidence_threshold:
            response_data["warning"] = {
                "message": "Prediction confidence below requested threshold",
                "confidence_threshold": request.confidence_threshold,
                "actual_confidence": prediction.confidence_score
            }
        
        # Calculate performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Build standardized response
        return response_builder.success(response_data) \
            .with_performance_metrics(processing_time, 1) \
            .with_confidence_score(prediction.confidence_score) \
            .with_model_metadata(model_type.value, "1.0") \
            .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        logger.error(f"Error predicting price: {e}")
        raise SystemError(
            error_code="ANALYTICS_007", 
            message="Failed to generate price prediction",
            details={"instrument_id": request.instrument_id, "error": str(e)}
        )


@router.get("/anomaly-detection/{instrument_id}")
@validate_instrument_exists
@validate_lookback_hours(min_hours=1, max_hours=168)
async def detect_anomalies(
    instrument_id: int = Path(..., description="Instrument ID"),
    lookback_hours: int = Query(default=24, ge=1, le=168),
    session=Depends(get_db_session)
):
    """
    Detect anomalous market behavior using machine learning.
    
    Returns detected anomalies with severity scores and timestamps.
    """
    start_time = datetime.utcnow()
    response_builder = AnalyticsResponseBuilder()
    
    try:
        # Get instrument (validation decorator already confirmed it exists)
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one()
        
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
        
        # Calculate performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        data_points = len(anomalies)
        
        # Build standardized response
        return response_builder.success(response_data) \
            .with_performance_metrics(processing_time, data_points) \
            .with_model_metadata("anomaly_detector", "1.0") \
            .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise SystemError(
            error_code="ANALYTICS_008", 
            message="Failed to detect market anomalies",
            details={"instrument_id": instrument_id, "error": str(e)}
        )


@router.get("/trend-classification/{instrument_id}")
@validate_instrument_exists
async def classify_trend(
    instrument_id: int = Path(..., description="Instrument ID"),
    session=Depends(get_db_session)
):
    """
    Classify current market trend using machine learning.
    
    Returns trend classification (bullish, bearish, sideways) with confidence.
    """
    start_time = datetime.utcnow()
    response_builder = AnalyticsResponseBuilder()
    
    try:
        # Get instrument (validation decorator already confirmed it exists)
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one()
        
        # Classify trend
        trend_result = await ml_service.classify_trend(instrument_id)
        
        response_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "instrument_id": instrument_id,
            "instrument_symbol": instrument.symbol,
            **trend_result
        }
        
        # Calculate performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Build standardized response
        return response_builder.success(response_data) \
            .with_performance_metrics(processing_time, 1) \
            .with_confidence_score(trend_result.get("confidence", 1.0)) \
            .with_model_metadata("trend_classifier", "1.0") \
            .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        logger.error(f"Error classifying trend: {e}")
        raise SystemError(
            error_code="ANALYTICS_009", 
            message="Failed to classify market trend",
            details={"instrument_id": instrument_id, "error": str(e)}
        )


@router.post("/calculate-var")
@validate_instrument_exists
@validate_confidence_level(allowed=[0.90, 0.95, 0.99, 0.999])
async def calculate_var(request: RiskRequest, session=Depends(get_db_session)):
    """
    Calculate Value at Risk (VaR) for a position.
    
    Methods: historical, parametric, monte_carlo
    Confidence levels: 0.90, 0.95, 0.99, 0.999
    """
    start_time = datetime.utcnow()
    response_builder = AnalyticsResponseBuilder()
    
    try:
        # Get instrument (validation decorator already confirmed it exists)
        result = await session.execute(
            select(Instrument).where(Instrument.id == request.instrument_id)
        )
        instrument = result.scalar_one()
        
        # Convert confidence level to enum
        confidence_enum_map = {
            0.90: ConfidenceLevel.NINETY,
            0.95: ConfidenceLevel.NINETY_FIVE,
            0.99: ConfidenceLevel.NINETY_NINE,
            0.999: ConfidenceLevel.NINETY_NINE_NINE
        }
        
        confidence_enum = confidence_enum_map.get(request.confidence_level)
        if not confidence_enum:
            raise ValidationError(
                error_code="ANALYTICS_010",
                message="Invalid confidence level for VaR calculation",
                details={"provided": request.confidence_level, "supported": list(confidence_enum_map.keys())}
            )
        
        # Calculate VaR
        var_result = await risk_calculator.calculate_var(
            request.instrument_id,
            confidence_enum,
            request.time_horizon_days,
            request.position_size,
            request.method
        )
        
        if not var_result:
            raise ValidationError(
                error_code="ANALYTICS_011",
                message="Unable to calculate VaR",
                details={"instrument_id": request.instrument_id, "reason": "insufficient_data"}
            )
        
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
        
        # Calculate performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Build standardized response
        return response_builder.success(response_data) \
            .with_performance_metrics(processing_time, 1) \
            .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        logger.error(f"Error calculating VaR: {e}")
        raise SystemError(
            error_code="ANALYTICS_012", 
            message="Failed to calculate Value at Risk",
            details={"instrument_id": request.instrument_id, "error": str(e)}
        )


@router.get("/risk-metrics/{instrument_id}")
@validate_instrument_exists
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
    start_time = datetime.utcnow()
    response_builder = AnalyticsResponseBuilder()
    
    try:
        # Get instrument (validation decorator already confirmed it exists)
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one()
        
        # Validate benchmark if provided
        benchmark = None
        if benchmark_id:
            result = await session.execute(
                select(Instrument).where(Instrument.id == benchmark_id)
            )
            benchmark = result.scalar_one_or_none()
            if not benchmark:
                raise ValidationError(
                    error_code="ANALYTICS_013",
                    message="Benchmark instrument not found",
                    details={"benchmark_id": benchmark_id}
                )
        
        # Calculate risk metrics
        risk_metrics = await risk_calculator.calculate_comprehensive_risk_metrics(
            instrument_id, lookback_days, benchmark_id
        )
        
        if not risk_metrics:
            raise ValidationError(
                error_code="ANALYTICS_014",
                message="Unable to calculate risk metrics",
                details={"instrument_id": instrument_id, "reason": "insufficient_data"}
            )
        
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
                "benchmark_symbol": benchmark.symbol if benchmark else None,
                "last_updated": risk_metrics.last_updated.isoformat()
            }
        }
        
        # Calculate performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Build standardized response
        return response_builder.success(response_data) \
            .with_performance_metrics(processing_time, len(risk_metrics.risk_metrics)) \
            .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise SystemError(
            error_code="ANALYTICS_015", 
            message="Failed to calculate comprehensive risk metrics",
            details={"instrument_id": instrument_id, "error": str(e)}
        )


@router.post("/stress-test")
@validate_instrument_exists
async def perform_stress_test(
    request: StressTestRequest,
    session=Depends(get_db_session)
):
    """
    Perform stress testing on an instrument position.
    
    Tests various market shock scenarios and estimates recovery times.
    """
    start_time = datetime.utcnow()
    response_builder = AnalyticsResponseBuilder()
    
    try:
        # Get instrument (validation decorator already confirmed it exists)
        result = await session.execute(
            select(Instrument).where(Instrument.id == request.instrument_id)
        )
        instrument = result.scalar_one()
        
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
        
        # Calculate performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Build standardized response
        return response_builder.success(response_data) \
            .with_performance_metrics(processing_time, len(stress_results)) \
            .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        logger.error(f"Error performing stress test: {e}")
        raise SystemError(
            error_code="ANALYTICS_016", 
            message="Failed to perform stress test",
            details={"instrument_id": request.instrument_id, "error": str(e)}
        )


@router.post("/volume-profile")
@validate_instrument_exists
@validate_lookback_hours(min_hours=1, max_hours=168)
async def get_volume_profile(
    request: VolumeProfileRequest,
    session=Depends(get_db_session)
):
    """
    Get volume profile analysis for an instrument.
    
    Returns Point of Control (POC), value area, and volume distribution.
    """
    start_time = datetime.utcnow()
    response_builder = AnalyticsResponseBuilder()
    
    try:
        # Get instrument (validation decorator already confirmed it exists)
        result = await session.execute(
            select(Instrument).where(Instrument.id == request.instrument_id)
        )
        instrument = result.scalar_one()
        
        # Get volume profile
        volume_profile = await market_data_processor.analyze_volume_profile(
            request.instrument_id, request.lookback_hours, request.price_bins
        )
        
        if not volume_profile:
            raise ValidationError(
                error_code="ANALYTICS_021",
                message="Unable to generate volume profile",
                details={"instrument_id": request.instrument_id, "reason": "insufficient_data"}
            )
        
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
        
        # Calculate performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Build standardized response
        return response_builder.success(response_data) \
            .with_performance_metrics(processing_time, len(volume_profile.price_levels)) \
            .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        logger.error(f"Error getting volume profile: {e}")
        raise SystemError(
            error_code="ANALYTICS_022", 
            message="Failed to generate volume profile",
            details={"instrument_id": request.instrument_id, "error": str(e)}
        )


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
    start_time = datetime.utcnow()
    response_builder = AnalyticsResponseBuilder()
    
    try:
        if len(instrument_ids) < 2:
            raise ValidationError(
                error_code="ANALYTICS_017",
                message="At least 2 instruments required for correlation matrix",
                details={"provided_count": len(instrument_ids)}
            )
        
        # Validate all instruments exist
        result = await session.execute(
            select(Instrument).where(Instrument.id.in_(instrument_ids))
        )
        instruments = result.scalars().all()
        found_ids = [inst.id for inst in instruments]
        
        missing_ids = set(instrument_ids) - set(found_ids)
        if missing_ids:
            raise ValidationError(
                error_code="ANALYTICS_018",
                message="Some instruments not found",
                details={"missing_instrument_ids": list(missing_ids)}
            )
        
        # Calculate correlation matrix
        correlation_result = await risk_calculator.calculate_correlation_matrix(
            instrument_ids, lookback_days
        )
        
        if not correlation_result:
            raise ValidationError(
                error_code="ANALYTICS_019",
                message="Unable to calculate correlation matrix",
                details={"instrument_ids": instrument_ids, "reason": "insufficient_data"}
            )
        
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
        
        # Calculate performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        matrix_size = len(instrument_ids)
        
        # Build standardized response
        return response_builder.success(response_data) \
            .with_performance_metrics(processing_time, matrix_size) \
            .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        logger.error(f"Error calculating correlation matrix: {e}")
        raise SystemError(
            error_code="ANALYTICS_020", 
            message="Failed to calculate correlation matrix",
            details={"instrument_ids": instrument_ids, "error": str(e)}
        )


@router.get("/market-microstructure/{instrument_id}")
@validate_instrument_exists
async def get_market_microstructure(
    instrument_id: int = Path(..., description="Instrument ID"),
    lookback_minutes: int = Query(default=60, ge=5, le=1440),
    session=Depends(get_db_session)
):
    """
    Get market microstructure analysis for an instrument.
    
    Returns bid-ask spreads, market impact, and order flow metrics.
    """
    start_time = datetime.utcnow()
    response_builder = AnalyticsResponseBuilder()
    
    try:
        # Get instrument (validation decorator already confirmed it exists)
        result = await session.execute(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = result.scalar_one()
        
        # Get microstructure analysis
        microstructure = await market_data_processor.calculate_market_microstructure(
            instrument_id, lookback_minutes
        )
        
        if not microstructure:
            raise ValidationError(
                error_code="ANALYTICS_023",
                message="Unable to calculate market microstructure",
                details={"instrument_id": instrument_id, "reason": "insufficient_data"}
            )
        
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
        
        # Calculate performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Build standardized response
        return response_builder.success(response_data) \
            .with_performance_metrics(processing_time, 6) \
            .build()
        
    except StandardAPIError:
        raise
    except Exception as e:
        logger.error(f"Error getting market microstructure: {e}")
        raise SystemError(
            error_code="ANALYTICS_024", 
            message="Failed to calculate market microstructure",
            details={"instrument_id": instrument_id, "error": str(e)}
        )


# Health check endpoint
# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for analytics services."""
    response_builder = AnalyticsResponseBuilder()
    
    try:
        # Check service availability
        services_status = {
            "analytics_engine": "available",
            "ml_service": "available" if ml_service else "unavailable",
            "risk_calculator": "available",
            "market_data_processor": "available"
        }
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_status
        }
        
        return response_builder.success(health_data).build()
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise SystemError(
            error_code="ANALYTICS_025",
            message="Analytics health check failed", 
            details={"error": str(e)}
        )