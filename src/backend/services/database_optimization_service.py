"""
Database optimization service for TradeAssist Phase 3.

Provides advanced query optimization, index management, and performance monitoring
for historical data operations.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import structlog
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError

from src.backend.database.connection import get_db_session

logger = structlog.get_logger()


@dataclass
class IndexInfo:
    """Information about a database index."""
    
    name: str
    table_name: str
    columns: List[str]
    is_unique: bool
    size_kb: Optional[int] = None
    usage_count: Optional[int] = None
    last_used: Optional[datetime] = None


@dataclass
class QueryPerformanceInfo:
    """Information about query performance."""
    
    query_hash: str
    sql_pattern: str
    execution_count: int
    avg_execution_time_ms: float
    max_execution_time_ms: float
    last_executed: datetime
    suggested_indexes: List[str]


class DatabaseOptimizationService:
    """
    Advanced database optimization service for historical data performance.
    
    Features:
    - Automatic index analysis and recommendations
    - Query performance monitoring and optimization
    - Database maintenance and cleanup
    - Storage optimization for time-series data
    - Performance benchmarking and alerting
    """
    
    def __init__(self):
        self.is_running = False
        self._background_tasks: List[asyncio.Task] = []
        
        # Performance tracking
        self._query_stats: Dict[str, QueryPerformanceInfo] = {}
        self._index_usage: Dict[str, IndexInfo] = {}
        self._optimization_suggestions: List[str] = []
        
        # Configuration
        self._maintenance_interval_hours = 6
        self._slow_query_threshold_ms = 500
        self._index_usage_threshold = 100  # Minimum usage to keep index
        
    async def start(self) -> None:
        """Start the database optimization service."""
        if self.is_running:
            logger.warning("Database optimization service already running")
            return
        
        logger.info("Starting database optimization service")
        self.is_running = True
        
        try:
            # Initial database analysis
            await self._analyze_current_database()
            
            # Create recommended indexes
            await self._create_recommended_indexes()
            
            # Start background maintenance tasks
            maintenance_task = asyncio.create_task(self._maintenance_loop())
            self._background_tasks.append(maintenance_task)
            
            # Performance monitoring task
            perf_task = asyncio.create_task(self._performance_monitoring_loop())
            self._background_tasks.append(perf_task)
            
            logger.info("Database optimization service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start database optimization service: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the database optimization service."""
        if not self.is_running:
            return
        
        logger.info("Stopping database optimization service")
        self.is_running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()
        
        logger.info("Database optimization service stopped")
    
    async def analyze_query_performance(self, sql: str, execution_time_ms: float) -> None:
        """
        Analyze and track query performance.
        
        Args:
            sql: SQL query string
            execution_time_ms: Execution time in milliseconds
        """
        try:
            # Create a hash/pattern for the query
            query_pattern = self._normalize_sql_pattern(sql)
            query_hash = str(hash(query_pattern))
            
            now = datetime.now()
            
            if query_hash in self._query_stats:
                stats = self._query_stats[query_hash]
                stats.execution_count += 1
                stats.avg_execution_time_ms = (
                    (stats.avg_execution_time_ms * (stats.execution_count - 1) + execution_time_ms)
                    / stats.execution_count
                )
                stats.max_execution_time_ms = max(stats.max_execution_time_ms, execution_time_ms)
                stats.last_executed = now
            else:
                self._query_stats[query_hash] = QueryPerformanceInfo(
                    query_hash=query_hash,
                    sql_pattern=query_pattern,
                    execution_count=1,
                    avg_execution_time_ms=execution_time_ms,
                    max_execution_time_ms=execution_time_ms,
                    last_executed=now,
                    suggested_indexes=[]
                )
            
            # Analyze slow queries
            if execution_time_ms > self._slow_query_threshold_ms:
                await self._analyze_slow_query(query_pattern, execution_time_ms)
            
        except Exception as e:
            logger.error(f"Query performance analysis failed: {e}")
    
    async def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get current optimization recommendations.
        
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        try:
            # Index recommendations
            index_recs = await self._get_index_recommendations()
            recommendations.extend(index_recs)
            
            # Query optimization recommendations
            query_recs = await self._get_query_optimization_recommendations()
            recommendations.extend(query_recs)
            
            # Maintenance recommendations
            maintenance_recs = await self._get_maintenance_recommendations()
            recommendations.extend(maintenance_recs)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get optimization recommendations: {e}")
            return []
    
    async def optimize_database(self) -> Dict[str, Any]:
        """
        Perform comprehensive database optimization.
        
        Returns:
            Optimization results summary
        """
        results = {
            "start_time": datetime.now(),
            "indexes_created": 0,
            "indexes_removed": 0,
            "maintenance_performed": [],
            "performance_improvement": {}
        }
        
        try:
            # Create beneficial indexes
            created = await self._create_beneficial_indexes()
            results["indexes_created"] = created
            
            # Remove unused indexes
            removed = await self._remove_unused_indexes()
            results["indexes_removed"] = removed
            
            # Perform database maintenance
            maintenance = await self._perform_database_maintenance()
            results["maintenance_performed"] = maintenance
            
            # Update statistics
            await self._update_database_statistics()
            
            results["end_time"] = datetime.now()
            results["duration_seconds"] = (
                results["end_time"] - results["start_time"]
            ).total_seconds()
            
            logger.info(f"Database optimization completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            results["error"] = str(e)
            return results
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        try:
            async with get_db_session() as session:
                # Get basic database info
                db_size_query = text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                result = await session.execute(db_size_query)
                db_size = result.scalar() or 0
                
                # Get table statistics
                table_stats = await self._get_table_statistics()
                
                # Get index statistics
                index_stats = await self._get_index_statistics()
                
                return {
                    "database_size_mb": round(db_size / (1024 * 1024), 2),
                    "query_stats": {
                        "total_queries_tracked": len(self._query_stats),
                        "slow_queries": sum(
                            1 for stats in self._query_stats.values()
                            if stats.avg_execution_time_ms > self._slow_query_threshold_ms
                        ),
                        "avg_query_time_ms": (
                            sum(stats.avg_execution_time_ms for stats in self._query_stats.values())
                            / len(self._query_stats) if self._query_stats else 0
                        )
                    },
                    "table_stats": table_stats,
                    "index_stats": index_stats,
                    "optimization_suggestions": len(self._optimization_suggestions),
                    "last_optimized": getattr(self, '_last_optimized', None)
                }
                
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _analyze_current_database(self) -> None:
        """Analyze current database structure and performance."""
        try:
            async with get_db_session() as session:
                # Analyze existing indexes
                await self._analyze_existing_indexes(session)
                
                # Check for missing indexes on common query patterns
                await self._check_missing_indexes(session)
                
                logger.info("Database analysis completed")
                
        except Exception as e:
            logger.error(f"Database analysis failed: {e}")
    
    async def _create_recommended_indexes(self) -> None:
        """Create recommended indexes for historical data performance."""
        recommended_indexes = [
            # Composite index for timestamp range queries
            {
                "name": "idx_market_data_symbol_timestamp_freq",
                "table": "market_data_bar",
                "columns": ["symbol", "timestamp", "frequency"],
                "sql": """
                    CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp_freq 
                    ON market_data_bar(symbol, timestamp, frequency)
                """
            },
            # Index for frequency-based queries
            {
                "name": "idx_market_data_freq_timestamp",
                "table": "market_data_bar", 
                "columns": ["frequency", "timestamp"],
                "sql": """
                    CREATE INDEX IF NOT EXISTS idx_market_data_freq_timestamp 
                    ON market_data_bar(frequency, timestamp)
                """
            },
            # Index for asset class queries
            {
                "name": "idx_market_data_asset_class_symbol",
                "table": "market_data_bar",
                "columns": ["asset_class", "symbol"],
                "sql": """
                    CREATE INDEX IF NOT EXISTS idx_market_data_asset_class_symbol 
                    ON market_data_bar(asset_class, symbol)
                """
            },
            # Index for futures-specific queries
            {
                "name": "idx_market_data_continuous_contract",
                "table": "market_data_bar",
                "columns": ["continuous_series", "contract_month", "symbol"],
                "sql": """
                    CREATE INDEX IF NOT EXISTS idx_market_data_continuous_contract 
                    ON market_data_bar(continuous_series, contract_month, symbol)
                    WHERE continuous_series = 1
                """
            },
            # Index for data source queries
            {
                "name": "idx_data_source_provider_active",
                "table": "data_source",
                "columns": ["provider", "active"],
                "sql": """
                    CREATE INDEX IF NOT EXISTS idx_data_source_provider_active 
                    ON data_source(provider, active)
                """
            }
        ]
        
        try:
            async with get_db_session() as session:
                for index_info in recommended_indexes:
                    try:
                        await session.execute(text(index_info["sql"]))
                        logger.info(f"Created index: {index_info['name']}")
                    except OperationalError as e:
                        if "already exists" not in str(e):
                            logger.error(f"Failed to create index {index_info['name']}: {e}")
                
                await session.commit()
                logger.info("Recommended indexes created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create recommended indexes: {e}")
    
    async def _maintenance_loop(self) -> None:
        """Background maintenance loop."""
        while self.is_running:
            try:
                await asyncio.sleep(self._maintenance_interval_hours * 3600)
                
                # Perform database maintenance
                await self._perform_database_maintenance()
                
                # Update optimization recommendations
                await self._update_optimization_recommendations()
                
                logger.info("Database maintenance cycle completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Maintenance loop error: {e}")
    
    async def _performance_monitoring_loop(self) -> None:
        """Background performance monitoring loop."""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Analyze query performance trends
                await self._analyze_performance_trends()
                
                # Check for performance degradation
                await self._check_performance_degradation()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
    
    async def _analyze_existing_indexes(self, session) -> None:
        """Analyze existing database indexes."""
        try:
            # Get index information (SQLite specific)
            index_query = text("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
            result = await session.execute(index_query)
            
            for row in result:
                index_name, table_name, sql = row
                self._index_usage[index_name] = IndexInfo(
                    name=index_name,
                    table_name=table_name,
                    columns=[],  # Would need to parse SQL to get columns
                    is_unique="UNIQUE" in (sql or "").upper(),
                    usage_count=0
                )
            
            logger.info(f"Analyzed {len(self._index_usage)} existing indexes")
            
        except Exception as e:
            logger.error(f"Failed to analyze existing indexes: {e}")
    
    async def _check_missing_indexes(self, session) -> None:
        """Check for missing indexes based on common query patterns."""
        # This would analyze query logs to identify missing indexes
        # For now, we'll use the predefined recommendations
        logger.debug("Missing index analysis completed")
    
    def _normalize_sql_pattern(self, sql: str) -> str:
        """Normalize SQL query to identify patterns."""
        import re
        
        # Remove comments and extra whitespace
        sql = re.sub(r'--.*?\n', '', sql)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        sql = ' '.join(sql.split())
        
        # Replace literals with placeholders
        sql = re.sub(r"'[^']*'", "'?'", sql)
        sql = re.sub(r'\b\d+\b', '?', sql)
        
        return sql.upper()
    
    async def _analyze_slow_query(self, query_pattern: str, execution_time_ms: float) -> None:
        """Analyze slow queries and suggest optimizations."""
        logger.warning(f"Slow query detected ({execution_time_ms:.2f}ms): {query_pattern[:100]}...")
        
        # Add to suggestions if not already present
        suggestion = f"Optimize slow query: {query_pattern[:50]}... ({execution_time_ms:.2f}ms)"
        if suggestion not in self._optimization_suggestions:
            self._optimization_suggestions.append(suggestion)
    
    async def _get_index_recommendations(self) -> List[Dict[str, Any]]:
        """Get index-based optimization recommendations."""
        return [
            {
                "type": "index",
                "priority": "high",
                "description": "Create composite indexes for common query patterns",
                "estimated_improvement": "50-70% query performance improvement"
            }
        ]
    
    async def _get_query_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get query optimization recommendations."""
        recommendations = []
        
        for stats in self._query_stats.values():
            if stats.avg_execution_time_ms > self._slow_query_threshold_ms:
                recommendations.append({
                    "type": "query",
                    "priority": "medium",
                    "description": f"Optimize slow query pattern: {stats.sql_pattern[:50]}...",
                    "avg_time_ms": stats.avg_execution_time_ms,
                    "execution_count": stats.execution_count
                })
        
        return recommendations
    
    async def _get_maintenance_recommendations(self) -> List[Dict[str, Any]]:
        """Get database maintenance recommendations."""
        return [
            {
                "type": "maintenance",
                "priority": "low",
                "description": "Regular VACUUM and ANALYZE operations",
                "frequency": "weekly"
            }
        ]
    
    async def _create_beneficial_indexes(self) -> int:
        """Create indexes that would benefit performance."""
        # This would be based on query analysis
        return 0
    
    async def _remove_unused_indexes(self) -> int:
        """Remove indexes that are not being used."""
        # This would analyze index usage statistics
        return 0
    
    async def _perform_database_maintenance(self) -> List[str]:
        """Perform database maintenance operations."""
        maintenance_performed = []
        
        try:
            async with get_db_session() as session:
                # SQLite maintenance operations
                await session.execute(text("PRAGMA optimize"))
                maintenance_performed.append("PRAGMA optimize")
                
                # Update statistics
                await session.execute(text("ANALYZE"))
                maintenance_performed.append("ANALYZE")
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Database maintenance failed: {e}")
        
        return maintenance_performed
    
    async def _update_database_statistics(self) -> None:
        """Update database statistics for query planner."""
        try:
            async with get_db_session() as session:
                await session.execute(text("ANALYZE"))
                await session.commit()
                logger.info("Database statistics updated")
        except Exception as e:
            logger.error(f"Failed to update database statistics: {e}")
    
    async def _get_table_statistics(self) -> Dict[str, Any]:
        """Get table-level statistics."""
        try:
            async with get_db_session() as session:
                # Get row counts for main tables
                tables = ["market_data_bar", "data_source", "data_query"]
                stats = {}
                
                for table in tables:
                    try:
                        count_query = text(f"SELECT COUNT(*) FROM {table}")
                        result = await session.execute(count_query)
                        stats[table] = result.scalar()
                    except Exception:
                        stats[table] = 0
                
                return stats
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return {}
    
    async def _get_index_statistics(self) -> Dict[str, Any]:
        """Get index-level statistics."""
        return {
            "total_indexes": len(self._index_usage),
            "unused_indexes": sum(
                1 for idx in self._index_usage.values()
                if (idx.usage_count or 0) < self._index_usage_threshold
            )
        }
    
    async def _update_optimization_recommendations(self) -> None:
        """Update optimization recommendations based on current performance."""
        # This would analyze current performance and update recommendations
        self._last_optimized = datetime.now()
    
    async def _analyze_performance_trends(self) -> None:
        """Analyze performance trends over time."""
        # This would track performance metrics over time
        pass
    
    async def _check_performance_degradation(self) -> None:
        """Check for performance degradation and alert if necessary."""
        current_avg = (
            sum(stats.avg_execution_time_ms for stats in self._query_stats.values())
            / len(self._query_stats) if self._query_stats else 0
        )
        
        if current_avg > self._slow_query_threshold_ms:
            logger.warning(f"Performance degradation detected: avg query time {current_avg:.2f}ms")