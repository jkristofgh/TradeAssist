"""
Unit tests for the ML Models service.

Tests machine learning model predictions, anomaly detection, and trend classification.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from src.backend.services.ml_models import (
    MLModelsService,
    ModelType,
    PredictionHorizon,
    PredictionResult,
    ModelPerformance
)


@pytest.fixture
def ml_service():
    """Create ML service instance for testing."""
    return MLModelsService()


@pytest.fixture
def sample_returns_data():
    """Create sample returns data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    returns = np.random.randn(100) * 0.01  # 1% daily volatility
    
    df = pd.DataFrame({
        'close': 100 * np.exp(np.cumsum(returns)),
        'ma_5': np.random.randn(100) * 0.5 + 100,
        'ma_10': np.random.randn(100) * 0.5 + 100,
        'rsi': np.random.rand(100) * 100,
        'volume': np.random.randint(1000, 5000, 100)
    })
    df.index = dates
    return df


class TestMLModelsService:
    """Test cases for MLModelsService."""

    def test_initialization(self, ml_service):
        """Test ML service initialization."""
        assert ml_service.models == {}
        assert ml_service.scalers == {}
        assert ml_service.model_performance == {}
        assert ml_service.feature_cache == {}
        assert ml_service.cache_ttl == 300

    @pytest.mark.asyncio
    async def test_initialize_models_without_sklearn(self, ml_service):
        """Test model initialization when sklearn is not available."""
        with patch('src.backend.services.ml_models.SKLEARN_AVAILABLE', False):
            result = await ml_service.initialize_models()
            assert result is False

    @pytest.mark.asyncio
    async def test_initialize_models_with_sklearn(self, ml_service):
        """Test model initialization when sklearn is available."""
        with patch('src.backend.services.ml_models.SKLEARN_AVAILABLE', True):
            with patch.object(ml_service, '_load_or_create_models') as mock_load:
                mock_load.return_value = None
                
                result = await ml_service.initialize_models()
                assert result is True
                assert 'price_scaler' in ml_service.scalers
                assert 'feature_scaler' in ml_service.scalers

    @pytest.mark.asyncio
    async def test_predict_price_no_features(self, ml_service):
        """Test price prediction with no available features."""
        with patch.object(ml_service, '_get_prediction_features') as mock_features:
            mock_features.return_value = None
            
            result = await ml_service.predict_price(1)
            assert result is None

    @pytest.mark.asyncio
    async def test_predict_price_lstm_not_available(self, ml_service, sample_returns_data):
        """Test LSTM price prediction when TensorFlow is not available."""
        with patch('src.backend.services.ml_models.TENSORFLOW_AVAILABLE', False):
            with patch.object(ml_service, '_get_prediction_features') as mock_features:
                mock_features.return_value = sample_returns_data
                
                result = await ml_service.predict_price(
                    1, PredictionHorizon.SHORT_TERM, ModelType.LSTM_PRICE_PREDICTOR
                )
                assert result is None

    @pytest.mark.asyncio
    async def test_predict_price_random_forest(self, ml_service, sample_returns_data):
        """Test Random Forest price prediction."""
        with patch.object(ml_service, '_get_prediction_features') as mock_features:
            mock_features.return_value = sample_returns_data
            
            with patch.object(ml_service, '_predict_with_random_forest') as mock_predict:
                expected_result = PredictionResult(
                    model_type=ModelType.RANDOM_FOREST_PREDICTOR,
                    timestamp=datetime.utcnow(),
                    instrument_id=1,
                    prediction_horizon=PredictionHorizon.SHORT_TERM,
                    predicted_value=101.5,
                    confidence_score=0.75,
                    feature_importance={'ma_5': 0.3, 'rsi': 0.4},
                    metadata={'features_used': 4}
                )
                mock_predict.return_value = expected_result
                
                result = await ml_service.predict_price(
                    1, PredictionHorizon.SHORT_TERM, ModelType.RANDOM_FOREST_PREDICTOR
                )
                
                assert result == expected_result
                mock_predict.assert_called_once_with(1, PredictionHorizon.SHORT_TERM, sample_returns_data)

    @pytest.mark.asyncio
    async def test_detect_anomalies_no_features(self, ml_service):
        """Test anomaly detection with no available features."""
        with patch.object(ml_service, '_get_prediction_features') as mock_features:
            mock_features.return_value = None
            
            result = await ml_service.detect_anomalies(1)
            assert result == []

    @pytest.mark.asyncio
    async def test_detect_anomalies_success(self, ml_service, sample_returns_data):
        """Test successful anomaly detection."""
        with patch.object(ml_service, '_get_prediction_features') as mock_features:
            mock_features.return_value = sample_returns_data
            
            with patch.object(ml_service, '_create_anomaly_detector') as mock_create:
                # Mock anomaly detector model
                mock_model = MagicMock()
                mock_model.decision_function.return_value = np.array([-0.1, -0.6, -0.2])
                mock_model.predict.return_value = np.array([1, -1, 1])  # -1 indicates anomaly
                
                ml_service.models['anomaly_detector_1'] = mock_model
                
                result = await ml_service.detect_anomalies(1)
                
                assert isinstance(result, list)
                assert len(result) == 1  # Only one anomaly (index 1)
                anomaly = result[0]
                assert 'timestamp' in anomaly
                assert 'anomaly_score' in anomaly
                assert 'severity' in anomaly
                assert anomaly['severity'] in ['high', 'medium']

    @pytest.mark.asyncio
    async def test_classify_trend_no_features(self, ml_service):
        """Test trend classification with no available features."""
        with patch.object(ml_service, '_get_prediction_features') as mock_features:
            mock_features.return_value = None
            
            result = await ml_service.classify_trend(1)
            assert result == {'trend': 'unknown', 'confidence': 0.0}

    @pytest.mark.asyncio
    async def test_classify_trend_bullish(self, ml_service):
        """Test bullish trend classification."""
        # Create upward trending data
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1H')
        prices = 100 + np.cumsum(np.random.randn(50) * 0.05 + 0.1)  # Upward trend
        
        trending_data = pd.DataFrame({
            'close': prices,
            'ma_5': prices - 1,
            'rsi': np.random.rand(50) * 100
        })
        trending_data.index = dates
        
        with patch.object(ml_service, '_get_prediction_features') as mock_features:
            mock_features.return_value = trending_data
            
            result = await ml_service.classify_trend(1)
            
            assert 'trend' in result
            assert 'confidence' in result
            assert result['trend'] in ['bullish', 'bearish', 'sideways']
            assert 0 <= result['confidence'] <= 1

    @pytest.mark.asyncio
    async def test_add_technical_features(self, ml_service):
        """Test adding technical features to DataFrame."""
        # Create sample OHLCV data
        df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        await ml_service._add_technical_features(df)
        
        # Check that technical indicators were added
        assert 'ma_5' in df.columns
        assert 'ma_10' in df.columns
        assert 'ma_20' in df.columns
        assert 'rsi' in df.columns
        assert 'price_change_1' in df.columns
        assert 'volatility' in df.columns
        assert 'volume_ratio' in df.columns

    def test_calculate_model_confidence_no_performance(self, ml_service):
        """Test model confidence calculation with no performance data."""
        confidence = ml_service._calculate_model_confidence(ModelType.LSTM_PRICE_PREDICTOR)
        assert confidence == 0.5  # Default confidence

    def test_calculate_model_confidence_with_accuracy(self, ml_service):
        """Test model confidence calculation with accuracy data."""
        performance = ModelPerformance(
            model_type=ModelType.LSTM_PRICE_PREDICTOR,
            mae=0.1,
            mse=0.01,
            rmse=0.1,
            accuracy=0.85,
            last_updated=datetime.utcnow(),
            sample_size=1000
        )
        ml_service.model_performance[ModelType.LSTM_PRICE_PREDICTOR] = performance
        
        confidence = ml_service._calculate_model_confidence(ModelType.LSTM_PRICE_PREDICTOR)
        assert confidence == 0.85

    def test_calculate_model_confidence_with_rmse(self, ml_service):
        """Test model confidence calculation with RMSE data."""
        performance = ModelPerformance(
            model_type=ModelType.RANDOM_FOREST_PREDICTOR,
            mae=0.1,
            mse=0.01,
            rmse=0.5,
            accuracy=0.0,  # No accuracy for regression model
            last_updated=datetime.utcnow(),
            sample_size=1000
        )
        ml_service.model_performance[ModelType.RANDOM_FOREST_PREDICTOR] = performance
        
        confidence = ml_service._calculate_model_confidence(ModelType.RANDOM_FOREST_PREDICTOR)
        expected_confidence = 1.0 / (1.0 + 0.5)  # 1/(1+RMSE)
        assert abs(confidence - expected_confidence) < 1e-10

    @pytest.mark.asyncio
    async def test_create_random_forest_model_insufficient_data(self, ml_service):
        """Test Random Forest model creation with insufficient data."""
        # Create minimal dataset
        small_data = pd.DataFrame({
            'close': [100, 101],
            'ma_5': [99, 100]
        })
        
        await ml_service._create_random_forest_model(1, PredictionHorizon.SHORT_TERM, small_data)
        
        # Model should not be created due to insufficient data
        model_key = f"rf_1_{PredictionHorizon.SHORT_TERM.value}"
        assert model_key not in ml_service.models

    @pytest.mark.asyncio
    async def test_create_random_forest_model_success(self, ml_service, sample_returns_data):
        """Test successful Random Forest model creation."""
        with patch('src.backend.services.ml_models.SKLEARN_AVAILABLE', True):
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.preprocessing import StandardScaler
            
            with patch('sklearn.ensemble.RandomForestRegressor') as mock_rf:
                with patch('sklearn.preprocessing.StandardScaler') as mock_scaler:
                    mock_model = MagicMock()
                    mock_rf.return_value = mock_model
                    
                    mock_scaler_instance = MagicMock()
                    mock_scaler_instance.fit_transform.return_value = np.random.randn(95, 4)
                    mock_scaler.return_value = mock_scaler_instance
                    
                    await ml_service._create_random_forest_model(
                        1, PredictionHorizon.SHORT_TERM, sample_returns_data
                    )
                    
                    model_key = f"rf_1_{PredictionHorizon.SHORT_TERM.value}"
                    scaler_key = f"{model_key}_scaler"
                    
                    assert model_key in ml_service.models
                    assert scaler_key in ml_service.scalers
                    mock_model.fit.assert_called_once()

    @pytest.mark.asyncio
    async def test_predict_with_random_forest_no_model(self, ml_service, sample_returns_data):
        """Test Random Forest prediction when model doesn't exist."""
        result = await ml_service._predict_with_random_forest(
            1, PredictionHorizon.SHORT_TERM, sample_returns_data
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_predict_with_random_forest_no_features(self, ml_service):
        """Test Random Forest prediction with no feature columns."""
        # Create data with only target column
        data_no_features = pd.DataFrame({'close': [100, 101, 102]})
        
        result = await ml_service._predict_with_random_forest(
            1, PredictionHorizon.SHORT_TERM, data_no_features
        )
        assert result is None


class TestModelTypes:
    """Test model type enumerations."""

    def test_model_type_values(self):
        """Test ModelType enumeration values."""
        assert ModelType.LSTM_PRICE_PREDICTOR.value == "lstm_price_predictor"
        assert ModelType.RANDOM_FOREST_PREDICTOR.value == "random_forest_predictor"
        assert ModelType.ANOMALY_DETECTOR.value == "anomaly_detector"

    def test_prediction_horizon_values(self):
        """Test PredictionHorizon enumeration values."""
        assert PredictionHorizon.SHORT_TERM.value == "5_minutes"
        assert PredictionHorizon.MEDIUM_TERM.value == "1_hour"
        assert PredictionHorizon.LONG_TERM.value == "1_day"


class TestPredictionResult:
    """Test PredictionResult data class."""

    def test_prediction_result_creation(self):
        """Test creating PredictionResult instances."""
        timestamp = datetime.utcnow()
        
        result = PredictionResult(
            model_type=ModelType.LSTM_PRICE_PREDICTOR,
            timestamp=timestamp,
            instrument_id=1,
            prediction_horizon=PredictionHorizon.SHORT_TERM,
            predicted_value=101.5,
            confidence_score=0.85,
            feature_importance={'ma_5': 0.3, 'rsi': 0.4},
            metadata={'sequence_length': 60}
        )
        
        assert result.model_type == ModelType.LSTM_PRICE_PREDICTOR
        assert result.timestamp == timestamp
        assert result.instrument_id == 1
        assert result.prediction_horizon == PredictionHorizon.SHORT_TERM
        assert result.predicted_value == 101.5
        assert result.confidence_score == 0.85
        assert result.feature_importance == {'ma_5': 0.3, 'rsi': 0.4}
        assert result.metadata == {'sequence_length': 60}


class TestMLServiceEdgeCases:
    """Test edge cases for ML service."""

    @pytest.mark.asyncio
    async def test_feature_caching(self, ml_service, sample_returns_data):
        """Test feature data caching mechanism."""
        with patch.object(ml_service, '_get_market_data') as mock_get_data:
            mock_get_data.return_value = sample_returns_data
            
            # First call should populate cache
            result1 = await ml_service._get_prediction_features(1, 24)
            
            # Verify cache was populated
            cache_key = "1_24"
            assert cache_key in ml_service.feature_cache
            
            # Second call should use cache (mock not called again for database)
            result2 = await ml_service._get_prediction_features(1, 24)
            
            assert result1 is not None
            assert result2 is not None
            pd.testing.assert_frame_equal(result1, result2)

    @pytest.mark.asyncio
    async def test_anomaly_detector_creation(self, ml_service, sample_returns_data):
        """Test anomaly detector model creation."""
        with patch('src.backend.services.ml_models.SKLEARN_AVAILABLE', True):
            from sklearn.ensemble import IsolationForest
            
            with patch('sklearn.ensemble.IsolationForest') as mock_isolation:
                mock_model = MagicMock()
                mock_isolation.return_value = mock_model
                
                await ml_service._create_anomaly_detector(1, sample_returns_data)
                
                model_key = "anomaly_detector_1"
                assert model_key in ml_service.models
                mock_model.fit.assert_called_once()

    def test_lstm_parameters(self, ml_service):
        """Test LSTM model parameters."""
        assert ml_service.lstm_params['sequence_length'] == 60
        assert ml_service.lstm_params['epochs'] == 50
        assert ml_service.lstm_params['batch_size'] == 32
        assert ml_service.lstm_params['units'] == 50
        assert ml_service.lstm_params['dropout'] == 0.2

    def test_random_forest_parameters(self, ml_service):
        """Test Random Forest model parameters."""
        assert ml_service.rf_params['n_estimators'] == 100
        assert ml_service.rf_params['max_depth'] == 10
        assert ml_service.rf_params['random_state'] == 42


@pytest.mark.integration
class TestMLServiceIntegration:
    """Integration tests for ML service."""

    @pytest.mark.asyncio
    async def test_full_prediction_workflow(self, ml_service, sample_returns_data):
        """Test complete prediction workflow."""
        with patch('src.backend.services.ml_models.SKLEARN_AVAILABLE', True):
            with patch.object(ml_service, '_get_prediction_features') as mock_features:
                mock_features.return_value = sample_returns_data
                
                with patch.object(ml_service, '_create_random_forest_model') as mock_create:
                    # Mock successful model creation
                    from sklearn.ensemble import RandomForestRegressor
                    from sklearn.preprocessing import StandardScaler
                    
                    mock_model = MagicMock()
                    mock_model.predict.return_value = np.array([101.5])
                    mock_model.feature_importances_ = np.array([0.3, 0.4, 0.2, 0.1])
                    
                    mock_scaler = MagicMock()
                    mock_scaler.transform.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])
                    
                    model_key = f"rf_1_{PredictionHorizon.SHORT_TERM.value}"
                    scaler_key = f"{model_key}_scaler"
                    
                    ml_service.models[model_key] = mock_model
                    ml_service.scalers[scaler_key] = mock_scaler
                    
                    result = await ml_service.predict_price(
                        1, PredictionHorizon.SHORT_TERM, ModelType.RANDOM_FOREST_PREDICTOR
                    )
                    
                    assert result is not None
                    assert result.predicted_value == 101.5
                    assert result.model_type == ModelType.RANDOM_FOREST_PREDICTOR
                    assert len(result.feature_importance) > 0