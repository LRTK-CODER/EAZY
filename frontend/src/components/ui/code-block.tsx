/**
 * CodeBlock Component
 * Syntax-highlighted code display with copy functionality
 */

import * as React from 'react';
import { Highlight, themes } from 'prism-react-renderer';
import { Check, Copy } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  detectLanguage,
  detectLanguageFromContentType,
  type SupportedLanguage,
} from '@/utils/detect-language';
import { Button } from './button';

// Map our language types to Prism language names
const LANGUAGE_MAP: Record<SupportedLanguage, string> = {
  json: 'json',
  xml: 'xml',
  html: 'markup',
  javascript: 'javascript',
  css: 'css',
  text: 'text',
};

interface CodeBlockProps {
  /** The code content to display */
  code: string | null | undefined;
  /** Programming language for syntax highlighting */
  language?: SupportedLanguage;
  /** Content-Type header for auto-detection */
  contentType?: string;
  /** Theme: 'light', 'dark', or 'auto' (system preference) */
  theme?: 'light' | 'dark' | 'auto';
  /** Show line numbers */
  showLineNumbers?: boolean;
  /** Maximum content length before truncation */
  maxLength?: number;
  /** Custom className */
  className?: string;
  /** Test ID for testing */
  'data-testid'?: string;
  /** Accessible label */
  'aria-label'?: string;
}

const DEFAULT_MAX_LENGTH = 100000;

export function CodeBlock({
  code,
  language,
  contentType,
  theme = 'auto',
  showLineNumbers = false,
  maxLength = DEFAULT_MAX_LENGTH,
  className,
  'data-testid': dataTestId,
  'aria-label': ariaLabel,
}: CodeBlockProps) {
  const [copied, setCopied] = React.useState(false);
  const [isDarkMode, setIsDarkMode] = React.useState(false);

  // Detect system color scheme
  React.useEffect(() => {
    if (theme === 'auto') {
      // Safe check for matchMedia (not available in test environments)
      if (typeof window !== 'undefined' && window.matchMedia) {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        setIsDarkMode(mediaQuery.matches);

        const handler = (e: MediaQueryListEvent) => setIsDarkMode(e.matches);
        mediaQuery.addEventListener('change', handler);
        return () => mediaQuery.removeEventListener('change', handler);
      }
    } else {
      setIsDarkMode(theme === 'dark');
    }
  }, [theme]);

  // Handle empty/null content
  if (!code) {
    return (
      <div
        className={cn(
          'bg-muted p-4 rounded-md text-sm text-muted-foreground text-center',
          className
        )}
        data-testid={dataTestId}
        aria-label={ariaLabel}
      >
        No content
      </div>
    );
  }

  // Detect language
  const detectedLanguage = language
    ? language
    : contentType
      ? detectLanguageFromContentType(contentType)
      : detectLanguage(code);

  const prismLanguage = LANGUAGE_MAP[detectedLanguage] || 'text';

  // Truncate large content
  const isTruncated = code.length > maxLength;
  const displayCode = isTruncated ? code.slice(0, maxLength) : code;

  // Copy handler
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Select theme
  const prismTheme = isDarkMode ? themes.vsDark : themes.vsLight;

  // Compute theme class
  const themeClass = theme === 'auto' ? (isDarkMode ? 'dark' : 'light') : theme;

  return (
    <div
      className={cn('relative group', themeClass, className)}
      data-testid={dataTestId || 'code-block-container'}
      aria-label={ariaLabel}
    >
      {/* Copy Button */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-2 right-2 h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity z-10"
        onClick={handleCopy}
        aria-label={copied ? 'Copied' : 'Copy code'}
      >
        {copied ? (
          <Check className="h-4 w-4 text-green-500" />
        ) : (
          <Copy className="h-4 w-4" />
        )}
      </Button>

      {/* Copy feedback */}
      {copied && (
        <span className="absolute top-2 right-12 text-xs text-green-500 bg-background px-2 py-1 rounded">
          Copied!
        </span>
      )}

      {/* Truncation warning */}
      {isTruncated && (
        <div className="bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 text-xs px-3 py-1 rounded-t-md">
          Content truncated ({Math.round(code.length / 1024)}KB). Showing first{' '}
          {Math.round(maxLength / 1024)}KB.
        </div>
      )}

      {/* Code Block */}
      <Highlight theme={prismTheme} code={displayCode} language={prismLanguage}>
        {({ className: highlightClassName, style, tokens, getLineProps, getTokenProps }) => (
          <pre
            className={cn(
              'bg-muted p-4 rounded-md overflow-auto max-h-96 text-sm',
              isTruncated && 'rounded-t-none',
              highlightClassName
            )}
            style={style}
          >
            <code role="code" className="font-mono">
              {showLineNumbers && (
                <span
                  data-testid="line-numbers"
                  className="inline-block mr-4 text-muted-foreground select-none"
                  aria-hidden="true"
                >
                  {tokens.map((_, i) => (
                    <span key={i} className="block text-right pr-2 border-r border-border">
                      {i + 1}
                    </span>
                  ))}
                </span>
              )}
              <span className={showLineNumbers ? 'inline-block align-top' : undefined}>
                {tokens.map((line, i) => (
                  <span key={i} {...getLineProps({ line })}>
                    {line.map((token, key) => (
                      <span key={key} {...getTokenProps({ token })} />
                    ))}
                    {i < tokens.length - 1 && '\n'}
                  </span>
                ))}
              </span>
            </code>
          </pre>
        )}
      </Highlight>
    </div>
  );
}

export default CodeBlock;
