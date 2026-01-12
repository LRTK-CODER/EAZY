import { describe, it, expect } from 'vitest';
import { inferType, formatParameters } from './parameterType';

describe('inferType', () => {
  describe('empty values', () => {
    it('should return "empty" for null', () => {
      expect(inferType(null)).toBe('empty');
    });

    it('should return "empty" for undefined', () => {
      expect(inferType(undefined)).toBe('empty');
    });

    it('should return "empty" for empty string', () => {
      expect(inferType('')).toBe('empty');
    });
  });

  describe('boolean values', () => {
    it('should return "boolean" for "true"', () => {
      expect(inferType('true')).toBe('boolean');
    });

    it('should return "boolean" for "false"', () => {
      expect(inferType('false')).toBe('boolean');
    });

    it('should return "boolean" for "TRUE" (case insensitive)', () => {
      expect(inferType('TRUE')).toBe('boolean');
    });

    it('should return "boolean" for "False" (case insensitive)', () => {
      expect(inferType('False')).toBe('boolean');
    });
  });

  describe('number values', () => {
    it('should return "number" for integer string', () => {
      expect(inferType('123')).toBe('number');
    });

    it('should return "number" for negative integer', () => {
      expect(inferType('-456')).toBe('number');
    });

    it('should return "number" for decimal string', () => {
      expect(inferType('3.14')).toBe('number');
    });

    it('should return "number" for zero', () => {
      expect(inferType('0')).toBe('number');
    });
  });

  describe('encoded values', () => {
    it('should return "encoded" for URL encoded string with %XX', () => {
      expect(inferType('%2F')).toBe('encoded');
    });

    it('should return "encoded" for string containing %20', () => {
      expect(inferType('hello%20world')).toBe('encoded');
    });

    it('should return "encoded" for complex encoded string', () => {
      expect(inferType('%2Fpayments%3Fid%3D123')).toBe('encoded');
    });

    it('should return "encoded" for lowercase hex', () => {
      expect(inferType('%2f%3a')).toBe('encoded');
    });
  });

  describe('json values', () => {
    it('should return "json" for JSON object', () => {
      expect(inferType('{"key":"value"}')).toBe('json');
    });

    it('should return "json" for JSON array', () => {
      expect(inferType('[1,2,3]')).toBe('json');
    });

    it('should return "json" for nested JSON', () => {
      expect(inferType('{"nested":{"key":"value"}}')).toBe('json');
    });

    it('should return "json" for empty JSON object', () => {
      expect(inferType('{}')).toBe('json');
    });

    it('should return "json" for empty JSON array', () => {
      expect(inferType('[]')).toBe('json');
    });
  });

  describe('string values (fallback)', () => {
    it('should return "string" for plain text', () => {
      expect(inferType('hello')).toBe('string');
    });

    it('should return "string" for alphanumeric', () => {
      expect(inferType('abc123')).toBe('string');
    });

    it('should return "string" for special characters without encoding', () => {
      expect(inferType('hello-world_test')).toBe('string');
    });

    it('should return "string" for invalid JSON', () => {
      expect(inferType('{invalid}')).toBe('string');
    });

    it('should return "string" for partial number', () => {
      expect(inferType('123abc')).toBe('string');
    });
  });

  describe('edge cases', () => {
    it('should return "string" for "%" without hex digits', () => {
      expect(inferType('100%')).toBe('string');
    });

    it('should return "encoded" for valid percent encoding even with text', () => {
      expect(inferType('test%20value')).toBe('encoded');
    });

    it('should return "number" for scientific notation', () => {
      expect(inferType('1e10')).toBe('number');
    });
  });
});

describe('formatParameters', () => {
  it('should return "-" for null parameters', () => {
    expect(formatParameters(null)).toBe('-');
  });

  it('should return "-" for undefined parameters', () => {
    expect(formatParameters(undefined)).toBe('-');
  });

  it('should return "-" for empty object', () => {
    expect(formatParameters({})).toBe('-');
  });

  it('should format single parameter with type', () => {
    expect(formatParameters({ name: 'john' })).toBe('name <string>');
  });

  it('should format two parameters', () => {
    expect(formatParameters({ name: 'john', age: '25' })).toBe(
      'name <string>, age <number>'
    );
  });

  it('should format three parameters', () => {
    expect(formatParameters({ a: '1', b: '2', c: '3' })).toBe(
      'a <number>, b <number>, c <number>'
    );
  });

  it('should truncate and show "+N more" for more than 3 parameters', () => {
    const params = { a: '1', b: '2', c: '3', d: '4' };
    expect(formatParameters(params)).toBe('a <number>, b <number>, c <number> +1 more');
  });

  it('should show correct count for many extra parameters', () => {
    const params = { a: '1', b: '2', c: '3', d: '4', e: '5', f: '6' };
    expect(formatParameters(params)).toBe('a <number>, b <number>, c <number> +3 more');
  });

  it('should handle mixed types', () => {
    const params = { redirect: '%2F', enabled: 'true', count: '10' };
    expect(formatParameters(params)).toBe(
      'redirect <encoded>, enabled <boolean>, count <number>'
    );
  });

  it('should handle null values in parameters', () => {
    const params = { name: null, active: 'true' };
    expect(formatParameters(params)).toBe('name <empty>, active <boolean>');
  });
});
