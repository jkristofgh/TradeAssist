"""
Performance benchmarking and validation service.

Provides comprehensive performance testing to validate database optimizations
and measure improvements against baseline targets.
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import structlog

from pydantic import BaseModel
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_db_session
from ..models.market_data import MarketData
from ..models.instruments import Instrument

logger = structlog.get_logger(__name__)


class BenchmarkConfig(BaseModel):
    """Performance benchmark configuration."""
    insert_test_duration_seconds: int = 60
    insert_test_batch_size: int = 100
    calculation_test_iterations: int = 1000
    capacity_test_duration_minutes: int = 5
    capacity_test_target_per_minute: int = 10000
    
    # Performance targets
    insert_improvement_target_pct: float = 30.0
    calculation_speedup_target: float = 2.0
    capacity_target_inserts_per_minute: int = 10000


class BenchmarkResult(BaseModel):
    """Benchmark test result."""
    test_name: str
    test_type: str
    duration_seconds: float
    operations_performed: int
    operations_per_second: float
    target_value: Optional[float] = None
    baseline_value: Optional[float] = None
    improvement_percentage: Optional[float] = None
    target_met: bool = False
    timestamp: datetime
    details: Dict[str, Any] = {}


class PerformanceBenchmarkService:
    """
    Service for comprehensive database performance benchmarking.
    
    Validates the performance improvements from all optimization phases:
    - Phase 1: DECIMAL to FLOAT optimization (2-3x calculation speedup)
    - Phase 2: Connection pool optimization
    - Phase 3: Time-series partitioning benefits
    - Phase 4: Overall system capacity validation (10,000+ inserts/minute)
    """
    
    def __init__(self, config: Optional[BenchmarkConfig] = None):
        """Initialize benchmark service."""
        self.config = config or BenchmarkConfig()
        self._baseline_data: Dict[str, float] = {
            "insert_ops_per_sec": 100.0,  # Baseline before optimizations
            "calculation_time_ms": 10.0,   # Baseline DECIMAL calculation time
            "query_response_time_ms": 50.0  # Baseline query response time
        }
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """
        Run comprehensive performance benchmark covering all optimization areas.
        
        Returns:
            Complete benchmark results with baseline comparisons and target validation.
        """
        logger.info("Starting comprehensive performance benchmark suite")
        start_time = datetime.utcnow()
        
        try:
            # Run all benchmark tests
            results = {
                "benchmark_id": f"benchmark_{int(time.time())}",
                "start_time": start_time.isoformat(),
                "config": self.config.model_dump(),
                "baseline_data": self._baseline_data.copy()
            }
            
            # 1. INSERT Performance Test (Phase 1 & 2 optimizations)
            logger.info("Running INSERT performance benchmark")
            insert_results = await self._benchmark_insert_performance()
            results["insert_performance"] = insert_results
            
            # 2. Calculation Performance Test (Phase 1 DECIMAL->FLOAT)
            logger.info("Running calculation performance benchmark")
            calc_results = await self._benchmark_calculation_performance()
            results["calculation_performance"] = calc_results
            
            # 3. Query Performance Test (Phase 1 indexes + Phase 3 partitioning)
            logger.info("Running query performance benchmark")
            query_results = await self._benchmark_query_performance()
            results["query_performance"] = query_results
            
            # 4. High-Frequency Capacity Test (Phase 4 overall capacity)
            logger.info("Running high-frequency capacity test")
            capacity_results = await self._benchmark_high_frequency_capacity()
            results["capacity_test"] = capacity_results
            
            # 5. Connection Pool Performance Test (Phase 2 optimization)
            logger.info("Running connection pool performance benchmark")
            pool_results = await self._benchmark_connection_pool()
            results["connection_pool_performance"] = pool_results
            
            # Calculate overall results
            end_time = datetime.utcnow()
            results["end_time"] = end_time.isoformat()
            results["total_duration_seconds"] = (end_time - start_time).total_seconds()
            results["overall_summary"] = self._calculate_overall_summary(results)
            
            logger.info("Comprehensive benchmark completed", 
                       duration=results["total_duration_seconds"],
                       targets_met=results["overall_summary"]["targets_met"])
            
            return results
            
        except Exception as e:
            logger.error("Error running comprehensive benchmark", error=str(e))
            return {
                "benchmark_id": f"benchmark_error_{int(time.time())}",
                "start_time": start_time.isoformat(),
                "error": str(e),
                "status": "failed"
            }
    
    async def _benchmark_insert_performance(self) -> BenchmarkResult:
        """Benchmark INSERT performance measuring ops/second improvement."""
        start_time = time.time()
        total_inserts = 0
        
        # Get test instrument
        async with get_db_session() as session:
            instrument_result = await session.execute(
                select(Instrument).where(Instrument.status == "active").limit(1)
            )
            instrument = instrument_result.scalar_one_or_none()
            
            if not instrument:
                # Create test instrument if none exists
                test_instrument = Instrument(
                    symbol="TEST_PERF",
                    name="Performance Test Instrument",
                    instrument_type="stock",
                    status="active"
                )
                session.add(test_instrument)
                await session.commit()
                instrument = test_instrument
        
        # Run INSERT performance test
        test_end_time = start_time + self.config.insert_test_duration_seconds
        
        while time.time() < test_end_time:
            batch_start = time.time()
            
            # Create batch of market data
            market_data_batch = []
            for i in range(self.config.insert_test_batch_size):
                market_data = MarketData(
                    instrument_id=instrument.id,
                    timestamp=datetime.utcnow() - timedelta(seconds=i),
                    price=100.0 + random.uniform(-5, 5),  # Using FLOAT (optimized)
                    volume=random.randint(100, 10000),
                    bid_price=99.0 + random.uniform(-5, 5),
                    ask_price=101.0 + random.uniform(-5, 5),
                    high_price=105.0,
                    low_price=95.0
                )
                market_data_batch.append(market_data)
            
            # Insert batch
            async with get_db_session() as session:
                session.add_all(market_data_batch)
                await session.commit()
            
            total_inserts += len(market_data_batch)
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.01)
        
        end_time = time.time()
        duration = end_time - start_time
        ops_per_sec = total_inserts / duration
        
        # Calculate improvement vs baseline
        baseline_ops = self._baseline_data["insert_ops_per_sec"]
        improvement_pct = ((ops_per_sec - baseline_ops) / baseline_ops) * 100
        target_met = improvement_pct >= self.config.insert_improvement_target_pct
        
        return BenchmarkResult(
            test_name="INSERT Performance Test",
            test_type="insert_performance",
            duration_seconds=duration,
            operations_performed=total_inserts,
            operations_per_second=ops_per_sec,
            target_value=self.config.insert_improvement_target_pct,
            baseline_value=baseline_ops,
            improvement_percentage=improvement_pct,
            target_met=target_met,
            timestamp=datetime.utcnow(),
            details={
                "batch_size": self.config.insert_test_batch_size,
                "total_batches": total_inserts // self.config.insert_test_batch_size,
                "optimization": "DECIMAL_to_FLOAT_conversion"
            }
        )
    
    async def _benchmark_calculation_performance(self) -> BenchmarkResult:
        """Benchmark FLOAT vs DECIMAL calculation performance."""
        iterations = self.config.calculation_test_iterations
        
        # Test FLOAT calculations (current optimized)
        float_values = [100.0 + random.uniform(-50, 50) for _ in range(iterations)]
        
        start_time = time.time()
        for i in range(iterations):
            # Simulate typical calculations done in market data processing
            result = float_values[i] * 1.025  # Price adjustment
            result = result + (result * 0.001)  # Fee calculation
            result = max(result, 0.01)  # Minimum price check
            result = round(result, 2)  # Price precision
        end_time = time.time()
        
        float_duration_ms = (end_time - start_time) * 1000
        
        # Test DECIMAL calculations (baseline/legacy)
        decimal_values = [Decimal(str(100.0 + random.uniform(-50, 50))) for _ in range(iterations)]
        
        start_time = time.time()
        for i in range(iterations):
            # Same calculations with Decimal
            result = decimal_values[i] * Decimal('1.025')
            result = result + (result * Decimal('0.001'))
            result = max(result, Decimal('0.01'))
            result = round(result, 2)
        end_time = time.time()
        
        decimal_duration_ms = (end_time - start_time) * 1000
        
        # Calculate speedup
        speedup_multiplier = decimal_duration_ms / float_duration_ms if float_duration_ms > 0 else 0
        target_met = speedup_multiplier >= self.config.calculation_speedup_target
        
        return BenchmarkResult(
            test_name="Calculation Performance Test",
            test_type="calculation_performance",
            duration_seconds=float_duration_ms / 1000,
            operations_performed=iterations,
            operations_per_second=iterations / (float_duration_ms / 1000),
            target_value=self.config.calculation_speedup_target,
            baseline_value=decimal_duration_ms,
            improvement_percentage=((speedup_multiplier - 1) * 100),
            target_met=target_met,
            timestamp=datetime.utcnow(),
            details={
                "float_duration_ms": float_duration_ms,
                "decimal_duration_ms": decimal_duration_ms,
                "speedup_multiplier": speedup_multiplier,
                "optimization": "DECIMAL_to_FLOAT_data_types"
            }
        )
    
    async def _benchmark_query_performance(self) -> BenchmarkResult:
        """Benchmark query performance with optimized indexes and partitioning."""
        start_time = time.time()
        total_queries = 0
        
        # Get test instrument
        async with get_db_session() as session:
            instrument_result = await session.execute(
                select(Instrument).where(Instrument.status == "active").limit(1)
            )
            instrument = instrument_result.scalar_one()
        
        # Run various optimized queries
        test_queries = [
            # Timestamp-based queries (optimized with indexes)
            lambda session: session.execute(
                select(MarketData).where(
                    MarketData.timestamp >= datetime.utcnow() - timedelta(hours=1)
                ).limit(100)
            ),
            
            # Instrument-specific queries (optimized with compound indexes)
            lambda session: session.execute(
                select(MarketData).where(
                    MarketData.instrument_id == instrument.id
                ).order_by(MarketData.timestamp.desc()).limit(50)
            ),
            
            # Price-based queries (optimized with indexes)
            lambda session: session.execute(
                select(MarketData).where(
                    MarketData.price.between(90.0, 110.0)
                ).limit(50)
            ),
            
            # Aggregation queries (optimized with partitioning)
            lambda session: session.execute(
                select(func.avg(MarketData.price), func.count(MarketData.id))
                .where(MarketData.timestamp >= datetime.utcnow() - timedelta(hours=24))
            )
        ]
        
        query_times = []
        
        # Run queries multiple times to get average performance
        for _ in range(25):  # 25 iterations of each query type
            for query_func in test_queries:
                query_start = time.time()
                
                async with get_db_session() as session:
                    await query_func(session)
                
                query_end = time.time()
                query_times.append((query_end - query_start) * 1000)  # Convert to ms
                total_queries += 1
        
        end_time = time.time()
        duration = end_time - start_time
        avg_query_time_ms = sum(query_times) / len(query_times)
        queries_per_sec = total_queries / duration
        
        # Calculate improvement vs baseline
        baseline_query_time = self._baseline_data["query_response_time_ms"]
        improvement_pct = ((baseline_query_time - avg_query_time_ms) / baseline_query_time) * 100
        target_met = avg_query_time_ms <= baseline_query_time * 0.7  # 30% improvement target
        
        return BenchmarkResult(
            test_name="Query Performance Test",
            test_type="query_performance",
            duration_seconds=duration,
            operations_performed=total_queries,
            operations_per_second=queries_per_sec,
            target_value=baseline_query_time * 0.7,
            baseline_value=baseline_query_time,
            improvement_percentage=improvement_pct,
            target_met=target_met,
            timestamp=datetime.utcnow(),
            details={
                "avg_query_time_ms": avg_query_time_ms,
                "min_query_time_ms": min(query_times),
                "max_query_time_ms": max(query_times),
                "query_types_tested": len(test_queries),
                "optimization": "compound_indexes_and_partitioning"
            }
        )
    
    async def _benchmark_high_frequency_capacity(self) -> BenchmarkResult:
        """Benchmark high-frequency insert capacity (10,000+ per minute target)."""
        start_time = time.time()
        total_inserts = 0
        target_duration = self.config.capacity_test_duration_minutes * 60
        
        # Get test instrument
        async with get_db_session() as session:
            instrument_result = await session.execute(
                select(Instrument).where(Instrument.status == "active").limit(1)
            )
            instrument = instrument_result.scalar_one()
        
        # High-frequency insert test
        test_end_time = start_time + target_duration
        
        while time.time() < test_end_time:
            batch_start = time.time()
            
            # Create larger batches for high-frequency test
            batch_size = 200
            market_data_batch = []
            
            for i in range(batch_size):
                market_data = MarketData(
                    instrument_id=instrument.id,
                    timestamp=datetime.utcnow() - timedelta(microseconds=i*1000),
                    price=100.0 + random.uniform(-10, 10),
                    volume=random.randint(50, 5000),
                    bid_price=99.0 + random.uniform(-10, 10),
                    ask_price=101.0 + random.uniform(-10, 10),
                    high_price=110.0,
                    low_price=90.0
                )
                market_data_batch.append(market_data)
            
            # Fast batch insert
            async with get_db_session() as session:
                session.add_all(market_data_batch)
                await session.commit()
            
            total_inserts += batch_size
            
            # Minimal delay for sustained high-frequency
            await asyncio.sleep(0.005)
        
        end_time = time.time()
        duration = end_time - start_time
        inserts_per_minute = (total_inserts / duration) * 60
        
        target_met = inserts_per_minute >= self.config.capacity_target_inserts_per_minute
        
        return BenchmarkResult(
            test_name="High-Frequency Capacity Test",
            test_type="capacity_test",
            duration_seconds=duration,
            operations_performed=total_inserts,
            operations_per_second=total_inserts / duration,
            target_value=self.config.capacity_target_inserts_per_minute,
            baseline_value=6000,  # Estimated baseline capacity
            improvement_percentage=((inserts_per_minute - 6000) / 6000) * 100,
            target_met=target_met,
            timestamp=datetime.utcnow(),
            details={
                "inserts_per_minute": inserts_per_minute,
                "sustained_duration_minutes": duration / 60,
                "average_batch_size": 200,
                "optimization": "all_phases_combined"
            }
        )
    
    async def _benchmark_connection_pool(self) -> BenchmarkResult:
        """Benchmark connection pool performance and efficiency."""
        start_time = time.time()
        concurrent_operations = 20
        operations_per_task = 10
        
        async def connection_intensive_task():
            """Task that requires multiple database connections."""
            operations = 0
            for _ in range(operations_per_task):
                async with get_db_session() as session:
                    # Simulate typical database operation
                    await session.execute(select(func.count(MarketData.id)))
                    operations += 1
                    await asyncio.sleep(0.01)  # Small delay
            return operations
        
        # Run concurrent tasks to test connection pool
        tasks = [connection_intensive_task() for _ in range(concurrent_operations)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        total_operations = sum(results)
        operations_per_sec = total_operations / duration
        
        # Connection pool efficiency metric
        # Higher ops/sec indicates better pool management
        baseline_efficiency = 50.0  # Baseline ops/sec with poor connection management
        improvement_pct = ((operations_per_sec - baseline_efficiency) / baseline_efficiency) * 100
        target_met = operations_per_sec >= baseline_efficiency * 1.5  # 50% improvement target
        
        return BenchmarkResult(
            test_name="Connection Pool Performance Test",
            test_type="connection_pool_performance",
            duration_seconds=duration,
            operations_performed=total_operations,
            operations_per_second=operations_per_sec,
            target_value=baseline_efficiency * 1.5,
            baseline_value=baseline_efficiency,
            improvement_percentage=improvement_pct,
            target_met=target_met,
            timestamp=datetime.utcnow(),
            details={
                "concurrent_tasks": concurrent_operations,
                "operations_per_task": operations_per_task,
                "optimization": "optimized_connection_pool_configuration"
            }
        )
    
    def _calculate_overall_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall benchmark summary and target achievement."""
        test_results = [
            results.get("insert_performance", {}),
            results.get("calculation_performance", {}),
            results.get("query_performance", {}),
            results.get("capacity_test", {}),
            results.get("connection_pool_performance", {})
        ]
        
        targets_met = sum(1 for result in test_results if result.get("target_met", False))
        total_tests = len([r for r in test_results if r])
        
        overall_status = "EXCELLENT" if targets_met == total_tests else \
                        "GOOD" if targets_met >= total_tests * 0.8 else \
                        "NEEDS_IMPROVEMENT"
        
        # Key achievements
        achievements = []
        if results.get("insert_performance", {}).get("target_met", False):
            achievements.append("30%+ INSERT performance improvement achieved")
        if results.get("calculation_performance", {}).get("target_met", False):
            achievements.append("2x+ calculation speedup achieved")
        if results.get("capacity_test", {}).get("target_met", False):
            achievements.append("10,000+ inserts/minute capacity achieved")
        
        return {
            "overall_status": overall_status,
            "targets_met": targets_met,
            "total_tests": total_tests,
            "success_rate_percentage": (targets_met / total_tests * 100) if total_tests > 0 else 0,
            "key_achievements": achievements,
            "performance_summary": {
                "insert_improvement_pct": results.get("insert_performance", {}).get("improvement_percentage", 0),
                "calculation_speedup": results.get("calculation_performance", {}).get("details", {}).get("speedup_multiplier", 0),
                "capacity_inserts_per_minute": results.get("capacity_test", {}).get("details", {}).get("inserts_per_minute", 0),
                "all_targets_met": targets_met == total_tests
            }
        }
    
    async def validate_performance_targets(self) -> Dict[str, Any]:
        """Validate that all performance targets are being met in production."""
        logger.info("Validating performance targets against production metrics")
        
        try:
            # Run quick validation tests
            validation_results = {}
            
            # Quick INSERT test (30 seconds)
            quick_config = BenchmarkConfig(
                insert_test_duration_seconds=30,
                insert_test_batch_size=50,
                calculation_test_iterations=500,
                capacity_test_duration_minutes=1
            )
            
            benchmark_service = PerformanceBenchmarkService(quick_config)
            
            insert_result = await benchmark_service._benchmark_insert_performance()
            calc_result = await benchmark_service._benchmark_calculation_performance()
            
            validation_results = {
                "validation_timestamp": datetime.utcnow().isoformat(),
                "insert_performance_validated": insert_result.target_met,
                "calculation_performance_validated": calc_result.target_met,
                "insert_ops_per_sec": insert_result.operations_per_second,
                "calculation_speedup": calc_result.details.get("speedup_multiplier", 0),
                "overall_validation": insert_result.target_met and calc_result.target_met
            }
            
            logger.info("Performance target validation completed",
                       insert_validated=insert_result.target_met,
                       calc_validated=calc_result.target_met)
            
            return validation_results
            
        except Exception as e:
            logger.error("Error validating performance targets", error=str(e))
            return {
                "validation_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "overall_validation": False
            }


# Global service instance
_performance_benchmark_service: Optional[PerformanceBenchmarkService] = None


def get_performance_benchmark_service(
    config: Optional[BenchmarkConfig] = None
) -> PerformanceBenchmarkService:
    """Get global PerformanceBenchmarkService instance."""
    global _performance_benchmark_service
    
    if _performance_benchmark_service is None:
        _performance_benchmark_service = PerformanceBenchmarkService(config)
        logger.info("PerformanceBenchmarkService initialized")
    
    return _performance_benchmark_service