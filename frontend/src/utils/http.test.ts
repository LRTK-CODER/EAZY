import { describe, it, expect } from 'vitest';
import { parseJsonBody } from './http';

describe('parseJsonBody', () => {
  describe('Null and Empty Handling', () => {
    it('should return null for null input', () => {
      expect(parseJsonBody(null)).toBeNull();
    });

    it('should return empty string for empty string input', () => {
      expect(parseJsonBody('')).toBe('');
    });

    it('should return whitespace-only string as-is', () => {
      expect(parseJsonBody('   ')).toBe('   ');
    });
  });

  describe('Valid JSON String Parsing', () => {
    it('should parse valid JSON object string to object', () => {
      const input = '{"name": "test", "value": 123}';
      const result = parseJsonBody(input);

      expect(result).toEqual({ name: 'test', value: 123 });
      expect(typeof result).toBe('object');
    });

    it('should parse valid JSON array string to array', () => {
      const input = '[1, 2, 3, "test"]';
      const result = parseJsonBody(input);

      expect(result).toEqual([1, 2, 3, 'test']);
      expect(Array.isArray(result)).toBe(true);
    });

    it('should parse nested JSON structures', () => {
      const input = '{"user": {"name": "Alice", "age": 30}, "tags": ["admin", "user"]}';
      const result = parseJsonBody(input);

      expect(result).toEqual({
        user: { name: 'Alice', age: 30 },
        tags: ['admin', 'user'],
      });
    });

    it('should parse JSON with whitespace', () => {
      const input = '  { "key" : "value" }  ';
      const result = parseJsonBody(input);

      expect(result).toEqual({ key: 'value' });
    });

    it('should parse JSON boolean values', () => {
      const input = '{"active": true, "deleted": false}';
      const result = parseJsonBody(input);

      expect(result).toEqual({ active: true, deleted: false });
    });

    it('should parse JSON null values', () => {
      const input = '{"data": null}';
      const result = parseJsonBody(input);

      expect(result).toEqual({ data: null });
    });
  });

  describe('Invalid JSON String Handling', () => {
    it('should return original string for invalid JSON (missing quotes)', () => {
      const input = '{name: test}';
      expect(parseJsonBody(input)).toBe(input);
    });

    it('should return original string for plain text', () => {
      const input = 'This is plain text';
      expect(parseJsonBody(input)).toBe(input);
    });

    it('should return original string for malformed JSON (trailing comma)', () => {
      const input = '{"key": "value",}';
      expect(parseJsonBody(input)).toBe(input);
    });

    it('should return original string for incomplete JSON', () => {
      const input = '{"key": "value"';
      expect(parseJsonBody(input)).toBe(input);
    });

    it('should return original string for HTML content', () => {
      const input = '<html><body>Hello</body></html>';
      expect(parseJsonBody(input)).toBe(input);
    });
  });

  describe('Edge Cases', () => {
    it('should handle JSON with unicode characters', () => {
      const input = '{"message": "안녕하세요 🎉"}';
      const result = parseJsonBody(input);

      expect(result).toEqual({ message: '안녕하세요 🎉' });
    });
  });
});
