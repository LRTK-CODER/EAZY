/**
 * detectLanguage Utility Tests
 * Tests for automatic language detection based on content and content-type
 */

import { describe, it, expect } from 'vitest';
import { detectLanguage, detectLanguageFromContentType } from './detect-language';

describe('detectLanguage', () => {
  // =====================
  // JSON Detection
  // =====================
  describe('JSON Detection', () => {
    it('detects JSON object', () => {
      expect(detectLanguage('{"key": "value"}')).toBe('json');
    });

    it('detects JSON array', () => {
      expect(detectLanguage('[1, 2, 3]')).toBe('json');
    });

    it('detects formatted JSON', () => {
      const json = `{
        "name": "test",
        "value": 123
      }`;
      expect(detectLanguage(json)).toBe('json');
    });

    it('detects nested JSON', () => {
      const json = '{"outer": {"inner": {"deep": true}}}';
      expect(detectLanguage(json)).toBe('json');
    });
  });

  // =====================
  // XML Detection
  // =====================
  describe('XML Detection', () => {
    it('detects XML with declaration', () => {
      expect(detectLanguage('<?xml version="1.0"?><root></root>')).toBe('xml');
    });

    it('detects XML without declaration', () => {
      expect(detectLanguage('<root><item>test</item></root>')).toBe('xml');
    });

    it('detects XML with attributes', () => {
      expect(detectLanguage('<root id="1" class="test"></root>')).toBe('xml');
    });

    it('detects SOAP envelope', () => {
      const soap = '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"></soap:Envelope>';
      expect(detectLanguage(soap)).toBe('xml');
    });
  });

  // =====================
  // HTML Detection
  // =====================
  describe('HTML Detection', () => {
    it('detects HTML with DOCTYPE', () => {
      expect(detectLanguage('<!DOCTYPE html><html></html>')).toBe('html');
    });

    it('detects HTML with html tag', () => {
      expect(detectLanguage('<html><head></head><body></body></html>')).toBe('html');
    });

    it('detects HTML with common tags', () => {
      expect(detectLanguage('<div><p>Hello</p></div>')).toBe('html');
    });
  });

  // =====================
  // JavaScript Detection
  // =====================
  describe('JavaScript Detection', () => {
    it('detects function declaration', () => {
      expect(detectLanguage('function test() { return 1; }')).toBe('javascript');
    });

    it('detects arrow function', () => {
      expect(detectLanguage('const fn = () => { return true; }')).toBe('javascript');
    });

    it('detects const/let/var', () => {
      expect(detectLanguage('const x = 1; let y = 2; var z = 3;')).toBe('javascript');
    });

    it('detects async/await', () => {
      expect(detectLanguage('async function fetch() { await data; }')).toBe('javascript');
    });
  });

  // =====================
  // CSS Detection
  // =====================
  describe('CSS Detection', () => {
    it('detects CSS rules', () => {
      expect(detectLanguage('.class { color: red; }')).toBe('css');
    });

    it('detects CSS with multiple selectors', () => {
      expect(detectLanguage('#id, .class { margin: 0; padding: 0; }')).toBe('css');
    });

    it('detects CSS media queries', () => {
      expect(detectLanguage('@media (max-width: 768px) { .class { } }')).toBe('css');
    });
  });

  // =====================
  // Plain Text
  // =====================
  describe('Plain Text', () => {
    it('returns text for unrecognized content', () => {
      expect(detectLanguage('Just some random text')).toBe('text');
    });

    it('returns text for empty string', () => {
      expect(detectLanguage('')).toBe('text');
    });

    it('returns text for whitespace only', () => {
      expect(detectLanguage('   \n\t  ')).toBe('text');
    });
  });
});

describe('detectLanguageFromContentType', () => {
  // =====================
  // JSON Content Types
  // =====================
  describe('JSON Content Types', () => {
    it('detects application/json', () => {
      expect(detectLanguageFromContentType('application/json')).toBe('json');
    });

    it('detects application/json with charset', () => {
      expect(detectLanguageFromContentType('application/json; charset=utf-8')).toBe('json');
    });

    it('detects text/json', () => {
      expect(detectLanguageFromContentType('text/json')).toBe('json');
    });

    it('detects application/ld+json', () => {
      expect(detectLanguageFromContentType('application/ld+json')).toBe('json');
    });

    it('detects application/vnd.api+json', () => {
      expect(detectLanguageFromContentType('application/vnd.api+json')).toBe('json');
    });
  });

  // =====================
  // XML Content Types
  // =====================
  describe('XML Content Types', () => {
    it('detects application/xml', () => {
      expect(detectLanguageFromContentType('application/xml')).toBe('xml');
    });

    it('detects text/xml', () => {
      expect(detectLanguageFromContentType('text/xml')).toBe('xml');
    });

    it('detects application/soap+xml', () => {
      expect(detectLanguageFromContentType('application/soap+xml')).toBe('xml');
    });

    it('detects application/xhtml+xml', () => {
      expect(detectLanguageFromContentType('application/xhtml+xml')).toBe('xml');
    });
  });

  // =====================
  // HTML Content Types
  // =====================
  describe('HTML Content Types', () => {
    it('detects text/html', () => {
      expect(detectLanguageFromContentType('text/html')).toBe('html');
    });

    it('detects text/html with charset', () => {
      expect(detectLanguageFromContentType('text/html; charset=utf-8')).toBe('html');
    });
  });

  // =====================
  // JavaScript Content Types
  // =====================
  describe('JavaScript Content Types', () => {
    it('detects application/javascript', () => {
      expect(detectLanguageFromContentType('application/javascript')).toBe('javascript');
    });

    it('detects text/javascript', () => {
      expect(detectLanguageFromContentType('text/javascript')).toBe('javascript');
    });

    it('detects application/x-javascript', () => {
      expect(detectLanguageFromContentType('application/x-javascript')).toBe('javascript');
    });
  });

  // =====================
  // CSS Content Types
  // =====================
  describe('CSS Content Types', () => {
    it('detects text/css', () => {
      expect(detectLanguageFromContentType('text/css')).toBe('css');
    });
  });

  // =====================
  // Plain Text
  // =====================
  describe('Plain Text', () => {
    it('detects text/plain', () => {
      expect(detectLanguageFromContentType('text/plain')).toBe('text');
    });

    it('returns text for unknown content type', () => {
      expect(detectLanguageFromContentType('application/octet-stream')).toBe('text');
    });

    it('returns text for empty content type', () => {
      expect(detectLanguageFromContentType('')).toBe('text');
    });

    it('returns text for undefined', () => {
      expect(detectLanguageFromContentType(undefined)).toBe('text');
    });
  });
});
