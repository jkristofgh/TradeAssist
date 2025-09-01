/**
 * Runtime type validation utilities using Zod
 * 
 * Provides runtime validation for API responses and form data to ensure
 * type safety and catch schema mismatches at runtime.
 */

import { z } from 'zod';
import {
  InstrumentType,
  InstrumentStatus,
  RuleType,
  RuleCondition,
  AlertStatus,
  DeliveryStatus
} from '../types/models';

// =============================================================================
// ZOD ENUM SCHEMAS
// =============================================================================

export const InstrumentTypeSchema = z.nativeEnum(InstrumentType);
export const InstrumentStatusSchema = z.nativeEnum(InstrumentStatus);
export const RuleTypeSchema = z.nativeEnum(RuleType);
export const RuleConditionSchema = z.nativeEnum(RuleCondition);
export const AlertStatusSchema = z.nativeEnum(AlertStatus);
export const DeliveryStatusSchema = z.nativeEnum(DeliveryStatus);

// =============================================================================
// CORE MODEL SCHEMAS
// =============================================================================

export const InstrumentSchema = z.object({
  id: z.number(),
  symbol: z.string(),
  name: z.string(),
  type: InstrumentTypeSchema,
  status: InstrumentStatusSchema,
  lastTick: z.string().datetime().nullable().optional(),
  lastPrice: z.number().nullable().optional(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export const MarketDataSchema = z.object({
  id: z.number(),
  timestamp: z.string().datetime(),
  instrumentId: z.number(),
  price: z.number().nullable().optional(),
  volume: z.number().nullable().optional(),
  bid: z.number().nullable().optional(),
  ask: z.number().nullable().optional(),
  bidSize: z.number().nullable().optional(),
  askSize: z.number().nullable().optional(),
  openPrice: z.number().nullable().optional(),
  highPrice: z.number().nullable().optional(),
  lowPrice: z.number().nullable().optional(),
});

export const AlertRuleSchema = z.object({
  id: z.number(),
  instrumentId: z.number(),
  instrumentSymbol: z.string(),
  ruleType: RuleTypeSchema,
  condition: RuleConditionSchema,
  threshold: z.number(),
  active: z.boolean(),
  name: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  timeWindowSeconds: z.number().nullable().optional(),
  movingAveragePeriod: z.number().nullable().optional(),
  cooldownSeconds: z.number(),
  lastTriggered: z.string().datetime().nullable().optional(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export const AlertLogSchema = z.object({
  id: z.number(),
  timestamp: z.string().datetime(),
  ruleId: z.number(),
  instrumentId: z.number(),
  triggerValue: z.number(),
  thresholdValue: z.number(),
  firedStatus: AlertStatusSchema,
  deliveryStatus: DeliveryStatusSchema,
  evaluationTimeMs: z.number().nullable().optional(),
  ruleCondition: RuleConditionSchema,
  alertMessage: z.string().nullable().optional(),
  errorMessage: z.string().nullable().optional(),
  deliveryAttemptedAt: z.string().datetime().nullable().optional(),
  deliveryCompletedAt: z.string().datetime().nullable().optional(),
});

// =============================================================================
// ANALYTICS SCHEMAS
// =============================================================================

export const AnalyticsRequestSchema = z.object({
  instrumentId: z.number(),
  lookbackHours: z.number().min(1).max(8760).optional(),
  indicators: z.array(z.string()).nullable().optional(),
});

export const PredictionRequestSchema = z.object({
  instrumentId: z.number(),
  predictionHorizon: z.number().positive(),
  modelType: z.string().optional(),
});

export const RiskRequestSchema = z.object({
  instrumentId: z.number(),
  timeframe: z.string().optional(),
  confidenceLevel: z.number().min(0).max(1).optional(),
});

export const StressTestRequestSchema = z.object({
  instrumentId: z.number(),
  scenarios: z.array(z.string()).min(1),
  timeframe: z.string().optional(),
});

export const VolumeProfileRequestSchema = z.object({
  instrumentId: z.number(),
  timeframe: z.string().optional(),
  binSize: z.number().positive().optional(),
});

export const TechnicalIndicatorSchema = z.object({
  name: z.string(),
  value: z.number(),
  timestamp: z.string().datetime(),
  parameters: z.record(z.any()).optional(),
});

export const TechnicalIndicatorResponseSchema = z.object({
  indicators: z.object({
    rsi: z.number().optional(),
    macd: z.object({
      macd: z.number(),
      signal: z.number(),
      histogram: z.number(),
    }).optional(),
    bollingerBands: z.object({
      upper: z.number(),
      middle: z.number(),
      lower: z.number(),
    }).optional(),
    movingAverages: z.object({
      sma20: z.number().optional(),
      sma50: z.number().optional(),
      ema12: z.number().optional(),
      ema26: z.number().optional(),
    }).optional(),
    stochastic: z.object({
      k: z.number(),
      d: z.number(),
    }).optional(),
    atr: z.number().optional(),
  }),
  timestamp: z.string().datetime(),
});

export const MarketAnalysisResponseSchema = z.object({
  trend: z.string(),
  confidence: z.number(),
  indicators: z.array(TechnicalIndicatorSchema),
  timestamp: z.string().datetime(),
  summary: z.string().optional(),
  signals: z.array(z.object({
    type: z.string(),
    strength: z.number(),
    description: z.string(),
  })).optional(),
});

export const PredictionResponseSchema = z.object({
  predictedPrice: z.number(),
  confidence: z.number(),
  modelUsed: z.string(),
  predictionHorizon: z.number(),
  timestamp: z.string().datetime(),
  priceRange: z.object({
    low: z.number(),
    high: z.number(),
  }).optional(),
  factors: z.array(z.object({
    name: z.string(),
    impact: z.number(),
    description: z.string(),
  })).optional(),
});

export const AnomalyDetectionResponseSchema = z.object({
  anomalies: z.array(z.object({
    timestamp: z.string().datetime(),
    value: z.number(),
    anomalyScore: z.number(),
    type: z.string(),
    description: z.string(),
  })),
  overallRisk: z.number(),
  timeframe: z.string(),
});

export const TrendClassificationResponseSchema = z.object({
  trend: z.enum(['bullish', 'bearish', 'sideways']),
  strength: z.number(),
  duration: z.string(),
  confidence: z.number(),
  trendLines: z.array(z.object({
    type: z.enum(['support', 'resistance']),
    slope: z.number(),
    intercept: z.number(),
    confidence: z.number(),
  })).optional(),
  timestamp: z.string().datetime(),
});

export const VarCalculationResponseSchema = z.object({
  var95: z.number(),
  var99: z.number(),
  expectedShortfall: z.number(),
  timeframe: z.string(),
  methodology: z.string(),
  historicalPeriod: z.string(),
  timestamp: z.string().datetime(),
});

export const RiskMetricsResponseSchema = z.object({
  volatility: z.number(),
  sharpeRatio: z.number().optional(),
  maxDrawdown: z.number(),
  beta: z.number().optional(),
  var95: z.number(),
  var99: z.number(),
  timeframe: z.string(),
  timestamp: z.string().datetime(),
});

export const StressTestResponseSchema = z.object({
  scenarios: z.array(z.object({
    name: z.string(),
    description: z.string(),
    pnl: z.number(),
    percentageChange: z.number(),
    probability: z.number(),
  })),
  worstCase: z.object({
    scenario: z.string(),
    pnl: z.number(),
    percentageChange: z.number(),
  }),
  timestamp: z.string().datetime(),
});

export const VolumeProfileResponseSchema = z.object({
  profile: z.array(z.object({
    priceLevel: z.number(),
    volume: z.number(),
    percentage: z.number(),
  })),
  poc: z.number(),
  valueAreaHigh: z.number(),
  valueAreaLow: z.number(),
  valueAreaVolume: z.number(),
  timeframe: z.string(),
  timestamp: z.string().datetime(),
});

export const CorrelationMatrixResponseSchema = z.object({
  correlations: z.record(z.record(z.number())),
  instruments: z.array(z.string()),
  timeframe: z.string(),
  timestamp: z.string().datetime(),
});

export const MarketMicrostructureResponseSchema = z.object({
  bidAskSpread: z.object({
    current: z.number(),
    average: z.number(),
    volatility: z.number(),
  }),
  orderBookImbalance: z.number(),
  priceImpact: z.number(),
  marketDepth: z.object({
    bidDepth: z.number(),
    askDepth: z.number(),
    totalDepth: z.number(),
  }),
  timestamp: z.string().datetime(),
});

// =============================================================================
// API RESPONSE SCHEMAS
// =============================================================================

export const HealthStatusSchema = z.object({
  status: z.enum(['healthy', 'degraded', 'unhealthy']),
  ingestionActive: z.boolean(),
  lastTick: z.string().nullable(),
  apiConnected: z.boolean(),
  activeInstruments: z.number(),
  totalRules: z.number(),
  lastAlert: z.string().nullable(),
  historicalDataService: z.object({
    status: z.enum(['healthy', 'degraded', 'unhealthy']),
    serviceRunning: z.boolean(),
    schwabClientConnected: z.boolean().optional(),
    cacheSize: z.number().optional(),
    totalRequests: z.number().optional(),
    databaseHealthy: z.boolean().optional(),
    dataFreshnessMinutes: z.number().optional(),
    error: z.string().optional(),
  }).nullable().optional(),
});

export const ApiResponseSchema = <T>(dataSchema: z.ZodSchema<T>) => z.object({
  success: z.boolean(),
  data: dataSchema,
  message: z.string().optional(),
  error: z.string().optional(),
});

export const PaginatedResponseSchema = <T>(itemSchema: z.ZodSchema<T>) => z.object({
  items: z.array(itemSchema),
  total: z.number(),
  page: z.number(),
  perPage: z.number(),
  pages: z.number(),
});

// =============================================================================
// VALIDATION FUNCTIONS
// =============================================================================

/**
 * Validate an instrument object
 */
export function validateInstrument(data: unknown) {
  return InstrumentSchema.parse(data);
}

/**
 * Validate market data object
 */
export function validateMarketData(data: unknown) {
  return MarketDataSchema.parse(data);
}

/**
 * Validate alert rule object  
 */
export function validateAlertRule(data: unknown) {
  return AlertRuleSchema.parse(data);
}

/**
 * Validate alert log object
 */
export function validateAlertLog(data: unknown) {
  return AlertLogSchema.parse(data);
}

/**
 * Validate health status object
 */
export function validateHealthStatus(data: unknown) {
  return HealthStatusSchema.parse(data);
}

/**
 * Validate analytics request
 */
export function validateAnalyticsRequest(data: unknown) {
  return AnalyticsRequestSchema.parse(data);
}

/**
 * Validate prediction request
 */
export function validatePredictionRequest(data: unknown) {
  return PredictionRequestSchema.parse(data);
}

/**
 * Validate market analysis response
 */
export function validateMarketAnalysisResponse(data: unknown) {
  return MarketAnalysisResponseSchema.parse(data);
}

/**
 * Validate technical indicator response
 */
export function validateTechnicalIndicatorResponse(data: unknown) {
  return TechnicalIndicatorResponseSchema.parse(data);
}

/**
 * Validate prediction response
 */
export function validatePredictionResponse(data: unknown) {
  return PredictionResponseSchema.parse(data);
}

// =============================================================================
// GENERIC VALIDATION UTILITIES
// =============================================================================

/**
 * Safe validation that returns result with error information
 */
export function safeValidate<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; error: z.ZodError } {
  const result = schema.safeParse(data);
  return result.success
    ? { success: true, data: result.data }
    : { success: false, error: result.error };
}

/**
 * Validate array of items with a schema
 */
export function validateArray<T>(schema: z.ZodSchema<T>, data: unknown[]): T[] {
  return data.map(item => schema.parse(item));
}

/**
 * Validate API response with custom data schema
 */
export function validateApiResponse<T>(
  dataSchema: z.ZodSchema<T>,
  response: unknown
) {
  return ApiResponseSchema(dataSchema).parse(response);
}

/**
 * Validate paginated response with custom item schema
 */
export function validatePaginatedResponse<T>(
  itemSchema: z.ZodSchema<T>,
  response: unknown
) {
  return PaginatedResponseSchema(itemSchema).parse(response);
}

/**
 * Create a validator function for a specific schema
 */
export function createValidator<T>(schema: z.ZodSchema<T>) {
  return (data: unknown): T => schema.parse(data);
}

/**
 * Create a safe validator function for a specific schema
 */
export function createSafeValidator<T>(schema: z.ZodSchema<T>) {
  return (data: unknown) => safeValidate(schema, data);
}

/**
 * Type guard to check if validation result is successful
 */
export function isValidationSuccess<T>(
  result: { success: true; data: T } | { success: false; error: z.ZodError }
): result is { success: true; data: T } {
  return result.success;
}

/**
 * Extract human-readable error messages from Zod validation errors
 */
export function extractValidationErrors(error: z.ZodError): string[] {
  return error.errors.map(err => 
    `${err.path.join('.')}: ${err.message}`
  );
}

/**
 * Format validation error for user display
 */
export function formatValidationError(error: z.ZodError): string {
  const messages = extractValidationErrors(error);
  return messages.length === 1 
    ? messages[0]
    : `Multiple validation errors:\n${messages.map(msg => `• ${msg}`).join('\n')}`;
}