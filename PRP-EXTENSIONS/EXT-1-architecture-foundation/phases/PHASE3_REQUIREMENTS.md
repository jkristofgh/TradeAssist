# Phase 3: HistoricalDataService Decomposition

## Phase Overview
- **Phase Name**: HistoricalDataService Decomposition
- **Duration**: 6 days
- **Implementation Complexity**: High
- **Dependencies**: Phase 1 (Database decorators), Phase 2 (Strategy pattern validation)
- **Risk Level**: HIGH

## Phase Objectives

### Primary Goals
Decompose the massive 1,424-line HistoricalDataService into 4 focused, maintainable components:

1. **Service Decomposition**: Break down monolithic service into 4 specialized components
2. **Single Responsibility**: Each component handles one specific aspect of historical data management
3. **Coordinator Pattern**: Refactored main service orchestrates components while maintaining public API
4. **Performance Preservation**: Maintain or improve current response times (<2000ms for 30 days, 3 symbols)

### Success Criteria
- [ ] HistoricalDataService reduced from 1,424 lines to <500 lines (coordinator pattern)
- [ ] 4 focused component classes implemented with clear responsibilities
- [ ] All existing public API methods maintain identical behavior and signatures
- [ ] Performance target <2000ms for typical requests (30 days, 3 symbols) maintained
- [ ] Component integration seamless with comprehensive testing
- [ ] Backward compatibility 100% preserved for all external interfaces

## Technical Architecture Requirements

### 1. Component Architecture Overview

Based on comprehensive PRP analysis, decompose into 4 specialized components:

```
HistoricalDataService (Coordinator <500 lines)
├── HistoricalDataFetcher (~320 lines)    # External API integration
├── HistoricalDataCache (~280 lines)      # Cache management  
├── HistoricalDataQueryManager (~250 lines) # Query handling
└── HistoricalDataValidator (~200 lines)  # Data validation
```

### 2. Component Implementation Requirements

#### 2.1 HistoricalDataFetcher Component
**File**: `src/backend/services/historical_data/fetcher.py`
**Target Size**: ~320 lines
**Responsibility**: External API integration and data retrieval

**Current Method Analysis from PRP**:
- **Methods to migrate**: 8 methods from existing service
  - `fetch_symbol_data()` (45 lines)
  - `fetch_multiple_symbols()` (38 lines)
  - `_fetch_symbol_data_schwab()` (52 lines)
  - `_generate_mock_data()` (87 lines)
  - `_enforce_rate_limiting()` (23 lines)
  - `_transform_schwab_response()` (31 lines)
  - `_should_use_mock_data()` (12 lines)
  - `_handle_api_errors()` (28 lines)

**Required Implementation**:
```python
class HistoricalDataFetcher:
    """
    Handles all data retrieval operations from external APIs.
    
    Responsibilities (from PRP analysis):
    - Schwab API integration with authentication
    - Rate limiting and circuit breaker implementation  
    - Mock data generation for development/testing
    - Response transformation and normalization
    - Error handling for external API failures
    - Progress tracking for multiple symbol requests
    """
    
    def __init__(self, schwab_client):
        self.schwab_client = schwab_client
        self._last_api_call = None
        self._min_api_interval = 1.0  # Rate limiting
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 5
        self._mock_data_enabled = None  # Lazy initialization
        
    async def fetch_symbol_data(self, symbol: str, start_date: date, 
                               end_date: date, period_type: str = "daily") -> List[MarketDataBar]:
        """
        Primary data fetching method.
        
        Requirements from PRP:
        - Integrate with existing Schwab client authentication
        - Enforce rate limiting (1 second minimum between calls)
        - Handle circuit breaker for API failures (5 failure threshold)
        - Transform Schwab response to internal MarketDataBar format
        - Fallback to mock data in development mode
        - Log all API interactions with appropriate detail level
        """
        
    async def fetch_multiple_symbols(self, symbols: List[str], 
                                    request: HistoricalDataRequest,
                                    progress_callback=None) -> Dict[str, List[MarketDataBar]]:
        """
        Multi-symbol fetching with progress tracking.
        
        Requirements:
        - Process symbols sequentially to respect rate limits
        - Provide progress callbacks for UI updates
        - Handle partial failures (some symbols succeed, others fail)
        - Aggregate results with error reporting
        - Maintain performance target: <2000ms total for 3 symbols
        """
        
    async def generate_mock_data(self, symbol: str, start_date: date,
                                end_date: date) -> List[MarketDataBar]:
        """
        Mock data generation for development.
        
        Requirements (existing logic preservation):
        - Generate realistic price movements with volatility
        - Maintain consistent volume patterns
        - Support all period types (daily, weekly, monthly)
        - Ensure deterministic output for testing
        """
        
    async def _enforce_rate_limiting(self) -> None:
        """Rate limiting implementation with existing patterns."""
        
    def _transform_schwab_response(self, response: dict, symbol: str) -> List[MarketDataBar]:
        """Response transformation maintaining existing format."""
        
    def _should_use_mock_data(self) -> bool:
        """Environment-based mock data determination."""
```

#### 2.2 HistoricalDataCache Component
**File**: `src/backend/services/historical_data/cache.py`
**Target Size**: ~280 lines
**Responsibility**: Cache management and optimization

**Current Method Analysis from PRP**:
- **Methods to migrate**: 6 methods from existing service
  - `get_cached_data()` (28 lines)
  - `cache_data()` (35 lines)
  - `_build_cache_key()` (42 lines)
  - `invalidate_cache()` (31 lines)
  - `_cleanup_expired_cache()` (48 lines)
  - `get_cache_statistics()` (67 lines)

**Required Implementation**:
```python
class HistoricalDataCache:
    """
    Manages all caching operations for historical market data.
    
    Responsibilities (from PRP analysis):
    - In-memory cache management with TTL (30 minutes default)
    - Cache key generation with consistent hashing
    - Cache statistics and performance monitoring
    - Cache invalidation strategies (pattern-based)
    - Memory management and cleanup for expired entries
    - Cache warming strategies for frequently accessed data
    """
    
    def __init__(self, ttl_minutes: int = 30, max_cache_size_mb: int = 100):
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_access_counts: Dict[str, int] = {}
        self._cache_ttl_minutes = ttl_minutes
        self._max_cache_size_mb = max_cache_size_mb
        self._cache_hits = 0
        self._cache_misses = 0
        
    async def get_cached_data(self, cache_key: str) -> Optional[List[MarketDataBar]]:
        """
        Cache retrieval with TTL validation.
        
        Requirements from PRP:
        - Check TTL expiration before returning data
        - Update access statistics (hits/misses)
        - Track access patterns for optimization
        - Clean up expired entries during retrieval
        - Return None for expired or missing entries
        """
        
    async def cache_data(self, cache_key: str, data: List[MarketDataBar]) -> None:
        """
        Cache storage with size management.
        
        Requirements:
        - Store data with current timestamp
        - Enforce maximum cache size limits
        - Implement LRU eviction when size limit exceeded
        - Update cache statistics and access patterns
        - Handle serialization for complex data structures
        """
        
    def build_cache_key(self, symbol: str, start_date: date, end_date: date, 
                       period_type: str, **kwargs) -> str:
        """
        Consistent cache key generation.
        
        Requirements from existing implementation:
        - Include all request parameters in key
        - Handle parameter ordering consistency
        - Support additional parameters via kwargs
        - Generate short, collision-resistant keys
        - Include version hash for cache invalidation on code changes
        """
        
    async def invalidate_cache(self, pattern: str = None) -> int:
        """
        Pattern-based cache invalidation.
        
        Requirements:
        - Support regex patterns for selective invalidation
        - Invalidate all entries if no pattern provided
        - Return count of invalidated entries
        - Update cache statistics appropriately
        - Handle memory cleanup immediately
        """
        
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Comprehensive cache performance statistics.
        
        Requirements (from existing implementation):
        - Hit rate calculation (hits / (hits + misses))
        - Cache size (entry count and memory usage)
        - Most accessed cache keys
        - Average data age in cache
        - Eviction statistics and patterns
        """
```

#### 2.3 HistoricalDataQueryManager Component
**File**: `src/backend/services/historical_data/query_manager.py`
**Target Size**: ~250 lines
**Responsibility**: Query parameter validation and saved query management

**Current Method Analysis from PRP**:
- **Methods to migrate**: 4 methods from existing service
  - `validate_request()` (45 lines)
  - `save_query()` (38 lines)
  - `load_query()` (22 lines)
  - `_analyze_query_patterns()` (89 lines)

**Required Implementation**:
```python
class HistoricalDataQueryManager:
    """
    Handles query parameter validation, saved queries, and optimization.
    
    Responsibilities (from PRP analysis):
    - Request parameter validation and normalization
    - Saved query management (save/load/delete operations)
    - Query pattern analysis for optimization opportunities
    - Query performance tracking and reporting
    - Parameter sanitization and security validation
    """
    
    def __init__(self):
        self._query_patterns: Dict[str, int] = {}
        self._performance_stats: Dict[str, List[float]] = {}
        self._validation_rules = self._initialize_validation_rules()
        
    async def validate_request(self, request: HistoricalDataRequest) -> HistoricalDataRequest:
        """
        Request validation and normalization.
        
        Requirements from existing implementation:
        - Validate date ranges (start < end, not future dates)
        - Validate symbol formats (uppercase, valid characters)
        - Validate period types (daily, weekly, monthly)
        - Normalize date formats to consistent format
        - Apply business rules (max date range, weekend handling)
        - Sanitize inputs to prevent injection attacks
        """
        
    @with_db_session  # Using Phase 1 decorators
    async def save_query(self, session: AsyncSession, name: str, 
                        request: HistoricalDataRequest, 
                        description: str = None) -> int:
        """
        Save query for future reuse.
        
        Requirements:
        - Store query parameters in database
        - Validate query name uniqueness per user
        - Support optional description metadata
        - Return generated query ID
        - Handle duplicate name conflicts gracefully
        """
        
    @with_db_session  # Using Phase 1 decorators
    async def load_query(self, session: AsyncSession, query_id: int) -> Optional[HistoricalDataRequest]:
        """
        Load saved query by ID.
        
        Requirements:
        - Fetch query parameters from database
        - Validate query still meets current business rules
        - Return properly constructed HistoricalDataRequest
        - Handle missing queries gracefully (return None)
        - Log query usage for analytics
        """
        
    async def analyze_query_patterns(self) -> Dict[str, Any]:
        """
        Query pattern analysis for optimization.
        
        Requirements from existing logic:
        - Identify most frequently requested symbols
        - Analyze common date range patterns
        - Detect optimization opportunities (cache warming)
        - Generate performance recommendations
        - Track query complexity trends over time
        """
        
    def track_query_performance(self, query_signature: str, duration_ms: float) -> None:
        """Query performance tracking for optimization analysis."""
```

#### 2.4 HistoricalDataValidator Component
**File**: `src/backend/services/historical_data/validator.py`
**Target Size**: ~200 lines
**Responsibility**: Data validation and quality assurance

**Current Method Analysis from PRP**:
- **Methods to migrate**: 3 methods from existing service
  - `_handle_duplicate_bars()` (67 lines)
  - `_validate_data_quality()` (58 lines)
  - `_detect_data_gaps()` (45 lines)

**Required Implementation**:
```python
class HistoricalDataValidator:
    """
    Handles data validation, integrity checks, and quality assurance.
    
    Responsibilities (from PRP analysis):
    - Market data validation and sanitization
    - Duplicate detection and resolution strategies
    - Data quality scoring and reporting
    - Gap detection and reporting for time series data
    - Business rule validation (price ranges, volume checks)
    """
    
    def __init__(self):
        self._validation_rules = self._initialize_validation_rules()
        self._quality_thresholds = self._initialize_quality_thresholds()
        
    async def validate_market_data(self, data: List[MarketDataBar]) -> ValidationResult:
        """
        Comprehensive market data validation.
        
        Requirements from existing logic:
        - Validate price ranges (positive values, high >= low, etc.)
        - Validate volume data (non-negative, reasonable ranges)
        - Validate timestamp consistency and ordering
        - Check for obvious data errors (impossible price movements)
        - Generate detailed validation report with error specifics
        """
        
    async def handle_duplicates(self, data: List[MarketDataBar]) -> List[MarketDataBar]:
        """
        Duplicate detection and resolution.
        
        Requirements from existing implementation:
        - Detect duplicate entries by timestamp and symbol
        - Apply resolution strategy (keep latest, merge volumes, etc.)
        - Log duplicate handling actions for audit
        - Maintain data integrity during deduplication
        - Return cleaned dataset
        """
        
    def detect_data_gaps(self, data: List[MarketDataBar], 
                        expected_frequency: str) -> List[DataGap]:
        """
        Time series gap detection.
        
        Requirements:
        - Identify missing time periods in data series
        - Account for market closures (weekends, holidays)
        - Generate gap reports with date ranges and severity
        - Classify gap types (minor, major, critical)
        - Support different frequency expectations (daily, hourly, etc.)
        """
        
    def calculate_data_quality_score(self, data: List[MarketDataBar]) -> float:
        """
        Data quality scoring (0.0 to 1.0).
        
        Requirements:
        - Score based on completeness (no gaps)
        - Score based on accuracy (reasonable price movements)
        - Score based on consistency (proper ordering, valid values)
        - Weight different quality factors appropriately
        - Return standardized score for comparison
        """
```

### 3. Refactored HistoricalDataService (Coordinator)

#### 3.1 Coordinator Implementation
**File**: `src/backend/services/historical_data_service.py` (Refactored)
**Target Size**: <500 lines (down from 1,424 lines)
**Role**: Component orchestration and public API preservation

**Required Implementation**:
```python
class HistoricalDataService:
    """
    Main coordinator for historical data operations.
    
    Orchestrates the four specialized components while maintaining
    the same public interface for backward compatibility.
    
    New Architecture:
    - Delegates specialized tasks to focused components
    - Maintains existing public API contracts
    - Handles component initialization and lifecycle
    - Provides error handling and logging coordination
    - Manages component dependencies and communication
    """
    
    def __init__(self):
        self.schwab_client = None
        self.is_running = False
        
        # Initialize specialized components
        self.fetcher = None  # Initialized in start()
        self.cache = HistoricalDataCache()
        self.query_manager = HistoricalDataQueryManager()
        self.validator = HistoricalDataValidator()
        
    async def start(self) -> None:
        """
        Service startup with component initialization.
        
        Requirements:
        - Initialize Schwab client connection
        - Start all component services
        - Validate component dependencies
        - Set up monitoring and logging
        - Preserve existing startup behavior
        """
        logger.info("Starting HistoricalDataService")
        
        # Initialize Schwab client (existing pattern)
        self.schwab_client = await self._initialize_schwab_client()
        
        # Initialize components with dependencies
        self.fetcher = HistoricalDataFetcher(self.schwab_client)
        
        # Component health checks
        await self._validate_component_health()
        
        self.is_running = True
        logger.info("HistoricalDataService started successfully")
        
    async def stop(self) -> None:
        """
        Graceful service shutdown.
        
        Requirements:
        - Clean shutdown of all components
        - Cache cleanup and persistence
        - Connection cleanup
        - Preserve existing shutdown behavior
        """
        
    async def fetch_historical_data(self, request: HistoricalDataRequest) -> List[MarketDataBar]:
        """
        Main public interface - orchestrates all components.
        
        Component Orchestration Flow:
        1. QueryManager: Validate and normalize request
        2. Cache: Check for cached data
        3. Fetcher: Retrieve fresh data if cache miss
        4. Validator: Validate and clean retrieved data
        5. Cache: Store validated data for future use
        
        Requirements:
        - Maintain identical public interface
        - Preserve existing error handling patterns
        - Maintain performance targets (<2000ms)
        - Log component interactions for debugging
        """
        if not self.is_running:
            raise ServiceNotRunningError("HistoricalDataService not started")
            
        try:
            # Step 1: Validate request
            validated_request = await self.query_manager.validate_request(request)
            
            # Step 2: Check cache
            cache_key = self.cache.build_cache_key(
                symbols=validated_request.symbols,
                start_date=validated_request.start_date,
                end_date=validated_request.end_date,
                period_type=validated_request.period_type
            )
            
            cached_data = await self.cache.get_cached_data(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data
                
            # Step 3: Fetch fresh data
            logger.debug(f"Cache miss for {cache_key}, fetching fresh data")
            raw_data = await self.fetcher.fetch_multiple_symbols(
                validated_request.symbols, validated_request
            )
            
            # Step 4: Validate data
            all_data = []
            for symbol, symbol_data in raw_data.items():
                if symbol_data:  # Skip empty results
                    validation_result = await self.validator.validate_market_data(symbol_data)
                    if validation_result.is_valid:
                        cleaned_data = await self.validator.handle_duplicates(symbol_data)
                        all_data.extend(cleaned_data)
                    else:
                        logger.warning(f"Data validation failed for {symbol}: {validation_result.errors}")
                        
            # Step 5: Cache validated data
            if all_data:
                await self.cache.cache_data(cache_key, all_data)
                
            return all_data
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise
            
    # All other existing public methods preserved with component delegation
    async def store_historical_data(self, data: List[MarketDataBar]) -> int:
        """UNCHANGED interface - delegates to validator + database operations."""
        
    async def aggregate_data(self, request: AggregationRequest) -> List[MarketDataBar]:
        """UNCHANGED interface - uses components for data retrieval and processing."""
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        ENHANCED - aggregates statistics from all components.
        
        Requirements:
        - Combine statistics from all components
        - Maintain existing statistic formats
        - Add component-specific insights
        - Preserve existing monitoring integration
        """
        stats = {
            # Existing statistics
            'requests_served': self._requests_served,
            'average_response_time_ms': self._avg_response_time,
            'cache_hit_rate': self.cache.get_cache_statistics()['hit_rate'],
            
            # New component-specific statistics
            'component_stats': {
                'fetcher': {
                    'api_calls_made': getattr(self.fetcher, '_api_calls_made', 0),
                    'circuit_breaker_trips': getattr(self.fetcher, '_circuit_breaker_failures', 0),
                },
                'cache': self.cache.get_cache_statistics(),
                'validator': {
                    'validations_performed': getattr(self.validator, '_validations_performed', 0),
                    'duplicates_resolved': getattr(self.validator, '_duplicates_resolved', 0),
                },
                'query_manager': {
                    'queries_saved': len(self.query_manager._query_patterns),
                    'validation_failures': getattr(self.query_manager, '_validation_failures', 0),
                }
            }
        }
        return stats
```

## Implementation Plan

### Day 11-12: Component Architecture Setup

#### Day 11 Tasks:
- [ ] Create directory structure: `src/backend/services/historical_data/`
- [ ] Implement HistoricalDataFetcher class with API integration logic
- [ ] Migrate 8 fetching-related methods from original service
- [ ] Implement rate limiting and circuit breaker patterns
- [ ] Write unit tests for fetcher component

#### Day 12 Tasks:
- [ ] Implement HistoricalDataCache class with TTL and size management
- [ ] Migrate 6 caching-related methods from original service
- [ ] Implement LRU eviction and performance statistics
- [ ] Write unit tests for cache component
- [ ] Test cache performance and memory usage

### Day 13-14: Core Component Implementation

#### Day 13 Tasks:
- [ ] Implement HistoricalDataQueryManager with database decorators
- [ ] Migrate query validation and saved query functionality
- [ ] Integrate with Phase 1 database decorators
- [ ] Write unit tests for query manager
- [ ] Test database integration and performance

#### Day 14 Tasks:
- [ ] Implement HistoricalDataValidator with data quality checks
- [ ] Migrate duplicate handling and validation logic
- [ ] Implement data quality scoring algorithm
- [ ] Write unit tests for validator component
- [ ] Test validation accuracy and performance

### Day 15-16: Service Coordinator Implementation

#### Day 15 Tasks:
- [ ] Refactor main HistoricalDataService to coordinator pattern
- [ ] Implement component orchestration in main methods
- [ ] Preserve all existing public API methods and signatures
- [ ] Integrate component lifecycle management (start/stop)
- [ ] Test component communication and error handling

#### Day 16 Tasks:
- [ ] Complete service refactoring with all component integrations
- [ ] Implement enhanced performance statistics aggregation
- [ ] Test backward compatibility of all public interfaces
- [ ] Validate service startup and shutdown procedures
- [ ] Complete integration testing between components

### Day 17: Integration and Final Testing

#### Integration Testing:
- [ ] End-to-end testing of complete refactored service
- [ ] API endpoint testing for response format consistency
- [ ] Performance validation against <2000ms target
- [ ] WebSocket integration testing for real-time data
- [ ] Error propagation testing through all component layers

#### Final Validation:
- [ ] Memory usage analysis and optimization
- [ ] Concurrent operation testing
- [ ] Cache effectiveness validation
- [ ] Component isolation testing (individual component failures)
- [ ] Production readiness checklist completion

## Backward Compatibility Requirements

### 1. Public API Preservation
**All Existing Methods Must Remain Identical**:
```python
# Public interface signatures - UNCHANGED
async def fetch_historical_data(self, request: HistoricalDataRequest) -> List[MarketDataBar]
async def store_historical_data(self, data: List[MarketDataBar]) -> int  
async def aggregate_data(self, request: AggregationRequest) -> List[MarketDataBar]
def get_performance_stats(self) -> Dict[str, Any]
async def start(self) -> None
async def stop(self) -> None
```

### 2. Response Format Compatibility
**Data Structure Preservation**:
```python
# MarketDataBar structure - UNCHANGED
@dataclass
class MarketDataBar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
# All response formats remain identical
# Error message formats preserved
# Performance statistics format maintained
```

### 3. Configuration Compatibility
**Environment Variables**:
- No new required environment variables
- All existing configuration options preserved
- Component configuration via optional environment variables only

### 4. Integration Compatibility
**External Integration Points**:
- Schwab API client integration unchanged
- Database integration patterns preserved
- WebSocket integration maintained
- Caching behavior externally identical
- Error handling patterns preserved

## Quality Assurance Requirements

### 1. Testing Coverage Requirements
- [ ] Unit test coverage >90% for all new component classes
- [ ] Integration test coverage 100% of component interactions
- [ ] Regression test coverage 100% of existing public interfaces
- [ ] Performance test validation of all performance targets
- [ ] Error handling test coverage for all failure scenarios

### 2. Performance Requirements
- [ ] Historical data fetching: <2000ms for 30 days, 3 symbols
- [ ] Individual component overhead: <100ms per operation
- [ ] Memory usage: Neutral or improved by 5-10%
- [ ] Cache hit rate: Maintain or improve current rates
- [ ] Concurrent operation performance: No degradation

### 3. Code Quality Requirements
- [ ] Each component class <350 lines (meets size requirements)
- [ ] Single Responsibility Principle compliance for all components
- [ ] Clear component interfaces and dependencies
- [ ] Comprehensive error handling and logging
- [ ] Integration with existing monitoring and alerting

### 4. Security Requirements
- [ ] No new security vulnerabilities introduced
- [ ] API key and credential handling maintained securely
- [ ] Input validation maintains existing security standards
- [ ] Error messages don't expose sensitive information
- [ ] Component isolation prevents security boundary violations

## Phase 3 Completion Criteria

### Architectural Requirements Met
- [ ] HistoricalDataService reduced from 1,424 lines to <500 lines
- [ ] 4 specialized components implemented with clear responsibilities
- [ ] Component coordination seamless and well-tested
- [ ] Service decomposition follows established design patterns

### Functional Requirements Met
- [ ] All existing public API methods preserved and tested
- [ ] All response formats and error handling identical
- [ ] External integrations (Schwab API, database) maintained
- [ ] Cache behavior and performance statistics preserved

### Performance Requirements Met
- [ ] Performance targets maintained or exceeded
- [ ] Memory usage neutral or improved
- [ ] Component communication overhead minimized
- [ ] Concurrent operation performance preserved

### Quality Assurance Complete
- [ ] Comprehensive testing completed across all components
- [ ] Security review confirms no new vulnerabilities
- [ ] Documentation updated with component architecture
- [ ] Monitoring and alerting integration validated

Phase 3 represents the most complex refactoring in the extension, transforming a monolithic 1,424-line service into a clean, maintainable component-based architecture while preserving perfect backward compatibility and performance characteristics. This decomposition provides the foundation for future historical data enhancements and demonstrates the refactoring patterns for other large services.