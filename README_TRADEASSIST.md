# TradeAssist - Real-Time Trading Alerts System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A professional-grade, single-user trading alerts system with sub-second latency, real-time market data streaming, and multi-channel notifications.

## 🎯 Overview

TradeAssist is a self-hosted trading alerts application that streams real-time market data from Schwab API and generates actionable alerts with enterprise-grade reliability. Built with an ultra-light single-process architecture optimized for individual traders.

### ⚡ Key Features
- **Sub-second Alert Latency** - Target <500ms from data to notification
- **Real-Time Market Data** - Live streaming from Schwab API
- **Multi-Channel Notifications** - In-app, sound, and Slack alerts
- **Advanced Analytics** - ML-powered market insights and predictions
- **Professional Dashboard** - React-based responsive interface
- **Enterprise Security** - Google Cloud Secret Manager integration
- **High Availability** - Circuit breakers and automated recovery

### 🏗️ Architecture
- **Backend**: FastAPI with async WebSocket support
- **Frontend**: React with TypeScript and real-time updates
- **Database**: SQLite with WAL mode (PostgreSQL ready)
- **Security**: Google Cloud Secret Manager for credentials
- **Deployment**: Single-process architecture for minimal complexity

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- Node.js 16+ and npm
- Google Cloud account
- Schwab API credentials

### 2. Installation & Setup
```bash
# Clone repository
git clone <repository-url>
cd TradeAssist

# Setup environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Install frontend dependencies
cd src/frontend && npm install && cd ../..

# Build frontend
cd src/frontend && npm run build && cd ../..
```

### 3. Run Application
```bash
# Quick start (recommended)
chmod +x start.sh
./start.sh

# Or manually start backend
python run.py

# Access dashboard at http://localhost:8000
```

## 📚 Documentation

### 📖 Essential Guides
- **[📋 DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment and setup guide
- **[👤 USER_GUIDE.md](USER_GUIDE.md)** - How to use all features and functionality
- **[⚙️ CONFIGURATION.md](CONFIGURATION.md)** - Comprehensive configuration reference

### 🔧 Developer Resources
- **[💻 CLAUDE.md](CLAUDE.md)** - Development guidelines and conventions
- **[🏗️ Architecture Overview](#architecture)** - System design and components
- **[🧪 Testing Guide](#testing)** - Unit, integration, and performance testing

## 🎛️ Core Functionality

### Alert System
- **Price Alerts** - Threshold-based price notifications
- **Technical Indicators** - RSI, MACD, Moving Averages, Bollinger Bands
- **Market Conditions** - Volatility, volume, and sentiment alerts
- **Risk Management** - Position limits and correlation warnings

### Market Data
- **Real-Time Streaming** - Sub-second market data updates
- **Instrument Support** - Futures, stocks, ETFs, options, indices
- **Historical Data** - Charts and analysis with technical indicators
- **Data Quality** - Automatic validation and error handling

### Analytics & ML
- **Predictive Models** - Price forecasting and volatility prediction
- **Risk Analysis** - VaR, correlation, and exposure calculations
- **Market Sentiment** - Fear/greed indicators and market breadth
- **Performance Tracking** - Alert effectiveness and system metrics

## 🔒 Security & Compliance

- **Credential Management** - Google Cloud Secret Manager integration
- **Data Encryption** - TLS/SSL for all external communications
- **Access Control** - Single-user authentication and session management
- **Audit Logging** - Comprehensive activity and error logging
- **Security Headers** - CORS, HSTS, and CSP protection

## 📊 Performance Specifications

- **Alert Latency**: <500ms target (data to notification)
- **Throughput**: 1000+ alerts per minute processing capacity
- **Uptime**: 99%+ availability during market hours
- **Memory**: <2GB RAM typical usage
- **Storage**: <10GB including historical data
- **Concurrent Users**: Single-user optimized (extensible)

## 🛠️ Technology Stack

### Backend
- **FastAPI** - High-performance async web framework
- **SQLAlchemy** - Database ORM with async support
- **SQLite/PostgreSQL** - Database with migration support
- **WebSockets** - Real-time bidirectional communication
- **Pydantic** - Data validation and settings management

### Frontend  
- **React 18** - Component-based UI framework with hooks
- **TypeScript** - Type-safe development
- **React Query** - Data fetching and caching
- **Chart.js** - Real-time charting and visualizations
- **React Router** - Client-side routing
- **React Toastify** - Toast notifications
- **WebSocket Client** - Real-time data integration
- **Responsive Design** - Mobile-friendly interface

### Infrastructure
- **uvicorn** - ASGI server for production deployment
- **Alembic** - Database migration management
- **pytest** - Comprehensive testing framework
- **Google Cloud** - Secret management and future scaling

## 🧪 Testing

```bash
# Run all tests
source venv_linux/bin/activate
python -m pytest src/tests/unit/ -v

# Run specific test categories
python -m pytest src/tests/unit/ -m "not slow" -v          # Fast tests only
python -m pytest src/tests/integration/ -v                 # Integration tests
python -m pytest src/tests/performance/ -v                 # Performance tests

# Generate coverage report
python -m pytest src/tests/unit/ --cov=src --cov-report=html
```

## 🔧 Development

### Project Structure
```
TradeAssist/
├── src/
│   ├── backend/           # FastAPI application
│   ├── frontend/          # React application
│   ├── shared/            # Common utilities
│   └── tests/             # Test suites
├── DEPLOYMENT.md          # Deployment guide
├── USER_GUIDE.md          # Feature documentation
├── CONFIGURATION.md       # Configuration reference
└── requirements.txt       # Python dependencies
```

### Development Commands
```bash
# Backend development
source .venv/bin/activate
python run.py

# Frontend development  
cd src/frontend
npm run dev

# Run tests
source .venv/bin/activate
python -m pytest src/tests/unit/ -v

# Frontend code quality
cd src/frontend
npm run lint              # Lint TypeScript
npm run lint:fix          # Fix lint issues
npm run format            # Format with Prettier
npm run typecheck         # TypeScript checking

# Backend code quality (if configured)
black src/                # Format code
flake8 src/               # Lint code  
mypy src/                 # Type checking
```

## 📈 Roadmap

### Phase 4 (Future)
- [ ] Portfolio management integration
- [ ] Advanced order management
- [ ] Multi-broker support
- [ ] Mobile applications

### Phase 5 (Future)
- [ ] Multi-user support
- [ ] Cloud deployment options
- [ ] Advanced backtesting
- [ ] Strategy automation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the development guidelines in `CLAUDE.md`
4. Ensure tests pass: `python -m pytest src/tests/unit/ -v`
5. Submit a pull request

## 🆘 Support & Troubleshooting

### Common Issues
- **Database Errors**: Check `DEPLOYMENT.md` for database setup
- **API Authentication**: Verify Schwab credentials in `CONFIGURATION.md`
- **WebSocket Issues**: Review firewall and proxy settings
- **Performance**: See optimization tips in `USER_GUIDE.md`

### Getting Help
1. Check the **[USER_GUIDE.md](USER_GUIDE.md)** for usage questions
2. Review **[CONFIGURATION.md](CONFIGURATION.md)** for setup issues
3. Examine logs in `logs/tradeassist.log`
4. Use the health endpoint: `http://localhost:8000/api/health`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with the Complex PRP Framework for systematic development
- Powered by Schwab API for real-time market data
- Designed for individual traders requiring professional-grade tools

---

## ✨ Ready to Start Trading?

1. **Deploy** using the [DEPLOYMENT.md](DEPLOYMENT.md) guide
2. **Configure** your settings with [CONFIGURATION.md](CONFIGURATION.md)
3. **Learn** the features in [USER_GUIDE.md](USER_GUIDE.md)
4. **Start** receiving real-time trading alerts!

**Transform your trading with professional-grade alerts and sub-second market insights!**