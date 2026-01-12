/**
 * Parameter type inference utilities for URL/Parameter display improvement.
 */

export type ParameterType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'encoded'
  | 'json'
  | 'empty';

/**
 * Infers the type of a parameter value.
 *
 * Detection order (priority):
 * 1. empty - null, undefined, empty string
 * 2. encoded - contains URL encoding (%XX pattern)
 * 3. json - valid JSON object or array
 * 4. boolean - "true" or "false" (case insensitive)
 * 5. number - valid numeric value
 * 6. string - fallback for everything else
 *
 * @param value - The parameter value to analyze
 * @returns The inferred type
 *
 * @example
 * ```ts
 * inferType(null)           // 'empty'
 * inferType('%2F')          // 'encoded'
 * inferType('{"a":1}')      // 'json'
 * inferType('true')         // 'boolean'
 * inferType('123')          // 'number'
 * inferType('hello')        // 'string'
 * ```
 */
export function inferType(value: unknown): ParameterType {
  // 1. Check for empty values
  if (value === null || value === undefined || value === '') {
    return 'empty';
  }

  // Convert to string for analysis
  const str = String(value);

  // 2. Check for URL encoded values (%XX pattern)
  // Must have valid hex digits after %
  if (/%[0-9A-Fa-f]{2}/.test(str)) {
    return 'encoded';
  }

  // 3. Check for JSON (object or array)
  if (
    (str.startsWith('{') && str.endsWith('}')) ||
    (str.startsWith('[') && str.endsWith(']'))
  ) {
    try {
      JSON.parse(str);
      return 'json';
    } catch {
      // Not valid JSON, continue to other checks
    }
  }

  // 4. Check for boolean
  if (str.toLowerCase() === 'true' || str.toLowerCase() === 'false') {
    return 'boolean';
  }

  // 5. Check for number (including scientific notation)
  if (str.trim() !== '' && !isNaN(Number(str)) && isFinite(Number(str))) {
    return 'number';
  }

  // 6. Fallback to string
  return 'string';
}

/**
 * Formats a parameters object for display in the asset table.
 *
 * @param parameters - The parameters object (key-value pairs)
 * @returns Formatted string like "name <type>, name2 <type>" or "-" if empty
 *
 * @example
 * ```ts
 * formatParameters({ redirect: '%2F', count: '10' })
 * // 'redirect <encoded>, count <number>'
 *
 * formatParameters({ a: '1', b: '2', c: '3', d: '4' })
 * // 'a <number>, b <number>, c <number> +1 more'
 * ```
 */
export function formatParameters(
  parameters: Record<string, unknown> | null | undefined
): string {
  if (!parameters || typeof parameters !== 'object') {
    return '-';
  }

  const entries = Object.entries(parameters);

  if (entries.length === 0) {
    return '-';
  }

  const MAX_DISPLAY = 3;
  const displayEntries = entries.slice(0, MAX_DISPLAY);
  const remainingCount = entries.length - MAX_DISPLAY;

  const formatted = displayEntries
    .map(([key, value]) => `${key} <${inferType(value)}>`)
    .join(', ');

  if (remainingCount > 0) {
    return `${formatted} +${remainingCount} more`;
  }

  return formatted;
}
