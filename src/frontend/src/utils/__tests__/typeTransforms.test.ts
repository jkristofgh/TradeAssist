/**
 * Unit tests for type transformation utilities
 * 
 * Tests the snake_case <-> camelCase conversion functions and datetime normalization
 * to ensure proper data transformation between backend and frontend.
 */

import {
  snakeToCamel,
  camelToSnake,
  normalizeDateTime,
  normalizeDateTimeFields,
  transformApiResponse,
  transformApiRequest,
  TypedTransformer,
  extractErrorMessage,
  isValidDateTimeString,
  batchTransform
} from '../typeTransforms';

describe('Type Transformation Utilities', () => {
  
  describe('snakeToCamel', () => {
    test('converts simple snake_case keys to camelCase', () => {
      const input = {
        user_id: 1,
        created_at: '2024-01-01',
        is_active: true
      };
      
      const expected = {
        userId: 1,
        createdAt: '2024-01-01',
        isActive: true
      };
      
      expect(snakeToCamel(input)).toEqual(expected);
    });

    test('converts nested objects correctly', () => {
      const input = {
        user_id: 1,
        created_at: '2024-01-01',
        nested_obj: {
          inner_field: 'value',
          deep_nested: {
            very_deep_field: 42
          }
        }
      };
      
      const expected = {
        userId: 1,
        createdAt: '2024-01-01',
        nestedObj: {
          innerField: 'value',
          deepNested: {
            veryDeepField: 42
          }
        }
      };
      
      expect(snakeToCamel(input)).toEqual(expected);
    });

    test('converts arrays of objects correctly', () => {
      const input = [
        { user_id: 1, created_at: '2024-01-01' },
        { user_id: 2, created_at: '2024-01-02' }
      ];
      
      const expected = [
        { userId: 1, createdAt: '2024-01-01' },
        { userId: 2, createdAt: '2024-01-02' }
      ];
      
      expect(snakeToCamel(input)).toEqual(expected);
    });

    test('handles null and undefined values', () => {
      expect(snakeToCamel(null as any)).toBeNull();
      expect(snakeToCamel(undefined as any)).toBeUndefined();
    });

    test('handles non-object values', () => {
      expect(snakeToCamel('string' as any)).toBe('string');
      expect(snakeToCamel(42 as any)).toBe(42);
      expect(snakeToCamel(true as any)).toBe(true);
    });

    test('handles complex AlertRule-like objects', () => {
      const input = {
        id: 1,
        instrument_id: 123,
        rule_type: 'threshold',
        created_at: '2024-01-01T10:30:00Z',
        time_window_seconds: 300,
        moving_average_period: 20
      };
      
      const expected = {
        id: 1,
        instrumentId: 123,
        ruleType: 'threshold',
        createdAt: '2024-01-01T10:30:00Z',
        timeWindowSeconds: 300,
        movingAveragePeriod: 20
      };
      
      expect(snakeToCamel(input)).toEqual(expected);
    });
  });

  describe('camelToSnake', () => {
    test('converts simple camelCase keys to snake_case', () => {
      const input = {
        userId: 1,
        createdAt: '2024-01-01',
        isActive: true
      };
      
      const expected = {
        user_id: 1,
        created_at: '2024-01-01',
        is_active: true
      };
      
      expect(camelToSnake(input)).toEqual(expected);
    });

    test('converts nested objects correctly', () => {
      const input = {
        userId: 1,
        createdAt: '2024-01-01',
        nestedObj: {
          innerField: 'value',
          deepNested: {
            veryDeepField: 42
          }
        }
      };
      
      const expected = {
        user_id: 1,
        created_at: '2024-01-01',
        nested_obj: {
          inner_field: 'value',
          deep_nested: {
            very_deep_field: 42
          }
        }
      };
      
      expect(camelToSnake(input)).toEqual(expected);
    });

    test('converts arrays of objects correctly', () => {
      const input = [
        { userId: 1, createdAt: '2024-01-01' },
        { userId: 2, createdAt: '2024-01-02' }
      ];
      
      const expected = [
        { user_id: 1, created_at: '2024-01-01' },
        { user_id: 2, created_at: '2024-01-02' }
      ];
      
      expect(camelToSnake(input)).toEqual(expected);
    });

    test('handles null and undefined values', () => {
      expect(camelToSnake(null as any)).toBeNull();
      expect(camelToSnake(undefined as any)).toBeUndefined();
    });

    test('handles complex request objects', () => {
      const input = {
        instrumentId: 123,
        instrumentSymbol: 'ES',
        ruleType: 'threshold',
        timeWindowSeconds: 300,
        movingAveragePeriod: 20
      };
      
      const expected = {
        instrument_id: 123,
        instrument_symbol: 'ES',
        rule_type: 'threshold',
        time_window_seconds: 300,
        moving_average_period: 20
      };
      
      expect(camelToSnake(input)).toEqual(expected);
    });
  });

  describe('normalizeDateTime', () => {
    test('normalizes valid datetime strings', () => {
      const inputs = [
        '2024-01-01T10:30:00Z',
        '2024-01-01T10:30:00.000Z',
        '2024-01-01 10:30:00',
        '2024-01-01'
      ];
      
      inputs.forEach(input => {
        const result = normalizeDateTime(input);
        expect(result).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
        expect(new Date(result).toISOString()).toBe(result);
      });
    });

    test('normalizes Date objects', () => {
      const date = new Date('2024-01-01T10:30:00Z');
      const result = normalizeDateTime(date);
      
      expect(result).toBe('2024-01-01T10:30:00.000Z');
    });

    test('throws error for invalid datetime values', () => {
      const invalidInputs = [
        'invalid-date',
        'not-a-date',
        '',
        42,
        null,
        undefined,
        {}
      ];
      
      invalidInputs.forEach(input => {
        expect(() => normalizeDateTime(input)).toThrow();
      });
    });
  });

  describe('normalizeDateTimeFields', () => {
    test('normalizes common datetime fields', () => {
      const input = {
        id: 1,
        createdAt: '2024-01-01 10:30:00',
        updatedAt: '2024-01-02T15:45:00Z',
        timestamp: '2024-01-03',
        lastTick: '2024-01-04T08:00:00',
        regularField: 'not-a-date'
      };
      
      const result = normalizeDateTimeFields(input);
      
      expect(result.id).toBe(1);
      expect(result.regularField).toBe('not-a-date');
      expect(result.createdAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
      expect(result.updatedAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
      expect(result.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
      expect(result.lastTick).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
    });

    test('normalizes custom datetime fields', () => {
      const input = {
        customDate: '2024-01-01 10:30:00',
        otherField: 'value'
      };
      
      const result = normalizeDateTimeFields(input, ['customDate']);
      
      expect(result.customDate).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
      expect(result.otherField).toBe('value');
    });

    test('handles invalid datetime fields gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      const input = {
        createdAt: 'invalid-date',
        validField: 'value'
      };
      
      const result = normalizeDateTimeFields(input);
      
      expect(result.createdAt).toBe('invalid-date'); // Should remain unchanged
      expect(result.validField).toBe('value');
      expect(consoleSpy).toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });
  });

  describe('transformApiResponse', () => {
    test('transforms complete API response', () => {
      const backendResponse = {
        id: 1,
        instrument_id: 123,
        rule_type: 'threshold',
        created_at: '2024-01-01 10:30:00',
        updated_at: '2024-01-02T15:45:00Z',
        is_active: true
      };
      
      const result = transformApiResponse(backendResponse);
      
      expect(result).toEqual({
        id: 1,
        instrumentId: 123,
        ruleType: 'threshold',
        createdAt: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/),
        updatedAt: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/),
        isActive: true
      });
    });

    test('handles null/undefined responses', () => {
      expect(transformApiResponse(null)).toBeNull();
      expect(transformApiResponse(undefined)).toBeUndefined();
    });
  });

  describe('transformApiRequest', () => {
    test('transforms frontend request to backend format', () => {
      const frontendRequest = {
        instrumentId: 123,
        instrumentSymbol: 'ES',
        ruleType: 'threshold',
        isActive: true,
        timeWindowSeconds: 300
      };
      
      const result = transformApiRequest(frontendRequest);
      
      expect(result).toEqual({
        instrument_id: 123,
        instrument_symbol: 'ES',
        rule_type: 'threshold',
        is_active: true,
        time_window_seconds: 300
      });
    });

    test('handles null/undefined requests', () => {
      expect(transformApiRequest(null)).toBeNull();
      expect(transformApiRequest(undefined)).toBeUndefined();
    });
  });

  describe('TypedTransformer', () => {
    test('transforms AlertRule with instrumentSymbol derivation', () => {
      const backendRule = {
        id: 1,
        instrument_id: 123,
        rule_type: 'threshold',
        created_at: '2024-01-01T10:30:00Z',
        instrument: {
          symbol: 'ES'
        }
      };
      
      const result = TypedTransformer.transformAlertRule(backendRule);
      
      expect(result.instrumentId).toBe(123);
      expect(result.ruleType).toBe('threshold');
      expect(result.instrumentSymbol).toBe('ES');
    });

    test('transforms analytics responses', () => {
      const backendResponse = {
        predicted_price: 4500.50,
        confidence: 0.85,
        model_used: 'lstm',
        prediction_horizon: 24,
        timestamp: '2024-01-01T10:30:00Z'
      };
      
      const result = TypedTransformer.transformAnalyticsResponse(backendResponse);
      
      expect(result).toEqual({
        predictedPrice: 4500.50,
        confidence: 0.85,
        modelUsed: 'lstm',
        predictionHorizon: 24,
        timestamp: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/)
      });
    });
  });

  describe('extractErrorMessage', () => {
    test('extracts string messages', () => {
      expect(extractErrorMessage('Simple error')).toBe('Simple error');
    });

    test('extracts message property', () => {
      expect(extractErrorMessage({ message: 'Error message' })).toBe('Error message');
    });

    test('extracts detail property', () => {
      expect(extractErrorMessage({ detail: 'Error detail' })).toBe('Error detail');
    });

    test('extracts error property', () => {
      expect(extractErrorMessage({ error: 'Error text' })).toBe('Error text');
    });

    test('returns default for unknown errors', () => {
      expect(extractErrorMessage({})).toBe('An unknown error occurred');
      expect(extractErrorMessage(null)).toBe('An unknown error occurred');
      expect(extractErrorMessage(undefined)).toBe('An unknown error occurred');
    });
  });

  describe('isValidDateTimeString', () => {
    test('validates valid datetime strings', () => {
      const validDates = [
        '2024-01-01T10:30:00Z',
        '2024-01-01T10:30:00.000Z',
        '2024-12-31T23:59:59Z'
      ];
      
      validDates.forEach(date => {
        expect(isValidDateTimeString(date)).toBe(true);
      });
    });

    test('rejects invalid datetime strings', () => {
      const invalidDates = [
        'invalid-date',
        '2024-13-01T10:30:00Z', // Invalid month
        '2024-01-32T10:30:00Z', // Invalid day
        42,
        null,
        undefined,
        {}
      ];
      
      invalidDates.forEach(date => {
        expect(isValidDateTimeString(date)).toBe(false);
      });
    });
  });

  describe('batchTransform', () => {
    test('transforms array of items with transformer function', () => {
      const items = [
        { user_id: 1, created_at: '2024-01-01' },
        { user_id: 2, created_at: '2024-01-02' }
      ];
      
      const result = batchTransform(items, (item: any) => snakeToCamel(item));
      
      expect(result).toEqual([
        { userId: 1, createdAt: '2024-01-01' },
        { userId: 2, createdAt: '2024-01-02' }
      ]);
    });

    test('handles non-array inputs', () => {
      expect(batchTransform(null as any, (item: any) => snakeToCamel(item))).toEqual([]);
      expect(batchTransform(undefined as any, (item: any) => snakeToCamel(item))).toEqual([]);
      expect(batchTransform('not-array' as any, (item: any) => snakeToCamel(item))).toEqual([]);
    });

    test('handles empty arrays', () => {
      expect(batchTransform([], (item: any) => snakeToCamel(item))).toEqual([]);
    });
  });

  describe('Round-trip conversions', () => {
    test('snake_case -> camelCase -> snake_case preserves data', () => {
      const original = {
        user_id: 1,
        created_at: '2024-01-01T10:30:00Z',
        nested_obj: {
          inner_field: 'value',
          time_window_seconds: 300
        }
      };
      
      const roundTrip = camelToSnake(snakeToCamel(original));
      
      expect(roundTrip).toEqual(original);
    });

    test('camelCase -> snake_case -> camelCase preserves data', () => {
      const original = {
        userId: 1,
        createdAt: '2024-01-01T10:30:00Z',
        nestedObj: {
          innerField: 'value',
          timeWindowSeconds: 300
        }
      };
      
      const roundTrip = snakeToCamel(camelToSnake(original));
      
      expect(roundTrip).toEqual(original);
    });
  });

  describe('Edge cases', () => {
    test('handles objects with numeric keys', () => {
      const input = {
        1: 'numeric key',
        normal_key: 'normal value'
      };
      
      const result = snakeToCamel(input);
      
      expect(result).toEqual({
        1: 'numeric key',
        normalKey: 'normal value'
      });
    });

    test('handles objects with special characters', () => {
      const input = {
        'field_with_underscore': 'value',
        'field-with-dash': 'value',
        'field.with.dot': 'value'
      };
      
      const result = snakeToCamel(input);
      
      expect(result).toEqual({
        fieldWithUnderscore: 'value',
        'field-with-dash': 'value',
        'field.with.dot': 'value'
      });
    });

    test('handles very large objects', () => {
      const largeObject: any = {};
      for (let i = 0; i < 1000; i++) {
        largeObject[`field_${i}`] = `value_${i}`;
      }
      
      const result = snakeToCamel(largeObject);
      
      expect(Object.keys(result)).toHaveLength(1000);
      expect(result.field0).toBe('value_0');
      expect(result.field999).toBe('value_999');
    });
  });
});