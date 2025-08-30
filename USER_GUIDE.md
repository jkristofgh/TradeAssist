# TradeAssist User Guide

## 🎯 Getting Started

TradeAssist is your real-time trading alerts system with sub-second latency. This guide covers all current features and functionality.

### First Time Setup

1. **Access the Dashboard**: Open http://localhost:8000 in your browser
2. **System Health Check**: Verify all systems are green in the Health panel
3. **Add Instruments**: Add the trading instruments you want to monitor
4. **Create Alert Rules**: Define your first alert conditions
5. **Configure Notifications**: Set up your preferred alert channels

---

## 🏠 Dashboard Overview

### Main Dashboard Components

#### Real-Time Status Panel
- **Connection Status**: API and WebSocket connectivity indicators  
- **System Health**: Database, services, and overall system status
- **Alert Processing**: Live alert count and processing metrics
- **Market Status**: Current market session information

#### Instrument Watchlist
- **Live Prices**: Real-time streaming market data
- **Price Changes**: Visual indicators for price movements
- **Quick Actions**: Add/remove instruments from monitoring
- **Sorting**: Organize instruments by symbol, price, or change

#### Alert History
- **Recent Alerts**: Chronological list of triggered alerts
- **Alert Details**: Timestamps, conditions, and triggered values
- **Filtering**: Search and filter alerts by instrument or type
- **Export**: Download alert history for analysis

---

## 📊 Market Data & Instruments

### Current Supported Instruments

Based on the configuration, TradeAssist currently supports:

#### Futures Contracts
- **ES** - E-mini S&P 500
- **NQ** - E-mini NASDAQ-100
- **YM** - E-mini Dow Jones
- **CL** - Crude Oil
- **GC** - Gold

#### Major Indices
- **SPX** - S&P 500 Index
- **NDX** - NASDAQ-100 Index  
- **RUT** - Russell 2000 Index

#### Market Internals
- **VIX** - Volatility Index
- **TICK** - NYSE Tick Index
- **ADD** - NYSE Advance-Decline
- **TRIN** - Arms Index

### Adding Instruments to Monitor

1. Navigate to the **Dashboard**
2. Use the **Instrument Watchlist** component
3. Add instruments using the interface
4. Configure which instruments to monitor in your `.env` file:
   ```env
   TARGET_FUTURES=ES,NQ,YM,CL,GC
   TARGET_INDICES=SPX,NDX,RUT
   TARGET_INTERNALS=VIX,TICK,ADD,TRIN
   ```

### Watchlist Features
- **Real-time Updates**: Live price streaming
- **Visual Indicators**: Color-coded price changes
- **Quick Access**: Easy instrument selection for alerts
- **Performance Optimized**: Efficient data handling

---

## 🚨 Alert System

### Current Alert Management

#### Rule Management Interface
1. Navigate to **Rules** section in the dashboard
2. View existing alert rules
3. Create, edit, or delete rules
4. Enable/disable rules as needed

#### Alert Rule Configuration
The system supports configurable alert rules with:
- **Instrument Selection**: Choose from monitored instruments
- **Condition Settings**: Define trigger conditions
- **Message Customization**: Personalize alert messages
- **Channel Selection**: Choose notification methods

#### Alert History Tracking
- **Chronological Display**: View alerts in time order
- **Detailed Information**: See trigger conditions and values
- **Filtering Options**: Search by instrument, time, or condition
- **Performance Metrics**: Track alert frequency and patterns

### Alert Rule Types

#### 1. Price-Based Rules
- **Threshold Alerts**: Price above/below specific levels
- **Percentage Change**: Price moved X% from reference
- **Support/Resistance**: Price approaching key levels
- **Gap Alerts**: Opening gaps above threshold

#### 2. Technical Indicator Rules
- **RSI Alerts**: Overbought (>70) or oversold (<30) conditions
- **Moving Average**: Price crossing above/below MA
- **MACD Signals**: Bullish/bearish crossovers
- **Bollinger Bands**: Price touching upper/lower bands
- **Volume Indicators**: Above/below average volume

#### 3. Market Condition Rules
- **Volatility Alerts**: VIX above/below thresholds
- **Market Breadth**: Advance/decline ratios
- **Sector Rotation**: Relative strength changes
- **Market Sentiment**: Fear/greed indicators

#### 4. Risk Management Rules
- **Position Limits**: Maximum exposure warnings
- **Correlation Alerts**: High correlation between positions
- **Drawdown Warnings**: Portfolio decline thresholds
- **Margin Alerts**: Margin usage warnings

### Current Alert Channels

#### In-App Notifications
- **Dashboard Alerts**: Real-time notifications within the web interface
- **Toast Notifications**: Pop-up alerts using React Toastify
- **Alert History**: Comprehensive logging of all triggered alerts
- **Visual Indicators**: Real-time status updates in the UI

#### Slack Integration (Configurable)
Configure in your `.env` file:
```env
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_CHANNEL=#trading-alerts
```

#### Sound Alerts (Configurable) 
Enable in your `.env` file:
```env
SOUND_ALERTS_ENABLED=true
```
- **Browser-based**: Sound alerts play through the web interface
- **Customizable**: Configure different sounds for different alert types

### Managing Active Alerts

#### Alert History
- **View all alerts** with timestamps and details
- **Filter by instrument**, type, or date range
- **Export alerts** to CSV for analysis
- **Alert performance** tracking

#### Alert Rules Management
- **Enable/Disable rules** without deleting
- **Edit existing rules** with live preview
- **Duplicate rules** for similar setups
- **Rule templates** for common patterns

---

## 📈 Advanced Analytics

### Market Analytics Dashboard

#### Technical Indicators
- **Moving Averages**: SMA, EMA, WMA with customizable periods
- **Oscillators**: RSI, Stochastic, Williams %R
- **Momentum**: MACD, Rate of Change, ADX
- **Volatility**: Bollinger Bands, ATR, Volatility Index

#### Volume Analysis
- **Volume Profile**: Price-volume distribution
- **Volume Weighted Average Price (VWAP)**
- **On-Balance Volume (OBV)**
- **Volume Rate of Change**

#### Market Sentiment
- **VIX Analysis**: Fear and greed indicators
- **Put/Call Ratios**: Market sentiment metrics
- **Advance/Decline**: Market breadth indicators
- **High/Low Index**: Market strength analysis

### Risk Analysis Tools

#### Portfolio Risk Metrics
- **Value at Risk (VaR)**: Portfolio risk estimation
- **Beta Analysis**: Market correlation
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Worst-case scenarios

#### Correlation Analysis
- **Inter-instrument correlations**
- **Sector correlation heatmaps**
- **Rolling correlation analysis**
- **Correlation breakdown alerts**

### Predictive Models

#### Machine Learning Features
- **Price Prediction Models**: Short-term price forecasting
- **Volatility Forecasting**: Expected volatility ranges
- **Trend Analysis**: Trend strength and direction
- **Pattern Recognition**: Automated chart pattern detection

#### Model Performance
- **Prediction accuracy** tracking
- **Model confidence** indicators
- **Historical performance** analysis
- **Model retraining** schedules

---

## ⚡ Real-Time Features

### WebSocket Data Streaming

#### Live Data Updates
- **Sub-second latency** for market data
- **Real-time alert delivery**
- **Live system status updates**
- **Streaming chart updates**

#### Connection Management
- **Automatic reconnection** on connection loss
- **Connection status indicators**
- **Data quality monitoring**
- **Failover mechanisms**

### Performance Optimization

#### Alert Processing
- **Target latency**: <500ms from data to alert
- **Concurrent processing**: Multiple alerts simultaneously
- **Queue management**: Prioritized alert processing
- **Performance monitoring**: Real-time latency tracking

#### Data Efficiency
- **Selective subscriptions**: Only requested instruments
- **Data compression**: Optimized data transmission
- **Caching strategies**: Frequently accessed data
- **Memory management**: Efficient resource usage

---

## 🔧 System Configuration

### Notification Settings

#### Global Settings
```
Sound Enabled: Yes
Default Volume: 80%
Quiet Hours: 6 PM - 6 AM
Max Alerts per Minute: 10
```

#### Channel-Specific Settings
```
In-App Notifications:
  - Show popups: Yes
  - Auto-dismiss time: 10 seconds
  - Max visible alerts: 5

Slack Notifications:
  - Enabled: Yes
  - Channel: #alerts
  - Include charts: Yes
  - Mention users: @trader

Sound Notifications:
  - Alert sound: alert.wav
  - Volume: 80%
  - Different sounds per type: Yes
```

### Performance Settings

#### Alert Engine Configuration
```
Alert Latency Target: 500ms
Max Concurrent Alerts: 50
Alert Batch Size: 100
Queue Size: 1000
```

#### Data Processing
```
Market Data Buffer: 1000 ticks
Update Frequency: Real-time
Chart Update Interval: 100ms
History Retention: 30 days
```

### System Monitoring

#### Health Checks
- **Database connectivity**
- **Schwab API status**
- **WebSocket connections**
- **Alert processing latency**
- **Memory and CPU usage**

#### Performance Metrics
- **Alert processing times**
- **API response latencies**
- **WebSocket message rates**
- **Database query performance**

---

## 🐛 Troubleshooting

### Common Issues

#### No Real-Time Data
**Symptoms**: Charts not updating, no price feeds
**Solutions**:
1. Check Schwab API connection in Health panel
2. Verify API credentials in settings
3. Check internet connectivity
4. Restart the application

#### Alerts Not Triggering
**Symptoms**: Price conditions met but no alerts
**Solutions**:
1. Verify alert rules are enabled
2. Check rule conditions and syntax
3. Review notification channel settings
4. Check alert history for processing errors

#### High Alert Latency
**Symptoms**: Alerts delayed >1 second
**Solutions**:
1. Check system resources (CPU, memory)
2. Reduce number of active rules
3. Optimize alert conditions
4. Check network latency

#### WebSocket Connection Issues
**Symptoms**: Disconnection messages, no real-time updates
**Solutions**:
1. Check firewall settings
2. Verify WebSocket port availability
3. Review proxy/VPN settings
4. Restart browser/application

### Getting Help

#### Log Analysis
```bash
# Check application logs
tail -f logs/tradeassist.log

# Filter for errors
grep "ERROR" logs/tradeassist.log

# Monitor alert processing
grep "Alert processed" logs/tradeassist.log
```

#### System Diagnostics
- **Health endpoint**: http://localhost:8000/api/health
- **API documentation**: http://localhost:8000/docs
- **WebSocket test**: Use browser developer tools

#### Support Resources
1. **System Health Dashboard**: Real-time system status
2. **API Documentation**: Complete API reference
3. **Log Files**: Detailed error tracking
4. **Performance Metrics**: System performance analysis

---

## 📱 Mobile Access

### Responsive Design
- **Mobile-optimized dashboard**
- **Touch-friendly controls**
- **Responsive charts and data**
- **Mobile notifications** (if configured)

### Mobile Features
- **Quick alert overview**
- **Essential system status**
- **Alert acknowledgment**
- **Emergency stop/start controls**

---

## 🔒 Security Best Practices

### API Security
- **Secure credential storage** in Google Cloud Secret Manager
- **Token rotation** for Schwab API
- **HTTPS enforcement** for all communications
- **API rate limiting** protection

### System Security
- **Firewall configuration** for required ports only
- **Regular security updates**
- **Log monitoring** for suspicious activity
- **Backup encryption** for sensitive data

---

## 🚀 Advanced Usage

### Custom Alert Logic
```python
# Example: Custom technical analysis alert
def custom_rsi_divergence_alert(data):
    """
    Alert when price makes higher high but RSI makes lower high
    """
    price_trend = analyze_price_trend(data['price'])
    rsi_trend = analyze_rsi_trend(data['rsi'])
    
    if price_trend == 'higher_high' and rsi_trend == 'lower_high':
        return create_alert("RSI Bearish Divergence Detected")
```

### API Integration
```javascript
// Custom dashboard widgets
const customWidget = {
    fetchData: async () => {
        const response = await fetch('/api/custom-metrics');
        return response.json();
    },
    render: (data) => {
        // Custom visualization logic
    }
};
```

### Automation Scripts
```bash
# Automated trading session management
./scripts/market_open_setup.sh   # Run at market open
./scripts/market_close_cleanup.sh # Run at market close
```

---

## 📊 Performance Optimization Tips

### Optimal Configuration
1. **Limit active instruments** to those actively traded
2. **Use specific alert conditions** rather than broad ranges
3. **Set appropriate notification limits** to avoid spam
4. **Regular database maintenance** for optimal performance

### Resource Management
1. **Monitor system resources** during peak hours
2. **Archive old alert data** regularly
3. **Optimize WebSocket subscriptions**
4. **Use efficient chart timeframes**

### Best Practices
1. **Test alert rules** with paper trading first
2. **Use alert templates** for consistency
3. **Regular backup schedules**
4. **Keep software updated**

---

TradeAssist provides professional-grade trading alerts with enterprise reliability. Use this guide to maximize the system's potential for your trading strategy!