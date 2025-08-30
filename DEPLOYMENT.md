# TradeAssist Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites
- Python 3.9+ 
- Node.js 16+ and npm
- Git
- Google Cloud account (optional for secret management)
- Schwab API credentials

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
```

#### Schwab API Setup

1. Register at [Schwab Developer Portal](https://developer.schwab.com/)
2. Create a new app
3. Get your Client ID and Client Secret
4. Set redirect URL to `http://localhost:8080/callback`

#### Google Cloud Secret Manager Setup (Optional)

If you want to use Google Cloud Secret Manager:
1. Create a Google Cloud project
2. Enable Secret Manager API
3. Create a service account with Secret Manager access
4. Download the service account key JSON file
5. Add `GOOGLE_APPLICATION_CREDENTIALS` path in `.env`

### 3. Database Initialization

```bash
# Database migrations are handled automatically
# The database will be created in ./data/trade_assist.db

# If you want to run migrations manually:
alembic upgrade head
```

### 4. Build Frontend

```bash
cd src/frontend
npm run build
cd ../..
```

### 5. Start the Application

#### Quick Start (Recommended)

```bash
# Use the start script
chmod +x start.sh
./start.sh
```

#### Manual Start - Development Mode

```bash
# Backend (Terminal 1)
source .venv/bin/activate
python run.py

# Frontend development server (Terminal 2) 
cd src/frontend
npm run dev
```

#### Manual Start - Production Mode

```bash
# Start production server
source .venv/bin/activate
uvicorn src.backend.main:app --host 127.0.0.1 --port 8000
```

#### Production Mode

```bash
# Activate virtual environment
source venv_linux/bin/activate

# Start production server
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --workers 1
```

### 6. Access the Application

- **Frontend Dashboard**: http://localhost:3000 (dev) or http://localhost:8000 (prod)
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 🔧 Advanced Configuration

### Database Configuration

#### SQLite Optimization (Default)
```python
# Automatic WAL mode enabled for performance
# Connection pooling configured
# Async support enabled
```

#### Switching to PostgreSQL (Future)
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

### Notification Channels

#### Slack Configuration
```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL=#trading-alerts
SLACK_ENABLED=true
```

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
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Build frontend
RUN cd src/frontend && npm install && npm run build

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
      - DATABASE_URL=sqlite:///./data/tradeassist.db
    env_file:
      - .env
```

## 🔒 Security Configuration

### TLS/SSL Setup
```bash
# Generate self-signed certificate for development
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Start with HTTPS
uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 8000/tcp  # API/WebSocket
sudo ufw allow 3000/tcp  # Frontend (dev only)
sudo ufw enable
```

## 📊 Monitoring & Logging

### Log Configuration
```env
LOG_LEVEL=INFO
LOG_FILE=logs/tradeassist.log
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30
```

### Health Monitoring
- **Endpoint**: `/health`
- **Metrics**: Database connectivity, Schwab API status, alert processing latency
- **Alerts**: Automatic alerts for system failures

### Performance Monitoring
```env
ENABLE_METRICS=true
METRICS_PORT=9090
PROMETHEUS_ENABLED=false
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database file permissions
ls -la tradeassist.db

# Reset database
rm tradeassist.db
alembic upgrade head
```

#### Schwab API Connection Issues
```bash
# Test API connectivity
curl -X GET "https://api.schwabapi.com/v1/accounts" -H "Authorization: Bearer YOUR_TOKEN"

# Check credentials in Secret Manager
# Verify callback URL matches exactly
```

#### WebSocket Connection Problems
```javascript
// Check WebSocket connection in browser console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected');
ws.onerror = (error) => console.log('Error:', error);
```

#### High Alert Latency
```bash
# Check system resources
htop

# Monitor alert processing
tail -f logs/tradeassist.log | grep "Alert processed"

# Adjust performance settings in .env
```

### Log Analysis
```bash
# Alert processing times
grep "Alert processed" logs/tradeassist.log | tail -100

# API response times
grep "API request" logs/tradeassist.log | tail -100

# Error tracking
grep "ERROR" logs/tradeassist.log | tail -50
```

## 🔄 Updates & Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Update frontend
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
cp tradeassist.db "tradeassist_backup_$(date +%Y%m%d_%H%M%S).db"

# Automated backup script
echo "0 2 * * * cp /path/to/tradeassist.db /backups/tradeassist_$(date +\%Y\%m\%d).db" | crontab -
```

### System Maintenance
```bash
# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete

# Clean old alert data
python -c "from src.backend.services.data_retention import cleanup_old_data; cleanup_old_data()"

# Update system packages
sudo apt update && sudo apt upgrade
```

## 📈 Scaling Considerations

### Single-User Optimization (Current)
- SQLite with WAL mode
- In-memory queues
- Single process architecture
- Optimal for <1000 alerts/day

### Future Scaling Options
- PostgreSQL database
- Redis for caching and queues
- Multiple worker processes
- Load balancing
- Horizontal scaling with microservices

---

## ✅ Deployment Checklist

- [ ] Environment variables configured
- [ ] Google Cloud Secret Manager setup
- [ ] Schwab API credentials configured
- [ ] Database initialized
- [ ] Frontend built
- [ ] TLS/SSL configured (production)
- [ ] Firewall rules set
- [ ] Backup strategy implemented
- [ ] Monitoring enabled
- [ ] Health checks passing
- [ ] Alert notifications working

Your TradeAssist deployment should now be ready for real-time trading alerts with sub-second latency!