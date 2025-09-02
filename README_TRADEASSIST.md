# TradeAssist - Real-Time Trading Alerts System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A professional-grade, single-user trading alerts system with sub-second latency, real-time market data streaming, multi-channel notifications, and advanced analytics powered by machine learning.

## 🎯 Overview

TradeAssist is a comprehensive self-hosted trading platform that provides real-time market data streaming from Schwab API, advanced analytics, and intelligent alert generation. Built with enterprise-grade reliability and optimized for individual traders requiring professional-level market analysis tools.

### ⚡ Key Features

**🔄 Real-Time Market Data**
- Live streaming from Schwab API with sub-second latency
- 12 supported instruments: ES, NQ, YM, CL, GC, SPX, NDX, RUT, VIX, TICK, ADD, TRIN
- Circuit breaker protection for API reliability
- Automatic reconnection and failover

**📊 Advanced Analytics Engine**
- Machine learning-powered market predictions
- Technical indicators (RSI, MACD, Bollinger Bands, Moving Averages, ATR, Stochastic)
- Risk metrics and Value-at-Risk calculations
- Market microstructure analysis
- Anomaly detection and trend classification
- Volume profile analysis
- Stress testing and scenario analysis

**🔔 Multi-Channel Notifications**
- In-app real-time alerts
- Sound notifications (pygame-based)
- Slack integration
- Customizable alert rules and conditions

**📈 Historical Data Foundation**
- Complete OHLCV data retrieval and storage
- Efficient caching and query optimization
- Data validation and integrity checks
- Flexible data export (CSV/JSON)

**🎛️ Professional Dashboard**
- React-based responsive interface
- Real-time WebSocket updates
- Interactive charts and visualizations
- System health monitoring
- Alert history and management

**🏗️ Enterprise Architecture**
- FastAPI backend with async WebSocket support
- SQLite database with WAL mode (PostgreSQL ready)
- Google Cloud Secret Manager integration
- Comprehensive logging and monitoring
- Database performance optimization
- Production-ready deployment automation

### 🛠️ Tech Stack

**Backend**
- **Framework**: FastAPI 0.104+ with async support
- **Database**: SQLite with WAL mode, Alembic migrations
- **API Integration**: Schwab API via custom package
- **ML/Analytics**: scikit-learn, TensorFlow, TA-Lib, scipy, statsmodels
- **Security**: Google Cloud Secret Manager, cryptography
- **Monitoring**: structlog, psutil, performance metrics

**Frontend** 
- **Framework**: React 18+ with TypeScript
- **State Management**: TanStack React Query
- **Charts**: Chart.js with react-chartjs-2
- **UI Components**: Custom responsive components
- **Real-time**: WebSocket integration
- **Testing**: Jest, React Testing Library

**Infrastructure**
- **Deployment**: Single-process architecture
- **Monitoring**: Performance metrics, health checks
- **Security**: OAuth integration, secure credential management
- **Development**: Hot reload, comprehensive testing

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- Node.js 16+ and npm
- Schwab API credentials (from [Schwab Developer Portal](https://developer.schwab.com/))
- Google Cloud account (optional for secret management)

### 2. Installation & Setup

```bash
# Clone repository
git clone <repository-url>
cd TradeAssist

# Setup Python environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd src/frontend
npm install
cd ../..

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

### 3. Configuration

Create and edit `.env` file:

```env
# Application Settings
HOST=127.0.0.1
PORT=8000
DEBUG=true

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/trade_assist.db

# Schwab API (Required)
SCHWAB_CLIENT_ID=your_schwab_client_id_here
SCHWAB_CLIENT_SECRET=your_schwab_client_secret_here
SCHWAB_REDIRECT_URI=http://localhost:8080/callback

# Optional: Google Cloud Secret Manager
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Notifications (Optional)
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=#trading-alerts
SOUND_ALERTS_ENABLED=true
```

### 4. Database Setup

```bash
# Database is initialized automatically on first run
# For manual migrations:
alembic upgrade head
```

### 5. Start the Application

#### Option 1: Development Mode (Recommended)

```bash
# Terminal 1: Start backend
source .venv/bin/activate
.venv/bin/uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd src/frontend
npm run dev
```

#### Option 2: Quick Start Script

```bash
chmod +x start.sh
./start.sh
```

### 6. Access the Application

- **Frontend Dashboard**: http://localhost:3000 (development)
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **WebSocket**: ws://localhost:8000/ws/realtime

## 📖 Documentation

- **[User Guide](USER_GUIDE.md)** - Complete feature walkthrough
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- **[Configuration Reference](CONFIGURATION.md)** - Environment variables and settings
- **[Testing Guide](TESTING_WSL.md)** - Testing procedures and API validation
- **[Development Guidelines](CLAUDE.md)** - Coding standards and best practices

## 🏗️ Architecture Overview

```
TradeAssist/
├── src/backend/           # FastAPI backend
│   ├── api/              # REST API endpoints
│   ├── database/         # Database models and connections
│   ├── integrations/     # External API integrations (Schwab)
│   ├── models/           # Data models and schemas
│   ├── services/         # Business logic services
│   │   ├── analytics/    # ML and analytics engine
│   │   └── historical_data/ # Historical data management
│   └── websocket/        # Real-time WebSocket handlers
├── src/frontend/         # React frontend
│   ├── src/components/   # UI components
│   │   ├── Analytics/    # Analytics dashboard components
│   │   ├── Dashboard/    # Main dashboard components
│   │   ├── Health/       # System health components
│   │   └── common/       # Reusable UI components
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API client services
│   └── types/           # TypeScript definitions
├── tests/               # Test suites
├── alembic/            # Database migrations
└── data/               # Database and data files
```

## 🔌 API Endpoints

### Core Endpoints
- `GET /api/health` - System health status
- `GET /api/instruments` - Available trading instruments
- `GET /api/market-data/{instrument_id}` - Real-time market data
- `GET /api/alerts` - Alert history
- `POST /api/rules` - Create alert rules

### Analytics Endpoints
- `POST /api/analytics/market-analysis` - Market analysis
- `POST /api/analytics/technical-indicators` - Technical indicators
- `POST /api/analytics/price-prediction` - ML price predictions
- `POST /api/analytics/risk-metrics` - Risk analysis
- `POST /api/analytics/volume-profile` - Volume analysis

### Historical Data
- `GET /api/historical-data/query` - Query historical data
- `GET /api/historical-data/export` - Export data

## 🧪 Testing

```bash
# Run backend tests
source .venv/bin/activate
.venv/bin/python -m pytest tests/ -v

# Run frontend tests
cd src/frontend
npm test

# Run specific test categories
pytest tests/unit/ -v           # Unit tests
pytest tests/integration/ -v    # Integration tests
pytest tests/performance/ -v    # Performance tests

# Type checking
cd src/frontend
npm run typecheck
```

## 🚀 Deployment

### Development Deployment
Suitable for personal use and development:

```bash
# Start with hot reload
./start.sh
```

### Production Deployment
For production environments:

```bash
# Build frontend
cd src/frontend
npm run build
cd ../..

# Start production server
source .venv/bin/activate
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --workers 1
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment instructions.

## 🔒 Security Features

- **Secure Credential Management**: Google Cloud Secret Manager integration
- **API Security**: Rate limiting, request validation, error handling
- **Circuit Breakers**: Automatic failover and recovery
- **Data Validation**: Pydantic models for all data structures
- **Authentication**: OAuth integration for Schwab API

## 📊 Performance Metrics

- **Alert Latency**: <500ms from market data to notification
- **WebSocket Updates**: <50ms frontend rendering
- **API Response Time**: <100ms average
- **Database Queries**: Optimized with indexing and connection pooling
- **Memory Usage**: <100MB additional browser memory
- **Bundle Size**: <2MB initial load, <500KB per route

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: Check the comprehensive documentation in this repository
- **Schwab API**: Refer to [Schwab Developer Documentation](https://developer.schwab.com/docs)

## 🎯 Roadmap

**✅ Completed Phases**
- Phase 1: Core Infrastructure & Real-time Data
- Phase 2: Advanced Analytics & Machine Learning  
- Phase 3: Multi-Channel Notifications & Enterprise Features
- Phase 4: Production Monitoring & Advanced Analytics

**🔮 Future Enhancements**
- Multi-user support with user authentication
- Advanced portfolio management features
- Additional broker integrations
- Enhanced mobile responsive design
- Cloud deployment options

---

**⚡ Ready for professional trading with sub-second alerts and advanced analytics!**