# Trading Insights Application — Release 1 BRD (Compressed)

## TL;DR
Single-user, self-hosted web app connecting to Schwab API for real-time futures/indices streaming, historical storage, and sub-second actionable alerts via in-app, sound, and Slack channels. Target: day trader with 99% uptime during US market hours and future SaaS expansion path.

## Goals
### Business Goals
- Ship reliable MVP proving end-to-end data→alert→review workflow
- Establish technical foundations for future strategy detection (R1.5) and SaaS (R2/R3)
- Demonstrate sub-second alerting with 99% uptime during market hours
- Validate repeatable workflow reducing missed trades with complete audit trail

### User Goals
- Real-time status of watched instruments (futures, indices, internals)
- Configure reliable alert rules with instant multi-channel delivery
- Review complete alert logs to refine setups
- Minimal setup: single-user, LAB-hosted, lightweight UI

### Non-Goals (R1)
- No order execution, advanced charting, or multi-user support
- No strategy detection/backtesting beyond basic triggers
- No options data/alerts until R2+ (SPX R2; equities R3)

## User Stories
**Single-User Trader:**
- Connect Schwab API keys for streaming/historical data
- Create watchlist: ES, NQ, YM, CL, GC; SPX, NDX, RUT; VIX, TICK, ADD, TRIN
- Define threshold/level-based rules (price/volume/internals)
- Receive alerts via in-app, sound, Slack channels
- Access live alert feed and searchable historical logs
- Monitor basic health indicators (ingestion status, last tick time)

## Functional Requirements

### Data Integration (P0)
- Schwab brokerage API: streaming + historical data
- Instruments: Futures (ES, NQ, YM, CL, GC), Indices (SPX, NDX, RUT), Indicators (VIX, TICK, ADD, TRIN)
- Historical storage: daily + intraday, configurable retention

### Alerts (P0)
- Rule types: static thresholds, crossovers, rate-of-change by instrument/timeframe
- Delivery: in-app notifications, sound, Slack (channel/DM)
- Logging: persist alert context (rule, timestamp, instrument, value, delivery status)

### User Interface (P0)
- Minimal dashboard: real-time watchlist, recent alerts, health status
- Rule management: create/edit/enable/disable with per-instrument targeting
- Settings: API credentials, Slack connection, retention, sound toggle
- Secrets wallet: Google Cloud Secret Manager integration with connection status
- Optional secret rotation: toggle enable/disable, manual "Rotate now" (default OFF)

## User Experience

### Setup Flow
- Local web UI guided setup: Schwab keys, Slack connect, starter instruments
- Test connections, show ingestion health, pre-create sample rules

### Core Workflows
1. **Monitor**: Live instrument tiles, last tick/price, internals summary, stall warnings
2. **Create Rules**: From instrument detail, validate input, show firing examples
3. **Receive Alerts**: Multi-channel delivery with instrument/condition/values/timestamp
4. **Review**: Alerts tab with time/instrument/rule filters, CSV export

### Edge Cases
- API rate-limit: degrade gracefully, reduce frequency, queue checks, warn user
- Connectivity loss: buffer events, auto-reconnect, degraded state, recovery notice
- Duplicate suppression, delivery retries, channel status tracking

## Technical Requirements

### Components
- Data ingestion service, alert evaluation engine, time-series + alert log store
- Web UI, notification layers, credentials vault

### Integration Points
- **Schwab API**: Real-time streaming + historical data access
- **Slack**: OAuth + Web API for channel/DM delivery
- **Google Cloud Secret Manager**: Credential storage with optional rotation
- **Local sound**: Cross-platform notification system

### Data & Security
- **Credentials**: Store Schwab API keys + Slack tokens exclusively in GCSM
- **Authentication**: Service account key (local, least privilege)
- **Rotation**: Optional toggle (default OFF), manual "Rotate now" available
- **Storage**: Encrypt API keys at rest, localhost only, no PII collection
- **Fallback**: OS keyring or encrypted .env with GCSM migration prompt

### Performance
- **Latency**: Sub-second evaluation for typical watchlist sizes
- **Uptime**: 99% target during US market hours
- **Architecture**: Single-user now, stateless/queue-ready for horizontal scaling

## Success Metrics

### Technical Targets
- Signal-to-alert latency: <1 second
- System uptime: 99% during market hours (7am-6pm ET)
- Alert delivery success rate: >99.5%
- Data ingestion gaps: <0.1% of market hours

### Key Events Tracking
- app_start, api_connect_success/fail, tick_ingested, rule_created/fired
- alert_sent_{app|sound|slack}, alert_acknowledged, ingestion_gap_detected
- recovery_complete, export_performed

## Architecture Requirements

### Recommended: Ultra-Light Single Process
- **Core**: Single FastAPI app (web API + WebSocket + background tasks)
- **Storage**: SQLite with WAL mode (time-series + application data)
- **Queuing**: In-memory Python queues (asyncio.Queue)
- **Frontend**: React for UI complexity
- **Benefits**: Zero infrastructure, simple setup, meets latency requirements

### System Requirements
- CPU: 2+ cores, RAM: 2GB, Storage: 10GB
- No Docker required, direct Python execution

## Phase Breakdown

### Phase 1: Core Data and Alert MVP
- Schwab data ingestion (real-time + historical)
- Alert engine with sub-second latency
- In-app/sound/Slack notification delivery
- Rule creation/edit/delete UI
- Basic health/status indicators
- Alert logging and review interface

### Phase 2: Security and Production Readiness
- Google Cloud Secret Manager integration with rotation controls
- Data retention/cleanup automation
- Resilience features (buffering, reconnect, throttling)
- API rate limiting and error handling
- Production deployment optimization

## Dependencies

### External Requirements
- Schwab Open API availability and stable terms
- Slack API/OAuth app registration capabilities
- Stable internet connectivity from LAB device
- Google Cloud project with Secret Manager enabled
- Service account with Secret Manager Secret Accessor role

### Technical Assumptions
- LAB environment supports outbound HTTPS to Google Cloud APIs
- Single-user deployment sufficient for R1 scope
- SQLite performance adequate for expected data volumes
- Python ecosystem stability for real-time financial applications

## Future Roadmap
- **R1.5**: Strategy detection attached to alerts
- **R2**: SPX options alerts/data, multi-user SaaS preparation
- **R3**: Equity options, full SaaS multi-tenancy

---
*Compressed from 241 lines to 120 lines (50% reduction) while preserving all planning-critical information.*