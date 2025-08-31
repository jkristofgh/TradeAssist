# TradeAssist Integration Points

**Generated:** 2025-08-30  
**Target:** src/ directory  
**Analysis Type:** Specific extension and integration opportunities  

## Overview

This document identifies specific points in the TradeAssist codebase where extensions can integrate safely and effectively. Each integration point includes implementation patterns, examples, and compatibility guidelines to ensure seamless extension development.

## API Extension Points

### 1. FastAPI Router Integration

**Integration Pattern:**
```python
# Create new router following established pattern
from fastapi import APIRouter, HTTPException, Depends
from src.backend.models.base import get_db_session

router = APIRouter(prefix="/api/v1/your-extension", tags=["your-extension"])

@router.get("/your-endpoint")
async def your_endpoint(session=Depends(get_db_session)):
    # Implementation following established patterns
    pass
```

**Registration in main.py:**
```python
# Add to src/backend/main.py in create_app()
from .api.your_extension import router as your_extension_router

def create_app() -> FastAPI:
    app = FastAPI(...)
    
    # Include your extension router
    app.include_router(your_extension_router, tags=["your-extension"])
    
    return app
```

**Existing Router Patterns:**
- `src/backend/api/health.py` - Simple monitoring endpoints
- `src/backend/api/instruments.py` - CRUD operations with validation
- `src/backend/api/rules.py` - Complex business logic with caching
- `src/backend/api/analytics.py` - ML/AI endpoint patterns
- `src/backend/api/auth.py` - Authentication flow patterns

**Response Format Standards:**
```python
# Success response pattern
@router.get("/endpoint", response_model=YourResponseModel)
async def endpoint() -> YourResponseModel:
    return YourResponseModel(
        data=result,
        message="Success",
        timestamp=datetime.utcnow()
    )

# Error handling pattern
try:
    result = await your_operation()
    return result
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(
        status_code=400, 
        detail=f"Operation failed: {str(e)}"
    )
```

### 2. Middleware Integration Points

**Custom Middleware Pattern:**
```python
# Add to main.py before router inclusion
from fastapi.middleware.base import BaseHTTPMiddleware

class YourMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Pre-processing
        response = await call_next(request)
        # Post-processing
        return response

# Register in create_app()
app.add_middleware(YourMiddleware)
```

**Existing Middleware:**
- CORS middleware for frontend integration
- Request/response logging (via structlog)
- Error handling middleware (implicit)

### 3. WebSocket Integration

**WebSocket Message Extension:**
```python
# Extend WebSocket message types in src/backend/websocket/realtime.py
class YourMessage(WebSocketMessage):
    message_type: str = "your_message_type"
    data: YourDataModel

# Add handler in handle_client_message()
if message.message_type == "your_message_type":
    await handle_your_message(websocket, message.data)

# Broadcasting pattern
await manager.broadcast_message({
    "message_type": "your_broadcast",
    "data": your_data,
    "timestamp": datetime.utcnow().isoformat()
})
```

**Frontend WebSocket Integration:**
```typescript
// Extend message types in src/frontend/src/types/index.ts
interface YourMessage extends WebSocketIncomingMessage {
  type: 'your_message_type';
  data: YourDataType;
}

// Handle in WebSocketContext.tsx
case 'your_message_type':
  // Handle your message type
  break;
```

## Database Extension Points

### 1. Model Extension Patterns

**New Model Creation:**
```python
# src/backend/models/your_models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class YourModel(Base, TimestampMixin):
    """Your model following established patterns."""
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Foreign key relationships following patterns
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instrument.id"))
    instrument: Mapped["Instrument"] = relationship("Instrument")
    
    def to_dict(self) -> dict:
        # Inherit from Base class
        return super().to_dict()
```

**Pydantic Response Models:**
```python
# Create corresponding Pydantic models for API responses
from pydantic import BaseModel
from datetime import datetime

class YourModelResponse(BaseModel):
    id: int
    name: str
    instrument_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### 2. Database Migration Integration

**Alembic Migration Pattern:**
```python
# Generate migration
alembic revision --autogenerate -m "Add your_model table"

# Migration file pattern (generated)
def upgrade():
    op.create_table(
        'your_model',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('instrument_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['instrument_id'], ['instrument.id']),
        sa.PrimaryKeyConstraint('id')
    )
```

### 3. Database Session Integration

**Using Existing Session Management:**
```python
# Use established session pattern
from src.backend.database.connection import get_db_session

async def your_database_operation():
    async with get_db_session() as session:
        try:
            # Your database operations
            result = await session.execute(your_query)
            await session.commit()
            return result.scalars().all()
        except Exception as e:
            await session.rollback()
            raise
```

## Service Layer Extension Points

### 1. Service Class Pattern

**New Service Implementation:**
```python
# src/backend/services/your_service.py
import asyncio
import structlog
from typing import Optional, List, Dict, Any

logger = structlog.get_logger()

class YourService:
    """
    Your service following established patterns.
    
    Handles business logic for your extension with proper error handling,
    logging, and performance optimization.
    """
    
    def __init__(self):
        self.is_running = False
        self._background_tasks: List[asyncio.Task] = []
    
    async def start(self) -> None:
        """Start the service with proper lifecycle management."""
        if self.is_running:
            logger.warning("Your service already running")
            return
        
        logger.info("Starting your service")
        self.is_running = True
        
        # Initialize background tasks if needed
        task = asyncio.create_task(self._background_loop())
        self._background_tasks.append(task)
        
        logger.info("Your service started successfully")
    
    async def stop(self) -> None:
        """Stop the service gracefully."""
        if not self.is_running:
            return
        
        logger.info("Stopping your service")
        self.is_running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()
        
        logger.info("Your service stopped")
    
    async def _background_loop(self) -> None:
        """Background processing loop following established patterns."""
        while self.is_running:
            try:
                # Your background processing
                await asyncio.sleep(1.0)  # Adjust interval
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background loop: {e}")
                await asyncio.sleep(5.0)  # Error backoff
```

### 2. Service Registration in Lifespan Manager

**Integration into main.py:**
```python
# Add to src/backend/main.py lifespan manager
from .services.your_service import YourService

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # ... existing startup code ...
    
    # Initialize your service
    your_service = YourService()
    await your_service.start()
    
    # Store service instance for shutdown
    app.state.your_service = your_service
    
    yield
    
    # ... existing shutdown code ...
    
    # Stop your service
    await app.state.your_service.stop()
```

### 3. Service Dependency Injection

**Accessing Other Services:**
```python
class YourService:
    def __init__(self):
        # Access existing services through app state
        self.alert_engine = None  # Set during initialization
        self.notification_service = None  # Set during initialization
    
    def set_dependencies(self, alert_engine, notification_service):
        """Set service dependencies (called from main.py)."""
        self.alert_engine = alert_engine
        self.notification_service = notification_service
```

## Frontend Extension Points

### 1. Component Extension Patterns

**New Feature Component:**
```typescript
// src/frontend/src/components/YourFeature/YourComponent.tsx
import React, { useState, useEffect } from 'react';
import { useWebSocketContext } from '../../context/WebSocketContext';
import { apiClient } from '../../services/apiClient';
import { YourDataType } from '../../types';

interface YourComponentProps {
  // Component props
}

const YourComponent: React.FC<YourComponentProps> = ({ /* props */ }) => {
  const { realtimeData, isConnected } = useWebSocketContext();
  const [yourData, setYourData] = useState<YourDataType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    // Load initial data
    const loadData = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get('/your-endpoint');
        setYourData(response.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, []);
  
  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  
  return (
    <div className="your-component">
      {/* Your component JSX */}
    </div>
  );
};

export default YourComponent;
```

### 2. Route Integration

**Adding New Routes:**
```typescript
// Add to src/frontend/src/App.tsx
import YourComponent from './components/YourFeature/YourComponent';

// In the Routes section
<Route path="/your-feature" element={<YourComponent />} />

// Add navigation link
<Link 
  to="/your-feature" 
  className={`nav-link ${location.pathname === '/your-feature' ? 'active' : ''}`}
>
  Your Feature
</Link>
```

### 3. Context Integration

**Creating Feature-Specific Context:**
```typescript
// src/frontend/src/context/YourFeatureContext.tsx
import React, { createContext, useContext, useReducer } from 'react';

interface YourFeatureState {
  // State definition
}

type YourFeatureAction = 
  | { type: 'YOUR_ACTION'; payload: any };

const YourFeatureContext = createContext<{
  state: YourFeatureState;
  dispatch: React.Dispatch<YourFeatureAction>;
} | null>(null);

export const YourFeatureProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(yourFeatureReducer, initialState);
  
  return (
    <YourFeatureContext.Provider value={{ state, dispatch }}>
      {children}
    </YourFeatureContext.Provider>
  );
};

export const useYourFeature = () => {
  const context = useContext(YourFeatureContext);
  if (!context) {
    throw new Error('useYourFeature must be used within YourFeatureProvider');
  }
  return context;
};
```

### 4. Custom Hook Patterns

**Data Fetching Hook:**
```typescript
// src/frontend/src/hooks/useYourData.ts
import { useState, useEffect } from 'react';
import { apiClient } from '../services/apiClient';
import { YourDataType } from '../types';

export const useYourData = (params?: any) => {
  const [data, setData] = useState<YourDataType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/your-endpoint', { params });
      setData(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchData();
  }, [JSON.stringify(params)]);
  
  return { data, loading, error, refetch: fetchData };
};
```

## Configuration Extension Points

### 1. Environment Variable Integration

**Adding New Configuration:**
```python
# src/backend/config.py - Add to Settings class
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Your extension settings
    YOUR_EXTENSION_ENABLED: bool = Field(
        default=True,
        description="Enable your extension"
    )
    YOUR_EXTENSION_API_KEY: str = Field(
        default="",
        description="API key for your extension"
    )
    YOUR_EXTENSION_TIMEOUT: int = Field(
        default=30,
        description="Timeout for your extension operations"
    )
```

**Usage Pattern:**
```python
from src.backend.config import settings

if settings.YOUR_EXTENSION_ENABLED:
    # Your extension logic
    api_key = settings.YOUR_EXTENSION_API_KEY
```

### 2. Frontend Configuration

**Environment Variables:**
```typescript
// Add to src/frontend/.env
REACT_APP_YOUR_FEATURE_ENABLED=true
REACT_APP_YOUR_API_ENDPOINT=http://localhost:8000/api/v1/your-extension

// Usage in components
const isEnabled = process.env.REACT_APP_YOUR_FEATURE_ENABLED === 'true';
const apiEndpoint = process.env.REACT_APP_YOUR_API_ENDPOINT;
```

## Performance Optimization Integration

### 1. Caching Patterns

**Service-Level Caching:**
```python
from typing import Dict, Optional
from datetime import datetime, timedelta

class YourService:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def get_cached_data(self, key: str) -> Optional[Any]:
        """Get data from cache if valid."""
        if key not in self._cache:
            return None
        
        cache_time = self._cache_timestamps.get(key)
        if not cache_time:
            return None
        
        if datetime.utcnow() - cache_time > timedelta(seconds=self._cache_ttl):
            # Cache expired
            del self._cache[key]
            del self._cache_timestamps[key]
            return None
        
        return self._cache[key]
    
    async def set_cached_data(self, key: str, data: Any) -> None:
        """Set data in cache."""
        self._cache[key] = data
        self._cache_timestamps[key] = datetime.utcnow()
```

### 2. Database Query Optimization

**Following Established Patterns:**
```python
# Use selectinload for relationships (following alert_engine.py pattern)
from sqlalchemy.orm import selectinload

result = await session.execute(
    select(YourModel)
    .options(selectinload(YourModel.related_field))
    .where(YourModel.active == True)
    .order_by(YourModel.created_at.desc())
)
```

## Testing Integration Points

### 1. Unit Test Patterns

**Service Testing:**
```python
# src/tests/unit/test_your_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.backend.services.your_service import YourService

class TestYourService:
    @pytest.fixture
    def your_service(self):
        return YourService()
    
    @pytest.mark.asyncio
    async def test_start_service(self, your_service):
        """Test service startup."""
        await your_service.start()
        assert your_service.is_running
        
        # Cleanup
        await your_service.stop()
    
    @pytest.mark.asyncio
    async def test_your_method(self, your_service):
        """Test your service method."""
        # Setup mocks
        your_service.dependency = AsyncMock()
        
        # Execute
        result = await your_service.your_method()
        
        # Assert
        assert result is not None
        your_service.dependency.assert_called_once()
```

### 2. API Test Patterns

**FastAPI Testing:**
```python
# src/tests/integration/test_your_api.py
import pytest
from fastapi.testclient import TestClient
from src.backend.main import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_your_endpoint(client):
    """Test your API endpoint."""
    response = client.get("/api/v1/your-extension/endpoint")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
```

### 3. Frontend Test Patterns

**Component Testing:**
```typescript
// src/frontend/src/components/__tests__/YourComponent.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import YourComponent from '../YourFeature/YourComponent';
import { WebSocketProvider } from '../../context/WebSocketContext';

const MockWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <WebSocketProvider>
    {children}
  </WebSocketProvider>
);

describe('YourComponent', () => {
  it('renders without crashing', () => {
    render(
      <MockWrapper>
        <YourComponent />
      </MockWrapper>
    );
    
    expect(screen.getByText(/your content/i)).toBeInTheDocument();
  });
});
```

## Security Integration Points

### 1. Authentication Integration

**Using Existing Auth Patterns:**
```python
# Follow auth.py patterns for new authentication flows
from src.backend.services.secret_manager import SecretManager

class YourAuthService:
    def __init__(self):
        self.secret_manager = SecretManager()
    
    async def authenticate(self) -> bool:
        """Authenticate using established secret management patterns."""
        api_key = await self.secret_manager.get_secret("your-api-key")
        if not api_key:
            logger.error("API key not found in secret manager")
            return False
        
        # Your authentication logic
        return True
```

### 2. Input Validation

**Pydantic Validation Models:**
```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class YourRequestModel(BaseModel):
    """Request validation following established patterns."""
    
    name: str = Field(..., min_length=1, max_length=255)
    value: float = Field(..., ge=0)
    optional_field: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    class Config:
        str_strip_whitespace = True
```

## Compatibility Guidelines

### 1. Backward Compatibility

- **API Versioning**: Use `/api/v1/` prefix for new endpoints
- **Database Changes**: Always use migrations, never direct schema changes
- **Configuration**: Add new settings with sensible defaults
- **Dependencies**: Check compatibility with existing package versions

### 2. Performance Considerations

- **Database Queries**: Follow established async patterns
- **Caching**: Use existing caching strategies where possible
- **Logging**: Use structlog for consistent logging format
- **Error Handling**: Follow established error response formats

### 3. Code Quality Standards

- **Python**: Follow PEP 8, use type hints, include docstrings
- **TypeScript**: Use strict mode, follow existing component patterns
- **Testing**: Maintain test coverage, follow existing test patterns
- **Documentation**: Update relevant documentation files

This integration guide ensures that extensions seamlessly integrate with the existing TradeAssist architecture while maintaining performance, security, and code quality standards.