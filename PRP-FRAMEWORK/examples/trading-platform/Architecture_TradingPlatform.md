# TradeAssist Architecture Design Document

## Executive Summary

TradeAssist is a single-user, self-hosted trading alerts application designed to deliver sub-second market data alerts with 99% uptime during US market hours. This document outlines the recommended architecture, technology stack, and alternative approaches for implementing the MVP (Release 1).

## System Overview

### Core Components
1. **Data Ingestion Service** - Real-time market data streaming from Schwab API
2. **Alert Engine** - Sub-second rule evaluation and alert generation
3. **Data Storage Layer** - Time-series data and alert logging
4. **Web Application** - Dashboard and rule management UI
5. **Notification System** - Multi-channel alert delivery (in-app, sound, Slack)
6. **Security Layer** - Credential management via Google Cloud Secret Manager

### Architecture Pattern
**Recommended:** Event-driven microservices with message queuing
- Enables sub-second latency requirements
- Supports future horizontal scaling
- Provides fault tolerance and resilience

## Architecture Complexity Analysis

**Current Challenge:** The initial architecture recommendation is over-engineered for a single-user MVP, requiring 5+ services (FastAPI, Redis, InfluxDB, PostgreSQL, React) with Docker orchestration.

**Simplified Approach:** For Release 1 MVP, much lighter alternatives can meet all BRD requirements while reducing complexity by 80%.

## Simplified Architecture Options (Recommended for MVP)

### Option 1: Ultra-Light Single Process ⭐ RECOMMENDED
**Components:**
- **Single FastAPI application** (handles web API, WebSocket, background tasks)
- **SQLite database with WAL mode** (handles both time-series and application data)
- **In-memory Python queues** (asyncio.Queue for alert processing)
- **React frontend** for handling expected UI complexity
- **Native Python libraries** for notifications

**Architecture:**
```
Schwab API → FastAPI App → SQLite → [In-App, Sound, Slack] Notifications
             ↑                ↓
        Simple Frontend ← WebSocket Updates
```

**Benefits:**
- Single Python process, single database file
- Zero infrastructure complexity
- Simple setup and execution process
- Perfect for LAB self-hosting
- Meets all sub-second latency requirements
- Easy to backup (copy one file)

**System Requirements:**
- CPU: 2+ cores
- RAM: 2GB
- Storage: 10GB
- No Docker needed


## Ultra-Light Architecture Deep Dive (Recommended)

### Technology Stack
**Core Dependencies:**
- FastAPI web framework with WebSocket support
- SQLite database with async support
- HTTP client library for Schwab API integration
- Environment variable management
- Cross-platform sound notification libraries
- Slack SDK for notification delivery

### Data Storage Design
**Single SQLite Database:**
- Market data storage for time-series information
- Alert rules and configuration management
- Alert logging and audit trail
- User settings and preferences

### Application Architecture
**Single FastAPI Application:**
- Main application server handling web API and WebSocket connections
- Background task workers for market data ingestion and alert processing
- Async queue-based message processing for sub-second latency
- Database initialization and connection management

### Deployment Approach
**Native Installation:**
- Single Python process deployment
- Virtual environment setup with dependencies
- Direct execution without containerization
- Local web interface access

### Frontend Design
**React Web Interface:**
- React application served by FastAPI
- WebSocket integration for real-time updates
- Dashboard with instrument tiles and alert displays
- Mobile-responsive layout for cross-device access

## Original Complex Architecture (Advanced Option)

### Backend Services

#### Complex Option: Full Microservices Stack
**Technologies:**
- **Framework:** FastAPI (Python 3.11+)
- **Message Broker:** Redis with Redis Streams
- **Time-Series DB:** InfluxDB 2.x
- **Alert Storage:** PostgreSQL 15+
- **Real-time Communication:** WebSockets (FastAPI native)

**Rationale:**
- FastAPI provides async/await support essential for sub-second latency
- Redis Streams offer lightweight, high-performance message queuing
- InfluxDB optimized for time-series data with built-in retention policies
- PostgreSQL handles complex alert queries and relationship data
- Single language ecosystem reduces complexity

**Alternative Option 1: Node.js Stack**
- **Framework:** Express.js with TypeScript
- **Message Broker:** Bull Queue with Redis
- **Databases:** Same as primary recommendation
- **Pros:** Excellent for real-time applications, large ecosystem
- **Cons:** Less suited for data-heavy computations, callback complexity

**Alternative Option 2: Go Stack**
- **Framework:** Gin or Fiber
- **Message Broker:** NATS or Redis
- **Databases:** Same as primary recommendation  
- **Pros:** Superior performance, excellent concurrency
- **Cons:** Steeper learning curve, smaller ecosystem for trading APIs

### Frontend Application
*(For Complex Architecture Option)*

#### Primary Recommendation: React + TypeScript SPA
**Technologies:**
- **Framework:** React 18 with TypeScript
- **State Management:** Zustand or React Query
- **UI Library:** Chakra UI or Mantine
- **Real-time:** Socket.IO client or native WebSockets
- **Build Tool:** Vite

**Rationale:**
- React provides excellent real-time UI updates
- TypeScript ensures type safety for financial data
- Lightweight state management for single-user app
- Modern UI libraries offer accessibility out-of-the-box

**Alternative Option 1: Vue.js Stack**
- **Framework:** Vue 3 with Composition API
- **State:** Pinia
- **Pros:** Easier learning curve, excellent performance
- **Cons:** Smaller ecosystem for financial/trading components

**Alternative Option 2: Svelte/SvelteKit**
- **Framework:** SvelteKit
- **Pros:** Minimal bundle size, excellent performance
- **Cons:** Smaller ecosystem, newer framework

### Data Storage Architecture

#### Time-Series Data: InfluxDB 2.x
**Data Design:**
- Time-series measurements for market data with instrument tagging
- High-precision timestamps for sub-second accuracy
- Configurable retention policies for different data frequencies

**Alternative Options:**
- **TimescaleDB:** PostgreSQL extension, better for complex queries
- **QuestDB:** High-performance, but newer ecosystem
- **Apache Druid:** Excellent for analytics, overkill for single-user

#### Application Data: PostgreSQL
**Data Design:**
- Core entities for instruments, alert rules, and logging
- Relational structure for rule management and audit trails
- Settings storage for user configuration

### Message Queuing & Event Processing

#### Primary Recommendation: Redis with Redis Streams
**Queue Design:**
- `market-data-stream`: Real-time tick data
- `alert-evaluation-queue`: Rule evaluation tasks
- `notification-queue`: Alert delivery tasks

**Benefits:**
- Sub-millisecond latency
- Built-in persistence
- Simple deployment (single Redis instance)
- Excellent Python integration

**Alternative Options:**
- **Apache Kafka:** Better for high-throughput, complex for single-user
- **RabbitMQ:** More features, higher latency overhead
- **NATS:** Lightweight, less persistence guarantees

### Security & Credential Management

#### Google Cloud Secret Manager Integration
**Implementation Approach:**
- Service account authentication for secure access
- Manual and optional automatic credential rotation capabilities
- Fallback strategies for connectivity issues

**Local Fallback Strategy:**
- OS Keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- Encrypted environment file with migration prompt

## Deployment Architecture

### Self-Hosted LAB Environment
**Containerization Approach:**
- Docker Compose orchestration for complex architecture
- Service dependencies and networking configuration
- Container images for API, UI, and database services

**System Requirements:**
- CPU: 4+ cores (data ingestion + alert processing)
- RAM: 8GB+ (time-series data caching)
- Storage: 100GB+ SSD (historical data retention)
- Network: Stable broadband with <100ms latency to exchanges

**Alternative Deployment Options:**
1. **Native Installation:** Direct system installation without containers
2. **Kubernetes:** Overkill for single-user but prepares for SaaS migration
3. **Cloud VM:** GCP/AWS instance for better connectivity

## Performance Architecture

### Sub-Second Latency Requirements
**Data Pipeline Optimization:**
1. **Ingestion:** WebSocket connections with connection pooling
2. **Processing:** In-memory rule evaluation with Redis caching  
3. **Storage:** Async writes with batching for time-series data
4. **Alerting:** Parallel notification delivery

**Performance Monitoring:**
- Tick-to-alert latency tracking with sub-second targets
- Alert evaluation frequency monitoring
- WebSocket connection stability metrics
- Memory usage pattern analysis

### Scaling Considerations for Future SaaS
**Stateless Service Design:**
- JWT authentication preparation
- Database connection pooling
- Horizontal pod autoscaling readiness
- Multi-tenant data isolation patterns

## Integration Architecture

### Schwab API Integration
**Connection Strategy:**
- WebSocket streaming for real-time data
- REST API for historical data backfill
- OAuth 2.0 with refresh token management
- Rate limiting with exponential backoff

**Data Normalization:**
- Unified market data format across all instruments
- Standardized timestamp handling for sub-second precision
- Consistent data types for financial calculations
- Optional fields for bid/ask and market internals

### Slack Integration
**Implementation Approach:**
- OAuth 2.0 app registration
- Slack Web API for message delivery
- Bot token for channel posting
- User token for DM capability

### Sound Notification System
**Cross-Platform Solution:**
- Platform-specific audio library integration
- Support for Windows, macOS, and Linux environments
- Multiple audio library options for compatibility

## Data Flow Architecture

### Real-Time Data Pipeline
```
Schwab API → WebSocket Client → Data Normalizer → Redis Stream → 
Alert Engine → Rule Evaluator → Notification Router → 
[In-App, Sound, Slack] + Alert Logger → PostgreSQL
```

### Historical Data Pipeline
```
Schwab API → REST Client → Data Validator → InfluxDB Writer →
Background Aggregation → Retention Policy Enforcement
```

## Error Handling & Resilience

### Circuit Breaker Patterns
**API Connectivity Resilience:**
- Automatic failure detection and recovery mechanisms
- Configurable failure thresholds and recovery timeouts
- Fallback strategies for API connectivity issues

### Graceful Degradation Strategy
1. **API Rate Limits:** Reduce polling frequency, queue requests
2. **Connectivity Loss:** Buffer events, auto-reconnect, degraded UI state
3. **Alert Delivery Failures:** Retry with exponential backoff, fallback channels
4. **Storage Issues:** In-memory caching with periodic flush attempts

## Security Architecture


### Credential Rotation Strategy
**Manual Rotation (Release 1):**
- User-initiated credential rotation interface
- Health check validation for new credentials
- Fallback handling for rotation failures

**Future Auto-Rotation:**
- Configurable rotation intervals
- Automated credential testing and validation
- Zero-downtime rotation implementation

## Monitoring & Observability

### Application Metrics
**Business Metrics:**
- Alert generation frequency and effectiveness
- Alert response times and acknowledgment patterns
- Data ingestion reliability and gap detection
- User engagement and interaction patterns

**Technical Metrics:**
- API response times and availability
- System resource utilization monitoring
- Database performance and query optimization
- Real-time connection stability and health

### Logging Strategy
**Structured Logging Approach:**
- JSON-formatted logs for machine readability
- Consistent timestamp and component identification
- Event-based logging for alert generation and system events
- Latency and performance metric tracking

## Development & Testing Strategy

### Testing Architecture
**Unit Testing:**
- Alert rule evaluation logic validation
- Data normalization and transformation testing
- API client error handling verification

**Integration Testing:**
- Mock API response handling
- Database operation validation
- Multi-channel notification delivery testing

**Performance Testing:**
- Load testing with simulated market data
- Latency benchmarking and optimization
- Memory usage and leak detection

### CI/CD Pipeline Preparation
**Automated Quality Assurance:**
- Code quality tools and formatting standards
- Security vulnerability scanning
- Automated test suite execution
- Container image building and deployment processes

## Migration & Upgrade Strategy

### Data Migration Paths
1. **Configuration Export/Import:** JSON-based rule and settings backup
2. **Historical Data Migration:** InfluxDB backup/restore procedures
3. **Database Versioning:** Alembic migrations for PostgreSQL schema changes

### Future SaaS Preparation
- Multi-tenancy database design
- User authentication framework
- API rate limiting per tenant
- Billing/subscription hooks


## Additional Considerations

### Mobile Responsiveness
**Implementation Strategy:**
- Progressive Web App (PWA) capabilities for mobile access
- Touch-friendly alert acknowledgment interface
- Responsive breakpoints for dashboard tiles
- Offline notification queuing and sync

### Development Environment Setup
**Recommended Development Stack:**
- Python environment with virtual environment management
- Container orchestration tools for complex deployments
- Database administration tools for debugging and inspection
- Code quality automation with pre-commit hooks
- Hot reload capabilities for efficient development
- Mock API services for testing without live market data

### Configuration Management
**Environment-Based Configuration:**
- Separate development and production configurations
- Market data endpoint management for sandbox vs live trading
- Database connection and logging configuration
- Performance and rate limiting parameter tuning

### Backup & Recovery Strategy
**Data Protection Plan:**
1. **Configuration Backup:** Daily JSON exports of rules and settings
2. **Historical Data Backup:** Weekly InfluxDB snapshots to cloud storage
3. **Alert History Backup:** Daily PostgreSQL dumps
4. **Disaster Recovery:** Complete environment restoration in <1 hour

### Compliance & Audit Trail
**Regulatory Preparation:**
- Complete audit logging of all market data access
- Timestamped record of all alert rule changes
- Data retention compliance for financial records
- Export capabilities for regulatory reporting

## Phase Implementation Mapping

### Phase 1: Core MVP
**Architecture Components:**
- Basic FastAPI service with WebSocket support
- Redis message queuing setup
- InfluxDB time-series storage
- PostgreSQL alert logging
- React dashboard with real-time updates
- Schwab API integration (sandbox)

**Deliverables:**
- Working data ingestion pipeline
- Basic alert rule creation/editing
- In-app notifications
- Health monitoring dashboard

### Phase 2: Production Ready  
**Architecture Components:**
- Google Cloud Secret Manager integration
- Slack OAuth and notification delivery
- Sound notification system
- Production database optimization
- Error handling and circuit breakers
- Complete UI/UX implementation

**Deliverables:**
- Multi-channel alert delivery
- Production-ready security
- Complete rule management interface
- Performance optimization
- User documentation

## Final Recommendations

### For Release 1 MVP: Ultra-Light Architecture ⭐
**Recommended approach:** Single FastAPI process + SQLite + React frontend
- **Complexity:** Minimal (2-day setup vs 2-week complex architecture)
- **Maintenance:** Single file to manage
- **Performance:** Easily meets sub-second requirements
- **Cost:** Zero infrastructure costs
- **Scalability:** Handles single-user perfectly; migrate to complex architecture when needed

### When to Upgrade to Complex Architecture
Consider the complex microservices architecture when:
1. **Multi-user requirements** emerge (R2/R3 SaaS phase)
2. **Data volume** exceeds SQLite capabilities (>1M ticks/day)
3. **High availability** becomes critical (99.99% vs 99% uptime)
4. **Advanced analytics** require specialized time-series features

### Migration Path
**Progressive Architecture Evolution:**
- **Phase 1 (MVP):** Single process with SQLite to distributed services
- **Data Migration:** Export/import capabilities for database transitions
- **Service Extraction:** Modular design enables component separation
- **Phase 2 (SaaS):** Add enterprise features like orchestration and monitoring

## Key Architectural Decisions (Revised)
1. **Start simple, scale when needed** - avoid over-engineering
2. **SQLite + FastAPI** provides excellent single-user performance  
3. **Direct deployment** eliminates Docker complexity for MVP
4. **Modular code design** enables future service extraction
5. **Security-first approach** with environment-based credential management
6. **Progressive enhancement** from working MVP to enterprise-ready

### Success Metrics Alignment
**Technical Metrics (from BRD):**
- Sub-second alert latency: ✅ Event-driven architecture supports <500ms
- 99% uptime target: ✅ Circuit breakers and graceful degradation
- Data integrity: ✅ ACID compliance with PostgreSQL + InfluxDB durability
- Security compliance: ✅ GCSM encryption + TLS communications

**Business Metrics Preparation:**
- Alert effectiveness tracking via PostgreSQL analytics
- User engagement metrics through structured logging
- System reliability metrics via application monitoring
- Performance bottleneck identification through APM integration

### Next Steps
1. Set up development environment with recommended stack
2. Implement Schwab API integration proof-of-concept  
3. Build alert engine core with Redis messaging
4. Develop React UI for rule management
5. Integrate notification channels (Slack, sound)
6. Performance testing and optimization
7. Security hardening and GCSM integration
8. User acceptance testing with real market data

This architecture supports all BRD requirements while maintaining flexibility for future enhancements and scaling needs. The modular design enables incremental development and testing while ensuring all critical functionality is delivered in Release 1.