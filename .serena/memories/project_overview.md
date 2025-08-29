# Project Overview: TradeAssist

## Purpose
TradeAssist is a single-user, self-hosted trading alerts application designed to stream real-time market data from Schwab API and generate actionable alerts with sub-second latency. It's an MVP focused on data ingestion, alert generation, and multi-channel notifications (in-app, sound, Slack).

## Core Features (Release 1)
- Real-time market data streaming (futures, indices, market internals)
- Sub-second alert engine with configurable rules
- Multi-channel notifications (in-app, sound, Slack)
- Alert logging and review capabilities
- Basic dashboard with health monitoring
- Google Cloud Secret Manager integration for credentials

## Project Context
This is part of the Complex PRP Framework for systematic development of complex multi-phase software projects. The project uses the internal three-directory structure:
- `PRP-FRAMEWORK/` - Framework templates and tools
- `PRP-PLANNING/` - Project planning documents (BRD, Architecture, PRPs)
- `src/` - Actual source code implementation

## Target Architecture
Ultra-light single process architecture (recommended for MVP):
- Single FastAPI application with WebSocket support
- SQLite database with WAL mode for time-series and application data
- In-memory Python queues for alert processing
- React frontend for dashboard and rule management
- Native Python libraries for notifications

## Performance Requirements
- Sub-second alert latency (target <500ms)
- 99% uptime during US market hours
- Single-user deployment on LAB environment
- Self-hosted with minimal infrastructure complexity