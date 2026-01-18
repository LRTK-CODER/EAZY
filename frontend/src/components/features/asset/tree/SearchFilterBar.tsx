/**
 * SearchFilterBar Component
 * Search input and HTTP method filter badges for asset tree filtering (multiple selection)
 */

import { useCallback } from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getHttpMethodVariant, HTTP_METHODS } from '@/lib/http-method';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { HttpMethod } from './AssetTreeView';

/**
 * Props for SearchFilterBar
 */
interface SearchFilterBarProps {
  /** Current search query */
  searchQuery: string;
  /** Callback when search query changes */
  onSearchChange: (query: string) => void;
  /** Currently selected HTTP method filters */
  filterMethods: HttpMethod[];
  /** Callback when method filter is toggled */
  onFilterMethodToggle: (method: HttpMethod) => void;
  /** Callback to clear all method filters */
  onFilterMethodsClear: () => void;
  /** Additional className */
  className?: string;
}

/**
 * SearchFilterBar
 * Provides search input and HTTP method filter badges for filtering the asset tree
 * Supports multiple method selection
 */
export function SearchFilterBar({
  searchQuery,
  onSearchChange,
  filterMethods,
  onFilterMethodToggle,
  onFilterMethodsClear,
  className,
}: SearchFilterBarProps) {
  const handleClearSearch = useCallback(() => {
    onSearchChange('');
  }, [onSearchChange]);

  const handleMethodClick = useCallback(
    (method: HttpMethod) => {
      onFilterMethodToggle(method);
    },
    [onFilterMethodToggle]
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
        {HTTP_METHODS.map((method) => {
          const isSelected = filterMethods.includes(method as HttpMethod);
          return (
            <Badge
              key={method}
              variant={isSelected ? getHttpMethodVariant(method) : 'outline'}
              className={cn(
                'cursor-pointer text-xs transition-colors',
                isSelected && 'ring-1 ring-ring'
              )}
              onClick={() => handleMethodClick(method as HttpMethod)}
              role="checkbox"
              aria-checked={isSelected}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleMethodClick(method as HttpMethod);
                }
              }}
              data-testid={`filter-method-${method.toLowerCase()}`}
            >
              {method}
            </Badge>
          );
        })}
        {filterMethods.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onFilterMethodsClear}
            className="h-5 px-1 text-xs text-muted-foreground"
            data-testid="clear-filter-button"
          >
            Clear ({filterMethods.length})
          </Button>
        )}
      </div>
    </div>
  );
}

export default SearchFilterBar;
