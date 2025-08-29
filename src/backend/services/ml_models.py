"""
Machine Learning Models Service

Provides predictive analytics, pattern recognition, and ML-based insights
for the TradeAssist platform Phase 4 implementation.
"""

import asyncio
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Machine learning imports
try:
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    from sklearn.model_selection import train_test_split
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    SKLEARN_AVAILABLE = True
    TENSORFLOW_AVAILABLE = True
except ImportError as e:
    SKLEARN_AVAILABLE = False
    TENSORFLOW_AVAILABLE = False

from ..database.connection import get_db_session
from ..models.market_data import MarketData
from ..models.instruments import Instrument
from sqlalchemy import select, and_
from .analytics_engine import analytics_engine

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Machine learning model types."""
    LSTM_PRICE_PREDICTOR = "lstm_price_predictor"
    RANDOM_FOREST_PREDICTOR = "random_forest_predictor"
    ANOMALY_DETECTOR = "anomaly_detector"
    VOLATILITY_PREDICTOR = "volatility_predictor"
    TREND_CLASSIFIER = "trend_classifier"


class PredictionHorizon(Enum):
    """Prediction time horizons."""
    SHORT_TERM = "5_minutes"
    MEDIUM_TERM = "1_hour"
    LONG_TERM = "1_day"


@dataclass
class PredictionResult:
    """Result from ML model prediction."""
    model_type: ModelType
    timestamp: datetime
    instrument_id: int
    prediction_horizon: PredictionHorizon
    predicted_value: float
    confidence_score: float
    feature_importance: Dict[str, float]
    metadata: Dict[str, Any]


@dataclass
class ModelPerformance:
    """Model performance metrics."""
    model_type: ModelType
    mae: float  # Mean Absolute Error
    mse: float  # Mean Squared Error
    rmse: float  # Root Mean Squared Error
    accuracy: float  # For classification models
    last_updated: datetime
    sample_size: int


class MLModelsService:
    """
    Machine Learning Models Service for predictive analytics.
    
    Provides price prediction, anomaly detection, trend classification,
    and volatility forecasting using various ML algorithms.
    """
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.model_performance: Dict[ModelType, ModelPerformance] = {}
        self.feature_cache: Dict[int, pd.DataFrame] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Model parameters
        self.lstm_params = {
            'sequence_length': 60,
            'epochs': 50,
            'batch_size': 32,
            'units': 50,
            'dropout': 0.2
        }
        
        self.rf_params = {
            'n_estimators': 100,
            'max_depth': 10,
            'random_state': 42
        }
    
    async def initialize_models(self) -> bool:
        """
        Initialize and load pre-trained models.
        
        Returns:
            bool: True if initialization successful.
        """
        if not SKLEARN_AVAILABLE:
            logger.error("Scikit-learn not available. ML features will be limited.")
            return False
        
        try:
            logger.info("Initializing ML models...")
            
            # Initialize scalers
            self.scalers['price_scaler'] = MinMaxScaler(feature_range=(0, 1))
            self.scalers['feature_scaler'] = StandardScaler()
            
            # Try to load existing models, create new ones if not found
            await self._load_or_create_models()
            
            logger.info("ML models initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
            return False
    
    async def predict_price(
        self,
        instrument_id: int,
        horizon: PredictionHorizon = PredictionHorizon.SHORT_TERM,
        model_type: ModelType = ModelType.LSTM_PRICE_PREDICTOR
    ) -> Optional[PredictionResult]:
        """
        Predict future price using ML models.
        
        Args:
            instrument_id: ID of instrument to predict.
            horizon: Prediction time horizon.
            model_type: Type of ML model to use.
            
        Returns:
            PredictionResult: Prediction result or None.
        """
        try:
            # Get features for prediction
            features = await self._get_prediction_features(instrument_id)
            if features is None or features.empty:
                logger.warning(f"No features available for prediction")
                return None
            
            # Route to appropriate prediction method
            if model_type == ModelType.LSTM_PRICE_PREDICTOR and TENSORFLOW_AVAILABLE:
                return await self._predict_with_lstm(instrument_id, horizon, features)
            elif model_type == ModelType.RANDOM_FOREST_PREDICTOR:
                return await self._predict_with_random_forest(instrument_id, horizon, features)
            else:
                logger.warning(f"Model type {model_type.value} not available")
                return None
                
        except Exception as e:
            logger.error(f"Error in price prediction: {e}")
            return None
    
    async def detect_anomalies(
        self,
        instrument_id: int,
        lookback_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous market behavior.
        
        Args:
            instrument_id: ID of instrument to analyze.
            lookback_hours: Hours of data to analyze.
            
        Returns:
            List: Detected anomalies with details.
        """
        try:
            features = await self._get_prediction_features(instrument_id, lookback_hours)
            if features is None or features.empty:
                return []
            
            # Use Isolation Forest for anomaly detection
            model_key = f"anomaly_detector_{instrument_id}"
            if model_key not in self.models:
                await self._create_anomaly_detector(instrument_id, features)
            
            model = self.models.get(model_key)
            if not model:
                return []
            
            # Predict anomalies
            anomaly_scores = model.decision_function(features.values)
            is_anomaly = model.predict(features.values)
            
            anomalies = []
            for i, (score, is_anom) in enumerate(zip(anomaly_scores, is_anomaly)):
                if is_anom == -1:  # Anomaly detected
                    anomalies.append({
                        'timestamp': features.index[i],
                        'anomaly_score': float(score),
                        'severity': 'high' if score < -0.5 else 'medium',
                        'features': features.iloc[i].to_dict()
                    })
            
            # Sort by severity (most anomalous first)
            anomalies.sort(key=lambda x: x['anomaly_score'])
            
            return anomalies[:10]  # Return top 10 anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    async def classify_trend(
        self,
        instrument_id: int
    ) -> Dict[str, Any]:
        """
        Classify current trend using ML.
        
        Args:
            instrument_id: ID of instrument to analyze.
            
        Returns:
            Dict: Trend classification results.
        """
        try:
            features = await self._get_prediction_features(instrument_id, 48)  # 48 hours
            if features is None or features.empty:
                return {'trend': 'unknown', 'confidence': 0.0}
            
            # Simple trend classification based on price movement
            prices = features['close'] if 'close' in features.columns else features.iloc[:, 0]
            
            # Calculate trend metrics
            recent_prices = prices.tail(20)
            trend_slope = np.polyfit(range(len(recent_prices)), recent_prices.values, 1)[0]
            
            # Classify trend
            if trend_slope > 0.001:
                trend = 'bullish'
                confidence = min(abs(trend_slope) * 1000, 1.0)
            elif trend_slope < -0.001:
                trend = 'bearish'
                confidence = min(abs(trend_slope) * 1000, 1.0)
            else:
                trend = 'sideways'
                confidence = 0.5
            
            # Calculate additional metrics
            volatility = prices.pct_change().std()
            momentum = (prices.iloc[-1] - prices.iloc[-10]) / prices.iloc[-10] if len(prices) >= 10 else 0
            
            return {
                'trend': trend,
                'confidence': confidence,
                'trend_slope': trend_slope,
                'volatility': volatility,
                'momentum': momentum,
                'analysis_period': '20_periods'
            }
            
        except Exception as e:
            logger.error(f"Error classifying trend: {e}")
            return {'trend': 'unknown', 'confidence': 0.0}
    
    async def _predict_with_lstm(
        self,
        instrument_id: int,
        horizon: PredictionHorizon,
        features: pd.DataFrame
    ) -> Optional[PredictionResult]:
        """Predict using LSTM neural network."""
        try:
            if not TENSORFLOW_AVAILABLE:
                logger.warning("TensorFlow not available for LSTM prediction")
                return None
            
            model_key = f"lstm_{instrument_id}_{horizon.value}"
            
            # Check if model exists, create if not
            if model_key not in self.models:
                await self._create_lstm_model(instrument_id, horizon, features)
            
            model = self.models.get(model_key)
            scaler = self.scalers.get(f"{model_key}_scaler")
            
            if not model or not scaler:
                logger.warning(f"LSTM model or scaler not available for {model_key}")
                return None
            
            # Prepare sequence for prediction
            sequence_length = self.lstm_params['sequence_length']
            prices = features['close'].values.reshape(-1, 1)
            
            if len(prices) < sequence_length:
                logger.warning(f"Insufficient data for LSTM prediction ({len(prices)} < {sequence_length})")
                return None
            
            # Scale the data
            scaled_prices = scaler.transform(prices)
            
            # Create sequence for prediction
            sequence = scaled_prices[-sequence_length:].reshape(1, sequence_length, 1)
            
            # Make prediction
            scaled_prediction = model.predict(sequence, verbose=0)[0][0]
            prediction = scaler.inverse_transform([[scaled_prediction]])[0][0]
            
            # Calculate confidence based on recent model performance
            confidence = self._calculate_model_confidence(ModelType.LSTM_PRICE_PREDICTOR)
            
            return PredictionResult(
                model_type=ModelType.LSTM_PRICE_PREDICTOR,
                timestamp=datetime.utcnow(),
                instrument_id=instrument_id,
                prediction_horizon=horizon,
                predicted_value=float(prediction),
                confidence_score=confidence,
                feature_importance={},
                metadata={
                    'sequence_length': sequence_length,
                    'current_price': float(prices[-1][0])
                }
            )
            
        except Exception as e:
            logger.error(f"Error in LSTM prediction: {e}")
            return None
    
    async def _predict_with_random_forest(
        self,
        instrument_id: int,
        horizon: PredictionHorizon,
        features: pd.DataFrame
    ) -> Optional[PredictionResult]:
        """Predict using Random Forest."""
        try:
            model_key = f"rf_{instrument_id}_{horizon.value}"
            
            # Check if model exists, create if not
            if model_key not in self.models:
                await self._create_random_forest_model(instrument_id, horizon, features)
            
            model = self.models.get(model_key)
            scaler = self.scalers.get(f"{model_key}_scaler")
            
            if not model:
                logger.warning(f"Random Forest model not available for {model_key}")
                return None
            
            # Prepare features for prediction
            feature_columns = [col for col in features.columns if col != 'close']
            if not feature_columns:
                logger.warning("No features available for Random Forest prediction")
                return None
            
            # Use latest data point
            latest_features = features[feature_columns].iloc[-1:].values
            
            # Scale features if scaler exists
            if scaler:
                latest_features = scaler.transform(latest_features)
            
            # Make prediction
            prediction = model.predict(latest_features)[0]
            
            # Get feature importance
            feature_importance = {}
            if hasattr(model, 'feature_importances_'):
                for i, col in enumerate(feature_columns):
                    feature_importance[col] = float(model.feature_importances_[i])
            
            # Calculate confidence
            confidence = self._calculate_model_confidence(ModelType.RANDOM_FOREST_PREDICTOR)
            
            return PredictionResult(
                model_type=ModelType.RANDOM_FOREST_PREDICTOR,
                timestamp=datetime.utcnow(),
                instrument_id=instrument_id,
                prediction_horizon=horizon,
                predicted_value=float(prediction),
                confidence_score=confidence,
                feature_importance=feature_importance,
                metadata={
                    'features_used': len(feature_columns),
                    'current_price': float(features['close'].iloc[-1])
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Random Forest prediction: {e}")
            return None
    
    async def _get_prediction_features(
        self,
        instrument_id: int,
        lookback_hours: int = 24
    ) -> Optional[pd.DataFrame]:
        """Get features for ML prediction."""
        try:
            # Check cache first
            cache_key = f"{instrument_id}_{lookback_hours}"
            if cache_key in self.feature_cache:
                cached_features = self.feature_cache[cache_key]
                if (datetime.utcnow() - cached_features.index[-1]).total_seconds() < self.cache_ttl:
                    return cached_features
            
            # Get market analysis from analytics engine
            analysis = await analytics_engine.get_market_analysis(instrument_id, lookback_hours)
            if not analysis:
                return None
            
            # Get raw market data
            async with get_db_session() as session:
                cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
                
                result = await session.execute(
                    select(MarketData)
                    .where(
                        and_(
                            MarketData.instrument_id == instrument_id,
                            MarketData.timestamp >= cutoff_time
                        )
                    )
                    .order_by(MarketData.timestamp)
                )
                
                records = result.scalars().all()
                
                if not records:
                    return None
                
                # Convert to DataFrame
                data = []
                for record in records:
                    data.append({
                        'timestamp': record.timestamp,
                        'open': float(record.price) if record.price else 0.0,
                        'high': float(record.price) if record.price else 0.0,
                        'low': float(record.price) if record.price else 0.0,
                        'close': float(record.price) if record.price else 0.0,
                        'volume': record.volume if record.volume else 0
                    })
                
                df = pd.DataFrame(data)
                if df.empty:
                    return None
                
                df.set_index('timestamp', inplace=True)
                
                # Add technical indicators as features
                await self._add_technical_features(df)
                
                # Cache the result
                self.feature_cache[cache_key] = df
                
                return df
                
        except Exception as e:
            logger.error(f"Error getting prediction features: {e}")
            return None
    
    async def _add_technical_features(self, df: pd.DataFrame) -> None:
        """Add technical indicators as features to DataFrame."""
        try:
            prices = df['close']
            
            # Moving averages
            df['ma_5'] = prices.rolling(window=5).mean()
            df['ma_10'] = prices.rolling(window=10).mean()
            df['ma_20'] = prices.rolling(window=20).mean()
            
            # RSI
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Price changes
            df['price_change_1'] = prices.pct_change(1)
            df['price_change_5'] = prices.pct_change(5)
            df['price_change_10'] = prices.pct_change(10)
            
            # Volume indicators
            df['volume_ma'] = df['volume'].rolling(window=10).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            
            # Volatility
            df['volatility'] = prices.rolling(window=20).std()
            
            # Price position relative to recent range
            df['price_position'] = (prices - prices.rolling(window=20).min()) / (
                prices.rolling(window=20).max() - prices.rolling(window=20).min()
            )
            
            # Fill NaN values
            df.fillna(method='ffill', inplace=True)
            df.fillna(0, inplace=True)
            
        except Exception as e:
            logger.error(f"Error adding technical features: {e}")
    
    async def _create_lstm_model(
        self,
        instrument_id: int,
        horizon: PredictionHorizon,
        features: pd.DataFrame
    ) -> None:
        """Create and train LSTM model."""
        try:
            if not TENSORFLOW_AVAILABLE:
                return
            
            model_key = f"lstm_{instrument_id}_{horizon.value}"
            scaler_key = f"{model_key}_scaler"
            
            # Prepare training data
            prices = features['close'].values.reshape(-1, 1)
            
            # Create scaler and scale data
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(prices)
            self.scalers[scaler_key] = scaler
            
            # Create sequences
            sequence_length = self.lstm_params['sequence_length']
            X, y = [], []
            
            for i in range(sequence_length, len(scaled_data)):
                X.append(scaled_data[i-sequence_length:i, 0])
                y.append(scaled_data[i, 0])
            
            X, y = np.array(X), np.array(y)
            X = np.reshape(X, (X.shape[0], X.shape[1], 1))
            
            if len(X) < 10:  # Need minimum data for training
                logger.warning(f"Insufficient data for LSTM training: {len(X)} samples")
                return
            
            # Create model
            model = Sequential([
                LSTM(units=self.lstm_params['units'], 
                     return_sequences=True, 
                     input_shape=(X.shape[1], 1)),
                Dropout(self.lstm_params['dropout']),
                LSTM(units=self.lstm_params['units'], return_sequences=False),
                Dropout(self.lstm_params['dropout']),
                Dense(units=25),
                Dense(units=1)
            ])
            
            model.compile(optimizer='adam', loss='mean_squared_error')
            
            # Train model
            model.fit(X, y, batch_size=self.lstm_params['batch_size'],
                     epochs=min(self.lstm_params['epochs'], 10),  # Limit epochs for quick training
                     verbose=0)
            
            self.models[model_key] = model
            
            logger.info(f"LSTM model created and trained for {model_key}")
            
        except Exception as e:
            logger.error(f"Error creating LSTM model: {e}")
    
    async def _create_random_forest_model(
        self,
        instrument_id: int,
        horizon: PredictionHorizon,
        features: pd.DataFrame
    ) -> None:
        """Create and train Random Forest model."""
        try:
            model_key = f"rf_{instrument_id}_{horizon.value}"
            scaler_key = f"{model_key}_scaler"
            
            # Prepare features and targets
            feature_columns = [col for col in features.columns if col != 'close']
            if not feature_columns:
                logger.warning("No features available for Random Forest model")
                return
            
            X = features[feature_columns].values
            y = features['close'].values
            
            # Create shifted target (future price)
            shift_periods = 1 if horizon == PredictionHorizon.SHORT_TERM else 5
            y = np.roll(y, -shift_periods)
            
            # Remove last few rows due to shifting
            X = X[:-shift_periods]
            y = y[:-shift_periods]
            
            if len(X) < 20:  # Need minimum data for training
                logger.warning(f"Insufficient data for Random Forest training: {len(X)} samples")
                return
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers[scaler_key] = scaler
            
            # Create and train model
            model = RandomForestRegressor(**self.rf_params)
            model.fit(X_scaled, y)
            
            self.models[model_key] = model
            
            logger.info(f"Random Forest model created and trained for {model_key}")
            
        except Exception as e:
            logger.error(f"Error creating Random Forest model: {e}")
    
    async def _create_anomaly_detector(
        self,
        instrument_id: int,
        features: pd.DataFrame
    ) -> None:
        """Create anomaly detection model."""
        try:
            model_key = f"anomaly_detector_{instrument_id}"
            
            # Use all features for anomaly detection
            X = features.values
            
            # Create Isolation Forest model
            model = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100
            )
            
            model.fit(X)
            self.models[model_key] = model
            
            logger.info(f"Anomaly detector created for instrument {instrument_id}")
            
        except Exception as e:
            logger.error(f"Error creating anomaly detector: {e}")
    
    def _calculate_model_confidence(self, model_type: ModelType) -> float:
        """Calculate model confidence based on performance metrics."""
        if model_type not in self.model_performance:
            return 0.5  # Default confidence
        
        performance = self.model_performance[model_type]
        
        # Simple confidence calculation based on accuracy/error
        if hasattr(performance, 'accuracy') and performance.accuracy > 0:
            return min(performance.accuracy, 0.95)
        else:
            # For regression models, use inverse of RMSE (normalized)
            confidence = 1.0 / (1.0 + performance.rmse)
            return min(confidence, 0.95)
    
    async def _load_or_create_models(self) -> None:
        """Load existing models or initialize new ones."""
        try:
            # For now, we'll create models on-demand
            # In production, this would load pre-trained models from disk
            logger.info("Models will be created on-demand for each instrument")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")


# Global ML models service instance
ml_service = MLModelsService()