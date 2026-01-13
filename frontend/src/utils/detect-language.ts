/**
 * Language Detection Utility
 * Auto-detects programming language from content or content-type header
 */

export type SupportedLanguage =
  | 'json'
  | 'xml'
  | 'html'
  | 'javascript'
  | 'css'
  | 'text';

/**
 * Detects language from content using pattern matching
 */
export function detectLanguage(content: string): SupportedLanguage {
  if (!content || typeof content !== 'string') {
    return 'text';
  }

  const trimmed = content.trim();
  if (!trimmed) {
    return 'text';
  }

  // JSON detection - starts with { or [
  if (/^[\s]*[{\[]/.test(trimmed)) {
    try {
      JSON.parse(trimmed);
      return 'json';
    } catch {
      // Not valid JSON, continue checking
    }
  }

  // XML detection - starts with <? or < and contains closing tags
  if (/^<\?xml/i.test(trimmed)) {
    return 'xml';
  }

  // HTML detection - DOCTYPE or common HTML structure
  if (/^<!DOCTYPE\s+html/i.test(trimmed)) {
    return 'html';
  }

  if (/<html[\s>]/i.test(trimmed)) {
    return 'html';
  }

  // Check for common HTML tags (div, p, span, etc.)
  if (/<(div|span|p|a|img|ul|ol|li|table|form|input|button|header|footer|nav|section|article|main)[\s>]/i.test(trimmed)) {
    return 'html';
  }

  // XML detection - starts with < and has XML-like structure (but not HTML)
  if (/^<[a-zA-Z][\w:-]*[\s>]/.test(trimmed) && /<\/[a-zA-Z][\w:-]*>/.test(trimmed)) {
    return 'xml';
  }

  // JavaScript detection
  if (
    /^(const|let|var|function|class|import|export|async|await)\s/.test(trimmed) ||
    /=>\s*{/.test(trimmed) ||
    /function\s*\(/.test(trimmed)
  ) {
    return 'javascript';
  }

  // CSS detection - selectors followed by { }
  if (
    /^[.#@]?[\w-]+[\s,]*.*{/.test(trimmed) ||
    /@(media|keyframes|import|font-face)\s/.test(trimmed)
  ) {
    return 'css';
  }

  return 'text';
}

/**
 * Detects language from Content-Type header
 */
export function detectLanguageFromContentType(
  contentType: string | undefined | null
): SupportedLanguage {
  if (!contentType) {
    return 'text';
  }

  const type = contentType.toLowerCase().split(';')[0].trim();

  // JSON types
  if (
    type === 'application/json' ||
    type === 'text/json' ||
    type.endsWith('+json')
  ) {
    return 'json';
  }

  // XML types
  if (
    type === 'application/xml' ||
    type === 'text/xml' ||
    type === 'application/xhtml+xml' ||
    type.endsWith('+xml')
  ) {
    return 'xml';
  }

  // HTML types
  if (type === 'text/html') {
    return 'html';
  }

  // JavaScript types
  if (
    type === 'application/javascript' ||
    type === 'text/javascript' ||
    type === 'application/x-javascript'
  ) {
    return 'javascript';
  }

  // CSS types
  if (type === 'text/css') {
    return 'css';
  }

  return 'text';
}

/**
 * Combined detection: prioritize contentType, fallback to content analysis
 */
export function detectLanguageAuto(
  content: string,
  contentType?: string | null
): SupportedLanguage {
  // First try content-type if provided
  if (contentType) {
    const fromContentType = detectLanguageFromContentType(contentType);
    if (fromContentType !== 'text') {
      return fromContentType;
    }
  }

  // Fallback to content analysis
  return detectLanguage(content);
}
