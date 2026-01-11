/**
 * Parses a URL parameter string to a valid number.
 * Returns null if the parameter is undefined, empty, or not a valid number.
 *
 * @param param - The URL parameter string to parse
 * @returns The parsed number or null if invalid
 *
 * @example
 * ```ts
 * parseNumericParam("123") // 123
 * parseNumericParam("abc") // null
 * parseNumericParam(undefined) // null
 * parseNumericParam("") // null
 * ```
 */
export function parseNumericParam(param: string | undefined): number | null {
  if (!param || param.trim() === '') {
    return null;
  }

  const parsed = Number(param);

  if (Number.isNaN(parsed) || !Number.isFinite(parsed)) {
    return null;
  }

  return parsed;
}

/**
 * Type guard to check if a value is a valid numeric ID (positive integer)
 *
 * @param value - The value to check
 * @returns True if the value is a positive integer
 */
export function isValidId(value: number | null): value is number {
  return value !== null && Number.isInteger(value) && value > 0;
}
