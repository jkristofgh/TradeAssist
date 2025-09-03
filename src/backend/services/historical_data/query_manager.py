"""
Historical Data Query Manager Component

Handles query parameter validation, saved queries, and optimization.
Extracted from HistoricalDataService as part of Phase 3 decomposition.
"""

import json
import re
import structlog
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Set

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.decorators import with_db_session, handle_db_errors
from ...models.historical_data import DataQuery, DataFrequency

logger = structlog.get_logger()


@dataclass 
class HistoricalDataRequest:
    """Request structure for historical data retrieval."""
    symbols: List[str]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    frequency: str = DataFrequency.DAILY.value
    include_extended_hours: bool = False
    max_records: Optional[int] = None


@dataclass
class ValidationResult:
    """Result of request validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    normalized_request: Optional[HistoricalDataRequest] = None


class HistoricalDataQueryManager:
    """
    Handles query parameter validation, saved queries, and optimization.
    
    Responsibilities:
    - Request parameter validation and normalization
    - Saved query management (save/load/delete operations)
    - Query pattern analysis for optimization opportunities
    - Query performance tracking and reporting
    - Parameter sanitization and security validation
    """
    
    def __init__(self):
        self._query_patterns: Dict[str, int] = defaultdict(int)
        self._performance_stats: Dict[str, List[float]] = defaultdict(list)
        self._validation_rules = self._initialize_validation_rules()
        self._validation_failures = 0
        self._validation_successes = 0
        
        # Query optimization tracking
        self._popular_symbols: Dict[str, int] = defaultdict(int)
        self._popular_date_ranges: Dict[str, int] = defaultdict(int)
        self._popular_frequencies: Dict[str, int] = defaultdict(int)
        
        logger.debug("HistoricalDataQueryManager initialized")

    async def validate_request(self, request: HistoricalDataRequest) -> HistoricalDataRequest:
        """
        Validate and normalize historical data request parameters.
        
        Args:
            request: The request to validate
            
        Returns:
            Normalized and validated request
            
        Raises:
            ValueError: If validation fails with critical errors
        """
        logger.debug("Validating historical data request", symbols=request.symbols)
        
        validation_result = await self._validate_request_internal(request)
        
        if not validation_result.is_valid:
            self._validation_failures += 1
            error_msg = f"Request validation failed: {', '.join(validation_result.errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        if validation_result.warnings:
            logger.warning(f"Request validation warnings: {', '.join(validation_result.warnings)}")
            
        self._validation_successes += 1
        
        # Track patterns for optimization
        self._track_query_patterns(validation_result.normalized_request)
        
        logger.debug("Request validation successful")
        return validation_result.normalized_request

    @with_db_session
    @handle_db_errors("Save query operation")
    async def save_query(
        self, 
        session: AsyncSession,
        name: str, 
        request: HistoricalDataRequest,
        description: Optional[str] = None,
        is_favorite: bool = False
    ) -> int:
        """
        Save query for future reuse.
        
        Args:
            session: Database session
            name: Query name
            request: Historical data request to save
            description: Optional description
            is_favorite: Whether to mark as favorite
            
        Returns:
            Generated query ID
            
        Raises:
            ValueError: If query name already exists or parameters invalid
        """
        logger.info(f"Saving query: {name}")
        
        # Validate query name
        if not name or not name.strip():
            raise ValueError("Query name cannot be empty")
            
        if len(name) > 100:
            raise ValueError("Query name too long (max 100 characters)")
            
        # Check for name uniqueness
        existing_query = await session.execute(
            select(DataQuery).where(DataQuery.name == name)
        )
        if existing_query.scalar_one_or_none():
            raise ValueError(f"Query with name '{name}' already exists")
            
        # Validate the request before saving
        validated_request = await self.validate_request(request)
        
        # Create query record
        query = DataQuery(
            name=name.strip(),
            description=description.strip() if description else None,
            symbols=json.dumps(validated_request.symbols),
            frequency=validated_request.frequency,
            start_date=validated_request.start_date,
            end_date=validated_request.end_date,
            filters=json.dumps({
                "include_extended_hours": validated_request.include_extended_hours,
                "max_records": validated_request.max_records
            }),
            is_favorite=is_favorite
        )
        
        session.add(query)
        await session.commit()
        await session.refresh(query)
        
        logger.info(f"Query saved successfully with ID: {query.id}")
        return query.id

    @with_db_session
    @handle_db_errors("Load query operation")
    async def load_query(self, session: AsyncSession, query_id: int) -> Optional[HistoricalDataRequest]:
        """
        Load saved query by ID.
        
        Args:
            session: Database session
            query_id: Query ID to load
            
        Returns:
            HistoricalDataRequest if found, None otherwise
        """
        logger.debug(f"Loading query ID: {query_id}")
        
        result = await session.execute(
            select(DataQuery).where(DataQuery.id == query_id)
        )
        query = result.scalar_one_or_none()
        
        if not query:
            logger.warning(f"Query ID {query_id} not found")
            return None
            
        try:
            # Parse stored data
            symbols = json.loads(query.symbols)
            filters = json.loads(query.filters) if query.filters else {}
            
            # Create request object
            request = HistoricalDataRequest(
                symbols=symbols,
                start_date=query.start_date,
                end_date=query.end_date,
                frequency=query.frequency,
                include_extended_hours=filters.get("include_extended_hours", False),
                max_records=filters.get("max_records")
            )
            
            # Validate the loaded request still meets current business rules
            try:
                validated_request = await self.validate_request(request)
            except ValueError as e:
                logger.warning(f"Loaded query {query_id} no longer valid: {e}")
                return None
                
            # Update usage tracking
            query.execution_count += 1
            query.last_executed = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Query {query_id} loaded and executed successfully")
            return validated_request
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse stored query {query_id}: {e}")
            return None

    @with_db_session
    @handle_db_errors("Delete query operation")
    async def delete_query(self, session: AsyncSession, query_id: int) -> bool:
        """
        Delete a saved query.
        
        Args:
            session: Database session
            query_id: Query ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        result = await session.execute(
            select(DataQuery).where(DataQuery.id == query_id)
        )
        query = result.scalar_one_or_none()
        
        if not query:
            return False
            
        await session.delete(query)
        await session.commit()
        
        logger.info(f"Query {query_id} deleted successfully")
        return True

    @with_db_session
    async def list_saved_queries(
        self, 
        session: AsyncSession,
        favorites_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List saved queries with metadata.
        
        Args:
            session: Database session
            favorites_only: Only return favorite queries
            limit: Maximum number of queries to return
            
        Returns:
            List of query metadata dictionaries
        """
        query = select(DataQuery).order_by(DataQuery.last_executed.desc())
        
        if favorites_only:
            query = query.where(DataQuery.is_favorite == True)
            
        query = query.limit(limit)
        
        result = await session.execute(query)
        queries = result.scalars().all()
        
        return [
            {
                "id": q.id,
                "name": q.name,
                "description": q.description,
                "frequency": q.frequency,
                "symbol_count": len(json.loads(q.symbols)),
                "is_favorite": q.is_favorite,
                "execution_count": q.execution_count,
                "last_executed": q.last_executed,
                "created_at": q.created_at
            }
            for q in queries
        ]

    async def analyze_query_patterns(self) -> Dict[str, Any]:
        """
        Analyze query patterns for optimization opportunities.
        
        Returns:
            Dictionary with analysis results and recommendations
        """
        logger.debug("Analyzing query patterns")
        
        # Most popular symbols
        top_symbols = sorted(
            self._popular_symbols.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Most popular frequencies
        top_frequencies = sorted(
            self._popular_frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Most popular date ranges (by range length)
        top_date_ranges = sorted(
            self._popular_date_ranges.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Performance statistics
        avg_performance = {}
        for query_sig, times in self._performance_stats.items():
            if times:
                avg_performance[query_sig] = {
                    "avg_time_ms": sum(times) / len(times),
                    "min_time_ms": min(times),
                    "max_time_ms": max(times),
                    "execution_count": len(times)
                }
        
        # Generate recommendations
        recommendations = self._generate_optimization_recommendations(
            top_symbols, top_frequencies, avg_performance
        )
        
        analysis = {
            "analysis_timestamp": datetime.utcnow(),
            "total_queries_analyzed": sum(self._query_patterns.values()),
            "validation_success_rate": (
                self._validation_successes / 
                max(self._validation_successes + self._validation_failures, 1) * 100
            ),
            "top_symbols": top_symbols,
            "top_frequencies": top_frequencies,
            "top_date_ranges": top_date_ranges,
            "performance_stats": avg_performance,
            "recommendations": recommendations
        }
        
        logger.info(f"Query pattern analysis completed: {len(top_symbols)} popular symbols found")
        return analysis

    def track_query_performance(self, query_signature: str, duration_ms: float) -> None:
        """
        Track query performance for optimization analysis.
        
        Args:
            query_signature: Unique signature identifying the query type
            duration_ms: Execution time in milliseconds
        """
        self._performance_stats[query_signature].append(duration_ms)
        
        # Keep only recent performance data (last 1000 executions per signature)
        if len(self._performance_stats[query_signature]) > 1000:
            self._performance_stats[query_signature] = (
                self._performance_stats[query_signature][-1000:]
            )

    def get_query_manager_stats(self) -> Dict[str, Any]:
        """
        Get query manager performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        total_validations = self._validation_successes + self._validation_failures
        
        return {
            "total_validations": total_validations,
            "validation_successes": self._validation_successes,
            "validation_failures": self._validation_failures,
            "validation_success_rate": (
                self._validation_successes / max(total_validations, 1) * 100
            ),
            "tracked_query_patterns": len(self._query_patterns),
            "tracked_performance_signatures": len(self._performance_stats),
            "popular_symbols_count": len(self._popular_symbols),
            "popular_frequencies_count": len(self._popular_frequencies)
        }

    # Private helper methods
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for request parameters."""
        return {
            "max_symbols": 50,  # Maximum symbols per request
            "max_date_range_days": 365 * 2,  # Maximum 2 years
            "min_date_range_days": 1,  # Minimum 1 day
            "max_records": 10000,  # Maximum records per request
            "valid_frequencies": [f.value for f in DataFrequency],
            "symbol_pattern": re.compile(r"^[A-Z0-9\.\-\/$]{1,10}$"),  # Valid symbol format (includes / for futures and $ for indices)
            "max_query_name_length": 100,
            "max_description_length": 500
        }

    async def _validate_request_internal(self, request: HistoricalDataRequest) -> ValidationResult:
        """Internal request validation logic."""
        errors = []
        warnings = []
        
        # Create a copy for normalization
        normalized_request = HistoricalDataRequest(
            symbols=request.symbols.copy() if request.symbols else [],
            start_date=request.start_date,
            end_date=request.end_date,
            frequency=request.frequency,
            include_extended_hours=request.include_extended_hours,
            max_records=request.max_records
        )
        
        # Validate symbols
        if not normalized_request.symbols:
            errors.append("At least one symbol is required")
        else:
            # Check symbol count
            if len(normalized_request.symbols) > self._validation_rules["max_symbols"]:
                errors.append(
                    f"Too many symbols: {len(normalized_request.symbols)} "
                    f"(max: {self._validation_rules['max_symbols']})"
                )
                
            # Normalize and validate symbol format
            normalized_symbols = []
            for symbol in normalized_request.symbols:
                symbol = symbol.strip().upper()
                if not symbol:
                    continue
                    
                if not self._validation_rules["symbol_pattern"].match(symbol):
                    errors.append(f"Invalid symbol format: {symbol}")
                    continue
                    
                normalized_symbols.append(symbol)
                
            # Remove duplicates while preserving order
            seen = set()
            normalized_request.symbols = [
                s for s in normalized_symbols 
                if s not in seen and not seen.add(s)
            ]
            
            if len(normalized_symbols) != len(request.symbols):
                warnings.append("Some symbols were normalized or removed due to invalid format")
        
        # Validate frequency
        if normalized_request.frequency not in self._validation_rules["valid_frequencies"]:
            errors.append(f"Invalid frequency: {normalized_request.frequency}")
        
        # Validate date range
        if normalized_request.start_date and normalized_request.end_date:
            # Ensure both dates are timezone-aware before comparison
            start_date = normalized_request.start_date
            end_date = normalized_request.end_date
            
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
                normalized_request.start_date = start_date
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
                normalized_request.end_date = end_date
                
            if start_date >= end_date:
                errors.append("Start date must be before end date")
            else:
                date_range_days = (end_date - start_date).days
                
                if date_range_days > self._validation_rules["max_date_range_days"]:
                    errors.append(
                        f"Date range too large: {date_range_days} days "
                        f"(max: {self._validation_rules['max_date_range_days']})"
                    )
                elif date_range_days < self._validation_rules["min_date_range_days"]:
                    warnings.append(f"Very small date range: {date_range_days} days")
        
        # Validate future dates
        now = datetime.now(timezone.utc)
        if normalized_request.start_date:
            # Make start_date timezone-aware if it's naive
            if normalized_request.start_date.tzinfo is None:
                normalized_request.start_date = normalized_request.start_date.replace(tzinfo=timezone.utc)
            if normalized_request.start_date > now:
                errors.append("Start date cannot be in the future")
        if normalized_request.end_date:
            # Make end_date timezone-aware if it's naive
            if normalized_request.end_date.tzinfo is None:
                normalized_request.end_date = normalized_request.end_date.replace(tzinfo=timezone.utc)
            if normalized_request.end_date > now:
                warnings.append("End date is in the future, will be limited to current time")
                normalized_request.end_date = now
        
        # Validate max_records
        if normalized_request.max_records is not None:
            if normalized_request.max_records <= 0:
                errors.append("max_records must be positive")
            elif normalized_request.max_records > self._validation_rules["max_records"]:
                warnings.append(
                    f"max_records reduced from {normalized_request.max_records} "
                    f"to {self._validation_rules['max_records']}"
                )
                normalized_request.max_records = self._validation_rules["max_records"]
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_request=normalized_request if len(errors) == 0 else None
        )

    def _track_query_patterns(self, request: HistoricalDataRequest) -> None:
        """Track query patterns for optimization analysis."""
        # Track symbol popularity
        for symbol in request.symbols:
            self._popular_symbols[symbol] += 1
            
        # Track frequency popularity
        self._popular_frequencies[request.frequency] += 1
        
        # Track date range patterns
        if request.start_date and request.end_date:
            range_days = (request.end_date - request.start_date).days
            range_key = f"{range_days}_days"
            self._popular_date_ranges[range_key] += 1
            
        # Track overall query pattern
        pattern_key = f"{len(request.symbols)}_{request.frequency}"
        self._query_patterns[pattern_key] += 1

    def _generate_optimization_recommendations(
        self,
        top_symbols: List[tuple],
        top_frequencies: List[tuple], 
        performance_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations based on patterns."""
        recommendations = []
        
        # Cache warming recommendations
        if top_symbols:
            top_5_symbols = [symbol for symbol, count in top_symbols[:5]]
            recommendations.append(
                f"Consider cache warming for top symbols: {', '.join(top_5_symbols)}"
            )
            
        # Frequency optimization
        if top_frequencies:
            top_freq = top_frequencies[0][0]
            recommendations.append(
                f"Most requested frequency is {top_freq} - optimize for this timeframe"
            )
            
        # Performance optimization
        slow_queries = [
            sig for sig, stats in performance_stats.items()
            if stats["avg_time_ms"] > 2000  # Slower than 2 seconds
        ]
        if slow_queries:
            recommendations.append(
                f"Consider optimizing slow query patterns: {len(slow_queries)} patterns identified"
            )
            
        return recommendations