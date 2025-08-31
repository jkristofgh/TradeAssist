# TradeAssist Configuration Guide

## 🔧 Complete Configuration Reference

This guide covers all configuration options for TradeAssist, from basic setup to advanced performance tuning.

---

## 📁 Configuration Files

### Primary Configuration Files
- **`.env`** - Environment variables and secrets
- **`alembic.ini`** - Database migration settings
- **`src/backend/config.py`** - Application configuration class
- **`src/frontend/package.json`** - Frontend dependencies and scripts
- **`run.py`** - Main application runner
- **`start.sh`** - Quick start script

### Secondary Configuration Files
- **`conftest.py`** - Pytest configuration
- **`pytest.ini`** - Testing configuration
- **`requirements.txt`** - Python dependencies
- **`.gitignore`** - Git ignore rules
- **`src/frontend/tsconfig.json`** - TypeScript configuration

---

## 🌍 Environment Variables (.env)

### Core Application Settings

```env
# Application Environment
HOST=127.0.0.1                # Server host address
PORT=8000                      # Server port
DEBUG=true                     # Enable debug mode (development only)
LOG_LEVEL=INFO                 # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Database Configuration

```env
# SQLite Configuration (Current Default)
DATABASE_URL=sqlite+aiosqlite:///./data/trade_assist.db
MARKET_DATA_RETENTION_DAYS=30  # How long to keep market data

# Advanced SQLite Settings
# DATABASE_ECHO=false            # Log all SQL queries
# DATABASE_POOL_SIZE=20          # Connection pool size
# DATABASE_MAX_OVERFLOW=30       # Max overflow connections

# PostgreSQL Configuration (Future)
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/tradeassist
# DATABASE_SSL_MODE=prefer
```

### Schwab API Configuration

```env
# Schwab API Credentials (Required for real-time data)
SCHWAB_CLIENT_ID=your_schwab_client_id_here
SCHWAB_CLIENT_SECRET=your_schwab_client_secret_here
SCHWAB_REDIRECT_URI=https://127.0.0.1

# API Rate Limiting
# SCHWAB_REQUESTS_PER_SECOND=10  # API rate limit
# SCHWAB_BURST_LIMIT=50          # Burst request limit
# SCHWAB_TIMEOUT_SECONDS=30      # Request timeout
# SCHWAB_RETRY_ATTEMPTS=3        # Retry failed requests
```

### Historical Data Service Configuration

```env
# Historical Data Cache Settings
HISTORICAL_DATA_CACHE_TTL=300              # Cache TTL in seconds (5 minutes)
HISTORICAL_DATA_MAX_SYMBOLS_PER_REQUEST=50  # Max symbols per API request
HISTORICAL_DATA_MAX_RECORDS_DEFAULT=10000   # Default max records per symbol

# API Rate Limiting for Historical Data
HISTORICAL_DATA_RATE_LIMIT_REQUESTS=100     # Requests per minute limit
HISTORICAL_DATA_BATCH_SIZE=25               # Batch size for API requests
HISTORICAL_DATA_RETRY_ATTEMPTS=3            # Retry attempts for failed requests
HISTORICAL_DATA_RETRY_DELAY=1               # Delay between retries (seconds)

# Database Performance Settings
DATABASE_QUERY_TIMEOUT=30                   # Query timeout in seconds
DATABASE_CONNECTION_POOL_SIZE=10            # Connection pool size
DATABASE_CONNECTION_OVERFLOW=20             # Pool overflow connections

# Cache Backend Configuration
CACHE_BACKEND=memory                        # Cache type (memory, redis)
CACHE_REDIS_URL=redis://localhost:6379/0   # Redis URL (if using Redis)
CACHE_DEFAULT_TTL=300                       # Default cache TTL in seconds
```

### Google Cloud Secret Manager

```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
SECRET_MANAGER_ENABLED=true
SECRET_CACHE_TTL=3600          # Cache secrets for 1 hour

# Secret Names in Secret Manager
SECRET_SCHWAB_APP_KEY=schwab-app-key
SECRET_SCHWAB_APP_SECRET=schwab-app-secret
SECRET_SLACK_BOT_TOKEN=slack-bot-token
```

### Performance Configuration

```env
# WebSocket Settings
MAX_WEBSOCKET_CONNECTIONS=10   # Maximum concurrent connections
ALERT_EVALUATION_INTERVAL_MS=100 # Alert evaluation frequency
DATA_INGESTION_BATCH_SIZE=100  # Batch size for data processing

# Performance Targets
# ALERT_LATENCY_TARGET_MS=500    # Target alert processing latency
# MAX_CONCURRENT_ALERTS=50       # Maximum alerts processed concurrently
# WEBSOCKET_PING_INTERVAL=30     # Ping interval in seconds
# WEBSOCKET_PING_TIMEOUT=10      # Ping timeout in seconds
```

### Notification Configuration

```env
# Slack Notifications
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_CHANNEL=#trading-alerts

# Sound Alerts
SOUND_ALERTS_ENABLED=true

# Advanced Notification Settings (Optional)
# WEBAPP_NOTIFICATIONS=true
# NOTIFICATION_AUTO_DISMISS=10   # Auto-dismiss notifications after N seconds
# MAX_VISIBLE_NOTIFICATIONS=5   # Maximum visible notifications
# NOTIFICATION_RETENTION_DAYS=30 # Keep notifications for N days
# SOUND_DEFAULT_VOLUME=0.8      # Volume (0.0 to 1.0)
```

### Target Instruments

```env
# Instrument Configuration (comma-separated lists)
TARGET_FUTURES=ES,NQ,YM,CL,GC  # Futures contracts to monitor
TARGET_INDICES=SPX,NDX,RUT     # Index symbols to track
TARGET_INTERNALS=VIX,TICK,ADD,TRIN # Market internals
```

### Performance Configuration

```env
# Server Performance
UVICORN_WORKERS=1             # Number of worker processes
UVICORN_HOST=0.0.0.0         # Server host
UVICORN_PORT=8000            # Server port
UVICORN_LOG_LEVEL=info       # Logging level
UVICORN_ACCESS_LOG=true      # Enable access logging
UVICORN_RELOAD=false         # Auto-reload on code changes (dev only)

# Memory Management
MAX_MEMORY_USAGE_MB=2048     # Maximum memory usage
GARBAGE_COLLECTION_THRESHOLD=1000  # GC threshold
DATA_RETENTION_DAYS=90       # Retain data for N days
```

### Security Configuration

```env
# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# SSL/TLS Configuration
SSL_ENABLED=true
SSL_CERT_PATH=/path/to/certificate.pem
SSL_KEY_PATH=/path/to/private-key.pem
SSL_CA_CERTS=/path/to/ca-certificates.pem

# Security Headers
SECURITY_HEADERS_ENABLED=true
HSTS_MAX_AGE=31536000        # HSTS max age
CONTENT_SECURITY_POLICY=default-src 'self'
```

### Production Logging Configuration

```env
# Core Logging Settings
LOG_LEVEL=INFO                              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_TO_FILE=true                           # Enable file logging (false for development)
LOG_FILE_PATH=./logs/tradeassist.log       # Log file path
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s  # Log format

# Log File Rotation Settings
LOG_FILE_MAX_SIZE=10485760                 # Max file size in bytes (10MB)
LOG_FILE_BACKUP_COUNT=5                    # Number of backup files to keep

# Production Logging Features
# - Structured logging with JSON format in production
# - File rotation with configurable size and retention
# - Performance metrics logging for historical data operations
# - Audit logging for data access and API usage
# - Error tracking with full context for troubleshooting

# Historical Data Logging (Automatic)
# - Request/response logging with performance metrics
# - Cache hit/miss tracking for optimization
# - Error logging with full context for debugging
# - Audit trail for data access and queries
```

---

## ⚙️ Advanced Configuration

### Database Performance Tuning

#### SQLite Configuration
```env
# SQLite WAL Mode Settings
SQLITE_WAL_MODE=true
SQLITE_SYNCHRONOUS=NORMAL     # NORMAL, FULL, OFF
SQLITE_CACHE_SIZE=10000       # Cache size in KB
SQLITE_TEMP_STORE=memory      # memory, file
SQLITE_JOURNAL_MODE=WAL       # DELETE, WAL, MEMORY
SQLITE_BUSY_TIMEOUT=30000     # Busy timeout in milliseconds
```

#### Database Connection Pool
```python
# src/backend/config.py
class DatabaseConfig:
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
```

### Market Data Processing

```env
# Data Processing Configuration
MARKET_DATA_BUFFER_SIZE=10000 # Buffer size for market data
MARKET_DATA_BATCH_SIZE=1000   # Batch processing size
MARKET_DATA_COMPRESSION=gzip  # Compression for stored data
MARKET_DATA_SAMPLING_RATE=100 # Sample rate in milliseconds

# Real-time Data Settings
REALTIME_DATA_ENABLED=true
REALTIME_THROTTLE_MS=50      # Minimum time between updates
REALTIME_MAX_UPDATES_PER_SEC=20
REALTIME_PRIORITY_INSTRUMENTS=ES,NQ,YM,RTY  # High priority instruments
```

### Circuit Breaker Configuration

```env
# Circuit Breaker Settings
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5    # Failures before opening
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60    # Recovery timeout in seconds
CIRCUIT_BREAKER_EXPECTED_EXCEPTION=HTTPException

# Service-specific Circuit Breakers
SCHWAB_API_CIRCUIT_BREAKER=true
DATABASE_CIRCUIT_BREAKER=true
NOTIFICATION_CIRCUIT_BREAKER=true
```

### Machine Learning Configuration

```env
# ML Model Settings
ML_MODELS_ENABLED=true
ML_MODEL_UPDATE_INTERVAL=3600 # Update models every hour
ML_PREDICTION_CACHE_TTL=300   # Cache predictions for 5 minutes
ML_FEATURE_WINDOW_SIZE=100    # Number of data points for features
ML_CONFIDENCE_THRESHOLD=0.7   # Minimum confidence for predictions

# Specific Model Settings
PRICE_PREDICTION_MODEL=lstm
VOLATILITY_MODEL=garch
SENTIMENT_MODEL=transformer
```

---

## 📊 Monitoring Configuration

### Metrics and Observability

```env
# Metrics Configuration
METRICS_ENABLED=true
METRICS_PORT=9090
METRICS_PATH=/metrics
PROMETHEUS_ENABLED=false     # Enable Prometheus integration
STATSD_ENABLED=false        # Enable StatsD integration
STATSD_HOST=localhost
STATSD_PORT=8125

# Custom Metrics
ALERT_LATENCY_HISTOGRAM=true
API_RESPONSE_TIME_HISTOGRAM=true
WEBSOCKET_CONNECTION_GAUGE=true
DATABASE_QUERY_DURATION=true
```

### Health Check Configuration

```env
# Health Check Settings
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_PATH=/health
HEALTH_CHECK_INTERVAL=30     # Health check interval in seconds
HEALTH_CHECK_TIMEOUT=10      # Timeout for health checks

# Component Health Checks
CHECK_DATABASE_HEALTH=true
CHECK_SCHWAB_API_HEALTH=true
CHECK_WEBSOCKET_HEALTH=true
CHECK_DISK_SPACE=true
CHECK_MEMORY_USAGE=true
```

---

## 🎛️ Frontend Configuration

### React Application Settings

#### package.json (Frontend)
```json
{
  "name": "tradeassist-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "lint": "eslint src --ext .ts,.tsx",
    "lint:fix": "eslint src --ext .ts,.tsx --fix",
    "format": "prettier --write src/**/*.{ts,tsx,json,css,md}",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@tanstack/react-query": "^4.24.0",
    "chart.js": "^4.2.1",
    "react": "^18.2.0",
    "react-chartjs-2": "^5.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "react-scripts": "5.0.1",
    "react-toastify": "^11.0.5",
    "web-vitals": "^3.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.28",
    "@types/react-dom": "^18.0.11",
    "typescript": "^4.9.5",
    "prettier": "^2.8.4"
  }
}
```

#### Environment Variables for Frontend
```env
# Frontend Configuration (Set via build process)
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WEBSOCKET_URL=ws://localhost:8000/ws
REACT_APP_ENVIRONMENT=development
REACT_APP_VERSION=0.1.0

# Feature Flags (Optional)
# REACT_APP_ENABLE_DEBUG=false
# REACT_APP_ENABLE_ANALYTICS=true
# REACT_APP_ENABLE_ML_PREDICTIONS=true
# REACT_APP_ENABLE_SOUND_ALERTS=true
```

#### TypeScript Configuration (tsconfig.json)
```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
```

---

## 🧪 Testing Configuration

### Pytest Configuration (pytest.ini)

```ini
[tool:pytest]
testpaths = src/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### Test Environment Variables

```env
# Test Configuration
TEST_DATABASE_URL=sqlite+aiosqlite:///:memory:
TEST_SCHWAB_API_MOCK=true
TEST_NOTIFICATION_MOCK=true
TEST_WEBSOCKET_MOCK=true
TEST_TIMEOUT=30
TEST_LOG_LEVEL=DEBUG
```

---

## 🔄 Development vs Production Configurations

### Development Settings (.env.development)

```env
# Development Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
UVICORN_RELOAD=true
CORS_ORIGINS=http://localhost:3000
DATABASE_ECHO=true
SCHWAB_SANDBOX_MODE=true

# Development-specific
HOT_RELOAD_ENABLED=true
DEV_TOOLS_ENABLED=true
MOCK_MARKET_DATA=true
DISABLE_RATE_LIMITING=true
```

### Production Settings (.env.production)

```env
# Production Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
UVICORN_RELOAD=false
SSL_ENABLED=true
SECURITY_HEADERS_ENABLED=true
SCHWAB_SANDBOX_MODE=false

# Production-specific
RATE_LIMITING_ENABLED=true
SECURITY_MONITORING=true
PERFORMANCE_MONITORING=true
BACKUP_ENABLED=true
```

### Staging Settings (.env.staging)

```env
# Staging Environment
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=DEBUG
SCHWAB_SANDBOX_MODE=true
MOCK_NOTIFICATIONS=true

# Staging-specific
LOAD_TESTING_ENABLED=true
PERFORMANCE_PROFILING=true
```

---

## 🔧 Configuration Management

### Loading Configuration

#### Python Configuration Class
```python
# src/backend/config.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    app_name: str = "TradeAssist"
    app_version: str = "1.0.0"
    environment: str = "production"
    debug: bool = False
    secret_key: str

    # Database
    database_url: str = "sqlite+aiosqlite:///./tradeassist.db"
    database_echo: bool = False

    # Schwab API
    schwab_app_key: str
    schwab_app_secret: str
    schwab_callback_url: str = "https://localhost:8000/callback"

    # Alert Engine
    alert_latency_target_ms: int = 500
    max_concurrent_alerts: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Configuration Validation

```python
# Configuration validation
def validate_config():
    """Validate critical configuration settings"""
    errors = []

    if not settings.secret_key:
        errors.append("SECRET_KEY is required")

    if len(settings.secret_key) < 32:
        errors.append("SECRET_KEY must be at least 32 characters")

    if not settings.schwab_app_key:
        errors.append("SCHWAB_APP_KEY is required")

    if settings.alert_latency_target_ms < 100:
        errors.append("ALERT_LATENCY_TARGET_MS too low (minimum 100ms)")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
```

### Dynamic Configuration Updates

```python
# Runtime configuration updates
class DynamicConfig:
    def __init__(self):
        self.config_cache = {}
        self.last_reload = 0

    def reload_config(self):
        """Reload configuration from environment"""
        # Reload non-critical settings without restart
        pass

    def update_alert_settings(self, new_settings: dict):
        """Update alert engine settings"""
        # Validate and apply new alert settings
        pass
```

---

## 📋 Configuration Checklist

### Pre-Deployment Checklist

- [ ] **Environment variables** set correctly for target environment
- [ ] **Database connection** string configured
- [ ] **Schwab API credentials** configured and tested
- [ ] **Google Cloud Secret Manager** setup and accessible
- [ ] **SSL certificates** installed and configured (production)
- [ ] **CORS origins** set correctly for frontend access
- [ ] **Log levels** appropriate for environment
- [ ] **Alert thresholds** set correctly
- [ ] **Notification channels** configured and tested
- [ ] **Performance settings** tuned for expected load
- [ ] **Security settings** enabled for production
- [ ] **Backup configuration** verified
- [ ] **Monitoring** enabled and functional

### Post-Deployment Verification

- [ ] **Health checks** passing
- [ ] **Database migrations** applied successfully
- [ ] **WebSocket connections** working
- [ ] **Real-time data** flowing correctly
- [ ] **Alert processing** within latency targets
- [ ] **Notifications** delivering successfully
- [ ] **Performance metrics** within acceptable ranges
- [ ] **Error rates** at acceptable levels
- [ ] **Security scans** completed
- [ ] **Backup processes** running correctly

---

## 🆘 Configuration Troubleshooting

### Common Configuration Issues

#### Database Connection Problems
```bash
# Check database URL format
echo $DATABASE_URL

# Test database connectivity
python -c "from src.backend.database.connection import test_connection; test_connection()"
```

#### API Authentication Issues
```bash
# Verify Schwab API credentials
python -c "from src.backend.integrations.schwab_client import test_auth; test_auth()"

# Check Google Cloud credentials
gcloud auth application-default print-access-token
```

#### WebSocket Configuration Issues
```bash
# Test WebSocket connectivity
wscat -c ws://localhost:8000/ws

# Check port availability
netstat -ln | grep :8000
```

#### Performance Configuration Issues
```bash
# Monitor alert processing latency
tail -f logs/tradeassist.log | grep "Alert processed"

# Check memory usage
ps aux | grep python

# Monitor CPU usage
top -p $(pgrep -f "main.py")
```

### Configuration Validation Tools

```python
# Automated configuration validation
def validate_all_config():
    """Comprehensive configuration validation"""
    validators = [
        validate_database_config,
        validate_api_config,
        validate_security_config,
        validate_performance_config,
        validate_notification_config
    ]

    for validator in validators:
        try:
            validator()
            print(f"✅ {validator.__name__} passed")
        except Exception as e:
            print(f"❌ {validator.__name__} failed: {e}")
```

This configuration guide ensures your TradeAssist system is properly configured for optimal performance, security, and reliability across all environments.
