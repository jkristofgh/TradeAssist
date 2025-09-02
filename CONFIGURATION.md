# TradeAssist Configuration Reference

This comprehensive guide covers all configuration options for TradeAssist, including environment variables, application settings, and advanced configuration parameters.

## 🔧 Environment Configuration

### Setting Up Configuration Files

```bash
# Copy the example configuration file
cp .env.example .env

# Edit the configuration file
nano .env  # or use your preferred editor
```

**⚠️ Important**: Never commit your actual `.env` file to version control. It contains sensitive credentials.

---

## 📝 Core Configuration

### Application Settings

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `HOST` | `127.0.0.1` | Server bind address | No |
| `PORT` | `8000` | Server port number | No |
| `DEBUG` | `true` | Enable debug mode for development | No |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | No |

```env
# Application Settings
HOST=127.0.0.1
PORT=8000
DEBUG=true
LOG_LEVEL=INFO
```

### Database Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/trade_assist.db` | Database connection string | No |
| `MARKET_DATA_RETENTION_DAYS` | `30` | Days to retain market data | No |

```env
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./data/trade_assist.db
MARKET_DATA_RETENTION_DAYS=30
```

**Database URL Formats:**
- **SQLite**: `sqlite+aiosqlite:///./data/trade_assist.db`
- **PostgreSQL**: `postgresql+asyncpg://user:password@localhost/tradeassist`

---

## 🔐 API Integration

### Schwab API Configuration (Required)

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `SCHWAB_CLIENT_ID` | - | Schwab application client ID | **Yes** |
| `SCHWAB_CLIENT_SECRET` | - | Schwab application client secret | **Yes** |
| `SCHWAB_REDIRECT_URI` | `http://localhost:8080/callback` | OAuth callback URL | No |

```env
# Schwab API Configuration (Required)
SCHWAB_CLIENT_ID=your_schwab_client_id_here
SCHWAB_CLIENT_SECRET=your_schwab_client_secret_here
SCHWAB_REDIRECT_URI=http://localhost:8080/callback
```

**Getting Schwab API Credentials:**
1. Register at [Schwab Developer Portal](https://developer.schwab.com/)
2. Create a new application
3. Note your Client ID and Client Secret
4. Set the redirect URI to match your configuration
5. Complete OAuth flow using `authenticate_schwab.py`

### Google Cloud Secret Manager (Optional)

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `GOOGLE_APPLICATION_CREDENTIALS` | - | Path to service account JSON file | No |

```env
# Google Cloud Secret Manager (Optional)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

## ⚡ Performance Configuration

### WebSocket & Real-time Settings

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `MAX_WEBSOCKET_CONNECTIONS` | `10` | Maximum concurrent WebSocket connections | 1-100 |
| `ALERT_EVALUATION_INTERVAL_MS` | `100` | Alert evaluation frequency | 50-1000 |
| `DATA_INGESTION_BATCH_SIZE` | `100` | Market data batch processing size | 10-1000 |

```env
# Performance Configuration
MAX_WEBSOCKET_CONNECTIONS=10
ALERT_EVALUATION_INTERVAL_MS=100
DATA_INGESTION_BATCH_SIZE=100
```

### API Rate Limiting

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_API_MAX_REQUESTS_PER_MINUTE` | `100` | Max requests per minute per client | 10-1000 |
| `TRADEASSIST_API_MAX_REQUESTS_PER_HOUR` | `1000` | Max requests per hour per client | 100-10000 |
| `TRADEASSIST_API_MAX_CONCURRENT_REQUESTS` | `10` | Max concurrent requests | 1-50 |
| `TRADEASSIST_API_REQUEST_TIMEOUT_SECONDS` | `30.0` | Request timeout | 5.0-120.0 |

```env
# API Rate Limiting
TRADEASSIST_API_MAX_REQUESTS_PER_MINUTE=100
TRADEASSIST_API_MAX_REQUESTS_PER_HOUR=1000
TRADEASSIST_API_MAX_CONCURRENT_REQUESTS=10
TRADEASSIST_API_REQUEST_TIMEOUT_SECONDS=30.0
```

### Pagination Settings

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_API_DEFAULT_PAGE_SIZE` | `25` | Default items per page | 10-100 |
| `TRADEASSIST_API_MAX_PAGE_SIZE` | `100` | Maximum items per page | 50-500 |
| `TRADEASSIST_API_MAX_PAGE_NUMBER` | `1000` | Maximum page number | 100-10000 |

```env
# Pagination Settings
TRADEASSIST_API_DEFAULT_PAGE_SIZE=25
TRADEASSIST_API_MAX_PAGE_SIZE=100
TRADEASSIST_API_MAX_PAGE_NUMBER=1000
```

---

## 🔔 Notification Configuration

### Slack Integration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `SLACK_BOT_TOKEN` | - | Slack Bot User OAuth Token | No |
| `SLACK_CHANNEL` | `#trading-alerts` | Default Slack channel | No |
| `SLACK_ENABLED` | `true` | Enable Slack notifications | No |

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=#trading-alerts
SLACK_ENABLED=true
```

**Setting up Slack Integration:**
1. Create a Slack app at https://api.slack.com/apps
2. Add Bot Token Scopes: `chat:write`, `chat:write.public`
3. Install app to your workspace
4. Copy the Bot User OAuth Token

### Sound Notifications

| Variable | Default | Description | Options |
|----------|---------|-------------|---------|
| `SOUND_ALERTS_ENABLED` | `true` | Enable sound notifications | true/false |
| `SOUND_ALERT_FILE` | `alert.wav` | Custom alert sound file | Any .wav file |
| `SOUND_VOLUME` | `0.8` | Alert sound volume | 0.0-1.0 |

```env
# Sound Notifications
SOUND_ALERTS_ENABLED=true
SOUND_ALERT_FILE=alert.wav
SOUND_VOLUME=0.8
```

### In-App Notifications

| Variable | Default | Description | Options |
|----------|---------|-------------|---------|
| `WEBAPP_NOTIFICATIONS` | `true` | Enable web app notifications | true/false |
| `NOTIFICATION_RETENTION_DAYS` | `30` | Days to keep notification history | 1-365 |

```env
# In-App Notifications
WEBAPP_NOTIFICATIONS=true
NOTIFICATION_RETENTION_DAYS=30
```

---

## 📊 Market Data & Instruments

### Target Instruments

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_FUTURES` | `ES,NQ,YM,CL,GC` | Comma-separated list of future symbols |
| `TARGET_INDICES` | `SPX,NDX,RUT` | Comma-separated list of index symbols |
| `TARGET_INTERNALS` | `VIX,TICK,ADD,TRIN` | Comma-separated list of market internal symbols |

```env
# Target Instruments
TARGET_FUTURES=ES,NQ,YM,CL,GC
TARGET_INDICES=SPX,NDX,RUT
TARGET_INTERNALS=VIX,TICK,ADD,TRIN
```

**Available Instruments:**
- **Futures**: ES (S&P 500), NQ (NASDAQ), YM (Dow), CL (Crude Oil), GC (Gold)
- **Indices**: SPX (S&P 500), NDX (NASDAQ 100), RUT (Russell 2000)
- **Internals**: VIX (Volatility), TICK (NYSE TICK), ADD (Advance/Decline), TRIN (Arms Index)

---

## 📈 Technical Indicators Configuration

### RSI (Relative Strength Index)

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_INDICATOR_RSI_DEFAULT_PERIOD` | `14` | RSI calculation period | 2-50 |
| `TRADEASSIST_INDICATOR_RSI_OVERBOUGHT_THRESHOLD` | `70.0` | Overbought level | 60.0-90.0 |
| `TRADEASSIST_INDICATOR_RSI_OVERSOLD_THRESHOLD` | `30.0` | Oversold level | 10.0-40.0 |

### MACD (Moving Average Convergence Divergence)

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_INDICATOR_MACD_FAST_PERIOD` | `12` | Fast EMA period | 5-20 |
| `TRADEASSIST_INDICATOR_MACD_SLOW_PERIOD` | `26` | Slow EMA period | 15-50 |
| `TRADEASSIST_INDICATOR_MACD_SIGNAL_PERIOD` | `9` | Signal line period | 5-15 |

### Bollinger Bands

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_INDICATOR_BOLLINGER_PERIOD` | `20` | Moving average period | 10-50 |
| `TRADEASSIST_INDICATOR_BOLLINGER_STD_DEV` | `2.0` | Standard deviation multiplier | 1.0-3.0 |

### Moving Averages

| Variable | Default | Description |
|----------|---------|-------------|
| `TRADEASSIST_INDICATOR_SMA_DEFAULT_PERIODS` | `10,20,50,100,200` | Simple MA periods |
| `TRADEASSIST_INDICATOR_EMA_DEFAULT_PERIODS` | `10,20,50,100,200` | Exponential MA periods |

### Stochastic Oscillator

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_INDICATOR_STOCHASTIC_K_PERIOD` | `14` | %K period | 5-30 |
| `TRADEASSIST_INDICATOR_STOCHASTIC_D_PERIOD` | `3` | %D period | 1-10 |
| `TRADEASSIST_INDICATOR_STOCHASTIC_OVERBOUGHT` | `80.0` | Overbought level | 70.0-90.0 |
| `TRADEASSIST_INDICATOR_STOCHASTIC_OVERSOLD` | `20.0` | Oversold level | 10.0-30.0 |

### Volume & ATR

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_INDICATOR_VOLUME_SMA_PERIOD` | `20` | Volume SMA period | 10-50 |
| `TRADEASSIST_INDICATOR_VOLUME_SPIKE_THRESHOLD` | `2.0` | Volume spike multiplier | 1.5-5.0 |
| `TRADEASSIST_INDICATOR_ATR_PERIOD` | `14` | ATR calculation period | 5-30 |

```env
# Technical Indicators Configuration
TRADEASSIST_INDICATOR_RSI_DEFAULT_PERIOD=14
TRADEASSIST_INDICATOR_RSI_OVERBOUGHT_THRESHOLD=70.0
TRADEASSIST_INDICATOR_RSI_OVERSOLD_THRESHOLD=30.0
TRADEASSIST_INDICATOR_MACD_FAST_PERIOD=12
TRADEASSIST_INDICATOR_MACD_SLOW_PERIOD=26
TRADEASSIST_INDICATOR_MACD_SIGNAL_PERIOD=9
TRADEASSIST_INDICATOR_BOLLINGER_PERIOD=20
TRADEASSIST_INDICATOR_BOLLINGER_STD_DEV=2.0
```

---

## 🗄️ Caching Configuration

### Local Caching

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_CACHE_MARKET_DATA_TTL` | `60` | Market data cache TTL (seconds) | 10-300 |
| `TRADEASSIST_CACHE_ANALYTICS_TTL` | `300` | Analytics cache TTL (seconds) | 60-3600 |
| `TRADEASSIST_CACHE_HISTORICAL_DATA_TTL` | `3600` | Historical data cache TTL (seconds) | 300-86400 |
| `TRADEASSIST_CACHE_MAX_SIZE_MB` | `256` | Maximum cache size | 64-2048 |
| `TRADEASSIST_CACHE_MAX_ENTRIES` | `10000` | Maximum cache entries | 1000-100000 |

```env
# Caching Configuration
TRADEASSIST_CACHE_MARKET_DATA_TTL=60
TRADEASSIST_CACHE_ANALYTICS_TTL=300
TRADEASSIST_CACHE_HISTORICAL_DATA_TTL=3600
TRADEASSIST_CACHE_MAX_SIZE_MB=256
TRADEASSIST_CACHE_MAX_ENTRIES=10000
```

### Redis Cache (Optional)

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `TRADEASSIST_CACHE_REDIS_ENABLED` | `false` | Enable Redis caching | No |
| `TRADEASSIST_CACHE_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL | No |
| `TRADEASSIST_CACHE_REDIS_KEY_PREFIX` | `tradeassist:` | Redis key prefix | No |
| `TRADEASSIST_CACHE_REDIS_CONNECTION_TIMEOUT` | `5` | Connection timeout (seconds) | No |

```env
# Redis Configuration (Optional)
TRADEASSIST_CACHE_REDIS_ENABLED=false
TRADEASSIST_CACHE_REDIS_URL=redis://localhost:6379/0
TRADEASSIST_CACHE_REDIS_KEY_PREFIX=tradeassist:
TRADEASSIST_CACHE_REDIS_CONNECTION_TIMEOUT=5
```

---

## 📊 Monitoring & Analytics

### Performance Monitoring

| Variable | Default | Description | Options |
|----------|---------|-------------|---------|
| `TRADEASSIST_MONITORING_ENABLE_PERFORMANCE_TRACKING` | `true` | Enable performance monitoring | true/false |
| `TRADEASSIST_MONITORING_PERFORMANCE_SAMPLE_RATE` | `1.0` | Performance sampling rate | 0.0-1.0 |
| `TRADEASSIST_MONITORING_SLOW_QUERY_THRESHOLD_MS` | `1000.0` | Slow query threshold | 100.0-5000.0 |
| `TRADEASSIST_MONITORING_SLOW_REQUEST_THRESHOLD_MS` | `2000.0` | Slow request threshold | 500.0-10000.0 |

### Error Tracking

| Variable | Default | Description | Options |
|----------|---------|-------------|---------|
| `TRADEASSIST_MONITORING_ENABLE_ERROR_TRACKING` | `true` | Enable error tracking | true/false |
| `TRADEASSIST_MONITORING_ERROR_SAMPLE_RATE` | `1.0` | Error sampling rate | 0.0-1.0 |
| `TRADEASSIST_MONITORING_MAX_ERROR_DETAILS_LENGTH` | `1000` | Max error detail length | 100-5000 |

### Alerting

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_MONITORING_ENABLE_ALERTING` | `false` | Enable system alerting | true/false |
| `TRADEASSIST_MONITORING_ERROR_RATE_ALERT_THRESHOLD` | `0.05` | Error rate alert threshold | 0.01-0.50 |
| `TRADEASSIST_MONITORING_RESPONSE_TIME_ALERT_THRESHOLD_MS` | `5000.0` | Response time alert threshold | 1000.0-30000.0 |
| `TRADEASSIST_MONITORING_ALERT_COOLDOWN_MINUTES` | `15` | Alert cooldown period | 5-120 |

### Resource Monitoring

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_MONITORING_ENABLE_RESOURCE_MONITORING` | `true` | Enable resource monitoring | true/false |
| `TRADEASSIST_MONITORING_RESOURCE_CHECK_INTERVAL_SECONDS` | `30` | Resource check interval | 10-300 |
| `TRADEASSIST_MONITORING_MEMORY_USAGE_ALERT_THRESHOLD_MB` | `1024` | Memory alert threshold | 256-8192 |
| `TRADEASSIST_MONITORING_CPU_USAGE_ALERT_THRESHOLD_PERCENT` | `80.0` | CPU alert threshold | 50.0-95.0 |

```env
# Monitoring Configuration
TRADEASSIST_MONITORING_ENABLE_PERFORMANCE_TRACKING=true
TRADEASSIST_MONITORING_PERFORMANCE_SAMPLE_RATE=1.0
TRADEASSIST_MONITORING_SLOW_QUERY_THRESHOLD_MS=1000.0
TRADEASSIST_MONITORING_ENABLE_ERROR_TRACKING=true
TRADEASSIST_MONITORING_ERROR_SAMPLE_RATE=1.0
```

---

## 🔒 Security Configuration

### Data Validation

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_VALIDATION_MIN_LOOKBACK_HOURS` | `1` | Minimum lookback period | 1-24 |
| `TRADEASSIST_VALIDATION_MAX_LOOKBACK_HOURS` | `8760` | Maximum lookback period | 168-8760 |
| `TRADEASSIST_VALIDATION_MAX_DATE_RANGE_DAYS` | `365` | Maximum date range | 1-1095 |
| `TRADEASSIST_VALIDATION_MAX_STRING_LENGTH` | `1000` | Maximum string length | 100-5000 |
| `TRADEASSIST_VALIDATION_MAX_SYMBOL_LENGTH` | `20` | Maximum symbol length | 5-50 |

### Request Limits

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_API_MAX_REQUEST_SIZE_MB` | `10.0` | Maximum request size | 1.0-100.0 |
| `TRADEASSIST_API_MAX_JSON_DEPTH` | `10` | Maximum JSON nesting depth | 5-20 |
| `TRADEASSIST_API_DATABASE_QUERY_TIMEOUT_SECONDS` | `15.0` | Database query timeout | 5.0-60.0 |
| `TRADEASSIST_API_EXTERNAL_API_TIMEOUT_SECONDS` | `10.0` | External API timeout | 5.0-30.0 |

```env
# Security Configuration
TRADEASSIST_VALIDATION_MIN_LOOKBACK_HOURS=1
TRADEASSIST_VALIDATION_MAX_LOOKBACK_HOURS=8760
TRADEASSIST_VALIDATION_MAX_DATE_RANGE_DAYS=365
TRADEASSIST_API_MAX_REQUEST_SIZE_MB=10.0
TRADEASSIST_API_MAX_JSON_DEPTH=10
```

---

## 🧪 Machine Learning Configuration

### ML Model Settings

| Variable | Default | Description | Options |
|----------|---------|-------------|---------|
| `ML_MODELS_ENABLED` | `true` | Enable ML-powered analytics | true/false |
| `ML_MODEL_REFRESH_INTERVAL` | `24` | Model refresh interval (hours) | 1-168 |
| `TECHNICAL_INDICATORS_ENABLED` | `true` | Enable technical indicators | true/false |

### Advanced Analytics

| Variable | Default | Description | Range |
|----------|---------|-------------|--------|
| `TRADEASSIST_VALIDATION_ALLOWED_CONFIDENCE_LEVELS` | `0.90,0.95,0.99,0.999` | Allowed confidence levels | 0.80-0.999 |
| `TRADEASSIST_VALIDATION_DEFAULT_CONFIDENCE_LEVEL` | `0.95` | Default confidence level | 0.80-0.999 |
| `TRADEASSIST_VALIDATION_MAX_CALCULATION_PRECISION` | `8` | Maximum decimal precision | 2-15 |

```env
# Machine Learning Configuration
ML_MODELS_ENABLED=true
ML_MODEL_REFRESH_INTERVAL=24
TECHNICAL_INDICATORS_ENABLED=true
TRADEASSIST_VALIDATION_DEFAULT_CONFIDENCE_LEVEL=0.95
```

---

## 🐳 Docker Configuration

### Docker Environment Variables

When running in Docker containers, ensure the following environment variables are properly set:

```yaml
# docker-compose.yml
version: '3.8'
services:
  tradeassist:
    environment:
      - HOST=0.0.0.0  # Bind to all interfaces in container
      - PORT=8000
      - DATABASE_URL=sqlite+aiosqlite:///./data/trade_assist.db
      - SCHWAB_CLIENT_ID=${SCHWAB_CLIENT_ID}
      - SCHWAB_CLIENT_SECRET=${SCHWAB_CLIENT_SECRET}
    env_file:
      - .env
```

---

## 📋 Configuration Validation

### Configuration Checker

TradeAssist includes built-in configuration validation. Access it via:

```bash
# Check configuration validity
curl http://localhost:8000/api/config/validate

# Get current configuration (non-sensitive values)
curl http://localhost:8000/api/config/current
```

### Common Configuration Issues

#### 1. Invalid Schwab Credentials
**Symptoms**: API connection failures, authentication errors
**Solution**: Verify credentials at Schwab Developer Portal, re-run OAuth flow

#### 2. Database Connection Issues
**Symptoms**: Database errors, migration failures
**Solution**: Check database URL format, ensure data directory exists and is writable

#### 3. Performance Issues
**Symptoms**: High latency, timeouts
**Solution**: Adjust timeout values, increase resource limits, optimize cache settings

#### 4. WebSocket Connection Problems
**Symptoms**: Real-time data not updating
**Solution**: Check WebSocket configuration, firewall rules, connection limits

---

## 🔄 Configuration Hot Reload

Some configuration changes can be applied without restarting the application:

### Hot-Reloadable Settings
- Logging levels
- Cache TTL values
- Monitoring thresholds
- Technical indicator parameters

### Restart Required Settings
- Database connection URL
- API credentials
- Network binding (HOST/PORT)
- Security settings

```bash
# Reload configuration without restart (for supported settings)
curl -X POST http://localhost:8000/api/config/reload
```

---

## 🎯 Performance Tuning Recommendations

### For Development
```env
DEBUG=true
LOG_LEVEL=DEBUG
TRADEASSIST_CACHE_MARKET_DATA_TTL=30
TRADEASSIST_API_REQUEST_TIMEOUT_SECONDS=60.0
```

### For Production
```env
DEBUG=false
LOG_LEVEL=INFO
TRADEASSIST_CACHE_MARKET_DATA_TTL=60
TRADEASSIST_API_REQUEST_TIMEOUT_SECONDS=30.0
TRADEASSIST_MONITORING_ENABLE_PERFORMANCE_TRACKING=true
```

### For High-Frequency Trading
```env
ALERT_EVALUATION_INTERVAL_MS=50
DATA_INGESTION_BATCH_SIZE=200
TRADEASSIST_CACHE_MARKET_DATA_TTL=30
MAX_WEBSOCKET_CONNECTIONS=20
```

---

## 📊 Configuration Templates

### Minimal Configuration (.env)
```env
# Required settings only
SCHWAB_CLIENT_ID=your_client_id
SCHWAB_CLIENT_SECRET=your_client_secret
```

### Complete Development Configuration
```env
# Development optimized
HOST=127.0.0.1
PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite+aiosqlite:///./data/trade_assist.db
SCHWAB_CLIENT_ID=your_client_id
SCHWAB_CLIENT_SECRET=your_client_secret
SOUND_ALERTS_ENABLED=true
ML_MODELS_ENABLED=true
TRADEASSIST_MONITORING_ENABLE_PERFORMANCE_TRACKING=true
```

### Production Configuration
```env
# Production optimized
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=sqlite+aiosqlite:///./data/trade_assist.db
SCHWAB_CLIENT_ID=your_client_id
SCHWAB_CLIENT_SECRET=your_client_secret
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
SLACK_BOT_TOKEN=your_slack_token
SLACK_CHANNEL=#trading-alerts
TRADEASSIST_MONITORING_ENABLE_PERFORMANCE_TRACKING=true
TRADEASSIST_MONITORING_ENABLE_ALERTING=true
```

---

## 🆘 Configuration Support

### Getting Help
- **API Documentation**: `/docs` endpoint for live configuration API
- **Configuration Validation**: `/api/config/validate` endpoint
- **Health Check**: `/api/health` includes configuration status
- **Logs**: Check application logs for configuration warnings

### Best Practices
1. **Start with minimal configuration** and add features incrementally
2. **Test configuration changes** in development before production
3. **Monitor performance metrics** after configuration changes
4. **Keep sensitive credentials** in secure credential managers
5. **Document custom configurations** for team collaboration

---

**🎯 Your TradeAssist system is now fully configured for professional trading!**

For deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md). For usage information, see [USER_GUIDE.md](USER_GUIDE.md).