"""
Unit tests for HistoricalDataFetcher component.
Tests Phase 3 decomposition: data retrieval and API integration functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from src.backend.services.historical_data.fetcher import (
    HistoricalDataFetcher,
    CircuitBreakerError,
    RateLimitError
)
from src.backend.models.historical_data import DataFrequency


class TestHistoricalDataFetcher:
    """Test suite for HistoricalDataFetcher component."""

    @pytest.fixture
    def mock_schwab_client(self):
        """Create mock Schwab client."""
        client = Mock()
        client.client = AsyncMock()
        client.is_connected = True
        return client

    @pytest.fixture
    def fetcher_with_mock_client(self, mock_schwab_client):
        """Create fetcher with mock client."""
        return HistoricalDataFetcher(mock_schwab_client)

    @pytest.fixture
    def fetcher_mock_mode(self):
        """Create fetcher for mock data mode."""
        return HistoricalDataFetcher(None)

    @pytest.fixture
    def sample_schwab_response(self):
        """Sample DataFrame-like response from Schwab API."""
        import pandas as pd
        data = {
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [99.0, 100.0, 101.0],
            'close': [101.0, 102.0, 103.0],
            'volume': [1000000, 1100000, 1200000]
        }
        timestamps = [
            datetime(2024, 1, 1, 9, 30),
            datetime(2024, 1, 1, 10, 30),
            datetime(2024, 1, 1, 11, 30)
        ]
        return pd.DataFrame(data, index=timestamps)

    # Test initialization
    
    def test_init_with_client(self, mock_schwab_client):
        """Test fetcher initialization with Schwab client."""
        fetcher = HistoricalDataFetcher(mock_schwab_client)
        
        assert fetcher.schwab_client == mock_schwab_client
        assert fetcher._min_api_interval == 0.5
        assert fetcher._circuit_breaker_threshold == 5
        assert fetcher._circuit_breaker_failures == 0
        assert fetcher._api_calls_made == 0

    def test_init_without_client(self):
        """Test fetcher initialization without client (mock mode)."""
        fetcher = HistoricalDataFetcher(None)
        
        assert fetcher.schwab_client is None
        assert fetcher._should_use_mock_data() is True

    # Test single symbol fetching

    @pytest.mark.asyncio
    async def test_fetch_symbol_data_mock_mode(self, fetcher_mock_mode):
        """Test fetching data in mock mode."""
        result = await fetcher_mock_mode.fetch_symbol_data(
            symbol="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 3)
        )
        
        assert isinstance(result, list)
        assert len(result) >= 2  # At least 2 days of data
        
        # Validate mock data structure
        for bar in result:
            assert 'timestamp' in bar
            assert 'open' in bar
            assert 'high' in bar
            assert 'low' in bar
            assert 'close' in bar
            assert 'volume' in bar
            assert isinstance(bar['timestamp'], datetime)
            assert bar['open'] > 0
            assert bar['high'] >= bar['open']
            assert bar['low'] <= bar['close']

    @pytest.mark.asyncio
    async def test_fetch_symbol_data_api_mode(self, fetcher_with_mock_client, sample_schwab_response):
        """Test fetching data via API."""
        # Configure mock to return sample data
        fetcher_with_mock_client.schwab_client.client.get_historical_data.return_value = sample_schwab_response
        
        result = await fetcher_with_mock_client.fetch_symbol_data(
            symbol="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 3)
        )
        
        assert len(result) == 3
        assert result[0]['open'] == 100.0
        assert result[0]['high'] == 105.0
        assert result[1]['close'] == 102.0
        
        # Verify API was called
        fetcher_with_mock_client.schwab_client.client.get_historical_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_symbol_data_validation_errors(self, fetcher_mock_mode):
        """Test parameter validation."""
        # Empty symbol should raise ValueError
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            await fetcher_mock_mode.fetch_symbol_data(symbol="")

    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, fetcher_with_mock_client):
        """Test circuit breaker protection."""
        # Simulate failures to trigger circuit breaker
        fetcher_with_mock_client.schwab_client.client.get_historical_data.side_effect = Exception("API Error")
        
        # Make enough failed calls to trigger circuit breaker
        for _ in range(5):
            try:
                await fetcher_with_mock_client.fetch_symbol_data("AAPL")
            except:
                pass
        
        # Next call should trigger circuit breaker
        with pytest.raises(CircuitBreakerError):
            await fetcher_with_mock_client.fetch_symbol_data("AAPL")

    @pytest.mark.asyncio
    async def test_rate_limiting(self, fetcher_with_mock_client, sample_schwab_response):
        """Test rate limiting enforcement."""
        fetcher_with_mock_client.schwab_client.client.get_historical_data.return_value = sample_schwab_response
        
        start_time = datetime.utcnow()
        
        # Make two consecutive calls
        await fetcher_with_mock_client.fetch_symbol_data("AAPL")
        await fetcher_with_mock_client.fetch_symbol_data("MSFT")
        
        end_time = datetime.utcnow()
        elapsed = (end_time - start_time).total_seconds()
        
        # Should take at least the minimum interval
        assert elapsed >= fetcher_with_mock_client._min_api_interval

    # Test multiple symbol fetching

    @pytest.mark.asyncio
    async def test_fetch_multiple_symbols_mock_mode(self, fetcher_mock_mode):
        """Test fetching multiple symbols in mock mode."""
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        results = await fetcher_mock_mode.fetch_multiple_symbols(symbols)
        
        assert len(results) == 3
        assert all(symbol in results for symbol in symbols)
        assert all(isinstance(data, list) for data in results.values())
        assert all(len(data) > 0 for data in results.values())

    @pytest.mark.asyncio 
    async def test_fetch_multiple_symbols_with_progress(self, fetcher_mock_mode):
        """Test multiple symbol fetching with progress callback."""
        symbols = ["AAPL", "MSFT"]
        progress_calls = []
        
        async def progress_callback(message: str, progress: float):
            progress_calls.append((message, progress))
        
        results = await fetcher_mock_mode.fetch_multiple_symbols(
            symbols,
            progress_callback=progress_callback
        )
        
        assert len(results) == 2
        assert len(progress_calls) == 2  # One call per symbol
        assert progress_calls[0][1] == 50.0  # First symbol: 50% progress
        assert progress_calls[1][1] == 100.0  # Second symbol: 100% progress

    @pytest.mark.asyncio
    async def test_fetch_multiple_symbols_partial_failure(self, fetcher_with_mock_client):
        """Test multiple symbol fetching with some failures."""
        # Configure mock to succeed for AAPL, fail for MSFT
        def mock_response(symbol, **kwargs):
            if symbol == "AAPL":
                import pandas as pd
                return pd.DataFrame({
                    'open': [100.0], 'high': [105.0], 'low': [99.0], 
                    'close': [101.0], 'volume': [1000000]
                }, index=[datetime(2024, 1, 1)])
            else:
                raise Exception("API Error")
        
        fetcher_with_mock_client.schwab_client.client.get_historical_data.side_effect = mock_response
        
        results = await fetcher_with_mock_client.fetch_multiple_symbols(["AAPL", "MSFT"])
        
        assert len(results) == 2
        assert len(results["AAPL"]) > 0  # Success
        assert len(results["MSFT"]) == 0  # Failure (empty list)

    @pytest.mark.asyncio
    async def test_fetch_multiple_symbols_empty_list(self, fetcher_mock_mode):
        """Test multiple symbol fetching with empty symbol list."""
        with pytest.raises(ValueError, match="At least one symbol is required"):
            await fetcher_mock_mode.fetch_multiple_symbols([])

    # Test mock data generation

    @pytest.mark.asyncio
    async def test_generate_mock_data_default_dates(self, fetcher_mock_mode):
        """Test mock data generation with default date range."""
        result = await fetcher_mock_mode.generate_mock_data("AAPL")
        
        assert isinstance(result, list)
        assert len(result) > 25  # Should have around 30 days of data
        
        # Validate data structure and realism
        for i, bar in enumerate(result):
            assert all(key in bar for key in ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            assert bar['high'] >= bar['open']
            assert bar['high'] >= bar['close']
            assert bar['low'] <= bar['open']
            assert bar['low'] <= bar['close']
            assert bar['volume'] > 0
            
            # Check chronological order
            if i > 0:
                assert bar['timestamp'] > result[i-1]['timestamp']

    @pytest.mark.asyncio
    async def test_generate_mock_data_custom_dates(self, fetcher_mock_mode):
        """Test mock data generation with custom date range."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        
        result = await fetcher_mock_mode.generate_mock_data(
            "AAPL", start_date=start_date, end_date=end_date
        )
        
        assert len(result) == 5  # 5 days
        assert result[0]['timestamp'] >= start_date
        assert result[-1]['timestamp'] <= end_date

    @pytest.mark.asyncio
    async def test_generate_mock_data_different_frequencies(self, fetcher_mock_mode):
        """Test mock data generation with different frequencies."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 1, 5, 0)  # 5 hours
        
        # Test hourly frequency
        result = await fetcher_mock_mode.generate_mock_data(
            "AAPL", start_date=start_date, end_date=end_date, 
            frequency=DataFrequency.ONE_HOUR.value
        )
        
        assert len(result) == 6  # 6 hours (including start hour)
        
        # Check time intervals
        for i in range(1, len(result)):
            time_diff = result[i]['timestamp'] - result[i-1]['timestamp']
            assert time_diff.total_seconds() == 3600  # 1 hour

    # Test response transformation

    def test_transform_schwab_response_valid_data(self, fetcher_mock_mode, sample_schwab_response):
        """Test transformation of valid Schwab response."""
        result = fetcher_mock_mode._transform_schwab_response(sample_schwab_response, "AAPL")
        
        assert len(result) == 3
        assert result[0]['open'] == 100.0
        assert result[0]['high'] == 105.0
        assert result[2]['close'] == 103.0

    def test_transform_schwab_response_empty_data(self, fetcher_mock_mode):
        """Test transformation of empty Schwab response."""
        import pandas as pd
        empty_df = pd.DataFrame()
        
        result = fetcher_mock_mode._transform_schwab_response(empty_df, "AAPL")
        
        assert result == []

    def test_transform_schwab_response_none(self, fetcher_mock_mode):
        """Test transformation of None response."""
        result = fetcher_mock_mode._transform_schwab_response(None, "AAPL")
        
        assert result == []

    # Test statistics and monitoring

    @pytest.mark.asyncio
    async def test_get_fetcher_stats(self, fetcher_mock_mode):
        """Test fetcher statistics retrieval."""
        # Generate some activity
        await fetcher_mock_mode.fetch_symbol_data("AAPL")
        await fetcher_mock_mode.fetch_symbol_data("MSFT")
        
        stats = await fetcher_mock_mode.get_fetcher_stats()
        
        assert "api_calls_made" in stats
        assert "mock_data_calls" in stats
        assert "circuit_breaker_failures" in stats
        assert "circuit_breaker_open" in stats
        assert "mock_mode" in stats
        
        assert stats["mock_data_calls"] == 2  # Two mock data calls
        assert stats["mock_mode"] is True

    # Test base price calculation for mock data

    def test_get_base_price_for_known_symbols(self, fetcher_mock_mode):
        """Test base price calculation for known symbols."""
        assert fetcher_mock_mode._get_base_price_for_symbol("AAPL") == 150.0
        assert fetcher_mock_mode._get_base_price_for_symbol("GOOGL") == 2500.0
        assert fetcher_mock_mode._get_base_price_for_symbol("SPY") == 400.0

    def test_get_base_price_for_unknown_symbols(self, fetcher_mock_mode):
        """Test base price calculation for unknown symbols."""
        price1 = fetcher_mock_mode._get_base_price_for_symbol("UNKNOWN")
        price2 = fetcher_mock_mode._get_base_price_for_symbol("XYZ")
        
        assert 10 <= price1 <= 200  # Should be in reasonable range
        assert 10 <= price2 <= 200

    def test_get_base_price_for_special_symbols(self, fetcher_mock_mode):
        """Test base price calculation for special symbol types."""
        etf_price = fetcher_mock_mode._get_base_price_for_symbol("VT")  # Short symbol (ETF)
        class_a_price = fetcher_mock_mode._get_base_price_for_symbol("TEST.A")  # Class A
        
        assert 50 <= etf_price <= 500  # ETF range
        assert 100 <= class_a_price <= 1000  # Class A range

    # Test time delta calculation

    def test_get_time_delta_for_frequency(self, fetcher_mock_mode):
        """Test time delta calculation for different frequencies."""
        assert fetcher_mock_mode._get_time_delta_for_frequency(DataFrequency.ONE_MINUTE.value) == timedelta(minutes=1)
        assert fetcher_mock_mode._get_time_delta_for_frequency(DataFrequency.ONE_HOUR.value) == timedelta(hours=1)
        assert fetcher_mock_mode._get_time_delta_for_frequency(DataFrequency.DAILY.value) == timedelta(days=1)
        assert fetcher_mock_mode._get_time_delta_for_frequency(DataFrequency.WEEKLY.value) == timedelta(weeks=1)

    def test_get_time_delta_for_unknown_frequency(self, fetcher_mock_mode):
        """Test time delta calculation for unknown frequency."""
        result = fetcher_mock_mode._get_time_delta_for_frequency("unknown")
        assert result == timedelta(days=1)  # Default

    # Test error conditions

    @pytest.mark.asyncio
    async def test_fetch_symbol_data_api_unavailable(self, fetcher_with_mock_client):
        """Test behavior when API is unavailable."""
        fetcher_with_mock_client.schwab_client = None
        
        with pytest.raises(RuntimeError, match="Schwab client not available"):
            await fetcher_with_mock_client._fetch_from_schwab_api("AAPL", None, None, "daily", False)

    @pytest.mark.asyncio
    async def test_fallback_to_mock_data_on_api_failure(self, fetcher_with_mock_client):
        """Test fallback to mock data when API fails in demo mode."""
        # Configure to simulate demo mode and API failure
        fetcher_with_mock_client.schwab_client.client.get_historical_data.side_effect = Exception("API Error")
        
        with patch('src.backend.services.historical_data.fetcher.settings.DEMO_MODE', True):
            result = await fetcher_with_mock_client.fetch_symbol_data("AAPL")
            
            # Should return mock data instead of failing
            assert isinstance(result, list)
            assert len(result) > 0

    # Test max_records functionality

    @pytest.mark.asyncio
    async def test_fetch_symbol_data_with_max_records(self, fetcher_mock_mode):
        """Test max_records parameter functionality."""
        result = await fetcher_mock_mode.fetch_symbol_data(
            symbol="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),  # 10 days
            max_records=5
        )
        
        assert len(result) == 5  # Should be limited to 5 records

    # Test frequency mapping

    @pytest.mark.asyncio
    async def test_frequency_mapping_to_schwab_format(self, fetcher_with_mock_client, sample_schwab_response):
        """Test frequency mapping to Schwab API format."""
        fetcher_with_mock_client.schwab_client.client.get_historical_data.return_value = sample_schwab_response
        
        await fetcher_with_mock_client.fetch_symbol_data(
            "AAPL", frequency=DataFrequency.FIFTEEN_MINUTE.value
        )
        
        # Verify correct frequency was passed to API
        call_args = fetcher_with_mock_client.schwab_client.client.get_historical_data.call_args
        assert call_args[1]['interval'] == '15m'  # Should map to schwab format

    # Test extended hours parameter

    @pytest.mark.asyncio
    async def test_include_extended_hours_parameter(self, fetcher_with_mock_client, sample_schwab_response):
        """Test include_extended_hours parameter functionality."""
        fetcher_with_mock_client.schwab_client.client.get_historical_data.return_value = sample_schwab_response
        
        await fetcher_with_mock_client.fetch_symbol_data(
            "AAPL", include_extended_hours=True
        )
        
        # Verify extended hours flag was passed to API
        call_args = fetcher_with_mock_client.schwab_client.client.get_historical_data.call_args
        assert call_args[1]['include_extended_hours'] is True