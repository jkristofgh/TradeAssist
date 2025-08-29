# Phase 1: Foundation Data & Alert Engine

## 📋 Phase Information
- **Phase Number**: 1
- **Phase Name**: Foundation Data & Alert Engine
- **Dependencies**: None (Foundation phase)
- **Estimated Effort**: 5-6 weeks
- **Phase Type**: foundation
- **Complexity Level**: high

## 🔄 Previous Phase Context
### What Already Exists
```
This is the foundation phase - no previous implementation exists.
Starting from clean slate with:
- Project structure to be created
- Virtual environment setup required
- Initial FastAPI application framework
- SQLite database initialization
- Basic testing framework establishment
```

### Existing Codebase References
- **Backend Files**: `backend/` (to be created)
- **Database**: `data/trade_assist.db` (to be created)
- **Configuration**: `config/` (to be created)
- **Tests**: `tests/` (to be created)

### API Contracts Established
```
No existing API contracts - Phase 1 will establish the foundation APIs:
- RESTful endpoints for data access
- WebSocket connections for real-time streaming
- Authentication patterns for Schwab API integration
- Error handling and status reporting conventions
```

### Integration Points Available
```
No existing integration points - Phase 1 will create:
- Database connection patterns and ORM setup
- External API integration framework (Schwab API)
- WebSocket server infrastructure
- Async task processing foundations
```

## 🎯 Current Phase Requirements

### Primary Objectives
```
1. Establish real-time data ingestion from Schwab API with sub-second latency
2. Implement core alert engine with rule evaluation under 500ms
3. Create SQLite database with optimized time-series schema
4. Build FastAPI service with WebSocket real-time streaming
5. Ensure 99% API connection reliability with automatic reconnection
```

### Detailed Requirements

#### Real-Time Data Integration
```
- Schwab API Integration: OAuth 2.0 authentication with automatic token refresh
  * Real-time streaming connection for futures: ES, NQ, YM, CL, GC
  * Real-time streaming for indices: SPX, NDX, RUT 
  * Real-time streaming for internals: VIX, TICK, ADD, TRIN
  * Historical data backfill capabilities
  * Rate limiting compliance and circuit breaker implementation

- Data Normalization: Unified data format across all instrument types
  * Sub-second timestamp precision
  * Consistent field mapping (price, volume, timestamp)
  * Data validation and error handling
  * Missing data detection and handling
```

#### Alert Engine Implementation
```
- Rule Evaluation Engine: Sub-second alert processing
  * Static threshold rules (price above/below threshold)
  * Crossover detection (price crossing moving average)
  * Rate-of-change calculations (% change over time period)
  * Volume spike detection
  * Multi-condition rule combinations (AND/OR logic)

- Alert Generation: Real-time alert firing and logging
  * Alert context capture (rule, timestamp, instrument, trigger value)
  * Duplicate suppression within configurable time windows
  * Alert severity levels and priority handling
  * Alert delivery status tracking
```

#### Database Architecture
```
- SQLite with WAL Mode: Optimized for time-series and application data
  * instruments table: symbol, name, type, status, last_tick, created_at
  * market_data table: timestamp, instrument_id, price, volume, bid, ask
  * alert_rules table: id, instrument_id, rule_type, threshold, condition, active, created_at
  * alert_logs table: timestamp, rule_id, instrument_id, trigger_value, fired_status, delivery_status

- Performance Optimization:
  * Time-based partitioning strategies
  * Composite indexes on timestamp + instrument_id
  * Query optimization for real-time data access
  * Data retention policies and cleanup procedures
```

#### FastAPI Service Foundation
```
- Core Web Service: Single process architecture
  * FastAPI application with async/await patterns
  * WebSocket endpoints for real-time streaming
  * Background task management for data ingestion
  * Health check endpoints and system status

- API Endpoint Design:
  * GET/POST /api/instruments - Instrument management
  * GET/POST/PUT/DELETE /api/rules - Alert rule CRUD operations
  * GET /api/alerts - Alert history and status queries
  * GET /api/health - System health and connectivity status
  * WebSocket /ws/realtime - Real-time data and alert streaming
```

### Technical Specifications
```
- Technology Stack Additions:
  * FastAPI 0.104+ for async web framework
  * SQLAlchemy 2.0+ with AsyncSession for ORM
  * SQLite with WAL mode for database
  * WebSocket support via FastAPI WebSockets
  * Schwab API SDK or custom OAuth implementation
  * Pydantic models for data validation
  * pytest + pytest-asyncio for testing

- Architecture Patterns:
  * Event-driven architecture with async queues
  * Producer-consumer pattern for data ingestion
  * Observer pattern for alert rule evaluation
  * Circuit breaker pattern for external API calls

- Performance Requirements:
  * Tick-to-alert latency: <500ms for typical watchlist (10-15 instruments)
  * Data ingestion: 100+ ticks/second sustained throughput  
  * Database query response: <50ms for real-time queries
  * WebSocket message delivery: <100ms to connected clients
  * Memory usage: <512MB under normal load

- Security Considerations:
  * Schwab API credentials stored securely (preparation for GCSM in Phase 3)
  * SQLite database file permissions and access control
  * Rate limiting for external API calls
  * Input validation and sanitization for all endpoints
  * Error handling without exposing sensitive information
```

## 🔗 Integration Requirements

### Backward Compatibility
```
No backward compatibility required - this is the foundation phase.
However, establish patterns that will be maintained:
- RESTful API design principles
- Consistent error response formats
- WebSocket message structure standards
- Database schema evolution practices
```

### Forward Integration (For Phase 2)
```
Must expose interfaces and patterns for Phase 2 React UI:
- RESTful API endpoints with OpenAPI documentation
- WebSocket event streaming with defined message formats
- Database schema that supports UI data requirements
- Error handling patterns that provide user-friendly messages

Specific API Contracts for Phase 2:
- GET /api/instruments - Return all monitored instruments with status
- POST /api/rules - Accept alert rule creation with validation
- GET /api/alerts?limit=50&offset=0 - Paginated alert history
- WebSocket events: tick_update, alert_fired, health_status, rule_triggered
```

### Cross-Phase Communication
```
Data Flow Architecture:
- Schwab API → Data Ingestion Service → SQLite Database
- Alert Engine subscribes to data changes → Evaluates rules → Fires alerts
- WebSocket Service broadcasts real-time updates to connected clients
- All services share common database connection and models

Event Handling Patterns:
- Async event queues for decoupling data ingestion from processing
- WebSocket broadcasting for real-time UI updates
- Database triggers for alert rule evaluation optimization

Error Handling Framework:
- Structured error responses with error codes and user messages
- Circuit breaker patterns for external API resilience
- Graceful degradation when external services unavailable
- Error logging and monitoring for operational visibility
```

## ✅ Success Criteria

### Functional Validation
```
- [ ] Real-time data streaming from Schwab API for all target instruments (ES, NQ, YM, CL, GC, SPX, NDX, RUT, VIX, TICK, ADD, TRIN)
- [ ] Alert rules can be created, modified, and deleted via API endpoints
- [ ] Alert engine evaluates rules and fires alerts within 500ms of trigger conditions
- [ ] WebSocket connections deliver real-time tick updates to connected clients
- [ ] SQLite database stores time-series data with proper indexing and query performance
- [ ] System handles API disconnections with automatic reconnection and recovery
- [ ] Health monitoring endpoints provide accurate system status information
```

### Integration Validation
```
- [ ] No previous phases exist - focus on self-contained functionality
- [ ] API endpoints return consistent, well-formed responses
- [ ] WebSocket connections maintain stability under normal load
- [ ] Database transactions maintain ACID properties
- [ ] Error handling provides clear, actionable error messages
- [ ] Performance benchmarks established for Phase 2 baseline
```

### Performance Benchmarks
```
- Tick-to-alert latency: <500ms for watchlist of 10-15 instruments
- Data ingestion throughput: 100+ ticks/second sustained
- Database query performance: <50ms for real-time data queries
- WebSocket message delivery: <100ms from server to client
- Memory usage: <512MB under normal operation
- API response time: <100ms for CRUD operations
- System uptime: >95% during development and testing phase
```

## 📁 Expected Deliverables

### Code Components
```
Backend Core:
- main.py - FastAPI application entry point
- models/ - SQLAlchemy models for database schema
- api/ - RESTful API endpoint implementations
- services/ - Business logic services (data ingestion, alert engine)
- websocket/ - WebSocket connection handling
- integrations/ - Schwab API integration modules
- database/ - Database connection and initialization
- config/ - Configuration management and environment setup

Testing Infrastructure:
- tests/unit/ - Unit tests for all core components
- tests/integration/ - Integration tests for API endpoints
- tests/performance/ - Performance benchmarking tests
- conftest.py - pytest configuration and fixtures

Configuration:
- requirements.txt - Python dependencies
- alembic/ - Database migration scripts
- .env.example - Environment variable template
- docker-compose.yml - Development environment setup (optional)
```

### Documentation Updates
```
- [ ] API documentation (OpenAPI/Swagger) for all endpoints
- [ ] Database schema documentation with ERD diagrams
- [ ] WebSocket event documentation with message formats
- [ ] Development setup and installation instructions
- [ ] Performance benchmark baseline documentation
- [ ] Integration guide for Phase 2 development
```

### Configuration Changes
```
Environment Variables Required:
- SCHWAB_CLIENT_ID - Schwab API client identifier
- SCHWAB_CLIENT_SECRET - Schwab API client secret (temporary, moves to GCSM in Phase 3)
- DATABASE_URL - SQLite database file path
- LOG_LEVEL - Application logging level
- MARKET_DATA_RETENTION_DAYS - Data retention policy

Database Migrations:
- Initial schema creation with all required tables
- Indexes for performance optimization
- Foreign key constraints and relationships
- Default data seeding for instrument definitions
```

## 🔧 Implementation Guidelines

### Code Patterns to Follow
```
Error Handling Pattern:
- Custom exception classes for different error types
- Structured error responses with consistent format
- Async context managers for resource cleanup
- Circuit breaker pattern for external API calls

Logging Strategy:
- Structured logging with JSON format
- Performance metrics logging for optimization
- Error context capture for debugging
- Separate logs for audit trail and system events

Testing Patterns:
- Async test fixtures using pytest-asyncio
- Mock external API calls for unit tests
- Database transaction rollback for test isolation
- Performance benchmarking in CI/CD pipeline

Documentation Standards:
- Google-style docstrings for all functions
- Type hints for all function parameters and returns
- API endpoint documentation with examples
- Database schema documentation with relationships
```

### Dependencies and Constraints
```
Technology Versions:
- Python 3.11+ for optimal async performance
- FastAPI 0.104+ for latest WebSocket features
- SQLAlchemy 2.0+ for async ORM capabilities
- SQLite 3.38+ with WAL mode support
- Pydantic 2.0+ for data validation

External Services:
- Schwab API for market data (sandbox for development, live for testing)
- No other external dependencies for Phase 1

Performance Constraints:
- Sub-second alert latency requirement drives architecture decisions
- Memory efficiency required for sustained operation
- Database query optimization critical for real-time performance
- WebSocket connection limits based on system resources
```

## 🧪 Testing Strategy

### Unit Testing
```
Coverage Requirements: 80%+ for all core components

Mock Strategies:
- Mock Schwab API responses for data ingestion tests
- Mock database connections for service layer tests
- Mock WebSocket connections for real-time feature tests
- Performance benchmarking with synthetic data

Test Organization:
- tests/unit/models/ - Database model tests
- tests/unit/services/ - Business logic service tests  
- tests/unit/api/ - API endpoint tests
- tests/unit/integrations/ - External API integration tests
```

### Integration Testing
```
End-to-end Scenarios:
- Data ingestion → alert evaluation → alert firing workflow
- API CRUD operations with database persistence
- WebSocket connection lifecycle and message delivery
- Error handling and recovery scenarios

Performance Testing:
- Load testing with simulated market data volumes
- Latency measurement for tick-to-alert scenarios
- Database performance under concurrent access
- WebSocket connection scalability testing

System Integration:
- Schwab API integration with real sandbox data
- Database schema migration and rollback testing
- Configuration management and environment setup
- Health check and monitoring endpoint validation
```

## 🔄 Phase Completion Criteria

### Definition of Done
```
- [ ] All functional requirements implemented and tested
- [ ] API endpoints documented and tested with >95% uptime
- [ ] Alert engine meets <500ms latency requirement consistently
- [ ] Database schema optimized and performing within targets
- [ ] WebSocket real-time streaming functional and stable
- [ ] Unit test coverage >80% with all tests passing
- [ ] Integration tests passing for all major workflows
- [ ] Performance benchmarks established and documented
- [ ] Code review completed with security best practices validated
- [ ] Development environment setup documented and verified
```

### Handoff Requirements for Phase 2
```
API Contract Documentation:
- Complete OpenAPI specification for all endpoints
- WebSocket event schema definitions
- Error response format standards
- Authentication and rate limiting documentation

Database Schema Documentation:
- Entity relationship diagrams
- Table definitions with field descriptions
- Index strategy and performance characteristics
- Migration scripts and versioning approach

Integration Guide:
- How to connect React frontend to FastAPI backend
- WebSocket integration patterns and examples
- Real-time data subscription and state management
- Error handling and user feedback patterns

Performance Baseline:
- Benchmarking results and methodology
- Performance bottlenecks identified and documented
- Optimization opportunities for Phase 2
- Resource usage characteristics under load

Known Limitations:
- Schwab API rate limits and implications
- SQLite performance boundaries and scaling considerations
- WebSocket connection limits and memory usage
- Security temporary measures pending Phase 3 GCSM integration
```

## 🎯 Phase 1 Integration Contracts

### API Endpoints for Phase 2
```
GET /api/instruments
Response: [{"id": 1, "symbol": "ES", "name": "E-mini S&P 500", "type": "future", "status": "active", "last_tick": "2025-01-01T12:00:00Z", "last_price": 4500.25}]

POST /api/rules  
Request: {"instrument_id": 1, "rule_type": "threshold", "condition": "above", "threshold": 4500.0, "active": true}
Response: {"id": 123, "created_at": "2025-01-01T12:00:00Z", "status": "active"}

GET /api/alerts?limit=50&offset=0
Response: {"alerts": [...], "total": 150, "has_more": true}

GET /api/health
Response: {"status": "healthy", "ingestion_active": true, "last_tick": "2025-01-01T12:00:05Z", "api_connected": true}
```

### WebSocket Events for Phase 2
```
tick_update: {"type": "tick_update", "instrument_id": 1, "timestamp": "2025-01-01T12:00:00Z", "price": 4500.25, "volume": 100}

alert_fired: {"type": "alert_fired", "rule_id": 123, "instrument_id": 1, "value": 4501.0, "threshold": 4500.0, "timestamp": "2025-01-01T12:00:00Z"}

health_status: {"type": "health_status", "ingestion_status": "active", "last_tick_time": "2025-01-01T12:00:00Z", "api_status": "connected"}

rule_triggered: {"type": "rule_triggered", "rule_id": 123, "match_details": {"condition": "above", "actual": 4501.0, "threshold": 4500.0}, "evaluation_time": 450}
```

### Database Schema for Phase 2
```sql
-- Core tables that Phase 2 will query
CREATE TABLE instruments (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    last_tick TIMESTAMP,
    last_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alert_rules (
    id INTEGER PRIMARY KEY,
    instrument_id INTEGER NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    condition VARCHAR(20) NOT NULL,
    threshold DECIMAL(10,2) NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instrument_id) REFERENCES instruments(id)
);

CREATE TABLE alert_logs (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    rule_id INTEGER NOT NULL,
    instrument_id INTEGER NOT NULL,
    trigger_value DECIMAL(10,2) NOT NULL,
    fired_status VARCHAR(20) DEFAULT 'fired',
    delivery_status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (rule_id) REFERENCES alert_rules(id),
    FOREIGN KEY (instrument_id) REFERENCES instruments(id)
);
```

This Phase 1 foundation establishes all critical components needed for Phase 2 UI development while maintaining the sub-second performance requirements and providing a stable, well-documented API surface for frontend integration.