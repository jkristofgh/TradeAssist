"""
Performance benchmarking tests.

Tests system performance against PRP requirements including
alert evaluation latency, data ingestion throughput, and API response times.
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime
from typing import List

from src.backend.services.alert_engine import AlertEngine, RuleEvaluator
from src.backend.services.data_ingestion import DataNormalizer
from src.backend.models.instruments import Instrument, InstrumentType
from src.backend.models.market_data import MarketData
from src.backend.models.alert_rules import AlertRule, RuleType, RuleCondition


class TestAlertEnginePerformance:
    """Performance tests for alert engine with sub-500ms requirements."""
    
    @pytest.mark.asyncio
    async def test_threshold_rule_evaluation_latency(self, sample_instruments):
        """Test alert rule evaluation meets <500ms latency requirement."""
        evaluator = RuleEvaluator()
        instrument = sample_instruments[0]
        
        # Create test rule
        rule = AlertRule(
            id=1,
            instrument_id=instrument.id,
            rule_type=RuleType.THRESHOLD,
            condition=RuleCondition.ABOVE,
            threshold=4500.0,
        )
        rule.instrument = instrument
        
        # Test multiple evaluations to get average
        evaluation_times = []
        test_iterations = 100
        
        for i in range(test_iterations):
            start_time = time.time()
            
            # Price that will trigger the rule
            test_price = 4525.75 + (i * 0.01)  # Vary price slightly
            context = await evaluator.evaluate_threshold_rule(rule, test_price, None)
            
            end_time = time.time()
            evaluation_time_ms = (end_time - start_time) * 1000
            evaluation_times.append(evaluation_time_ms)
            
            # Verify rule was triggered
            assert context is not None
        
        # Analyze performance
        avg_time = statistics.mean(evaluation_times)
        max_time = max(evaluation_times)
        p95_time = statistics.quantiles(evaluation_times, n=20)[18]  # 95th percentile
        
        print(f"Threshold Rule Evaluation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")
        print(f"  95th percentile: {p95_time:.2f}ms")
        
        # Performance assertions based on PRP requirements
        assert avg_time < 50, f"Average evaluation time {avg_time:.2f}ms exceeds 50ms target"
        assert max_time < 500, f"Maximum evaluation time {max_time:.2f}ms exceeds 500ms limit"
        assert p95_time < 100, f"95th percentile {p95_time:.2f}ms exceeds 100ms target"
    
    @pytest.mark.asyncio
    async def test_volume_spike_rule_evaluation_latency(self, sample_instruments):
        """Test volume spike rule evaluation performance."""
        evaluator = RuleEvaluator()
        instrument = sample_instruments[0]
        
        rule = AlertRule(
            id=1,
            instrument_id=instrument.id,
            rule_type=RuleType.VOLUME_SPIKE,
            condition=RuleCondition.VOLUME_ABOVE,
            threshold=1000.0,
        )
        rule.instrument = instrument
        
        evaluation_times = []
        test_iterations = 100
        
        for i in range(test_iterations):
            start_time = time.time()
            
            # Volume that will trigger the rule
            test_volume = 1500 + (i * 10)  # Vary volume
            context = await evaluator.evaluate_volume_spike_rule(rule, test_volume, None)
            
            end_time = time.time()
            evaluation_time_ms = (end_time - start_time) * 1000
            evaluation_times.append(evaluation_time_ms)
            
            assert context is not None
        
        avg_time = statistics.mean(evaluation_times)
        max_time = max(evaluation_times)
        
        print(f"Volume Spike Rule Evaluation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")
        
        # Performance assertions
        assert avg_time < 50, f"Average evaluation time {avg_time:.2f}ms exceeds target"
        assert max_time < 500, f"Maximum evaluation time {max_time:.2f}ms exceeds limit"
    
    @pytest.mark.asyncio
    async def test_concurrent_rule_evaluations(self, sample_instruments):
        """Test concurrent rule evaluation performance."""
        evaluator = RuleEvaluator()
        instrument = sample_instruments[0]
        
        # Create multiple rules
        rules = []
        for i in range(10):  # 10 concurrent rules
            rule = AlertRule(
                id=i + 1,
                instrument_id=instrument.id,
                rule_type=RuleType.THRESHOLD,
                condition=RuleCondition.ABOVE,
                threshold=4500.0 + (i * 10),
            )
            rule.instrument = instrument
            rules.append(rule)
        
        async def evaluate_rule(rule: AlertRule, price: float) -> float:
            """Helper to evaluate a single rule and return time."""
            start_time = time.time()
            await evaluator.evaluate_threshold_rule(rule, price, None)
            return (time.time() - start_time) * 1000
        
        # Test concurrent evaluations
        test_price = 4550.0
        start_time = time.time()
        
        # Run all evaluations concurrently
        tasks = [evaluate_rule(rule, test_price) for rule in rules]
        evaluation_times = await asyncio.gather(*tasks)
        
        total_time = (time.time() - start_time) * 1000
        avg_time = statistics.mean(evaluation_times)
        
        print(f"Concurrent Rule Evaluation Performance ({len(rules)} rules):")
        print(f"  Total time: {total_time:.2f}ms")
        print(f"  Average per rule: {avg_time:.2f}ms")
        
        # Should handle 10 rules within 500ms total
        assert total_time < 500, f"Concurrent evaluation took {total_time:.2f}ms, exceeds 500ms"
        assert avg_time < 100, f"Average per rule {avg_time:.2f}ms exceeds 100ms target"


class TestDataIngestionPerformance:
    """Performance tests for data ingestion with throughput requirements."""
    
    def test_data_normalization_throughput(self, test_data_factory):
        """Test data normalization throughput meets PRP requirements."""
        normalizer = DataNormalizer()
        
        # Create test data
        raw_data_samples = []
        for i in range(1000):  # 1000 ticks
            raw_data = {
                "lastPrice": 4500.0 + (i * 0.25),
                "volume": 100 + (i * 5),
                "bid": 4499.75 + (i * 0.25),
                "ask": 4500.25 + (i * 0.25),
            }
            raw_data_samples.append(raw_data)
        
        # Measure normalization throughput
        start_time = time.time()
        
        normalized_count = 0
        for i, raw_data in enumerate(raw_data_samples):
            symbol = f"TEST{i % 10}"  # Rotate through 10 symbols
            normalized = normalizer.normalize_tick_data(symbol, raw_data)
            if normalized:
                normalized_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = normalized_count / total_time
        
        print(f"Data Normalization Performance:")
        print(f"  Total ticks: {len(raw_data_samples)}")
        print(f"  Normalized: {normalized_count}")
        print(f"  Time: {total_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} ticks/second")
        
        # PRP requirement: 100+ ticks/second sustained throughput
        assert throughput > 100, f"Throughput {throughput:.1f} ticks/s below 100 ticks/s requirement"
        assert normalized_count == len(raw_data_samples), "Some normalizations failed"
    
    @pytest.mark.asyncio
    async def test_queue_processing_performance(self):
        """Test data queue processing performance."""
        from asyncio import Queue
        
        # Create test queue
        data_queue = Queue(maxsize=2000)
        
        # Fill queue with test data
        test_data_count = 1000
        for i in range(test_data_count):
            test_tick = {
                "symbol": f"TEST{i % 5}",
                "timestamp": datetime.utcnow(),
                "price": 4500.0 + (i * 0.1),
                "volume": 100 + i,
                "queued_at": datetime.utcnow()
            }
            await data_queue.put(test_tick)
        
        # Measure queue processing time
        start_time = time.time()
        processed_count = 0
        
        while not data_queue.empty():
            try:
                data = await asyncio.wait_for(data_queue.get(), timeout=0.1)
                # Simulate minimal processing
                processed_count += 1
                data_queue.task_done()
            except asyncio.TimeoutError:
                break
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = processed_count / total_time
        
        print(f"Queue Processing Performance:")
        print(f"  Processed: {processed_count} items")
        print(f"  Time: {total_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} items/second")
        
        # Should process queued data quickly
        assert throughput > 1000, f"Queue processing throughput {throughput:.1f}/s too low"
        assert processed_count == test_data_count, "Not all queued items processed"


class TestDatabasePerformance:
    """Performance tests for database operations."""
    
    @pytest.mark.asyncio
    async def test_market_data_insertion_performance(self, test_session, sample_instruments):
        """Test market data insertion performance."""
        instrument = sample_instruments[0]
        
        # Create test market data records
        market_data_records = []
        record_count = 500  # 500 records for batch insert test
        
        for i in range(record_count):
            record = MarketData(
                timestamp=datetime.utcnow(),
                instrument_id=instrument.id,
                price=4500.0 + (i * 0.1),
                volume=100 + i,
                bid=4499.75 + (i * 0.1),
                ask=4500.25 + (i * 0.1),
            )
            market_data_records.append(record)
        
        # Measure insertion performance
        start_time = time.time()
        
        for record in market_data_records:
            test_session.add(record)
        
        await test_session.commit()
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = record_count / total_time
        
        print(f"Market Data Insertion Performance:")
        print(f"  Records: {record_count}")
        print(f"  Time: {total_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} records/second")
        
        # Should insert market data quickly for real-time processing
        assert throughput > 100, f"Insert throughput {throughput:.1f}/s too low for real-time data"
        assert total_time < 5.0, f"Batch insert took {total_time:.3f}s, too slow"
    
    @pytest.mark.asyncio
    async def test_alert_rule_query_performance(self, test_session, sample_instruments):
        """Test alert rule query performance."""
        from sqlalchemy import select
        from src.backend.models.alert_rules import AlertRule
        
        instrument = sample_instruments[0]
        
        # Create multiple alert rules
        rule_count = 50
        for i in range(rule_count):
            rule = AlertRule(
                instrument_id=instrument.id,
                rule_type=RuleType.THRESHOLD,
                condition=RuleCondition.ABOVE if i % 2 == 0 else RuleCondition.BELOW,
                threshold=4500.0 + (i * 10),
                active=True,
            )
            test_session.add(rule)
        
        await test_session.commit()
        
        # Measure query performance
        iterations = 100
        query_times = []
        
        for _ in range(iterations):
            start_time = time.time()
            
            # Query active rules for instrument (common query pattern)
            result = await test_session.execute(
                select(AlertRule).where(
                    AlertRule.instrument_id == instrument.id,
                    AlertRule.active == True
                )
            )
            rules = result.scalars().all()
            
            end_time = time.time()
            query_time_ms = (end_time - start_time) * 1000
            query_times.append(query_time_ms)
            
            assert len(rules) == rule_count
        
        avg_time = statistics.mean(query_times)
        max_time = max(query_times)
        
        print(f"Alert Rule Query Performance ({rule_count} rules):")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")
        
        # PRP requirement: <50ms for real-time queries
        assert avg_time < 50, f"Average query time {avg_time:.2f}ms exceeds 50ms target"
        assert max_time < 100, f"Maximum query time {max_time:.2f}ms exceeds 100ms limit"


class TestMemoryUsagePerformance:
    """Performance tests for memory usage requirements."""
    
    def test_memory_usage_under_load(self):
        """Test memory usage stays within PRP limits."""
        import psutil
        import os
        
        # Get current process
        process = psutil.Process(os.getpid())
        
        # Measure baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create memory load simulation
        large_data_structures = []
        
        # Simulate real-world data structures
        for i in range(1000):  # 1000 market data records
            market_data = {
                "id": i,
                "symbol": f"TEST{i % 10}",
                "timestamp": datetime.utcnow(),
                "price": 4500.0 + (i * 0.1),
                "volume": 100 + i,
                "bid": 4499.75,
                "ask": 4500.25,
                "metadata": {"source": "test", "processed": True}
            }
            large_data_structures.append(market_data)
        
        # Add alert rules simulation
        for i in range(100):  # 100 alert rules
            alert_rule = {
                "id": i,
                "instrument_id": i % 10,
                "rule_type": "threshold",
                "condition": "above",
                "threshold": 4500.0 + (i * 10),
                "active": True,
                "metadata": {"created": datetime.utcnow(), "version": 1}
            }
            large_data_structures.append(alert_rule)
        
        # Measure memory after load
        loaded_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = loaded_memory - baseline_memory
        
        print(f"Memory Usage Performance:")
        print(f"  Baseline: {baseline_memory:.1f}MB")
        print(f"  Under load: {loaded_memory:.1f}MB")
        print(f"  Increase: {memory_increase:.1f}MB")
        
        # PRP requirement: <512MB under normal load
        # This is a partial test - full load would include all services
        assert loaded_memory < 512, f"Memory usage {loaded_memory:.1f}MB exceeds 512MB limit"
        
        # Memory increase should be reasonable for the data structures created
        assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB too high for test data"
    
    def test_data_structure_efficiency(self):
        """Test efficiency of core data structures."""
        import sys
        
        # Test market data structure size
        sample_market_data = {
            "symbol": "ES",
            "timestamp": datetime.utcnow(),
            "price": 4525.75,
            "volume": 1000,
            "bid": 4525.50,
            "ask": 4525.75,
            "bid_size": 10,
            "ask_size": 15,
        }
        
        market_data_size = sys.getsizeof(sample_market_data)
        
        # Test alert rule structure size
        sample_alert_rule = {
            "id": 1,
            "instrument_id": 1,
            "rule_type": "threshold",
            "condition": "above",
            "threshold": 4500.0,
            "active": True,
            "cooldown_seconds": 60,
        }
        
        alert_rule_size = sys.getsizeof(sample_alert_rule)
        
        print(f"Data Structure Efficiency:")
        print(f"  Market data record: {market_data_size} bytes")
        print(f"  Alert rule record: {alert_rule_size} bytes")
        
        # Data structures should be reasonably compact
        assert market_data_size < 1000, f"Market data structure too large: {market_data_size} bytes"
        assert alert_rule_size < 500, f"Alert rule structure too large: {alert_rule_size} bytes"


@pytest.mark.asyncio
async def test_end_to_end_performance(sample_instruments):
    """Test end-to-end performance from data ingestion to alert firing."""
    from src.backend.services.alert_engine import AlertEngine
    
    # Create test components
    alert_engine = AlertEngine()
    instrument = sample_instruments[0]
    
    # Create test rule
    rule = AlertRule(
        id=1,
        instrument_id=instrument.id,
        rule_type=RuleType.THRESHOLD,
        condition=RuleCondition.ABOVE,
        threshold=4500.0,
        cooldown_seconds=1,  # Short cooldown for testing
    )
    
    # Cache the rule
    alert_engine._active_rules_cache[instrument.id] = [rule]
    
    # Create test market data
    market_data = MarketData(
        timestamp=datetime.utcnow(),
        instrument_id=instrument.id,
        price=4525.75,  # Above threshold
        volume=1000,
    )
    
    # Measure end-to-end processing time
    start_time = time.time()
    
    # Queue evaluation
    await alert_engine.queue_evaluation(instrument.id, market_data)
    
    # Process the evaluation (simulate processing loop)
    eval_data = await alert_engine.evaluation_queue.get()
    
    # Evaluate rule
    context = await alert_engine._evaluate_rule(rule, market_data, None)
    
    end_time = time.time()
    total_time_ms = (end_time - start_time) * 1000
    
    print(f"End-to-End Performance:")
    print(f"  Total time: {total_time_ms:.2f}ms")
    
    # Verify alert was triggered
    assert context is not None
    
    # PRP requirement: tick-to-alert latency <500ms
    assert total_time_ms < 500, f"End-to-end time {total_time_ms:.2f}ms exceeds 500ms limit"
    assert total_time_ms < 100, f"End-to-end time {total_time_ms:.2f}ms exceeds optimized 100ms target"