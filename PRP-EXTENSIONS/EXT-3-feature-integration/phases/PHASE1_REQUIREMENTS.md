# Phase 1: Type System Foundation & Model Alignment

## Phase Overview
- **Phase Name**: Type System Foundation & Model Alignment  
- **Phase Number**: 1 of 4
- **Estimated Duration**: 5-7 days
- **Implementation Effort**: 25% of total extension
- **Primary Focus**: Create type-safe foundation for all backend-frontend communication

## Phase Objectives

### Primary Goals
1. **Eliminate Type Safety Violations**: Remove all 'as any' type casting between backend and frontend
2. **Create Comprehensive Type Definitions**: TypeScript interfaces for all backend Pydantic models  
3. **Implement Field Transformation**: Utilities for snake_case ↔ camelCase conversion
4. **Standardize DateTime Handling**: Consistent ISO format across all timestamps
5. **Fix Existing Model Mismatches**: Add missing fields and align existing interfaces

### Success Criteria
- [ ] Zero TypeScript compilation errors in existing codebase
- [ ] All backend Pydantic models have matching TypeScript interfaces
- [ ] Case conversion utilities handle all field transformations correctly  
- [ ] Missing `instrument_symbol` field added to AlertRule interface
- [ ] DateTime handling standardized to ISO format across all models

## Technical Requirements

### Backend Analysis & Type Extraction

#### 1. Pydantic Model Analysis
```bash
# Extract all Pydantic models from backend codebase
- src/backend/models/alert_rules.py → AlertRule, AlertLog models
- src/backend/models/market_data.py → MarketData, Instrument models  
- src/backend/models/historical_data.py → HistoricalData models
- src/backend/api/analytics.py → All analytics request/response models
- src/backend/api/auth.py → Authentication models
```

#### 2. Field Mapping Analysis
```python
# Identify all field naming patterns requiring transformation
Backend (snake_case) → Frontend (camelCase):
- created_at → createdAt
- updated_at → updatedAt  
- instrument_id → instrumentId
- rule_type → ruleType
- alert_condition → alertCondition
- target_value → targetValue
```

### Frontend Type System Implementation

#### 1. Core Type Definitions
```typescript
// src/frontend/src/types/models.ts
// Complete type definitions extracted from backend Pydantic models

interface AlertRule {
  id: number;
  instrumentId: number;
  instrumentSymbol: string; // MISSING FIELD TO ADD
  name: string;
  ruleType: AlertRuleType;
  condition: AlertCondition;  
  targetValue: number;
  isActive: boolean;
  createdAt: string; // ISO datetime string
  updatedAt: string; // ISO datetime string
}

interface MarketData {
  id: number;
  instrumentId: number;
  timestamp: string; // ISO datetime string
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface Instrument {
  id: number;
  symbol: string;
  name: string;
  description?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// Analytics Request/Response Models (extracted from backend)
interface AnalyticsRequest {
  instrumentId: number;
  timeframe?: string;
  parameters?: Record<string, any>;
}

interface MarketAnalysisResponse {
  trend: string;
  confidence: number;
  indicators: TechnicalIndicator[];
  timestamp: string;
}

interface TechnicalIndicatorResponse {
  indicators: {
    rsi?: number;
    macd?: {
      macd: number;
      signal: number;
      histogram: number;
    };
    bollingerBands?: {
      upper: number;
      middle: number;
      lower: number;
    };
  };
  timestamp: string;
}

interface PredictionRequest {
  instrumentId: number;
  predictionHorizon: number; // hours
  modelType?: string;
}

interface PredictionResponse {
  predictedPrice: number;
  confidence: number;
  modelUsed: string;
  predictionHorizon: number;
  timestamp: string;
}
```

#### 2. Field Transformation Utilities
```typescript
// src/frontend/src/utils/typeTransforms.ts

type CamelCase<S extends string> = S extends `${infer P1}_${infer P2}${infer P3}`
  ? `${P1}${Capitalize<CamelCase<`${P2}${P3}`>>}`
  : S;

type SnakeCase<S extends string> = S extends `${infer T}${infer U}`
  ? `${T extends Capitalize<T> ? "_" : ""}${Lowercase<T>}${SnakeCase<U>}`
  : S;

/**
 * Convert snake_case object to camelCase
 */
export function snakeToCamel<T extends Record<string, any>>(obj: T): any {
  if (obj === null || obj === undefined) return obj;
  
  if (Array.isArray(obj)) {
    return obj.map(item => snakeToCamel(item));
  }
  
  if (typeof obj === 'object' && obj.constructor === Object) {
    const result: any = {};
    for (const [key, value] of Object.entries(obj)) {
      const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
      result[camelKey] = snakeToCamel(value);
    }
    return result;
  }
  
  return obj;
}

/**
 * Convert camelCase object to snake_case  
 */
export function camelToSnake<T extends Record<string, any>>(obj: T): any {
  if (obj === null || obj === undefined) return obj;
  
  if (Array.isArray(obj)) {
    return obj.map(item => camelToSnake(item));
  }
  
  if (typeof obj === 'object' && obj.constructor === Object) {
    const result: any = {};
    for (const [key, value] of Object.entries(obj)) {
      const snakeKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
      result[snakeKey] = camelToSnake(value);
    }
    return result;
  }
  
  return obj;
}

/**
 * Validate and transform datetime strings to ISO format
 */
export function normalizeDateTime(dateValue: any): string {
  if (typeof dateValue === 'string') {
    const date = new Date(dateValue);
    if (!isNaN(date.getTime())) {
      return date.toISOString();
    }
  }
  
  if (dateValue instanceof Date) {
    return dateValue.toISOString();
  }
  
  throw new Error(`Invalid datetime value: ${dateValue}`);
}
```

#### 3. API Client Type Integration
```typescript  
// src/frontend/src/services/apiClient.ts - Enhanced with type safety

export class ApiClient {
  // ... existing implementation ...

  private transformResponse<T>(data: any): T {
    // Apply field transformation and datetime normalization
    const transformed = snakeToCamel(data);
    
    // Normalize datetime fields if present
    if (transformed.createdAt) {
      transformed.createdAt = normalizeDateTime(transformed.createdAt);
    }
    if (transformed.updatedAt) {
      transformed.updatedAt = normalizeDateTime(transformed.updatedAt);
    }
    
    return transformed as T;
  }

  private transformRequest(data: any): any {
    // Convert camelCase to snake_case for backend
    return camelToSnake(data);
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    // ... existing request logic ...
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new ApiError(
        response.status,
        errorData.message || errorData.detail || 'Request failed',
        this.transformResponse(errorData) // Transform error data too
      );
    }

    const responseData = await response.json();
    return this.transformResponse<T>(responseData);
  }

  // Update existing methods with proper typing
  async getAlertRules(filters?: AlertRuleFilters): Promise<AlertRule[]> {
    const transformedFilters = this.transformRequest(filters || {});
    return this.get<AlertRule[]>('/api/rules', transformedFilters);
  }

  async createAlertRule(data: CreateAlertRuleRequest): Promise<AlertRule> {
    const transformedData = this.transformRequest(data);
    return this.post<AlertRule>('/api/rules', transformedData);
  }
}
```

#### 4. Runtime Type Validation
```typescript
// src/frontend/src/utils/typeValidation.ts

import { z } from 'zod';

// Zod schemas for runtime validation
export const AlertRuleSchema = z.object({
  id: z.number(),
  instrumentId: z.number(),
  instrumentSymbol: z.string(),
  name: z.string(),
  ruleType: z.enum(['price_above', 'price_below', 'volume_spike']),
  condition: z.enum(['greater_than', 'less_than', 'equals']),
  targetValue: z.number(),
  isActive: z.boolean(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export const MarketDataSchema = z.object({
  id: z.number(),
  instrumentId: z.number(),
  timestamp: z.string().datetime(),
  open: z.number(),
  high: z.number(),
  low: z.number(),
  close: z.number(),
  volume: z.number(),
});

// Validation utilities
export function validateAlertRule(data: unknown): AlertRule {
  return AlertRuleSchema.parse(data);
}

export function validateMarketData(data: unknown): MarketData {
  return MarketDataSchema.parse(data);
}
```

### Model Alignment Fixes

#### 1. AlertRule Interface Enhancement
```typescript
// Add missing instrument_symbol field to existing AlertRule interface
interface AlertRule {
  // ... existing fields ...
  instrumentSymbol: string; // NEW REQUIRED FIELD
}

// Update related interfaces that depend on AlertRule
interface CreateAlertRuleRequest {
  instrumentId: number;
  instrumentSymbol: string; // NEW FIELD
  name: string;
  ruleType: AlertRuleType;
  condition: AlertCondition;
  targetValue: number;
  isActive?: boolean;
}

interface UpdateAlertRuleRequest {
  name?: string;
  instrumentSymbol?: string; // NEW OPTIONAL FIELD
  ruleType?: AlertRuleType;
  condition?: AlertCondition;
  targetValue?: number;
  isActive?: boolean;
}
```

#### 2. DateTime Standardization
```typescript
// Ensure all datetime fields use consistent ISO string format
interface TimestampMixin {
  createdAt: string; // Always ISO 8601 format: "2024-12-15T10:30:00.000Z"
  updatedAt: string; // Always ISO 8601 format: "2024-12-15T10:30:00.000Z"
}

// Apply to all models that inherit timestamp mixin
interface AlertRule extends TimestampMixin {
  // ... other fields ...
}

interface MarketData {
  // ... other fields ...
  timestamp: string; // ISO 8601 format for market data timestamps
}
```

## Implementation Tasks

### Task 1: Backend Model Analysis (Day 1)
1. **Extract All Pydantic Models**
   - Scan all backend files for Pydantic model definitions
   - Document field names, types, and validation rules  
   - Identify inheritance relationships and mixins
   - Create comprehensive model inventory

2. **Field Mapping Documentation**
   - Create snake_case to camelCase mapping table
   - Identify special cases requiring custom transformation
   - Document datetime field handling requirements

### Task 2: TypeScript Interface Creation (Days 2-3)
1. **Create Core Model Interfaces**
   - Implement all extracted interfaces in `src/frontend/src/types/models.ts`
   - Ensure exact type matching with backend Pydantic models
   - Add missing fields identified in analysis

2. **Create Request/Response Interfaces**
   - Implement all API request interfaces
   - Implement all API response interfaces  
   - Ensure type consistency across all endpoints

### Task 3: Transformation Utilities Implementation (Day 4)
1. **Implement Field Transformation**
   - Create `snakeToCamel` utility with comprehensive testing
   - Create `camelToSnake` utility with comprehensive testing
   - Handle nested objects and arrays correctly

2. **Implement DateTime Normalization**
   - Create `normalizeDateTime` utility
   - Handle various input formats consistently
   - Ensure ISO 8601 output format

### Task 4: API Client Integration (Day 5)
1. **Update API Client with Transformations**
   - Integrate transformation utilities into request/response pipeline
   - Update all existing API methods with proper typing
   - Remove all 'as any' type casting

2. **Add Runtime Type Validation**
   - Implement Zod schemas for critical models
   - Add validation to API client response handling
   - Provide helpful error messages for type mismatches

### Task 5: Testing & Validation (Days 6-7)
1. **Unit Testing**
   - Test transformation utilities with various input scenarios
   - Test datetime normalization with edge cases
   - Test API client type integration

2. **Integration Testing**  
   - Verify all existing API calls work with new type system
   - Test field transformation in real API responses
   - Validate TypeScript compilation with strict mode

3. **Type Safety Validation**
   - Ensure zero TypeScript compilation errors
   - Verify no 'as any' casting remains in codebase
   - Test type checking in IDE for proper intellisense

## Dependencies and Prerequisites

### Required Before Phase 1
- [x] Comprehensive PRP completed with technical architecture
- [x] Backend analytics endpoints functional (Phase 4 baseline)
- [x] Frontend development environment set up with TypeScript strict mode

### Phase 1 Provides to Phase 2
- Complete TypeScript interfaces for analytics request/response models
- Field transformation utilities for API client integration  
- Type-safe foundation for extending API client with analytics methods

## Testing Requirements

### Unit Tests Required
```typescript
// Test transformation utilities
describe('Type Transformations', () => {
  test('snakeToCamel converts nested objects correctly', () => {
    const input = { user_id: 1, created_at: '2024-01-01', nested_obj: { inner_field: 'value' } };
    const expected = { userId: 1, createdAt: '2024-01-01', nestedObj: { innerField: 'value' } };
    expect(snakeToCamel(input)).toEqual(expected);
  });

  test('camelToSnake converts nested objects correctly', () => {
    const input = { userId: 1, createdAt: '2024-01-01', nestedObj: { innerField: 'value' } };
    const expected = { user_id: 1, created_at: '2024-01-01', nested_obj: { inner_field: 'value' } };
    expect(camelToSnake(input)).toEqual(expected);
  });

  test('normalizeDateTime handles various formats', () => {
    expect(normalizeDateTime('2024-01-01T10:30:00Z')).toBe('2024-01-01T10:30:00.000Z');
    expect(normalizeDateTime(new Date('2024-01-01'))).toMatch(/2024-01-01T\d{2}:\d{2}:\d{2}.\d{3}Z/);
  });
});
```

### Integration Tests Required
```typescript  
// Test API client integration
describe('API Client Type Integration', () => {
  test('getAlertRules returns properly typed and transformed data', async () => {
    const rules = await apiClient.getAlertRules();
    expect(rules[0]).toMatchObject({
      id: expect.any(Number),
      instrumentId: expect.any(Number),
      instrumentSymbol: expect.any(String),
      createdAt: expect.stringMatching(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z/)
    });
  });
});
```

## Phase 1 Completion Criteria

### Functional Completion
- [ ] All backend Pydantic models have corresponding TypeScript interfaces
- [ ] Field transformation utilities handle all identified patterns correctly
- [ ] DateTime handling consistently produces ISO 8601 format
- [ ] Missing `instrument_symbol` field added to AlertRule and related interfaces
- [ ] API client integrates transformation utilities without breaking existing functionality

### Technical Validation  
- [ ] TypeScript compilation passes in strict mode with zero errors
- [ ] No 'as any' type casting remains in existing codebase  
- [ ] All existing API methods work with enhanced type system
- [ ] Runtime type validation catches schema mismatches
- [ ] Comprehensive test coverage for transformation utilities

### Integration Readiness
- [ ] Type definitions ready for Phase 2 analytics API client extension
- [ ] Transformation utilities available for complex analytics response handling
- [ ] Type-safe foundation established for WebSocket message typing in Phase 3
- [ ] Error handling enhanced with proper type information

**Phase 1 Success Metric**: Zero TypeScript compilation errors + Complete type safety for all existing API interactions + Foundation ready for analytics integration