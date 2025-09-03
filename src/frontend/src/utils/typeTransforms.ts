/**
 * Type transformation utilities for TradeAssist Frontend
 * 
 * Provides utilities for converting between snake_case (backend) and camelCase (frontend)
 * field names, along with datetime normalization to ISO format.
 */

/**
 * Convert snake_case object to camelCase
 * Handles nested objects and arrays recursively
 * 
 * @param obj - Object with snake_case keys to convert
 * @returns Object with camelCase keys
 */
export function snakeToCamel(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj;
  }
  
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
 * Handles nested objects and arrays recursively
 * 
 * @param obj - Object with camelCase keys to convert  
 * @returns Object with snake_case keys
 */
export function camelToSnake(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj;
  }
  
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
 * Ensures consistent datetime handling across the application
 * 
 * @param dateValue - Date value to normalize (string, Date, or other)
 * @returns ISO 8601 formatted datetime string
 * @throws Error if dateValue cannot be converted to valid date
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

/**
 * Transform datetime fields in an object to ISO format
 * Commonly used datetime field names are automatically detected and normalized
 * 
 * @param obj - Object that may contain datetime fields
 * @param dateFields - Optional array of field names to treat as dates
 * @returns Object with normalized datetime fields
 */
export function normalizeDateTimeFields(
  obj: any,
  dateFields?: string[]
): any {
  if (!obj || typeof obj !== 'object') {
    return obj;
  }

  // Handle arrays by applying normalization to each item
  if (Array.isArray(obj)) {
    return obj.map(item => normalizeDateTimeFields(item, dateFields));
  }

  const commonDateFields = [
    'createdAt', 'updatedAt', 'timestamp', 'lastTick', 'lastTriggered',
    'deliveryAttemptedAt', 'deliveryCompletedAt', 'created_at', 'updated_at',
    'last_tick', 'last_triggered', 'delivery_attempted_at', 'delivery_completed_at'
  ];
  
  const fieldsToNormalize = dateFields || commonDateFields;
  const result = { ...obj };
  
  for (const field of fieldsToNormalize) {
    if (result[field] && typeof result[field] === 'string') {
      try {
        result[field] = normalizeDateTime(result[field]);
      } catch (error) {
        // If normalization fails, leave the field as-is
        console.warn(`Failed to normalize datetime field '${field}':`, error);
      }
    }
  }
  
  return result;
}

/**
 * Transform API response from backend format to frontend format
 * Converts snake_case to camelCase and normalizes datetime fields
 * 
 * @param data - Backend API response data
 * @returns Frontend-formatted data with camelCase keys and normalized datetimes
 */
export function transformApiResponse<T>(data: any): T {
  if (!data) {
    return data;
  }
  
  // First convert field names from snake_case to camelCase
  const camelCased = snakeToCamel(data);
  
  // Then normalize datetime fields
  const normalized = normalizeDateTimeFields(camelCased);
  
  return normalized as T;
}

/**
 * Transform frontend request data to backend format
 * Converts camelCase to snake_case for API requests
 * 
 * @param data - Frontend request data with camelCase keys
 * @returns Backend-formatted data with snake_case keys
 */
export function transformApiRequest(data: any): any {
  if (!data) {
    return data;
  }
  
  return camelToSnake(data);
}

/**
 * Type-safe transformation for known model types
 * Provides additional type safety for specific model transformations
 */
export class TypedTransformer {
  /**
   * Transform AlertRule from backend to frontend format
   */
  static transformAlertRule(backendRule: any): any {
    const transformed = transformApiResponse(backendRule) as any;
    
    // Ensure instrumentSymbol is included (may be derived from instrument.symbol)
    if (!transformed.instrumentSymbol && transformed.instrument?.symbol) {
      transformed.instrumentSymbol = transformed.instrument.symbol;
    }
    
    return transformed;
  }
  
  /**
   * Transform MarketData from backend to frontend format  
   */
  static transformMarketData(backendData: any): any {
    return transformApiResponse(backendData);
  }
  
  /**
   * Transform Instrument from backend to frontend format
   */
  static transformInstrument(backendInstrument: any): any {
    return transformApiResponse(backendInstrument);
  }
  
  /**
   * Transform AlertLog from backend to frontend format
   */
  static transformAlertLog(backendLog: any): any {
    return transformApiResponse(backendLog);
  }
  
  /**
   * Transform analytics responses from backend to frontend format
   */
  static transformAnalyticsResponse<T>(backendResponse: any): T {
    return transformApiResponse<T>(backendResponse);
  }
}

/**
 * Utility to safely extract error messages from API responses
 * Handles both transformed and untransformed error responses
 */
export function extractErrorMessage(error: any): string {
  if (typeof error === 'string') {
    return error;
  }
  
  if (error?.message) {
    return error.message;
  }
  
  if (error?.detail) {
    return error.detail;
  }
  
  if (error?.error) {
    return error.error;
  }
  
  return 'An unknown error occurred';
}

/**
 * Type guard to check if a value is a valid datetime string
 */
export function isValidDateTimeString(value: any): value is string {
  if (typeof value !== 'string') {
    return false;
  }
  
  const date = new Date(value);
  return !isNaN(date.getTime());
}

/**
 * Batch transform multiple items with the same transformation function
 */
export function batchTransform<T, U>(
  items: T[],
  transformer: (item: T) => U
): U[] {
  if (!Array.isArray(items)) {
    return [];
  }
  
  return items.map(transformer);
}