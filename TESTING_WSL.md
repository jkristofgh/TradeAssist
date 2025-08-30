# TradeAssist Testing Guide for WSL Ubuntu

This guide covers comprehensive testing methods for the TradeAssist application running on WSL Ubuntu, including API testing, WebSocket testing, frontend validation, and troubleshooting.

## 🚀 **Quick Start Testing**

### 1. **Start the Backend Server**

```bash
# Activate virtual environment
source .venv/bin/activate

# Start the backend using the runner script (recommended)
python run.py
```

**Alternative methods:**
```bash
# Method 1: Using Python module
python -m src.backend.main

# Method 2: Using uvicorn directly
uvicorn src.backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The server will start on `http://localhost:8000`

**Expected startup output:**
```
INFO: TradeAssist starting up...
INFO: Database connection established
INFO: WebSocket manager initialized
INFO: Application startup complete
INFO: Uvicorn running on http://127.0.0.1:8000
```

## 🌐 **Browser-Based Testing** (Easiest Method)

Since WSL shares networking with Windows, you can test directly from Windows browsers:

### Interactive API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health

### Testing in Swagger UI
1. Open http://localhost:8000/docs
2. Click on any endpoint (e.g., `/api/health`)
3. Click **"Try it out"**
4. Click **"Execute"** to test the API
5. View the response

## 📡 **Command Line API Testing**

### Method 1: Using curl (Built-in)

```bash
# Health check
curl http://localhost:8000/api/health

# Get all instruments
curl http://localhost:8000/api/instruments

# Get system analytics
curl http://localhost:8000/api/analytics

# Create a test alert rule
curl -X POST http://localhost:8000/api/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ES Test Alert",
    "instrument_id": "ES",
    "condition_type": "price_above",
    "threshold_value": 4500.0,
    "enabled": true,
    "message": "ES above 4500!"
  }'

# Get all alert rules
curl http://localhost:8000/api/rules

# Get alert history
curl http://localhost:8000/api/alerts
```

### Method 2: Using HTTPie (Recommended)

Install HTTPie for better API testing experience:

```bash
# Install HTTPie
pip install httpie

# Basic API tests
http GET localhost:8000/api/health
http GET localhost:8000/api/instruments
http GET localhost:8000/api/rules
http GET localhost:8000/api/alerts

# Create test data
http POST localhost:8000/api/rules \
  name="Test Price Alert" \
  instrument_id="ES" \
  condition_type="price_above" \
  threshold_value:=4500.0 \
  enabled:=true \
  message="ES crossed 4500"

# Update a rule (replace {rule_id} with actual ID)
http PUT localhost:8000/api/rules/{rule_id} \
  enabled:=false

# Delete a rule
http DELETE localhost:8000/api/rules/{rule_id}
```

### Method 3: Python Requests

```python
import requests
import json

# Test health endpoint
response = requests.get("http://localhost:8000/api/health")
print(f"Health Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Create test alert rule
rule_data = {
    "name": "Python Test Alert",
    "instrument_id": "NQ",
    "condition_type": "price_below",
    "threshold_value": 15000.0,
    "enabled": True,
    "message": "NQ below 15000"
}

response = requests.post("http://localhost:8000/api/rules", json=rule_data)
print(f"Rule Creation: {response.status_code}")
if response.status_code == 201:
    print(f"Created rule: {response.json()}")
```

## 🔌 **WebSocket Testing**

### Method 1: Using wscat (Node.js)

Install wscat:
```bash
# Install Node.js if not present
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install wscat globally
npm install -g wscat

# Test WebSocket connection
wscat -c ws://localhost:8000/ws

# Once connected, you can send messages:
# {"type": "subscribe", "channels": ["market_data", "alerts"]}
# {"type": "ping"}
```

### Method 2: Python WebSocket Client

```bash
# Install websockets if not present
pip install websockets

# Create and run test script
cat > test_websocket.py << 'EOF'
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket!")
            
            # Send subscription message
            subscribe_msg = {
                "type": "subscribe",
                "channels": ["market_data", "alerts", "system_status"]
            }
            await websocket.send(json.dumps(subscribe_msg))
            print("📡 Sent subscription message")
            
            # Listen for messages (timeout after 10 seconds)
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    print(f"📨 Received: {message}")
            except asyncio.TimeoutError:
                print("⏰ No messages received within timeout")
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
EOF

# Run the WebSocket test
python test_websocket.py
```

### Method 3: Browser Console WebSocket Test

Open browser console at http://localhost:8000/docs and run:

```javascript
// Test WebSocket connection from browser
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
    console.log('✅ WebSocket connected');
    ws.send(JSON.stringify({
        type: 'subscribe',
        channels: ['market_data', 'alerts']
    }));
};

ws.onmessage = function(event) {
    console.log('📨 Received:', event.data);
};

ws.onerror = function(error) {
    console.log('❌ WebSocket error:', error);
};

ws.onclose = function() {
    console.log('🔌 WebSocket disconnected');
};
```

## 🎨 **Frontend Testing**

### Option 1: Build and Serve Frontend (Production Mode)

```bash
# Install Node.js dependencies
cd src/frontend
npm install

# Build the frontend
npm run build

# Return to project root and restart (serves built frontend)
cd ../..
python run.py

# Access full application at http://localhost:8000
```

### Option 2: Development Server (Development Mode)

```bash
# Terminal 1: Start backend
cd src/backend
python main.py

# Terminal 2: Start frontend dev server
cd src/frontend
npm install
npm start

# Frontend available at http://localhost:3000
# Backend API at http://localhost:8000
```

### Frontend Testing Checklist

When frontend is running, test these features:

- [ ] **Dashboard loads** without errors
- [ ] **Real-time status** shows connected
- [ ] **Instrument list** displays correctly
- [ ] **Alert rules** can be created/edited
- [ ] **Alert history** shows test alerts
- [ ] **WebSocket connection** indicator is green
- [ ] **Responsive design** works on different window sizes

## 🧪 **Automated Testing**

### Unit Tests

```bash
# Run all unit tests
python -m pytest src/tests/unit/ -v

# Run specific test files
python -m pytest src/tests/unit/test_models.py -v
python -m pytest src/tests/unit/test_services.py -v
python -m pytest src/tests/unit/test_api.py -v

# Run with coverage report
python -m pytest src/tests/unit/ --cov=src --cov-report=html --cov-report=term-missing

# View coverage report
firefox htmlcov/index.html  # Or open in Windows browser
```

### Integration Tests

```bash
# Run integration tests
python -m pytest src/tests/integration/ -v

# Test specific integration scenarios
python -m pytest src/tests/integration/test_api.py::TestAPIIntegration::test_create_alert_rule -v
```

### Performance Tests

```bash
# Run performance benchmarks
python -m pytest src/tests/performance/ -v

# Run stress tests
python -m pytest src/tests/performance/test_benchmarks.py::TestAlertProcessingPerformance -v
```

## 🗄️ **Database Testing**

### SQLite Database Inspection

```bash
# Install SQLite CLI (if not present)
sudo apt update && sudo apt install sqlite3

# Open database
sqlite3 data/trade_assist.db

# Basic database exploration
.tables                           # List all tables
.schema instruments              # Show table schema
.schema alert_rules             # Show alert rules table
SELECT * FROM instruments LIMIT 5;   # View sample data
SELECT * FROM alert_rules;           # View alert rules
SELECT * FROM alert_logs LIMIT 10;  # View recent alerts
.quit                               # Exit
```

### Database Test Script

```bash
# Create database test script
cat > test_database.py << 'EOF'
import asyncio
import sqlite3
from pathlib import Path

async def test_database():
    db_path = "data/trade_assist.db"
    
    if not Path(db_path).exists():
        print(f"❌ Database not found at {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Database tables: {[table[0] for table in tables]}")
        
        # Test instruments table
        cursor.execute("SELECT COUNT(*) FROM instruments;")
        instrument_count = cursor.fetchone()[0]
        print(f"📊 Instruments count: {instrument_count}")
        
        # Test alert_rules table
        cursor.execute("SELECT COUNT(*) FROM alert_rules;")
        rules_count = cursor.fetchone()[0]
        print(f"⚠️ Alert rules count: {rules_count}")
        
        # Test alert_logs table
        cursor.execute("SELECT COUNT(*) FROM alert_logs;")
        alerts_count = cursor.fetchone()[0]
        print(f"📈 Alert logs count: {alerts_count}")
        
        conn.close()
        print("✅ Database test completed successfully")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_database())
EOF

# Run database test
python test_database.py
```

## 📊 **System Monitoring & Logging**

### Real-time Log Monitoring

```bash
# Monitor application logs (if logging to file)
tail -f logs/tradeassist.log

# Monitor specific log levels
tail -f logs/tradeassist.log | grep ERROR
tail -f logs/tradeassist.log | grep "Alert processed"

# Monitor system resources
htop  # Install with: sudo apt install htop

# Monitor network connections
netstat -tlnp | grep :8000
ss -tlnp | grep :8000
```

### Performance Monitoring

```bash
# Monitor Python process
ps aux | grep python
top -p $(pgrep -f "main.py")

# Memory usage
free -h
cat /proc/meminfo | grep Available

# Disk usage
df -h
du -sh data/
```

## 🔧 **Troubleshooting Common Issues**

### Issue 1: Port Already in Use

```bash
# Check what's using port 8000
sudo netstat -tlnp | grep :8000
sudo ss -tlnp sport = :8000

# Kill process using port 8000
sudo lsof -ti:8000 | xargs kill -9

# Or run on different port (from project root)
python -c "
import uvicorn
from src.backend.main import app
uvicorn.run(app, host='0.0.0.0', port=8001)
"
```

### Issue 2: Database Connection Issues

```bash
# Check database file permissions
ls -la data/trade_assist.db

# Recreate database if corrupted
rm data/trade_assist.db
alembic upgrade head
```

### Issue 3: WebSocket Connection Failed

```bash
# Test local WebSocket
telnet localhost 8000

# Check firewall (if applicable)
sudo ufw status

# Test from Windows side
# Use browser console: new WebSocket('ws://localhost:8000/ws')
```

### Issue 4: Windows Browser Can't Reach WSL

```bash
# Start server on all interfaces (from project root)
python -c "
import uvicorn
from src.backend.main import app
uvicorn.run(app, host='0.0.0.0', port=8000)
"

# Get WSL IP address
ip addr show eth0 | grep inet
# Then use WSL IP in Windows browser: http://172.x.x.x:8000
```

### Issue 5: Frontend Build Issues

```bash
# Clear npm cache
cd src/frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 16+
npm --version

# Install specific Node.js version if needed
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

## ✅ **Testing Checklist**

### Basic Functionality
- [ ] Backend starts without errors
- [ ] Health endpoint returns 200 OK
- [ ] Database connection successful
- [ ] WebSocket connection established
- [ ] API endpoints respond correctly
- [ ] CORS headers present for frontend

### API Testing
- [ ] GET endpoints return data
- [ ] POST endpoints create resources
- [ ] PUT endpoints update resources  
- [ ] DELETE endpoints remove resources
- [ ] Error handling returns appropriate codes
- [ ] Request validation works

### WebSocket Testing
- [ ] Connection establishes successfully
- [ ] Subscription messages work
- [ ] Real-time updates received
- [ ] Connection recovery on disconnect
- [ ] Multiple clients supported

### Frontend Testing (if built)
- [ ] Dashboard loads completely
- [ ] All components render
- [ ] WebSocket connection indicator
- [ ] Form submissions work
- [ ] Real-time updates display
- [ ] Mobile responsive design

### Performance Testing
- [ ] Alert processing <500ms
- [ ] API response times <200ms
- [ ] WebSocket message latency low
- [ ] Memory usage stable
- [ ] No memory leaks detected

### Security Testing
- [ ] CORS properly configured
- [ ] No sensitive data in responses
- [ ] Input validation working
- [ ] Error messages don't leak info
- [ ] Headers properly set

## 🎯 **Recommended Testing Sequence**

1. **Quick Health Check**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Interactive API Testing**
   - Open http://localhost:8000/docs
   - Test each endpoint manually

3. **WebSocket Testing**
   ```bash
   wscat -c ws://localhost:8000/ws
   ```

4. **Automated Tests**
   ```bash
   python -m pytest src/tests/unit/ -v
   ```

5. **Load Testing** (if needed)
   ```bash
   pip install locust
   # Create locustfile.py for load testing
   ```

This comprehensive testing guide ensures your TradeAssist application is thoroughly validated on WSL Ubuntu before moving to production deployment.

## 🔗 **Additional Resources**

- **API Documentation**: http://localhost:8000/docs
- **Application Logs**: `logs/tradeassist.log`
- **Database**: `data/trade_assist.db`
- **Configuration**: `.env` file
- **Source Code**: `src/` directory

**Happy Testing! 🚀**