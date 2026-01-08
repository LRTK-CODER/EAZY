/**
 * Parse HTTP body string to object if valid JSON, otherwise return original string
 *
 * This utility handles HTTP request/response bodies that may be stored as JSON strings
 * in the database. It attempts to parse the string as JSON and returns the parsed object
 * for pretty-printing. If parsing fails, it returns the original string.
 *
 * @param body - HTTP body content (string or null)
 * @returns Parsed JSON object/array, original string, or null
 *
 * @example
 * // Valid JSON string → Object
 * parseJsonBody('{"key": "value"}') // { key: "value" }
 *
 * @example
 * // Invalid JSON → Original string
 * parseJsonBody('plain text') // "plain text"
 *
 * @example
 * // Null input → null
 * parseJsonBody(null) // null
 *
 * @example
 * // Empty string → Empty string
 * parseJsonBody('') // ""
 */
export function parseJsonBody(body: string | null): string | object | null {
  // Handle null input
  if (body === null) {
    return null;
  }

  // Handle empty string (preserve as-is)
  if (body === '') {
    return '';
  }

  // Handle non-string types (defensive programming)
  if (typeof body !== 'string') {
    return body;
  }

  // Attempt JSON parsing
  try {
    const parsed = JSON.parse(body);
    return parsed;
  } catch (error) {
    // Parsing failed - return original string
    return body;
  }
}
