import { useState, type ReactNode } from 'react';
import { Search, Clock, X } from 'lucide-react';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useTargetSearch } from '@/hooks/useTargets';
import { useSearchHistory } from '@/hooks/useSearchHistory';
import type { Target } from '@/types/target';

interface TargetSearchBarProps {
  projectId: number;
  onSelect: (target: Target) => void;
  placeholder?: string;
}

/**
 * Highlight matching text in search results
 */
function highlightMatch(text: string, query: string): ReactNode {
  if (!query || query.length < 2) return text;

  // Escape special regex characters
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escaped})`, 'gi');
  const parts = text.split(regex);

  return parts.map((part, i) =>
    regex.test(part) ? (
      <mark key={i} className="bg-yellow-200 dark:bg-yellow-800 rounded-sm">
        {part}
      </mark>
    ) : (
      part
    )
  );
}

export function TargetSearchBar({
  projectId,
  onSelect,
  placeholder = 'Search targets...',
}: TargetSearchBarProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');

  const { data, isLoading, isError } = useTargetSearch(projectId, query);
  const { history, addToHistory, clearHistory } = useSearchHistory(projectId);

  const handleSelect = (target: Target) => {
    // Add successful search to history
    if (query.length >= 2) {
      addToHistory(query);
    }
    onSelect(target);
    setOpen(false);
    setQuery('');
  };

  const handleHistorySelect = (historyQuery: string) => {
    setQuery(historyQuery);
  };

  // Determine if we should show results (query is long enough)
  const showResults = query.length >= 2;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" aria-label="Search targets">
          <Search className="mr-2 h-4 w-4" />
          {placeholder}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="p-0 w-80" align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Search by name or URL..."
            value={query}
            onValueChange={setQuery}
          />
          <CommandList>
            {/* Loading state */}
            {showResults && isLoading && (
              <div className="py-6 text-center text-sm text-muted-foreground">
                Searching...
              </div>
            )}

            {/* Error state */}
            {showResults && isError && (
              <CommandEmpty>Search failed</CommandEmpty>
            )}

            {/* Empty state */}
            {showResults &&
              !isLoading &&
              !isError &&
              data?.items.length === 0 && (
                <CommandEmpty>No targets found</CommandEmpty>
              )}

            {/* Results */}
            {showResults && !isLoading && !isError && data?.items && data.items.length > 0 && (
              <CommandGroup>
                {data.items.map((target) => (
                  <CommandItem
                    key={target.id}
                    value={target.id.toString()}
                    onSelect={() => handleSelect(target)}
                    className="flex items-center justify-between"
                  >
                    <div className="flex flex-col min-w-0 flex-1">
                      <span className="truncate">
                        {highlightMatch(target.name, query)}
                      </span>
                      <span className="text-xs text-muted-foreground truncate">
                        {highlightMatch(target.url, query)}
                      </span>
                    </div>
                    <Badge variant="secondary" className="ml-2 shrink-0">
                      {target.asset_count ?? 0} assets
                    </Badge>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {/* Hint when query is too short */}
            {!showResults && query.length > 0 && (
              <div className="py-6 text-center text-sm text-muted-foreground">
                Type at least 2 characters to search
              </div>
            )}

            {/* Recent searches when no query */}
            {!query && history.length > 0 && (
              <CommandGroup>
                <div className="flex items-center justify-between px-2 py-1.5">
                  <span className="text-xs font-medium text-muted-foreground">
                    Recent searches
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto p-1 text-xs text-muted-foreground hover:text-foreground"
                    onClick={(e) => {
                      e.stopPropagation();
                      clearHistory();
                    }}
                  >
                    <X className="mr-1 h-3 w-3" />
                    Clear
                  </Button>
                </div>
                {history.map((historyQuery) => (
                  <CommandItem
                    key={historyQuery}
                    value={historyQuery}
                    onSelect={() => handleHistorySelect(historyQuery)}
                    className="flex items-center gap-2"
                  >
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>{historyQuery}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
