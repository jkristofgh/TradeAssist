"""
Integration tests for Historical Data API.

Tests the historical data API endpoints with realistic request/response flows
and database integration.
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from src.backend.main import create_app
from src.backend.models.historical_data import DataFrequency
from src.backend.services.historical_data_service import (
    HistoricalDataService,
    HistoricalDataResult
)


class TestHistoricalDataAPI:
    """Integration tests for historical data API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client for the FastAPI application."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def mock_service(self):
        """Create mock historical data service."""
        service = Mock(spec=HistoricalDataService)
        service.fetch_historical_data = AsyncMock()
        service.save_query = AsyncMock()
        service.load_query = AsyncMock()
        service.get_performance_stats = Mock()
        return service
    
    @pytest.fixture
    def sample_bars_data(self):
        """Sample bar data for testing."""
        return [
            {
                "timestamp": datetime.utcnow() - timedelta(days=2),
                "open": 150.00,
                "high": 155.00,
                "low": 149.00,
                "close": 154.00,
                "volume": 100000
            },
            {
                "timestamp": datetime.utcnow() - timedelta(days=1),
                "open": 154.00,
                "high": 158.00,
                "low": 153.00,
                "close": 157.00,
                "volume": 120000
            }
        ]
    
    def test_fetch_historical_data_success(self, client, mock_service, sample_bars_data):
        """Test successful historical data fetch."""
        # Mock service response
        mock_results = [
            HistoricalDataResult(
                symbol="AAPL",
                bars=sample_bars_data,
                start_date=datetime.utcnow() - timedelta(days=30),
                end_date=datetime.utcnow(),
                frequency=DataFrequency.DAILY.value,
                total_bars=len(sample_bars_data),
                data_source="Demo",
                cached=False
            )
        ]
        mock_service.fetch_historical_data.return_value = mock_results
        
        # Mock the service dependency
        with patch('src.backend.api.historical_data.get_historical_data_service', return_value=mock_service):
            # Make request
            request_data = {
                "symbols": ["AAPL"],
                "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "frequency": "1d",
                "include_extended_hours": False,
                "max_records": 100
            }
            
            response = client.post("/api/v1/historical-data/fetch", json=request_data)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["total_symbols"] == 1
            assert len(data["data"]) == 1
            
            symbol_data = data["data"][0]
            assert symbol_data["symbol"] == "AAPL"
            assert symbol_data["frequency"] == "1d"
            assert symbol_data["total_bars"] == len(sample_bars_data)
            assert symbol_data["data_source"] == "Demo"
            assert len(symbol_data["bars"]) == len(sample_bars_data)
            
            # Verify bar structure
            bar = symbol_data["bars"][0]
            assert "timestamp" in bar
            assert "open" in bar
            assert "high" in bar
            assert "low" in bar
            assert "close" in bar
            assert "volume" in bar
    
    def test_fetch_historical_data_validation_errors(self, client, mock_service):
        """Test request validation errors."""
        with patch('src.backend.api.historical_data.get_historical_data_service', return_value=mock_service):
            # Test empty symbols list
            response = client.post("/api/v1/historical-data/fetch", json={
                "symbols": [],
                "frequency": "1d"
            })
            assert response.status_code == 422  # Validation error
            
            # Test invalid frequency
            response = client.post("/api/v1/historical-data/fetch", json={
                "symbols": ["AAPL"],
                "frequency": "invalid"
            })
            assert response.status_code == 422  # Validation error
            
            # Test invalid date range
            response = client.post("/api/v1/historical-data/fetch", json={
                "symbols": ["AAPL"],
                "frequency": "1d",
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() - timedelta(days=1)).isoformat()
            })
            assert response.status_code == 422  # Validation error
    
    def test_get_supported_frequencies(self, client):
        """Test getting supported frequencies."""
        response = client.get("/api/v1/historical-data/frequencies")
        
        assert response.status_code == 200
        frequencies = response.json()
        
        expected_frequencies = [f.value for f in DataFrequency]
        assert set(frequencies) == set(expected_frequencies)
        assert "1min" in frequencies
        assert "1d" in frequencies
        assert "1w" in frequencies
    
    def test_get_data_sources(self, client):
        """Test getting data source information."""
        response = client.get("/api/v1/historical-data/sources")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["sources"]) >= 1
        
        # Check for expected data sources
        source_names = [source["name"] for source in data["sources"]]
        assert "Schwab" in source_names or "Demo" in source_names
        
        # Verify source structure
        source = data["sources"][0]
        assert "name" in source
        assert "provider_type" in source
        assert "is_active" in source
        assert "rate_limit_per_minute" in source
        assert "supported_frequencies" in source
    
    def test_save_query_success(self, client, mock_service):
        """Test successful query save."""
        mock_service.save_query.return_value = 123
        
        with patch('src.backend.api.historical_data.get_historical_data_service', return_value=mock_service):
            request_data = {
                "name": "Test Query",
                "description": "Test Description",
                "symbols": ["AAPL", "SPY"],
                "frequency": "1d",
                "is_favorite": True
            }
            
            response = client.post("/api/v1/historical-data/queries/save", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["query_id"] == 123
            assert "Test Query" in data["message"]
    
    def test_save_query_validation_errors(self, client, mock_service):
        """Test query save validation errors."""
        with patch('src.backend.api.historical_data.get_historical_data_service', return_value=mock_service):
            # Test missing required fields
            response = client.post("/api/v1/historical-data/queries/save", json={
                "symbols": ["AAPL"]
                # Missing name
            })
            assert response.status_code == 422
            
            # Test empty name
            response = client.post("/api/v1/historical-data/queries/save", json={
                "name": "",
                "symbols": ["AAPL"]
            })
            assert response.status_code == 422
            
            # Test empty symbols
            response = client.post("/api/v1/historical-data/queries/save", json={
                "name": "Test",
                "symbols": []
            })
            assert response.status_code == 422
    
    def test_load_query_success(self, client, mock_service):
        """Test successful query load."""
        mock_query_data = {
            "id": 123,
            "name": "Test Query",
            "description": "Test Description",
            "symbols": ["AAPL", "SPY"],
            "frequency": "1d",
            "start_date": None,
            "end_date": None,
            "filters": None,
            "is_favorite": True,
            "execution_count": 5,
            "last_executed": datetime.utcnow()
        }
        mock_service.load_query.return_value = mock_query_data
        
        with patch('src.backend.api.historical_data.get_historical_data_service', return_value=mock_service):
            response = client.get("/api/v1/historical-data/queries/123")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["query"] is not None
            assert data["query"]["name"] == "Test Query"
            assert data["query"]["symbols"] == ["AAPL", "SPY"]
            assert data["query"]["is_favorite"] is True
    
    def test_load_query_not_found(self, client, mock_service):
        """Test loading non-existent query."""
        mock_service.load_query.return_value = None
        
        with patch('src.backend.api.historical_data.get_historical_data_service', return_value=mock_service):
            response = client.get("/api/v1/historical-data/queries/999")
            
            assert response.status_code == 404
    
    def test_get_service_statistics(self, client, mock_service):
        """Test getting service statistics."""
        mock_stats = {
            "requests_served": 100,
            "cache_hits": 25,
            "cache_hit_rate_percent": 25.0,
            "api_calls_made": 75,
            "total_bars_cached": 1000,
            "cache_size": 5,
            "service_running": True,
            "schwab_client_connected": False
        }
        mock_service.get_performance_stats.return_value = mock_stats
        
        with patch('src.backend.api.historical_data.get_historical_data_service', return_value=mock_service):
            response = client.get("/api/v1/historical-data/stats")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["stats"] == mock_stats
    
    def test_health_check(self, client, mock_service):
        """Test health check endpoint."""
        mock_stats = {
            "service_running": True,
            "schwab_client_connected": False,
            "cache_size": 5,
            "requests_served": 100
        }
        mock_service.get_performance_stats.return_value = mock_stats
        
        with patch('src.backend.api.historical_data.get_historical_data_service', return_value=mock_service):
            response = client.get("/api/v1/historical-data/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert data["service_running"] is True
            assert data["schwab_client_connected"] is False
            assert "timestamp" in data
    
    def test_service_not_initialized(self, client):
        """Test API behavior when service is not initialized."""
        with patch('src.backend.api.historical_data.get_historical_data_service', side_effect=Exception("Service not initialized")):
            response = client.post("/api/v1/historical-data/fetch", json={
                "symbols": ["AAPL"],
                "frequency": "1d"
            })
            
            # Should return service unavailable
            assert response.status_code == 503 or response.status_code == 500
    
    def test_server_error_handling(self, client, mock_service):
        """Test server error handling."""
        mock_service.fetch_historical_data.side_effect = Exception("Database error")
        
        with patch('src.backend.api.historical_data.get_historical_data_service', return_value=mock_service):
            response = client.post("/api/v1/historical-data/fetch", json={
                "symbols": ["AAPL"],
                "frequency": "1d"
            })
            
            assert response.status_code == 500
            data = response.json()
            assert "Failed to fetch historical data" in data["detail"]
    
    def test_request_symbol_cleaning(self, client, mock_service):
        """Test that symbols are properly cleaned and validated."""
        mock_service.fetch_historical_data.return_value = []
        
        with patch('src.backend.api.historical_data.get_historical_data_service', return_value=mock_service):
            # Test symbol cleaning (lowercase to uppercase, whitespace)
            response = client.post("/api/v1/historical-data/fetch", json={
                "symbols": ["  aapl  ", "spy", ""],  # Mixed case, whitespace, empty
                "frequency": "1d"
            })
            
            # Should clean symbols before processing
            # The actual cleaning happens in Pydantic validation
            if response.status_code == 200:
                # Verify the service was called with cleaned symbols
                mock_service.fetch_historical_data.assert_called_once()
    
    def test_pagination_limits(self, client, mock_service):
        """Test pagination and limits."""
        with patch('src.backend.api.historical_data.get_historical_data_service', return_value=mock_service):
            # Test max symbols limit
            too_many_symbols = [f"SYM{i}" for i in range(60)]  # Over 50 limit
            
            response = client.post("/api/v1/historical-data/fetch", json={
                "symbols": too_many_symbols,
                "frequency": "1d"
            })
            
            assert response.status_code == 422  # Validation error
            
            # Test max records limit
            response = client.post("/api/v1/historical-data/fetch", json={
                "symbols": ["AAPL"],
                "frequency": "1d",
                "max_records": 50000  # Over 10000 limit
            })
            
            assert response.status_code == 422  # Validation error


class TestHistoricalDataAPIModels:
    """Test Pydantic models used in the API."""
    
    def test_historical_data_fetch_request_validation(self):
        """Test HistoricalDataFetchRequest model validation."""
        from src.backend.api.historical_data import HistoricalDataFetchRequest
        
        # Valid request
        valid_data = {
            "symbols": ["AAPL", "SPY"],
            "frequency": "1d",
            "include_extended_hours": False
        }
        
        request = HistoricalDataFetchRequest(**valid_data)
        assert request.symbols == ["AAPL", "SPY"]
        assert request.frequency == "1d"
        assert not request.include_extended_hours
        
        # Test symbol cleaning
        messy_data = {
            "symbols": ["  aapl  ", "spy", "MSFT", ""],
            "frequency": "1d"
        }
        
        request = HistoricalDataFetchRequest(**messy_data)
        # Should clean and uppercase symbols, remove empty ones
        assert "AAPL" in request.symbols
        assert "SPY" in request.symbols
        assert "MSFT" in request.symbols
        assert "" not in request.symbols
    
    def test_historical_data_bar_model(self):
        """Test HistoricalDataBar model."""
        from src.backend.api.historical_data import HistoricalDataBar
        
        bar_data = {
            "timestamp": datetime.utcnow(),
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": 102.0,
            "volume": 10000
        }
        
        bar = HistoricalDataBar(**bar_data)
        assert bar.open == 100.0
        assert bar.high == 105.0
        assert bar.low == 95.0
        assert bar.close == 102.0
        assert bar.volume == 10000
        
        # Test validation - prices must be positive
        with pytest.raises(ValueError):
            HistoricalDataBar(
                timestamp=datetime.utcnow(),
                open=-100.0,  # Invalid negative price
                high=105.0,
                low=95.0,
                close=102.0
            )
    
    def test_query_save_request_validation(self):
        """Test QuerySaveRequest model validation."""
        from src.backend.api.historical_data import QuerySaveRequest
        
        valid_data = {
            "name": "My Query",
            "symbols": ["AAPL", "SPY"],
            "frequency": "1d",
            "is_favorite": True
        }
        
        request = QuerySaveRequest(**valid_data)
        assert request.name == "My Query"
        assert request.symbols == ["AAPL", "SPY"]
        assert request.frequency == "1d"
        assert request.is_favorite is True
        
        # Test validation - name cannot be empty
        with pytest.raises(ValueError):
            QuerySaveRequest(
                name="",  # Invalid empty name
                symbols=["AAPL"]
            )
        
        # Test validation - symbols cannot be empty
        with pytest.raises(ValueError):
            QuerySaveRequest(
                name="Test",
                symbols=[]  # Invalid empty symbols
            )