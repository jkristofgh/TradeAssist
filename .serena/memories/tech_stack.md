# Technology Stack: TradeAssist

## Recommended Architecture (Ultra-Light Single Process)

### Backend
- **Framework**: FastAPI with WebSocket support
- **Database**: SQLite with WAL mode (single file)
- **Message Queue**: In-memory Python asyncio.Queue
- **API Integration**: HTTP client for Schwab API
- **Notifications**: Native Python libraries for sound, Slack SDK

### Frontend
- **Framework**: React (served by FastAPI)
- **Real-time**: WebSocket integration
- **UI**: Mobile-responsive dashboard
- **State Management**: React hooks (minimal complexity for single-user)

### Security & Configuration
- **Credentials**: Google Cloud Secret Manager integration
- **Config**: Environment variable management
- **Encryption**: TLS for all external communications

### System Requirements
- CPU: 2+ cores
- RAM: 2GB
- Storage: 10GB
- No Docker needed (native Python deployment)

### Key Dependencies (Estimated)
- FastAPI
- SQLite (async support)
- WebSockets
- Slack SDK
- Google Cloud Secret Manager client
- Cross-platform sound libraries
- React build tools

## Alternative Complex Architecture
Available but not recommended for MVP - microservices with Redis, InfluxDB, PostgreSQL, Docker orchestration. Reserved for future SaaS scaling.