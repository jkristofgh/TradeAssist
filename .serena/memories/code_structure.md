# Code Structure: TradeAssist

## Current Repository Structure
```
TradeAssist/
├── .claude/                     # Claude Code commands
├── PRP-FRAMEWORK/               # Complex PRP Framework templates and tools
├── PRP-PLANNING/                # Project planning documents
│   ├── PLANNING/               # BRD, Architecture, CLAUDE guidelines
│   └── PRPs/                   # Generated phase requirements (to be created)
├── src/                        # Source code (currently minimal)
│   ├── backend/               # Server-side implementation (.gitkeep only)
│   ├── frontend/              # Client-side implementation (.gitkeep only)  
│   ├── shared/                # Common utilities (.gitkeep only)
│   └── tests/                 # Test suites (.gitkeep only)
├── CLAUDE.md                   # Main project guidance
├── README.md                   # Framework documentation
└── LICENSE

## Planned Source Code Structure (From Architecture)
Based on the ultra-light single process architecture:

### Backend Structure (src/backend/)
```
src/backend/
├── main.py                    # FastAPI application entry point
├── api/                       # API routes and endpoints
├── services/                  # Business logic services
│   ├── data_ingestion.py     # Schwab API integration
│   ├── alert_engine.py       # Rule evaluation and alert generation
│   └── notification.py       # Multi-channel notifications
├── models/                    # Data models and database schemas
├── database/                  # Database management and SQLite setup
├── config/                    # Configuration management
└── utils/                     # Common utilities

### Frontend Structure (src/frontend/)
```
src/frontend/
├── public/                    # Static assets
├── src/                      # React application source
│   ├── components/           # Reusable UI components
│   ├── pages/               # Page-level components
│   ├── hooks/               # Custom React hooks for WebSocket
│   ├── services/            # API client and data services
│   └── utils/               # Frontend utilities
├── package.json             # Dependencies and scripts
└── webpack.config.js        # Build configuration

### Shared Structure (src/shared/)
```
src/shared/
├── types/                    # TypeScript/Python type definitions
├── constants/               # Shared constants
└── utils/                   # Cross-platform utilities

## Design Patterns
- Single responsibility principle for services
- Event-driven architecture with async/await
- Repository pattern for data access
- Factory pattern for notification channels
- Observer pattern for real-time updates