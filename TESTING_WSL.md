# TradeAssist Testing Guide for WSL Ubuntu

This comprehensive guide covers all testing methods for the TradeAssist application running on WSL Ubuntu, including API testing, WebSocket validation, frontend testing, performance verification, and troubleshooting.

## 🚀 Quick Start Testing

### 1. Start the Application

**Option 1: Development Mode (Recommended for Testing)**

```bash
# Terminal 1: Start backend
source .venv/bin/activate
.venv/bin/uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd src/frontend
npm run dev
```

**Option 2: Using Start Script**
```bash
chmod +x start.sh
./start.sh
```

**Expected Backend Startup Output:**
```
INFO: Starting TradeAssist application phase=4_production version=1.0.0
INFO: Database initialized successfully
INFO: Circuit breaker 'schwab_streaming' initialized
INFO: Schwab client initialized successfully
INFO: HistoricalDataService started successfully
INFO: Starting core services
INFO: Starting data ingestion service
INFO: Loaded 12 instrument mappings
INFO: Starting streaming for 12 symbols
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Expected Frontend Startup Output:**
```
Starting the development server...
Compiled successfully!
You can now view tradeassist-frontend in the browser.
  Local:            http://localhost:3000
  On Your Network:  http://172.x.x.x:3000
```

## 🌐 Browser-Based Testing (Easiest Method)

Since WSL shares networking with Windows, you can test directly from Windows browsers:

### Interactive API Documentation
- **Swagger UI**: http://localhost:8000/docs (Comprehensive API explorer)
- **ReDoc**: http://localhost:8000/redoc (Alternative documentation)
- **Health Check**: http://localhost:8000/api/health (System status)
- **Frontend Dashboard**: http://localhost:3000 (Development) or http://localhost:8000 (Production)

### Testing in Swagger UI
1. Open http://localhost:8000/docs
2. Click on any endpoint (e.g., `/api/health`)
3. Click **"Try it out"**
4. Click **"Execute"**
5. Review the response

### Core API Endpoints Testing

#### System Health
```bash
# Basic health check
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-09-01T19:12:39.123456",
  "version": "1.0.0",
  "uptime_seconds": 123.45,
  "database": {"status": "connected", "connection_count": 1},
  "schwab_api": {"status": "connected", "last_update": "2025-09-01T19:12:38"},
  "services": {
    "data_ingestion": {"status": "running", "active_instruments": 12},
    "alert_engine": {"status": "running", "active_rules": 0},
    "historical_data_service": {"service_running": true}
  }
}
```

#### Instruments
```bash
# Get all instruments
curl http://localhost:8000/api/instruments

# Expected response:
[
  {
    "id": 1,
    "symbol": "ES",
    "name": "E-mini S&P 500 Future",
    "type": "future",
    "status": "active",
    "last_price": 4525.75,
    "last_tick": "2025-09-01T19:12:39"
  },
  // ... more instruments
]
```

#### Market Data
```bash
# Get real-time market data for instrument
curl http://localhost:8000/api/market-data/1

# Expected response:
{
  "instrument_id": 1,
  "symbol": "ES",
  "price": 4525.75,
  "volume": 125000,
  "bid": 4525.50,
  "ask": 4526.00,
  "timestamp": "2025-09-01T19:12:39.123456"
}
```

#### Analytics Endpoints
```bash
# Technical indicators
curl -X POST http://localhost:8000/api/analytics/technical-indicators \
  -H "Content-Type: application/json" \
  -d '{"instrument_id": 1, "timeframe": "5m"}'

# Market analysis
curl -X POST http://localhost:8000/api/analytics/market-analysis \
  -H "Content-Type: application/json" \
  -d '{"instrument_id": 1, "timeframe": "15m"}'

# Price prediction
curl -X POST http://localhost:8000/api/analytics/price-prediction \
  -H "Content-Type: application/json" \
  -d '{"instrument_id": 1, "timeframe": "1h", "prediction_horizon": "30m"}'
```

#### Historical Data
```bash
# Query historical data
curl -X POST http://localhost:8000/api/historical-data/query \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "ES",
    "start_date": "2025-08-31",
    "end_date": "2025-09-01",
    "frequency": "5m"
  }'
```

## 🔌 WebSocket Testing

### Using Browser Console
```javascript
// Open browser console and test WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/realtime');

ws.onopen = function(event) {
    console.log('WebSocket connected!');
    // Subscribe to market data
    ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'market_data',
        symbols: ['ES', 'NQ', 'SPX']
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

ws.onerror = function(error) {
    console.log('WebSocket error:', error);
};

ws.onclose = function(event) {
    console.log('WebSocket closed:', event.code, event.reason);
};
```

### Using curl for WebSocket Testing
```bash
# Install websocat if not available
# sudo apt-get install websocat

# Test WebSocket connection
websocat ws://localhost:8000/ws/realtime

# Send test message (type this after connecting)
{"type": "ping"}

# Expected response
{"type": "pong", "timestamp": "2025-09-01T19:12:39.123456"}
```

### Python WebSocket Test
```python
# Create test file: test_websocket.py
import asyncio
import websockets
import json

async def test_websocket():
    try:
        uri = "ws://localhost:8000/ws/realtime"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Test ping
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            print(f"📥 Ping response: {response}")
            
            # Subscribe to market data
            await websocket.send(json.dumps({
                "type": "subscribe",
                "channel": "market_data",
                "symbols": ["ES", "NQ"]
            }))
            
            # Listen for a few messages
            for i in range(3):
                response = await websocket.recv()
                data = json.loads(response)
                print(f"📊 Market data {i+1}: {data}")
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

# Run the test
asyncio.run(test_websocket())
```

```bash
# Run WebSocket test
source .venv/bin/activate
python test_websocket.py
```

## 🎨 Frontend Testing

### Browser Testing
1. **Navigate to Frontend**: http://localhost:3000
2. **Check Components**:
   - System health indicators (should be green)
   - Real-time instrument watchlist (should show live prices)
   - Alert history panel
   - Historical data interface
   - Analytics dashboard

### UI Component Testing
```bash
# Run frontend tests
cd src/frontend
npm test

# Run with coverage
npm test -- --coverage

# Run TypeScript type checking
npm run typecheck

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix
```

### Performance Testing
```bash
# Run React performance profiler
cd src/frontend
npm run dev -- --profile

# Build and analyze bundle size
npm run build
npm install -g webpack-bundle-analyzer
npx webpack-bundle-analyzer build/static/js/*.js
```

## 🧪 Backend Testing

### Unit Tests
```bash
# Run all tests
source .venv/bin/activate
.venv/bin/python -m pytest tests/ -v --tb=short

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests
pytest tests/integration/ -v             # Integration tests  
pytest tests/performance/ -v             # Performance tests

# Run with coverage
pytest tests/ --cov=src/backend --cov-report=html

# Run specific test file
pytest tests/unit/test_analytics_engine.py -v

# Run specific test
pytest tests/unit/test_models.py::test_instrument_creation -v
```

### Integration Testing
```bash
# Test database operations
pytest tests/integration/test_database.py -v

# Test API endpoints
pytest tests/integration/test_api.py -v

# Test historical data service
pytest tests/integration/test_historical_data_api.py -v
```

### Performance Testing
```bash
# Run performance benchmarks
pytest tests/performance/test_benchmarks.py -v

# Test alert latency
pytest tests/performance/test_alert_latency.py -v

# Load testing (if available)
pytest tests/performance/test_load.py -v
```

## 📊 Performance Validation

### Alert Latency Testing
```bash
# Test alert processing speed
curl -X POST http://localhost:8000/api/test/alert-latency \
  -H "Content-Type: application/json" \
  -d '{"instrument_id": 1, "condition": "price > 4500", "count": 100}'

# Expected response:
{
  "average_latency_ms": 245.6,
  "min_latency_ms": 187.2,
  "max_latency_ms": 456.8,
  "p95_latency_ms": 378.4,
  "target_met": true
}
```

### API Performance Testing
```bash
# Test API response times
time curl http://localhost:8000/api/health
time curl http://localhost:8000/api/instruments
time curl http://localhost:8000/api/market-data/1

# Batch performance test
for i in {1..10}; do
  time curl -s http://localhost:8000/api/health > /dev/null
done
```

### WebSocket Performance Testing
```python
# Create test file: test_websocket_performance.py
import asyncio
import websockets
import json
import time
from statistics import mean

async def test_websocket_latency():
    uri = "ws://localhost:8000/ws/realtime"
    latencies = []
    
    async with websockets.connect(uri) as websocket:
        for i in range(10):
            start_time = time.time()
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            end_time = time.time()
            
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            latencies.append(latency)
            print(f"Ping {i+1}: {latency:.2f}ms")
            
        avg_latency = mean(latencies)
        print(f"Average latency: {avg_latency:.2f}ms")
        print(f"Target (<50ms): {'✅ PASS' if avg_latency < 50 else '❌ FAIL'}")

asyncio.run(test_websocket_latency())
```

### Database Performance Testing
```bash
# Test database query performance
source .venv/bin/activate
python -c "
from src.backend.services.database_monitoring_service import DatabaseMonitoringService
service = DatabaseMonitoringService()
metrics = service.get_performance_metrics()
print(f'Query avg time: {metrics.get(\"avg_query_time_ms\", 0):.2f}ms')
print(f'Connection pool: {metrics.get(\"connection_pool_size\", 0)}')
"
```

## 🔍 Advanced Testing

### Circuit Breaker Testing
```bash
# Test circuit breaker functionality
curl -X POST http://localhost:8000/api/test/circuit-breaker \
  -H "Content-Type: application/json" \
  -d '{"service": "schwab_api", "action": "trigger_failure"}'

# Check circuit breaker status
curl http://localhost:8000/api/monitoring/circuit-breakers
```

### Error Handling Testing
```bash
# Test invalid requests
curl -X POST http://localhost:8000/api/analytics/technical-indicators \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# Test rate limiting
for i in {1..150}; do
  curl -s http://localhost:8000/api/health > /dev/null &
done
wait
```

### Security Testing
```bash
# Test input validation
curl -X POST http://localhost:8000/api/analytics/market-analysis \
  -H "Content-Type: application/json" \
  -d '{"instrument_id": "invalid", "timeframe": "1000y"}'

# Test request size limits
curl -X POST http://localhost:8000/api/test/large-request \
  -H "Content-Type: application/json" \
  -d "$(python -c 'print("{\"data\": \"" + "x" * 20000000 + "\"}")' 2>/dev/null || echo '{"data": "test"}')"
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Backend Won't Start
```bash
# Check virtual environment
source .venv/bin/activate
python --version  # Should show Python 3.9+

# Check dependencies
pip install -r requirements.txt

# Check database
ls -la data/trade_assist.db
sqlite3 data/trade_assist.db ".tables"

# Check logs
tail -f logs/tradeassist.log
```

#### Frontend Issues
```bash
# Clear node modules and reinstall
cd src/frontend
rm -rf node_modules package-lock.json
npm install

# Check TypeScript errors
npm run typecheck

# Check console for errors
# Open browser dev tools (F12) and check Console tab
```

#### WebSocket Connection Issues
```bash
# Check if backend WebSocket is running
netstat -an | grep 8000

# Test with different WebSocket client
sudo apt-get install websocat
websocat ws://localhost:8000/ws/realtime

# Check firewall
sudo ufw status
```

#### API Connection Issues
```bash
# Test basic connectivity
curl -I http://localhost:8000/api/health

# Check if service is running
ps aux | grep uvicorn
ss -tlnp | grep 8000

# Check logs for errors
grep ERROR logs/tradeassist.log | tail -10
```

#### Schwab API Issues
```bash
# Check credentials
echo $SCHWAB_CLIENT_ID
echo $SCHWAB_CLIENT_SECRET

# Test authentication
python authenticate_schwab.py

# Check token file
ls -la data/schwab_tokens.json
cat data/schwab_tokens.json
```

#### Performance Issues
```bash
# Check system resources
htop
df -h
free -m

# Monitor application performance
curl http://localhost:8000/api/monitoring/performance

# Check database performance
python -c "
from src.backend.services.database_performance import DatabasePerformance
perf = DatabasePerformance()
print(perf.analyze_performance())
"
```

### Debug Commands

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
source .venv/bin/activate
.venv/bin/uvicorn src.backend.main:app --reload --log-level debug

# Check environment variables
env | grep TRADEASSIST
env | grep SCHWAB

# Test database connection
python -c "
from src.backend.database.connection import get_database
import asyncio
async def test():
    db = get_database()
    print('Database connection successful')
asyncio.run(test())
"

# Test individual services
python -c "
from src.backend.services.historical_data_service import HistoricalDataService
service = HistoricalDataService()
print('Historical data service initialized')
"
```

## 📋 Testing Checklist

### Development Testing
- [ ] Backend starts without errors
- [ ] Frontend starts without errors  
- [ ] Health check endpoint responds correctly
- [ ] WebSocket connection establishes
- [ ] Real-time data streams properly
- [ ] API endpoints return expected responses
- [ ] Unit tests pass
- [ ] Integration tests pass

### Performance Testing
- [ ] Alert latency < 500ms
- [ ] WebSocket updates < 50ms
- [ ] API response times < 100ms
- [ ] Database queries < 50ms
- [ ] Frontend load time < 2s

### Security Testing
- [ ] Input validation working
- [ ] Rate limiting active
- [ ] Request size limits enforced
- [ ] Authentication required where expected
- [ ] Error messages don't expose sensitive data

### Production Readiness
- [ ] All tests pass in production mode
- [ ] Configuration validation passes
- [ ] Circuit breakers function correctly
- [ ] Monitoring and alerting active
- [ ] Backup and recovery procedures tested
- [ ] Performance targets met under load

## 🎯 Automated Testing Scripts

### Complete Test Suite
```bash
#!/bin/bash
# test_suite.sh - Complete testing script

echo "🚀 Starting TradeAssist Test Suite"

# Backend tests
echo "🧪 Running backend tests..."
source .venv/bin/activate
.venv/bin/python -m pytest tests/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ Backend tests failed"
    exit 1
fi

# Frontend tests
echo "🎨 Running frontend tests..."
cd src/frontend
npm test -- --watchAll=false
if [ $? -ne 0 ]; then
    echo "❌ Frontend tests failed"
    exit 1
fi
cd ../..

# API tests
echo "🌐 Testing API endpoints..."
health_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health)
if [ "$health_status" != "200" ]; then
    echo "❌ API health check failed"
    exit 1
fi

echo "✅ All tests passed!"
```

```bash
# Make script executable and run
chmod +x test_suite.sh
./test_suite.sh
```

### Performance Test Script
```bash
#!/bin/bash
# performance_test.sh

echo "📊 Running performance tests..."

# API performance test
echo "Testing API performance..."
for endpoint in "health" "instruments" "market-data/1"; do
    echo -n "Testing /api/$endpoint: "
    time_result=$(curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/api/$endpoint)
    echo "$time_result"
done

# WebSocket latency test
echo "Testing WebSocket latency..."
python -c "
import asyncio
import websockets
import time
import json

async def test():
    uri = 'ws://localhost:8000/ws/realtime'
    async with websockets.connect(uri) as ws:
        start = time.time()
        await ws.send(json.dumps({'type': 'ping'}))
        await ws.recv()
        latency = (time.time() - start) * 1000
        print(f'WebSocket latency: {latency:.2f}ms')

asyncio.run(test())
"

echo "✅ Performance tests completed"
```

---

## ✅ Testing Summary

TradeAssist provides comprehensive testing capabilities:

- **🌐 Browser-based testing** for easy API exploration
- **🔌 WebSocket testing** for real-time functionality  
- **🎨 Frontend testing** with React testing utilities
- **🧪 Backend testing** with pytest and coverage
- **📊 Performance validation** with latency measurements
- **🔍 Advanced testing** for security and reliability
- **🚨 Troubleshooting** with detailed diagnostic commands

**Target Performance Metrics:**
- Alert latency: <500ms ✅
- WebSocket updates: <50ms ✅  
- API responses: <100ms ✅
- Database queries: <50ms ✅
- Frontend loading: <2s ✅

Your TradeAssist system is ready for professional trading with comprehensive testing coverage!