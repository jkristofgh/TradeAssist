"""
Integration tests for Phase 3 components working together.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from src.backend.services.cache_service import CacheService, CacheConfig
from src.backend.services.data_aggregation_service import DataAggregationService
from src.backend.services.database_optimization_service import DatabaseOptimizationService
from src.backend.services.historical_data_service import HistoricalDataService


@pytest.mark.integration
class TestPhase3Integration:
    """Test integration between Phase 3 components."""
    
    @pytest.mark.asyncio
    async def test_full_stack_integration(self):
        """Test full stack integration of all Phase 3 components."""
        # Initialize all services
        cache_config = CacheConfig(default_ttl=300)
        cache_service = CacheService(cache_config)
        await cache_service.start()
        
        aggregation_service = DataAggregationService(cache_service)
        await aggregation_service.start()
        
        db_optimization_service = DatabaseOptimizationService()
        await db_optimization_service.start()
        
        historical_service = HistoricalDataService(cache_service)
        
        # Mock WebSocket manager
        mock_websocket_manager = AsyncMock()
        historical_service.set_websocket_manager(mock_websocket_manager)
        
        await historical_service.start()
        
        try:
            # Test data flow through entire stack
            sample_data = []
            base_time = datetime.now()
            
            for i in range(30):
                sample_data.append({
                    "timestamp": base_time + timedelta(minutes=i),
                    "open": 100.0 + i * 0.1,
                    "high": 101.0 + i * 0.1, 
                    "low": 99.0 + i * 0.1,
                    "close": 100.5 + i * 0.1,
                    "volume": 1000 + i * 10
                })
            
            with patch.object(historical_service, '_fetch_symbol_data') as mock_fetch:
                mock_fetch.return_value = (sample_data, "mock_source")
                
                # 1. Historical data service fetches data (with caching)
                results = await historical_service.fetch_historical_data_with_progress(
                    symbols=["INTEGRATION_TEST"],
                    asset_class="stock",
                    frequency="1m",
                    start_date=base_time,
                    end_date=base_time + timedelta(minutes=30),
                    websocket_updates=True
                )
                
                assert len(results) == 1
                assert len(results[0]["bars"]) == 30
                
                # Verify WebSocket updates were sent
                assert mock_websocket_manager.broadcast_historical_data_progress.called
                assert mock_websocket_manager.broadcast_historical_data_complete.called
                
                # 2. Data aggregation service processes the data
                aggregated_result = await historical_service.aggregate_data_with_progress(
                    symbol="INTEGRATION_TEST",
                    source_frequency="1m",
                    target_frequency="5m",
                    start_date=base_time,
                    end_date=base_time + timedelta(minutes=30),
                    websocket_updates=True
                )
                
                assert aggregated_result is not None
                assert "aggregation_id" in aggregated_result
                
                # Verify aggregation WebSocket updates
                assert mock_websocket_manager.broadcast_aggregation_progress.called
                assert mock_websocket_manager.broadcast_aggregation_complete.called
                
                # 3. Cache service should have cached both operations
                cache_stats = await cache_service.get_comprehensive_stats()
                assert cache_stats["service"]["total_sets"] > 0
                assert cache_stats["service"]["total_gets"] > 0
                
                # 4. Database optimization service should track performance
                db_stats = await db_optimization_service.get_performance_stats()
                assert "database_size_mb" in db_stats
                
        finally:
            await historical_service.stop()
            await db_optimization_service.stop()
            await aggregation_service.stop()
            await cache_service.stop()
    
    @pytest.mark.asyncio
    async def test_cache_aggregation_integration(self):
        """Test cache and aggregation service integration."""
        cache_config = CacheConfig(
            default_ttl=300,
            historical_data_ttl=3600,
            query_results_ttl=1800
        )
        cache_service = CacheService(cache_config)
        await cache_service.start()
        
        aggregation_service = DataAggregationService(cache_service)
        await aggregation_service.start()
        
        try:
            # Create test data
            source_bars = []
            base_time = datetime.now()
            
            for i in range(20):
                source_bars.append({
                    "timestamp": base_time + timedelta(minutes=i),
                    "symbol": "CACHE_TEST",
                    "open_price": 150.0 + i * 0.1,
                    "high_price": 151.0 + i * 0.1,
                    "low_price": 149.0 + i * 0.1,
                    "close_price": 150.5 + i * 0.1,
                    "volume": 1000 + i * 10
                })
            
            with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
                mock_fetch.return_value = source_bars
                
                # First aggregation should fetch from source and cache result
                result1 = await aggregation_service.aggregate_data(
                    symbol="CACHE_TEST",
                    source_frequency="1m",
                    target_frequency="5m",
                    start_date=base_time,
                    end_date=base_time + timedelta(minutes=20),
                    use_cache=True
                )
                
                assert not result1.cache_hit
                assert mock_fetch.call_count == 1
                
                # Second identical aggregation should hit cache
                result2 = await aggregation_service.aggregate_data(
                    symbol="CACHE_TEST",
                    source_frequency="1m",
                    target_frequency="5m", 
                    start_date=base_time,
                    end_date=base_time + timedelta(minutes=20),
                    use_cache=True
                )
                
                assert result2.cache_hit
                assert mock_fetch.call_count == 1  # Should not fetch again
                
                # Results should be identical
                assert len(result1.bars) == len(result2.bars)
                
                # Cache stats should reflect operations
                cache_stats = await cache_service.get_comprehensive_stats()
                assert cache_stats["service"]["total_sets"] >= 1
                assert cache_stats["service"]["total_gets"] >= 1
        
        finally:
            await aggregation_service.stop()
            await cache_service.stop()
    
    @pytest.mark.asyncio
    async def test_websocket_integration(self):
        """Test WebSocket integration with all services."""
        cache_config = CacheConfig(default_ttl=300)
        cache_service = CacheService(cache_config)
        await cache_service.start()
        
        aggregation_service = DataAggregationService(cache_service)
        await aggregation_service.start()
        
        historical_service = HistoricalDataService(cache_service)
        
        # Mock WebSocket manager with detailed tracking
        mock_websocket_manager = AsyncMock()
        historical_service.set_websocket_manager(mock_websocket_manager)
        
        await historical_service.start()
        
        try:
            sample_data = [
                {
                    "timestamp": datetime.now(),
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.5,
                    "volume": 1000
                }
            ]
            
            with patch.object(historical_service, '_fetch_symbol_data') as mock_fetch:
                mock_fetch.return_value = (sample_data, "mock_source")
                
                # Test historical data WebSocket integration
                await historical_service.fetch_historical_data_with_progress(
                    symbols=["WS_TEST"],
                    asset_class="stock",
                    frequency="1d",
                    start_date=datetime.now() - timedelta(days=1),
                    end_date=datetime.now(),
                    websocket_updates=True
                )
                
                # Verify WebSocket calls were made with correct data
                progress_calls = mock_websocket_manager.broadcast_historical_data_progress.call_args_list
                complete_calls = mock_websocket_manager.broadcast_historical_data_complete.call_args_list
                
                assert len(progress_calls) >= 1
                assert len(complete_calls) >= 1
                
                # Check progress call structure
                progress_call = progress_calls[0]
                assert "query_id" in progress_call.kwargs
                assert progress_call.kwargs["symbol"] == "WS_TEST"
                assert isinstance(progress_call.kwargs["progress_percent"], (int, float))
                
                # Check completion call structure
                complete_call = complete_calls[0]
                assert "query_id" in complete_call.kwargs
                assert complete_call.kwargs["symbol"] == "WS_TEST"
                assert "bars_retrieved" in complete_call.kwargs
                assert "execution_time_ms" in complete_call.kwargs
                
                # Test aggregation WebSocket integration
                await historical_service.aggregate_data_with_progress(
                    symbol="WS_TEST",
                    source_frequency="1m",
                    target_frequency="5m",
                    start_date=datetime.now() - timedelta(hours=1),
                    end_date=datetime.now(),
                    websocket_updates=True
                )
                
                # Verify aggregation WebSocket calls
                agg_progress_calls = mock_websocket_manager.broadcast_aggregation_progress.call_args_list
                agg_complete_calls = mock_websocket_manager.broadcast_aggregation_complete.call_args_list
                
                assert len(agg_progress_calls) >= 1
                assert len(agg_complete_calls) >= 1
        
        finally:
            await historical_service.stop()
            await aggregation_service.stop()
            await cache_service.stop()
    
    @pytest.mark.asyncio
    async def test_error_propagation_integration(self):
        """Test error handling and propagation across integrated services."""
        cache_config = CacheConfig(default_ttl=300)
        cache_service = CacheService(cache_config)
        await cache_service.start()
        
        aggregation_service = DataAggregationService(cache_service)
        await aggregation_service.start()
        
        historical_service = HistoricalDataService(cache_service)
        mock_websocket_manager = AsyncMock()
        historical_service.set_websocket_manager(mock_websocket_manager)
        
        await historical_service.start()
        
        try:
            # Test error propagation from data source
            with patch.object(historical_service, '_fetch_symbol_data') as mock_fetch:
                mock_fetch.side_effect = Exception("Data source error")
                
                with pytest.raises(Exception, match="Data source error"):
                    await historical_service.fetch_historical_data_with_progress(
                        symbols=["ERROR_TEST"],
                        asset_class="stock",
                        frequency="1d",
                        start_date=datetime.now() - timedelta(days=1),
                        end_date=datetime.now(),
                        websocket_updates=True
                    )
                
                # Verify error was broadcast via WebSocket
                error_calls = mock_websocket_manager.broadcast_historical_data_error.call_args_list
                assert len(error_calls) >= 1
                
                error_call = error_calls[0]
                assert error_call.kwargs["symbol"] == "ERROR_TEST"
                assert "Data source error" in error_call.kwargs["error_message"]
            
            # Test aggregation service error handling
            with patch.object(aggregation_service, '_fetch_source_bars') as mock_fetch:
                mock_fetch.side_effect = Exception("Database error")
                
                with pytest.raises(RuntimeError, match="Aggregation failed"):
                    await aggregation_service.aggregate_data(
                        symbol="ERROR_TEST",
                        source_frequency="1m",
                        target_frequency="5m",
                        start_date=datetime.now() - timedelta(hours=1),
                        end_date=datetime.now()
                    )
        
        finally:
            await historical_service.stop()
            await aggregation_service.stop()
            await cache_service.stop()
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test performance monitoring across integrated services."""
        cache_config = CacheConfig(default_ttl=300)
        cache_service = CacheService(cache_config)
        await cache_service.start()
        
        aggregation_service = DataAggregationService(cache_service)
        await aggregation_service.start()
        
        historical_service = HistoricalDataService(cache_service)
        mock_websocket_manager = AsyncMock()
        historical_service.set_websocket_manager(mock_websocket_manager)
        
        await historical_service.start()
        
        try:
            # Generate activity across services
            sample_data = [
                {
                    "timestamp": datetime.now(),
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0, 
                    "close": 100.5,
                    "volume": 1000
                }
            ]
            
            with patch.object(historical_service, '_fetch_symbol_data') as mock_fetch:
                mock_fetch.return_value = (sample_data, "mock_source")
                
                # Perform operations
                await historical_service.fetch_historical_data_with_progress(
                    symbols=["PERF_TEST"],
                    asset_class="stock",
                    frequency="1d",
                    start_date=datetime.now() - timedelta(days=1),
                    end_date=datetime.now(),
                    websocket_updates=False
                )
                
                await historical_service.aggregate_data_with_progress(
                    symbol="PERF_TEST",
                    source_frequency="1m",
                    target_frequency="5m",
                    start_date=datetime.now() - timedelta(hours=1),
                    end_date=datetime.now(),
                    websocket_updates=False
                )
                
                # Check performance stats from historical service
                hist_stats = await historical_service.get_performance_stats()
                assert hist_stats["requests_served"] >= 1
                
                # Check cache performance stats
                cache_stats = await cache_service.get_comprehensive_stats()
                assert cache_stats["service"]["total_requests"] >= 2  # At least fetch + aggregation
                
                # Check aggregation performance stats
                agg_stats = await aggregation_service.get_aggregation_stats()
                assert agg_stats["aggregations_performed"] >= 1
                
                # Test performance metrics broadcasting
                await historical_service.broadcast_performance_metrics()
                
                # Verify performance broadcast was called
                perf_calls = mock_websocket_manager.broadcast_cache_performance_update.call_args_list
                assert len(perf_calls) >= 1
                
                perf_call = perf_calls[0]
                assert "cache_hit_rate" in perf_call.kwargs
                assert "total_requests" in perf_call.kwargs
                assert "redis_available" in perf_call.kwargs
        
        finally:
            await historical_service.stop()
            await aggregation_service.stop() 
            await cache_service.stop()


@pytest.mark.integration
class TestEndToEndScenarios:
    """Test realistic end-to-end scenarios."""
    
    @pytest.mark.asyncio
    async def test_trading_day_data_processing(self):
        """Test processing a full trading day of data."""
        cache_config = CacheConfig(
            default_ttl=300,
            historical_data_ttl=3600,
            max_memory_cache_items=2000
        )
        cache_service = CacheService(cache_config)
        await cache_service.start()
        
        aggregation_service = DataAggregationService(cache_service)
        await aggregation_service.start()
        
        historical_service = HistoricalDataService(cache_service)
        await historical_service.start()
        
        try:
            # Simulate full trading day (6.5 hours of minute data)
            trading_day_data = []
            market_open = datetime(2023, 6, 15, 9, 30)  # 9:30 AM
            
            for minute in range(390):  # 6.5 hours = 390 minutes
                trading_day_data.append({
                    "timestamp": market_open + timedelta(minutes=minute),
                    "open": 150.0 + (minute % 60) * 0.01,
                    "high": 150.5 + (minute % 60) * 0.01,
                    "low": 149.5 + (minute % 60) * 0.01,
                    "close": 150.2 + (minute % 60) * 0.01,
                    "volume": 1000 + minute * 5
                })
            
            with patch.object(historical_service, '_fetch_symbol_data') as mock_fetch:
                mock_fetch.return_value = (trading_day_data, "market_data")
                
                # Fetch the full trading day
                results = await historical_service.fetch_historical_data_with_progress(
                    symbols=["AAPL"],
                    asset_class="stock",
                    frequency="1m",
                    start_date=market_open,
                    end_date=market_open + timedelta(hours=6, minutes=30),
                    websocket_updates=False
                )
                
                assert len(results) == 1
                assert len(results[0]["bars"]) == 390
                
                # Aggregate to different timeframes
                timeframes = [("1m", "5m"), ("1m", "15m"), ("1m", "1h")]
                
                for source_freq, target_freq in timeframes:
                    agg_result = await historical_service.aggregate_data_with_progress(
                        symbol="AAPL",
                        source_frequency=source_freq,
                        target_frequency=target_freq,
                        start_date=market_open,
                        end_date=market_open + timedelta(hours=6, minutes=30),
                        websocket_updates=False
                    )
                    
                    assert agg_result is not None
                    assert len(agg_result["bars"]) > 0
                    
                    # Verify aggregation correctness
                    first_bar = agg_result["bars"][0]
                    assert "open_price" in first_bar
                    assert "high_price" in first_bar
                    assert "low_price" in first_bar
                    assert "close_price" in first_bar
                    assert "volume" in first_bar
                
                # Verify caching efficiency
                cache_stats = await cache_service.get_comprehensive_stats()
                total_operations = cache_stats["service"]["total_gets"] + cache_stats["service"]["total_sets"]
                assert total_operations > 0
                
        finally:
            await historical_service.stop()
            await aggregation_service.stop()
            await cache_service.stop()
    
    @pytest.mark.asyncio
    async def test_multi_symbol_portfolio_analysis(self):
        """Test processing multiple symbols for portfolio analysis."""
        cache_config = CacheConfig(default_ttl=300)
        cache_service = CacheService(cache_config)
        await cache_service.start()
        
        aggregation_service = DataAggregationService(cache_service)
        await aggregation_service.start()
        
        historical_service = HistoricalDataService(cache_service)
        await historical_service.start()
        
        try:
            portfolio_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
            
            # Create sample data for each symbol
            def create_symbol_data(symbol, base_price):
                data = []
                base_time = datetime.now() - timedelta(days=30)
                for day in range(30):
                    data.append({
                        "timestamp": base_time + timedelta(days=day),
                        "open": base_price + day * 0.5,
                        "high": base_price + day * 0.5 + 2.0,
                        "low": base_price + day * 0.5 - 1.5,
                        "close": base_price + day * 0.5 + 1.0,
                        "volume": 1000000 + day * 1000
                    })
                return data
            
            symbol_data = {
                "AAPL": create_symbol_data("AAPL", 150.0),
                "GOOGL": create_symbol_data("GOOGL", 2800.0),
                "MSFT": create_symbol_data("MSFT", 300.0),
                "TSLA": create_symbol_data("TSLA", 200.0),
                "AMZN": create_symbol_data("AMZN", 3000.0)
            }
            
            def mock_fetch_by_symbol(symbol, request):
                return (symbol_data[symbol], "portfolio_data")
            
            with patch.object(historical_service, '_fetch_symbol_data') as mock_fetch:
                mock_fetch.side_effect = lambda symbol, request: mock_fetch_by_symbol(symbol, request)
                
                # Fetch data for entire portfolio
                portfolio_results = await historical_service.fetch_historical_data_with_progress(
                    symbols=portfolio_symbols,
                    asset_class="stock",
                    frequency="1d",
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now(),
                    websocket_updates=False
                )
                
                assert len(portfolio_results) == len(portfolio_symbols)
                
                # Each symbol should have 30 days of data
                for result in portfolio_results:
                    assert len(result["bars"]) == 30
                    assert result["symbol"] in portfolio_symbols
                
                # Test portfolio-wide aggregations
                aggregation_tasks = []
                for symbol in portfolio_symbols:
                    task = historical_service.aggregate_data_with_progress(
                        symbol=symbol,
                        source_frequency="1d",
                        target_frequency="1w",
                        start_date=datetime.now() - timedelta(days=30),
                        end_date=datetime.now(),
                        websocket_updates=False
                    )
                    aggregation_tasks.append(task)
                
                weekly_results = await asyncio.gather(*aggregation_tasks)
                
                # Should have weekly aggregations for all symbols
                assert len(weekly_results) == len(portfolio_symbols)
                for result in weekly_results:
                    assert len(result["bars"]) >= 4  # At least 4 weeks
                
                # Verify performance across portfolio
                final_stats = await cache_service.get_comprehensive_stats()
                assert final_stats["service"]["total_requests"] >= len(portfolio_symbols) * 2  # Fetch + aggregate per symbol
                
        finally:
            await historical_service.stop()
            await aggregation_service.stop()
            await cache_service.stop()