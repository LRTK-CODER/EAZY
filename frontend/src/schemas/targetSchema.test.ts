import { describe, it, expect } from 'vitest';
import { targetFormSchema } from '@/schemas/targetSchema';
import { TargetScope } from '@/types/target';

describe('Target Form Schema Validation', () => {
  describe('name field validation', () => {
    it('should reject empty name (required)', () => {
      const result = targetFormSchema.safeParse({
        name: '',
        url: 'https://example.com',
      });

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('required');
      }
    });

    it('should reject name exceeding 255 characters', () => {
      const longName = 'a'.repeat(256);
      const result = targetFormSchema.safeParse({
        name: longName,
        url: 'https://example.com',
      });

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('255');
      }
    });

    it('should accept valid name (1-255 characters)', () => {
      const result = targetFormSchema.safeParse({
        name: 'Valid Target Name',
        url: 'https://example.com',
      });

      expect(result.success).toBe(true);
    });

    it('should accept name with exactly 255 characters', () => {
      const maxLengthName = 'a'.repeat(255);
      const result = targetFormSchema.safeParse({
        name: maxLengthName,
        url: 'https://example.com',
      });

      expect(result.success).toBe(true);
    });

    it('should accept name with exactly 1 character', () => {
      const result = targetFormSchema.safeParse({
        name: 'a',
        url: 'https://example.com',
      });

      expect(result.success).toBe(true);
    });
  });

  describe('url field validation', () => {
    it('should reject missing url (required)', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
      });

      expect(result.success).toBe(false);
      if (!result.success) {
        const urlError = result.error.issues.find(issue =>
          issue.path.includes('url')
        );
        expect(urlError).toBeDefined();
      }
    });

    it('should reject invalid URL format', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'not-a-valid-url',
      });

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('URL');
      }
    });

    it('should reject malformed URL', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'htp://missing-one-t.com',
      });

      expect(result.success).toBe(false);
    });

    it('should accept valid HTTP URL', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'http://example.com',
      });

      expect(result.success).toBe(true);
    });

    it('should accept valid HTTPS URL', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
      });

      expect(result.success).toBe(true);
    });

    it('should accept URL with path', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com/path/to/resource',
      });

      expect(result.success).toBe(true);
    });

    it('should accept URL with query parameters', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com?param=value',
      });

      expect(result.success).toBe(true);
    });

    it('should accept URL with port', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com:8080',
      });

      expect(result.success).toBe(true);
    });
  });

  describe('description field validation', () => {
    it('should accept missing description (optional)', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
      });

      expect(result.success).toBe(true);
    });

    it('should accept empty string description', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
        description: '',
      });

      expect(result.success).toBe(true);
    });

    it('should accept valid description', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
        description: 'This is a valid target description',
      });

      expect(result.success).toBe(true);
    });

    it('should accept long description', () => {
      const longDescription = 'a'.repeat(1000);
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
        description: longDescription,
      });

      expect(result.success).toBe(true);
    });
  });

  describe('scope field validation', () => {
    it('should apply default value DOMAIN when scope not provided', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
      });

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.scope).toBe(TargetScope.DOMAIN);
      }
    });

    it('should accept DOMAIN scope value', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
        scope: TargetScope.DOMAIN,
      });

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.scope).toBe(TargetScope.DOMAIN);
      }
    });

    it('should accept SUBDOMAIN scope value', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
        scope: TargetScope.SUBDOMAIN,
      });

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.scope).toBe(TargetScope.SUBDOMAIN);
      }
    });

    it('should accept URL_ONLY scope value', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
        scope: TargetScope.URL_ONLY,
      });

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.scope).toBe(TargetScope.URL_ONLY);
      }
    });

    it('should reject invalid scope value', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
        scope: 'INVALID_SCOPE',
      });

      expect(result.success).toBe(false);
    });

    it('should reject numeric scope value', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
        scope: 123,
      });

      expect(result.success).toBe(false);
    });

    it('should reject null scope value', () => {
      const result = targetFormSchema.safeParse({
        name: 'Test Target',
        url: 'https://example.com',
        scope: null,
      });

      expect(result.success).toBe(false);
    });
  });

  describe('complete form validation', () => {
    it('should accept complete valid form data with all fields', () => {
      const result = targetFormSchema.safeParse({
        name: 'Complete Target',
        url: 'https://example.com',
        description: 'A complete target with all fields',
        scope: TargetScope.SUBDOMAIN,
      });

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual({
          name: 'Complete Target',
          url: 'https://example.com',
          description: 'A complete target with all fields',
          scope: TargetScope.SUBDOMAIN,
        });
      }
    });

    it('should accept minimal valid form data', () => {
      const result = targetFormSchema.safeParse({
        name: 'Minimal Target',
        url: 'https://example.com',
      });

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.name).toBe('Minimal Target');
        expect(result.data.url).toBe('https://example.com');
        expect(result.data.scope).toBe(TargetScope.DOMAIN);
      }
    });

    it('should reject completely empty object', () => {
      const result = targetFormSchema.safeParse({});

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues.length).toBeGreaterThanOrEqual(2); // name and url required
      }
    });

    it('should reject form with only name', () => {
      const result = targetFormSchema.safeParse({
        name: 'Only Name',
      });

      expect(result.success).toBe(false);
      if (!result.success) {
        const urlError = result.error.issues.find(issue =>
          issue.path.includes('url')
        );
        expect(urlError).toBeDefined();
      }
    });

    it('should reject form with only url', () => {
      const result = targetFormSchema.safeParse({
        url: 'https://example.com',
      });

      expect(result.success).toBe(false);
      if (!result.success) {
        const nameError = result.error.issues.find(issue =>
          issue.path.includes('name')
        );
        expect(nameError).toBeDefined();
      }
    });
  });
});
