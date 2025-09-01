/**
 * Unit tests for runtime type validation utilities
 * 
 * Tests Zod schemas and validation functions to ensure proper runtime
 * type checking and error handling for API responses.
 */

import {
  validateInstrument,
  validateMarketData,
  validateAlertRule,
  validateAlertLog,
  validateHealthStatus,
  validateAnalyticsRequest,
  validatePredictionRequest,
  validateMarketAnalysisResponse,
  validateTechnicalIndicatorResponse,
  validatePredictionResponse,
  safeValidate,
  validateArray,
  validateApiResponse,
  validatePaginatedResponse,
  createValidator,
  createSafeValidator,
  isValidationSuccess,
  extractValidationErrors,
  formatValidationError,
  InstrumentSchema,
  AlertRuleSchema,
  MarketAnalysisResponseSchema,
  TechnicalIndicatorResponseSchema
} from '../typeValidation';

import {
  InstrumentType,
  InstrumentStatus,
  RuleType,
  RuleCondition,
  AlertStatus,
  DeliveryStatus
} from '../../types/models';

describe('Type Validation Utilities', () => {

  describe('validateInstrument', () => {
    test('validates correct instrument data', () => {
      const validInstrument = {
        id: 1,
        symbol: 'ES',
        name: 'E-mini S&P 500',
        type: InstrumentType.FUTURE,
        status: InstrumentStatus.ACTIVE,
        lastTick: '2024-01-01T10:30:00.000Z',
        lastPrice: 4500.50,
        createdAt: '2024-01-01T10:00:00.000Z',
        updatedAt: '2024-01-01T10:30:00.000Z'
      };

      const result = validateInstrument(validInstrument);
      expect(result).toEqual(validInstrument);
    });

    test('validates instrument with optional fields as null', () => {
      const validInstrument = {
        id: 1,
        symbol: 'ES',
        name: 'E-mini S&P 500',
        type: InstrumentType.FUTURE,
        status: InstrumentStatus.ACTIVE,
        lastTick: null,
        lastPrice: null,
        createdAt: '2024-01-01T10:00:00.000Z',
        updatedAt: '2024-01-01T10:30:00.000Z'
      };

      const result = validateInstrument(validInstrument);
      expect(result).toEqual(validInstrument);
    });

    test('throws error for invalid instrument data', () => {
      const invalidInstrument = {
        id: 'not-a-number',
        symbol: 'ES',
        name: 'E-mini S&P 500',
        type: 'invalid-type',
        status: InstrumentStatus.ACTIVE,
        createdAt: 'invalid-date',
        updatedAt: '2024-01-01T10:30:00.000Z'
      };

      expect(() => validateInstrument(invalidInstrument)).toThrow();
    });

    test('throws error for missing required fields', () => {
      const incompleteInstrument = {
        id: 1,
        symbol: 'ES',
        // Missing required fields
      };

      expect(() => validateInstrument(incompleteInstrument)).toThrow();
    });
  });

  describe('validateAlertRule', () => {
    test('validates correct alert rule data', () => {
      const validAlertRule = {
        id: 1,
        instrumentId: 123,
        instrumentSymbol: 'ES',
        ruleType: RuleType.THRESHOLD,
        condition: RuleCondition.ABOVE,
        threshold: 4500.0,
        active: true,
        name: 'ES Above 4500',
        description: 'Alert when ES futures above 4500',
        timeWindowSeconds: 300,
        movingAveragePeriod: 20,
        cooldownSeconds: 60,
        lastTriggered: '2024-01-01T10:30:00.000Z',
        createdAt: '2024-01-01T10:00:00.000Z',
        updatedAt: '2024-01-01T10:30:00.000Z'
      };

      const result = validateAlertRule(validAlertRule);
      expect(result).toEqual(validAlertRule);
    });

    test('validates alert rule with minimal required fields', () => {
      const minimalAlertRule = {
        id: 1,
        instrumentId: 123,
        instrumentSymbol: 'ES',
        ruleType: RuleType.THRESHOLD,
        condition: RuleCondition.ABOVE,
        threshold: 4500.0,
        active: true,
        cooldownSeconds: 60,
        createdAt: '2024-01-01T10:00:00.000Z',
        updatedAt: '2024-01-01T10:30:00.000Z'
      };

      const result = validateAlertRule(minimalAlertRule);
      expect(result).toEqual(minimalAlertRule);
    });

    test('throws error for invalid enum values', () => {
      const invalidAlertRule = {
        id: 1,
        instrumentId: 123,
        instrumentSymbol: 'ES',
        ruleType: 'invalid-rule-type',
        condition: 'invalid-condition',
        threshold: 4500.0,
        active: true,
        cooldownSeconds: 60,
        createdAt: '2024-01-01T10:00:00.000Z',
        updatedAt: '2024-01-01T10:30:00.000Z'
      };

      expect(() => validateAlertRule(invalidAlertRule)).toThrow();
    });
  });

  describe('validateMarketData', () => {
    test('validates complete market data', () => {
      const validMarketData = {
        id: 1,
        timestamp: '2024-01-01T10:30:00.000Z',
        instrumentId: 123,
        price: 4500.50,
        volume: 1000,
        bid: 4500.25,
        ask: 4500.75,
        bidSize: 50,
        askSize: 75,
        openPrice: 4495.00,
        highPrice: 4510.00,
        lowPrice: 4490.00
      };

      const result = validateMarketData(validMarketData);
      expect(result).toEqual(validMarketData);
    });

    test('validates market data with optional fields as null', () => {
      const marketDataWithNulls = {
        id: 1,
        timestamp: '2024-01-01T10:30:00.000Z',
        instrumentId: 123,
        price: null,
        volume: null,
        bid: null,
        ask: null,
        bidSize: null,
        askSize: null,
        openPrice: null,
        highPrice: null,
        lowPrice: null
      };

      const result = validateMarketData(marketDataWithNulls);
      expect(result).toEqual(marketDataWithNulls);
    });
  });

  describe('validateAnalyticsRequest', () => {
    test('validates basic analytics request', () => {
      const validRequest = {
        instrumentId: 123,
        lookbackHours: 24,
        indicators: ['rsi', 'macd']
      };

      const result = validateAnalyticsRequest(validRequest);
      expect(result).toEqual(validRequest);
    });

    test('validates minimal analytics request', () => {
      const minimalRequest = {
        instrumentId: 123
      };

      const result = validateAnalyticsRequest(minimalRequest);
      expect(result).toEqual(minimalRequest);
    });

    test('throws error for invalid lookbackHours range', () => {
      const invalidRequest = {
        instrumentId: 123,
        lookbackHours: 10000 // Too high
      };

      expect(() => validateAnalyticsRequest(invalidRequest)).toThrow();
    });
  });

  describe('validateMarketAnalysisResponse', () => {
    test('validates complete market analysis response', () => {
      const validResponse = {
        trend: 'bullish',
        confidence: 0.85,
        indicators: [
          {
            name: 'RSI',
            value: 65.5,
            timestamp: '2024-01-01T10:30:00.000Z',
            parameters: { period: 14 }
          }
        ],
        timestamp: '2024-01-01T10:30:00.000Z',
        summary: 'Strong bullish trend detected',
        signals: [
          {
            type: 'buy',
            strength: 0.8,
            description: 'RSI indicates oversold conditions'
          }
        ]
      };

      const result = validateMarketAnalysisResponse(validResponse);
      expect(result).toEqual(validResponse);
    });

    test('validates minimal market analysis response', () => {
      const minimalResponse = {
        trend: 'sideways',
        confidence: 0.5,
        indicators: [],
        timestamp: '2024-01-01T10:30:00.000Z'
      };

      const result = validateMarketAnalysisResponse(minimalResponse);
      expect(result).toEqual(minimalResponse);
    });
  });

  describe('validateTechnicalIndicatorResponse', () => {
    test('validates complete technical indicator response', () => {
      const validResponse = {
        indicators: {
          rsi: 65.5,
          macd: {
            macd: 12.5,
            signal: 10.2,
            histogram: 2.3
          },
          bollingerBands: {
            upper: 4520.0,
            middle: 4500.0,
            lower: 4480.0
          },
          movingAverages: {
            sma20: 4495.0,
            sma50: 4485.0,
            ema12: 4502.5,
            ema26: 4498.5
          },
          stochastic: {
            k: 75.5,
            d: 72.3
          },
          atr: 25.8
        },
        timestamp: '2024-01-01T10:30:00.000Z'
      };

      const result = validateTechnicalIndicatorResponse(validResponse);
      expect(result).toEqual(validResponse);
    });

    test('validates minimal technical indicator response', () => {
      const minimalResponse = {
        indicators: {},
        timestamp: '2024-01-01T10:30:00.000Z'
      };

      const result = validateTechnicalIndicatorResponse(minimalResponse);
      expect(result).toEqual(minimalResponse);
    });
  });

  describe('safeValidate', () => {
    test('returns success result for valid data', () => {
      const validData = {
        id: 1,
        symbol: 'ES',
        name: 'E-mini S&P 500',
        type: InstrumentType.FUTURE,
        status: InstrumentStatus.ACTIVE,
        createdAt: '2024-01-01T10:00:00.000Z',
        updatedAt: '2024-01-01T10:30:00.000Z'
      };

      const result = safeValidate(InstrumentSchema, validData);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validData);
      }
    });

    test('returns error result for invalid data', () => {
      const invalidData = {
        id: 'not-a-number',
        symbol: 'ES'
        // Missing required fields
      };

      const result = safeValidate(InstrumentSchema, invalidData);

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBeDefined();
        expect(result.error.errors).toBeInstanceOf(Array);
        expect(result.error.errors.length).toBeGreaterThan(0);
      }
    });
  });

  describe('validateArray', () => {
    test('validates array of valid instruments', () => {
      const instruments = [
        {
          id: 1,
          symbol: 'ES',
          name: 'E-mini S&P 500',
          type: InstrumentType.FUTURE,
          status: InstrumentStatus.ACTIVE,
          createdAt: '2024-01-01T10:00:00.000Z',
          updatedAt: '2024-01-01T10:30:00.000Z'
        },
        {
          id: 2,
          symbol: 'NQ',
          name: 'E-mini Nasdaq',
          type: InstrumentType.FUTURE,
          status: InstrumentStatus.ACTIVE,
          createdAt: '2024-01-01T10:00:00.000Z',
          updatedAt: '2024-01-01T10:30:00.000Z'
        }
      ];

      const result = validateArray(InstrumentSchema, instruments);
      expect(result).toEqual(instruments);
    });

    test('throws error if any item in array is invalid', () => {
      const instruments = [
        {
          id: 1,
          symbol: 'ES',
          name: 'E-mini S&P 500',
          type: InstrumentType.FUTURE,
          status: InstrumentStatus.ACTIVE,
          createdAt: '2024-01-01T10:00:00.000Z',
          updatedAt: '2024-01-01T10:30:00.000Z'
        },
        {
          id: 'invalid',
          symbol: 'NQ'
          // Missing required fields and invalid types
        }
      ];

      expect(() => validateArray(InstrumentSchema, instruments)).toThrow();
    });
  });

  describe('createValidator and createSafeValidator', () => {
    test('createValidator creates working validation function', () => {
      const validateInstrumentCustom = createValidator(InstrumentSchema);
      
      const validData = {
        id: 1,
        symbol: 'ES',
        name: 'E-mini S&P 500',
        type: InstrumentType.FUTURE,
        status: InstrumentStatus.ACTIVE,
        createdAt: '2024-01-01T10:00:00.000Z',
        updatedAt: '2024-01-01T10:30:00.000Z'
      };

      const result = validateInstrumentCustom(validData);
      expect(result).toEqual(validData);
    });

    test('createSafeValidator creates working safe validation function', () => {
      const safeValidateInstrument = createSafeValidator(InstrumentSchema);
      
      const validData = {
        id: 1,
        symbol: 'ES',
        name: 'E-mini S&P 500',
        type: InstrumentType.FUTURE,
        status: InstrumentStatus.ACTIVE,
        createdAt: '2024-01-01T10:00:00.000Z',
        updatedAt: '2024-01-01T10:30:00.000Z'
      };

      const result = safeValidateInstrument(validData);
      expect(result.success).toBe(true);
    });
  });

  describe('isValidationSuccess', () => {
    test('correctly identifies success results', () => {
      const successResult = { success: true as const, data: { test: 'data' } };
      const errorResult = { success: false as const, error: new Error('test') as any };

      expect(isValidationSuccess(successResult)).toBe(true);
      expect(isValidationSuccess(errorResult)).toBe(false);
    });
  });

  describe('extractValidationErrors and formatValidationError', () => {
    test('extracts and formats validation errors', () => {
      const invalidData = {
        id: 'not-a-number',
        symbol: 123, // Should be string
        // Missing required fields
      };

      try {
        validateInstrument(invalidData);
      } catch (error: any) {
        const errorMessages = extractValidationErrors(error);
        expect(errorMessages).toBeInstanceOf(Array);
        expect(errorMessages.length).toBeGreaterThan(0);
        
        const formatted = formatValidationError(error);
        expect(typeof formatted).toBe('string');
        expect(formatted.length).toBeGreaterThan(0);
      }
    });
  });

  describe('Complex validation scenarios', () => {
    test('validates nested analytics response with all optional fields', () => {
      const complexResponse = {
        indicators: {
          rsi: 65.5,
          macd: {
            macd: 12.5,
            signal: 10.2,
            histogram: 2.3
          },
          bollingerBands: {
            upper: 4520.0,
            middle: 4500.0,
            lower: 4480.0
          },
          movingAverages: {
            sma20: 4495.0,
            sma50: 4485.0,
            ema12: 4502.5,
            ema26: 4498.5
          },
          stochastic: {
            k: 75.5,
            d: 72.3
          },
          atr: 25.8
        },
        timestamp: '2024-01-01T10:30:00.000Z'
      };

      expect(() => validateTechnicalIndicatorResponse(complexResponse)).not.toThrow();
    });

    test('handles validation of response with partial nested data', () => {
      const partialResponse = {
        indicators: {
          rsi: 65.5,
          macd: {
            macd: 12.5,
            signal: 10.2,
            histogram: 2.3
          }
          // Other indicators missing
        },
        timestamp: '2024-01-01T10:30:00.000Z'
      };

      expect(() => validateTechnicalIndicatorResponse(partialResponse)).not.toThrow();
    });
  });

  describe('Error handling edge cases', () => {
    test('handles validation of completely wrong data type', () => {
      expect(() => validateInstrument('not-an-object')).toThrow();
      expect(() => validateInstrument(42)).toThrow();
      expect(() => validateInstrument(null)).toThrow();
      expect(() => validateInstrument(undefined)).toThrow();
    });

    test('handles empty objects', () => {
      expect(() => validateInstrument({})).toThrow();
      expect(() => validateAlertRule({})).toThrow();
    });

    test('handles arrays when objects expected', () => {
      expect(() => validateInstrument([])).toThrow();
      expect(() => validateAlertRule(['not', 'an', 'object'])).toThrow();
    });
  });
});