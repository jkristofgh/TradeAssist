# TradeAssist Architecture Design Document (Compressed)

## Executive Summary
TradeAssist delivers sub-second trading alerts with 99% uptime via single-user, self-hosted architecture. Ultra-light single process design (FastAPI + SQLite) meets all BRD requirements while avoiding over-engineering complexity.

## System Overview

### Core Components
1. **Data Ingestion Service** - Real-time Schwab API streaming
2. **Alert Engine** - Sub-second rule evaluation and generation
3. **Data Storage Layer** - SQLite time-series and alert logging
4. **Web Application** - React dashboard and rule management
5. **Notification System** - Multi-channel delivery (in-app, sound, Slack)
6. **Security Layer** - Google Cloud Secret Manager integration

### Architecture Pattern
**Event-driven single process** with async message queuing for sub-second latency and future scalability preparation.

## Recommended Architecture: Ultra-Light Single Process ⭐

### Technology Stack
- **Backend**: Single FastAPI application (web API + WebSocket + background tasks)
- **Database**: SQLite with WAL mode (time-series + application data)
- **Queuing**: In-memory Python queues (asyncio.Queue)
- **Frontend**: React with WebSocket real-time updates
- **Notifications**: Native Python libraries + Slack SDK

### Architecture Flow
```
Schwab API → FastAPI App → SQLite → [In-App, Sound, Slack] Notifications
             ↑                ↓
        React Frontend ← WebSocket Updates
```

### Benefits
- Single Python process, single database file
- Zero infrastructure complexity, perfect for LAB self-hosting
- Meets all sub-second latency requirements
- Simple backup (copy one file), easy development/debugging

### System Requirements
- CPU: 2+ cores, RAM: 2GB, Storage: 10GB
- No Docker/containers required

## Alternative Architecture: Complex Microservices

### When to Consider
- Multi-user requirements emerge (R2/R3 SaaS)
- Data volume exceeds SQLite capabilities (>1M ticks/day)
- High availability becomes critical (99.99% vs 99%)
- Advanced analytics require specialized time-series features

### Complex Stack (Future Migration)
- **Framework**: FastAPI with Redis Streams messaging
- **Time-Series**: InfluxDB 2.x with retention policies
- **Application Data**: PostgreSQL 15+ for complex queries
- **Frontend**: React + TypeScript SPA with Socket.IO
- **Deployment**: Docker Compose orchestration

## Data Storage Design

### SQLite Database Structure
**Single database handling:**
- Market data storage (time-series with instrument indexing)
- Alert rules and configuration management
- Alert logging and audit trail with delivery status
- User settings and API credentials (encrypted)

### Alternative Options (Complex Architecture)
- **InfluxDB**: Specialized time-series, better for analytics
- **PostgreSQL**: Complex relationships and queries
- **Redis**: High-performance caching and messaging

## Application Architecture

### FastAPI Single Process
**Core Responsibilities:**
- Main web server (API endpoints + WebSocket connections)
- Background task workers (data ingestion + alert processing)
- Async queue-based message processing for <500ms latency
- Database connection and transaction management

### Frontend Design
**React Web Interface:**
- Real-time dashboard with WebSocket integration
- Rule management with live validation
- Mobile-responsive for cross-device access
- Served directly by FastAPI static file serving

## Performance Architecture

### Sub-Second Latency Pipeline
1. **Ingestion**: WebSocket connection with connection pooling
2. **Processing**: In-memory rule evaluation with async queues
3. **Storage**: Async writes with batching optimization
4. **Alerting**: Parallel notification delivery across channels

### Performance Targets
- **Tick-to-Alert**: <500ms for typical watchlist (10-15 instruments)
- **API Response**: <100ms for dashboard updates
- **WebSocket**: <50ms update delivery to frontend
- **Alert Delivery**: <200ms across all channels

## Integration Architecture

### Schwab API Integration
**Connection Strategy:**
- WebSocket streaming for real-time data (primary)
- REST API for historical backfill and authentication
- OAuth 2.0 with automatic refresh token management
- Rate limiting with exponential backoff and circuit breakers

**Data Normalization:**
- Unified format across all instruments (futures, indices, internals)
- Sub-second timestamp precision for accurate sequencing
- Standardized data types for financial calculations

### Slack Integration
- OAuth 2.0 app registration with bot/user tokens
- Web API for message delivery to channels/DMs
- Error handling with retry logic and fallback channels

### Google Cloud Secret Manager
**Security Implementation:**
- Service account authentication with least privilege
- Encrypted credential storage with TLS transmission
- Optional manual rotation with health validation
- Local fallback via OS keyring during connectivity issues

## Security Architecture

### Credential Management
**Primary Strategy**: Google Cloud Secret Manager
- Service account key stored locally (install-time only)
- Secrets retrieved at boot, cached in memory only
- No credentials in application databases or logs
- TLS encryption for all external communications

**Fallback Strategy**: OS Keyring + encrypted .env with GCSM migration prompts

### Data Protection
- API keys encrypted at rest via GCSM
- Application limited to localhost access only
- Alert logs contain no sensitive user data
- Database file encryption via SQLite extensions

## Error Handling & Resilience

### Circuit Breaker Patterns
**API Connectivity:**
- Automatic failure detection with configurable thresholds
- Exponential backoff with maximum retry limits
- Fallback to cached data during outages
- User notification of degraded service states

### Graceful Degradation
1. **API Rate Limits**: Reduce polling frequency, queue requests
2. **Connectivity Loss**: Buffer events, auto-reconnect with status updates
3. **Alert Delivery Failures**: Multi-channel retry with exponential backoff
4. **Storage Issues**: In-memory caching with periodic flush attempts

## Deployment Architecture

### Self-Hosted LAB Environment
**Native Installation Approach:**
- Direct Python virtual environment setup
- Single process execution without containers
- Local web interface (http://localhost:8000)
- System service integration for auto-start

**Configuration Management:**
- Environment-based settings (development vs production)
- Market data endpoint management (sandbox vs live)
- Performance parameter tuning based on hardware

## Data Flow Architecture

### Real-Time Pipeline
```
Schwab WebSocket → Data Normalizer → Alert Engine → 
Rule Evaluator → Notification Router → [Multi-Channel Delivery] + 
SQLite Logger
```

### Historical Data Pipeline
```
Schwab REST → Data Validator → SQLite Writer → 
Background Aggregation → Retention Policy Enforcement
```

## Phase Implementation Mapping

### Phase 1: Foundation MVP
**Architecture Components:**
- Basic FastAPI service with WebSocket support
- SQLite database with market data schema
- Core alert engine with in-memory queuing
- Schwab API integration (sandbox testing)
- Basic React dashboard with real-time updates

### Phase 2: User Interface Complete
**Architecture Components:**
- Complete React UI with rule management
- WebSocket real-time updates for all dashboard components
- Alert logging and review interfaces
- Health monitoring and status displays
- Production Schwab API integration

### Phase 3: Production Integration
**Architecture Components:**
- Google Cloud Secret Manager integration
- Multi-channel notification system (Slack + sound)
- Advanced error handling and circuit breakers
- Data retention and cleanup automation
- Production security hardening

### Phase 4: Optimization & Monitoring
**Architecture Components:**
- Performance optimization and sub-second tuning
- Production deployment and monitoring setup
- Advanced resilience features and failover
- Documentation and operational procedures

## Migration Strategy

### Future SaaS Preparation
**Architecture Evolution Path:**
- **Phase 1→2**: Extract services from monolith when multi-user needed
- **Data Migration**: Export/import capabilities for database transitions
- **Service Separation**: Modular code design enables component extraction
- **Scaling Preparation**: Stateless design ready for horizontal scaling

### Component Extraction Priority
1. **Authentication Service**: First extraction for multi-tenancy
2. **Alert Engine**: Second extraction for independent scaling
3. **Data Ingestion**: Third extraction for multiple data sources
4. **Notification Service**: Fourth extraction for advanced delivery options

## Key Architectural Decisions

### Decision Matrix
1. **Simplicity Over Complexity**: Start simple, scale when business requirements justify
2. **Performance First**: Sub-second latency drives all technical choices
3. **Single User Optimization**: Avoid premature multi-user complexity
4. **Security Foundation**: Implement enterprise-grade security from start
5. **Migration Readiness**: Modular design enables future service extraction

### Success Metrics Alignment
**Technical Performance:**
- Sub-second alert latency: ✅ Event-driven architecture <500ms
- 99% uptime target: ✅ Circuit breakers and graceful degradation
- Data integrity: ✅ SQLite ACID compliance with WAL mode
- Security compliance: ✅ GCSM encryption + TLS communications

### Technology Rationale
**FastAPI**: Async/await native, excellent WebSocket support, automatic OpenAPI
**SQLite**: Zero administration, excellent performance for single-user, ACID compliance
**React**: Real-time UI capabilities, large ecosystem, TypeScript compatibility
**Python**: Single language ecosystem, excellent financial library support

## Next Steps
1. Development environment setup with recommended stack
2. Schwab API integration proof-of-concept
3. Alert engine core with async queue implementation
4. React UI foundation with WebSocket real-time updates
5. Multi-channel notification integration
6. Performance testing and sub-second optimization
7. Security hardening and GCSM integration
8. Production deployment and monitoring setup

---
*Compressed from 511 lines to 200 lines (60% reduction) preserving all architecture-critical decisions and implementation guidance.*