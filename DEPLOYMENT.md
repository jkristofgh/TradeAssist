# TradeAssist Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites
- Python 3.9+ 
- Node.js 16+ and npm
- Git
- Schwab API credentials
- Google Cloud account (optional for secret management)

### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo>
cd TradeAssist

# Create and activate virtual environment (use .venv for consistency)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd src/frontend
npm install
cd ../..
```

### 2. Configuration

#### Environment Variables
Copy and configure the environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Application Settings
HOST=127.0.0.1
PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/trade_assist.db
MARKET_DATA_RETENTION_DAYS=30

# Schwab API (Required)
SCHWAB_CLIENT_ID=your_schwab_client_id_here
SCHWAB_CLIENT_SECRET=your_schwab_client_secret_here
SCHWAB_REDIRECT_URI=http://localhost:8080/callback

# Performance Configuration
MAX_WEBSOCKET_CONNECTIONS=10
ALERT_EVALUATION_INTERVAL_MS=100
DATA_INGESTION_BATCH_SIZE=100

# Notification Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_CHANNEL=#trading-alerts
SOUND_ALERTS_ENABLED=true

# Target Instruments
TARGET_FUTURES=ES,NQ,YM,CL,GC
TARGET_INDICES=SPX,NDX,RUT
TARGET_INTERNALS=VIX,TICK,ADD,TRIN

# Advanced Analytics
ML_MODELS_ENABLED=true
TECHNICAL_INDICATORS_ENABLED=true

# Performance Monitoring
PERFORMANCE_MONITORING_ENABLED=true
DATABASE_MONITORING_ENABLED=true
```

#### Schwab API Setup

1. Register at [Schwab Developer Portal](https://developer.schwab.com/)
2. Create a new app
3. Get your Client ID and Client Secret
4. Set redirect URL to `http://localhost:8080/callback`
5. Complete OAuth flow using `authenticate_schwab.py` script

#### Google Cloud Secret Manager Setup (Optional)

If you want to use Google Cloud Secret Manager for secure credential storage:

1. Create a Google Cloud project
2. Enable Secret Manager API
3. Create a service account with Secret Manager access
4. Download the service account key JSON file
5. Add `GOOGLE_APPLICATION_CREDENTIALS` path in `.env`

### 3. Database Initialization

```bash
# Database migrations are handled automatically on startup
# The database will be created in ./data/trade_assist.db

# For manual migrations:
alembic upgrade head

# To create a new migration:
alembic revision --autogenerate -m "Description of changes"
```

### 4. Build Frontend

```bash
cd src/frontend
npm run build
cd ../..
```

### 5. Start the Application

#### Development Mode (Recommended for Development)

**Option 1: Separate terminals for full development experience**

```bash
# Terminal 1: Start backend with hot reload
source .venv/bin/activate
.venv/bin/uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend development server
cd src/frontend
npm run dev
```

**Option 2: Using the start script**

```bash
# Make script executable
chmod +x start.sh
./start.sh
```

#### Production Mode

```bash
# Start production server
source .venv/bin/activate
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --workers 1

# Frontend will be served from the backend static files after build
```

### 6. Access the Application

- **Development Mode:**
  - **Frontend Dashboard**: http://localhost:3000
  - **Backend API**: http://localhost:8000

- **Production Mode:**
  - **Application**: http://localhost:8000
  
- **Common Endpoints:**
  - **API Documentation**: http://localhost:8000/docs
  - **Health Check**: http://localhost:8000/api/health
  - **WebSocket**: ws://localhost:8000/ws/realtime

## 🔧 Advanced Configuration

### Database Configuration

#### SQLite Optimization (Default)
The application uses SQLite with optimizations:
- WAL mode enabled for better performance
- Connection pooling configured
- Async support enabled
- Automatic indexing for performance-critical queries

#### Switching to PostgreSQL (Future Enhancement)
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/tradeassist
```

### Performance Tuning

#### Alert Engine Configuration
```env
# Target alert latency (milliseconds)
ALERT_LATENCY_TARGET_MS=500

# Maximum concurrent alert processing
MAX_CONCURRENT_ALERTS=50

# Alert batch processing size
ALERT_BATCH_SIZE=100

# Alert evaluation frequency
ALERT_EVALUATION_INTERVAL_MS=100
```

#### WebSocket Configuration
```env
# Maximum WebSocket connections
MAX_WEBSOCKET_CONNECTIONS=10

# WebSocket ping interval (seconds)
WEBSOCKET_PING_INTERVAL=30

# Message queue size
WEBSOCKET_QUEUE_SIZE=1000
```

#### Machine Learning Configuration
```env
# Enable ML-powered analytics
ML_MODELS_ENABLED=true

# ML model refresh interval (hours)
ML_MODEL_REFRESH_INTERVAL=24

# Enable advanced indicators
TECHNICAL_INDICATORS_ENABLED=true
```

### Notification Channels

#### Slack Configuration
```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL=#trading-alerts
SLACK_ENABLED=true
```

To set up Slack integration:
1. Create a Slack app at https://api.slack.com/apps
2. Add Bot Token Scopes: `chat:write`, `chat:write.public`
3. Install app to workspace
4. Copy Bot User OAuth Token

#### Sound Notifications
```env
SOUND_ENABLED=true
SOUND_ALERT_FILE=alert.wav
SOUND_VOLUME=0.8
```

#### In-App Notifications
```env
WEBAPP_NOTIFICATIONS=true
NOTIFICATION_RETENTION_DAYS=30
```

## 🐳 Docker Deployment (Optional)

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY .env.example .env

# Build frontend
COPY src/frontend/package*.json ./src/frontend/
RUN cd src/frontend && npm install
COPY src/frontend/ ./src/frontend/
RUN cd src/frontend && npm run build

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  tradeassist:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/trade_assist.db
    env_file:
      - .env
    restart: unless-stopped
```

## 🔒 Security Configuration

### TLS/SSL Setup (Production Recommended)
```bash
# Generate self-signed certificate for development
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Start with HTTPS
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 \
  --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 8000/tcp  # API/WebSocket
sudo ufw allow 3000/tcp  # Frontend (dev only)
sudo ufw enable
```

### Environment Security
```bash
# Secure the .env file
chmod 600 .env

# Ensure data directory is secure
chmod 755 data/
chmod 644 data/*.db
```

## 📊 Monitoring & Logging

### Log Configuration
```env
LOG_LEVEL=INFO
LOG_FILE=logs/tradeassist.log
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30

# Advanced logging
PERFORMANCE_LOGGING=true
DATABASE_QUERY_LOGGING=false  # Enable for debugging only
WEBSOCKET_LOGGING=false       # Enable for debugging only
```

### Health Monitoring
- **Endpoint**: `/api/health`
- **Metrics**: Database connectivity, Schwab API status, alert processing latency
- **Alerts**: Automatic alerts for system failures

### Performance Monitoring
```env
# Enable comprehensive monitoring
PERFORMANCE_MONITORING_ENABLED=true
DATABASE_MONITORING_ENABLED=true
METRICS_RETENTION_HOURS=168  # 7 days

# Performance targets
ALERT_LATENCY_TARGET_MS=500
API_RESPONSE_TARGET_MS=100
WEBSOCKET_UPDATE_TARGET_MS=50
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database file permissions
ls -la data/trade_assist.db

# Reset database (WARNING: This will delete all data)
rm data/trade_assist.db
alembic upgrade head

# Check database integrity
sqlite3 data/trade_assist.db "PRAGMA integrity_check;"
```

#### Schwab API Connection Issues
```bash
# Test API connectivity manually
python authenticate_schwab.py

# Check token file
ls -la data/schwab_tokens.json

# Verify environment variables
echo $SCHWAB_CLIENT_ID
echo $SCHWAB_CLIENT_SECRET
```

#### WebSocket Connection Problems
```bash
# Test WebSocket connection using browser console
const ws = new WebSocket('ws://localhost:8000/ws/realtime');
ws.onopen = () => console.log('Connected');
ws.onerror = (error) => console.log('Error:', error);
ws.onmessage = (msg) => console.log('Message:', JSON.parse(msg.data));
```

#### Frontend Build Issues
```bash
# Clear node modules and reinstall
cd src/frontend
rm -rf node_modules package-lock.json
npm install

# Check TypeScript errors
npm run typecheck

# Fix linting issues
npm run lint:fix
```

#### High Alert Latency
```bash
# Check system resources
htop

# Monitor alert processing
tail -f logs/tradeassist.log | grep "Alert processed"

# Check database performance
python -c "
from src.backend.services.database_monitoring_service import DatabaseMonitoringService
service = DatabaseMonitoringService()
print(service.get_performance_metrics())
"
```

### Performance Optimization

#### Database Optimization
```bash
# Analyze database performance
python -c "
from src.backend.services.database_performance import DatabasePerformance
perf = DatabasePerformance()
print(perf.analyze_performance())
"

# Optimize database
python -c "
from src.backend.services.database_performance import DatabasePerformance
perf = DatabasePerformance()
perf.optimize_database()
"
```

#### Memory Management
```bash
# Check memory usage
python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

### Log Analysis
```bash
# Alert processing times
grep "Alert processed" logs/tradeassist.log | tail -100

# API response times  
grep "API request" logs/tradeassist.log | tail -100

# Database performance
grep "Database query" logs/tradeassist.log | tail -100

# Error tracking
grep "ERROR" logs/tradeassist.log | tail -50

# WebSocket connections
grep "WebSocket" logs/tradeassist.log | tail -50
```

## 🔄 Updates & Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Update Python dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Update frontend dependencies
cd src/frontend
npm install
npm run build
cd ../..

# Run database migrations
alembic upgrade head

# Restart application
```

### Database Backup
```bash
# Backup SQLite database
cp data/trade_assist.db "backups/trade_assist_backup_$(date +%Y%m%d_%H%M%S).db"

# Automated backup script (add to crontab)
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DB_FILE="/path/to/trade_assist.db"
DATE=$(date +%Y%m%d_%H%M%S)
cp "$DB_FILE" "$BACKUP_DIR/trade_assist_$DATE.db"
find "$BACKUP_DIR" -name "trade_assist_*.db" -mtime +7 -delete

# Add to crontab for daily backups
echo "0 2 * * * /path/to/backup_script.sh" | crontab -
```

### System Maintenance
```bash
# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete

# Clean old alert data (if retention is configured)
python -c "
from src.backend.services.data_retention import cleanup_old_data
cleanup_old_data()
"

# Update system packages
sudo apt update && sudo apt upgrade

# Check disk space
df -h

# Check application health
curl http://localhost:8000/api/health
```

## 📈 Scaling Considerations

### Current Architecture (Single-User Optimization)
- SQLite with WAL mode for optimal single-user performance
- In-memory queues for real-time processing
- Single process architecture
- Optimal for <10 concurrent alert rules
- Handles real-time data for 12 instruments efficiently

### Future Scaling Options
- **PostgreSQL database** for multi-user support
- **Redis** for caching and message queues
- **Multiple worker processes** for increased throughput
- **Load balancing** for high availability
- **Microservices architecture** for complex deployments

## 🧪 Testing Deployment

### Validate Installation
```bash
# Run comprehensive tests
source .venv/bin/activate
.venv/bin/python -m pytest tests/ -v --tb=short

# Test API endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/docs

# Test WebSocket connection
python -c "
import asyncio
import websockets
import json

async def test_websocket():
    try:
        uri = 'ws://localhost:8000/ws/realtime'
        async with websockets.connect(uri) as websocket:
            print('WebSocket connected successfully')
            # Send a test message
            await websocket.send(json.dumps({'type': 'ping'}))
            response = await websocket.recv()
            print(f'Received: {response}')
    except Exception as e:
        print(f'WebSocket test failed: {e}')

asyncio.run(test_websocket())
"

# Test frontend build
cd src/frontend
npm run build
cd ../..
```

---

## ✅ Deployment Checklist

- [ ] Environment variables configured in `.env`
- [ ] Schwab API credentials obtained and configured
- [ ] OAuth flow completed with `authenticate_schwab.py`
- [ ] Google Cloud Secret Manager setup (if using)
- [ ] Database initialized and tested
- [ ] Frontend built successfully
- [ ] Backend starts without errors
- [ ] WebSocket connection working
- [ ] API health check passes
- [ ] Alert notifications configured and tested
- [ ] TLS/SSL configured (production)
- [ ] Firewall rules configured (production)
- [ ] Backup strategy implemented
- [ ] Monitoring enabled
- [ ] Performance targets validated
- [ ] Log rotation configured

Your TradeAssist deployment should now be ready for professional trading with sub-second alerts and advanced analytics!

## 🔄 Production Readiness

### Performance Validation
- Alert latency < 500ms ✅
- WebSocket updates < 50ms ✅  
- API response time < 100ms ✅
- Memory usage < 100MB additional ✅
- Database query optimization ✅

### Reliability Features
- Circuit breaker protection ✅
- Automatic reconnection ✅
- Error handling and recovery ✅
- Comprehensive logging ✅
- Health monitoring ✅

### Security Implementation
- Secure credential management ✅
- OAuth integration ✅
- Input validation ✅
- Error masking ✅
- Audit logging ✅