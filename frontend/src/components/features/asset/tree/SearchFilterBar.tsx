/**
 * SearchFilterBar Component
 * Search input and HTTP method filter badges for asset tree filtering
 */

import { useCallback } from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { HttpMethod } from './AssetTreeView';

/**
 * HTTP methods available for filtering
 */
const HTTP_METHODS: HttpMethod[] = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];

/**
 * Get badge variant for HTTP method filter
 */
function getMethodFilterVariant(
  method: HttpMethod,
  selectedMethod: HttpMethod | null
): 'default' | 'secondary' | 'outline' | 'destructive' {
  if (selectedMethod === method) {
    switch (method) {
      case 'GET':
        return 'secondary';
      case 'POST':
        return 'default';
      case 'DELETE':
        return 'destructive';
      default:
        return 'outline';
    }
  }
  return 'outline';
}

/**
 * Props for SearchFilterBar
 */
interface SearchFilterBarProps {
  /** Current search query */
  searchQuery: string;
  /** Callback when search query changes */
  onSearchChange: (query: string) => void;
  /** Currently selected HTTP method filter */
  filterMethod: HttpMethod | null;
  /** Callback when method filter changes */
  onFilterMethodChange: (method: HttpMethod | null) => void;
  /** Additional className */
  className?: string;
}

/**
 * SearchFilterBar
 * Provides search input and HTTP method filter badges for filtering the asset tree
 */
export function SearchFilterBar({
  searchQuery,
  onSearchChange,
  filterMethod,
  onFilterMethodChange,
  className,
}: SearchFilterBarProps) {
  const handleClearSearch = useCallback(() => {
    onSearchChange('');
  }, [onSearchChange]);

  const handleMethodClick = useCallback(
    (method: HttpMethod) => {
      // Toggle: if already selected, clear the filter
      if (filterMethod === method) {
        onFilterMethodChange(null);
      } else {
        onFilterMethodChange(method);
      }
    },
    [filterMethod, onFilterMethodChange]
  );

  return (
    <div className={cn('space-y-2', className)} data-testid="search-filter-bar">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search assets..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-8 pl-8 pr-8 text-sm"
          aria-label="Search assets"
          data-testid="search-input"
        />
        {searchQuery && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearSearch}
            className="absolute right-1 top-1/2 h-6 w-6 -translate-y-1/2 p-0"
            aria-label="Clear search"
            data-testid="clear-search-button"
          >
            <X className="h-3 w-3" />
          </Button>
        )}
      </div>

      {/* HTTP Method Filter Badges */}
      <div className="flex flex-wrap gap-1" role="group" aria-label="Filter by HTTP method">
        {HTTP_METHODS.map((method) => (
          <Badge
            key={method}
            variant={getMethodFilterVariant(method, filterMethod)}
            className={cn(
              'cursor-pointer text-xs transition-colors',
              filterMethod === method && 'ring-1 ring-ring'
            )}
            onClick={() => handleMethodClick(method)}
            role="checkbox"
            aria-checked={filterMethod === method}
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleMethodClick(method);
              }
            }}
            data-testid={`filter-method-${method.toLowerCase()}`}
          >
            {method}
          </Badge>
        ))}
        {filterMethod && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onFilterMethodChange(null)}
            className="h-5 px-1 text-xs text-muted-foreground"
            data-testid="clear-filter-button"
          >
            Clear
          </Button>
        )}
      </div>
    </div>
  );
}

export default SearchFilterBar;
