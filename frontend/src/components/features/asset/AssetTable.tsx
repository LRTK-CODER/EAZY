import { useState, useEffect } from 'react';
import { Loader2, ChevronUp, ChevronDown, ExternalLink, Eye } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import * as assetService from '@/services/assetService';
import type { Asset, AssetType, AssetSource } from '@/types/asset';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { formatDistanceToNow } from '@/utils/date';
import { AssetDetailDialog } from './AssetDetailDialog';

interface AssetTableProps {
  projectId: number;
  targetId: number;
}

type SortBy = 'type' | 'url' | 'last_seen';
type SortOrder = 'asc' | 'desc';

interface SortState {
  sortBy: SortBy;
  sortOrder: SortOrder;
}

/**
 * Get variant for Type badge based on asset type
 */
const getTypeBadgeVariant = (type: AssetType): 'default' | 'secondary' | 'outline' => {
  switch (type) {
    case 'url':
      return 'default';
    case 'form':
      return 'secondary';
    case 'xhr':
      return 'outline';
    default:
      return 'default';
  }
};

/**
 * Get color classes for Source badge based on asset source
 */
const getSourceBadgeColor = (source: AssetSource): string => {
  switch (source) {
    case 'html':
      return 'bg-gray-50 text-gray-700 dark:bg-gray-950/30 dark:text-gray-400';
    case 'js':
      return 'bg-yellow-50 text-yellow-700 dark:bg-yellow-950/30 dark:text-yellow-400';
    case 'network':
      return 'bg-purple-50 text-purple-700 dark:bg-purple-950/30 dark:text-purple-400';
    case 'dom':
      return 'bg-green-50 text-green-700 dark:bg-green-950/30 dark:text-green-400';
    default:
      return 'bg-gray-50 text-gray-700 dark:bg-gray-950/30 dark:text-gray-400';
  }
};

/**
 * AssetTable component displays a table of discovered assets with sorting and pagination
 * Features:
 * - 8 columns: Type, Source, Method, URL, Path, Parameters, Last Seen, Actions
 * - Loading/Error/Empty states
 * - Sortable columns (Type, URL, Last Seen)
 * - Pagination with configurable page size
 * - LocalStorage persistence for sort state
 */
export function AssetTable({ projectId, targetId }: AssetTableProps) {
  // Fetch assets
  const { data: assets = [], isLoading, isError } = useQuery({
    queryKey: ['assets', projectId, targetId],
    queryFn: () => assetService.getTargetAssets(projectId, targetId),
  });

  // Asset Detail Dialog state
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Sort state with localStorage persistence
  const [sortState, setSortState] = useState<SortState>(() => {
    try {
      const stored = localStorage.getItem('assetTableSort');
      if (stored) {
        const parsed = JSON.parse(stored);
        return {
          sortBy: parsed.sortBy || 'last_seen',
          sortOrder: parsed.sortOrder || 'desc',
        };
      }
    } catch (error) {
      // Ignore parsing errors
    }
    return { sortBy: 'last_seen', sortOrder: 'desc' };
  });

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Save sort state to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('assetTableSort', JSON.stringify(sortState));
    } catch (error) {
      // Ignore storage errors
    }
  }, [sortState]);

  // Handle column header click for sorting
  const handleSort = (column: SortBy) => {
    setSortState((prev) => {
      if (prev.sortBy === column) {
        // Toggle sort order
        return { sortBy: column, sortOrder: prev.sortOrder === 'asc' ? 'desc' : 'asc' };
      }
      // New column, default to ascending
      return { sortBy: column, sortOrder: 'asc' };
    });
  };

  // Sort assets
  const sortedAssets = [...assets].sort((a, b) => {
    let compareResult = 0;

    switch (sortState.sortBy) {
      case 'type':
        compareResult = a.type.localeCompare(b.type);
        break;
      case 'url':
        compareResult = a.url.localeCompare(b.url);
        break;
      case 'last_seen':
        compareResult =
          new Date(a.last_seen_at).getTime() - new Date(b.last_seen_at).getTime();
        break;
    }

    return sortState.sortOrder === 'asc' ? compareResult : -compareResult;
  });

  // Paginate assets
  const totalPages = Math.ceil(sortedAssets.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedAssets = sortedAssets.slice(startIndex, endIndex);

  // Reset to page 1 when page size changes
  useEffect(() => {
    setCurrentPage(1);
  }, [pageSize]);

  // Render sort icon
  const renderSortIcon = (column: SortBy) => {
    if (sortState.sortBy !== column) return null;

    return sortState.sortOrder === 'asc' ? (
      <ChevronUp className="h-4 w-4 inline ml-1" />
    ) : (
      <ChevronDown className="h-4 w-4 inline ml-1" />
    );
  };

  // Truncate path if too long
  const truncatePath = (path: string, maxLength: number = 50): string => {
    if (path.length <= maxLength) return path;
    return path.slice(0, maxLength) + '...';
  };

  // Format parameters count
  const formatParameters = (parameters: Record<string, unknown> | null): string => {
    if (!parameters) return '-';
    const count = Object.keys(parameters).length;
    return count === 1 ? '1 param' : `${count} params`;
  };

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <ScrollArea className="w-full">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => handleSort('type')}
                >
                  Type {renderSortIcon('type')}
                </TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Method</TableHead>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => handleSort('url')}
                >
                  URL {renderSortIcon('url')}
                </TableHead>
                <TableHead>Path</TableHead>
                <TableHead>Parameters</TableHead>
                <TableHead
                  className="cursor-pointer select-none"
                  onClick={() => handleSort('last_seen')}
                >
                  Last Seen {renderSortIcon('last_seen')}
                </TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="h-24 text-center">
                    <div className="flex items-center justify-center">
                      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mr-2" />
                      <p className="text-sm text-muted-foreground">Loading assets...</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={8} className="h-24 text-center">
                    <p className="text-sm text-destructive">Error loading assets</p>
                  </TableCell>
                </TableRow>
              ) : assets.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="h-24 text-center">
                    <p className="text-sm text-muted-foreground">
                      No assets found. Run a scan to discover assets.
                    </p>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedAssets.map((asset) => (
                  <TableRow key={asset.id}>
                    {/* Type Badge */}
                    <TableCell>
                      <Badge variant={getTypeBadgeVariant(asset.type)} className="type-badge">
                        {asset.type.toUpperCase()}
                      </Badge>
                    </TableCell>

                    {/* Source Badge */}
                    <TableCell>
                      <Badge variant="outline" className={getSourceBadgeColor(asset.source)}>
                        {asset.source.toUpperCase()}
                      </Badge>
                    </TableCell>

                    {/* Method */}
                    <TableCell className="font-medium">{asset.method}</TableCell>

                    {/* URL with Tooltip */}
                    <TableCell>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <a
                              href={asset.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline dark:text-blue-400 flex items-center gap-1 max-w-xs"
                            >
                              <span className="truncate">{asset.url}</span>
                              <ExternalLink className="h-3 w-3 flex-shrink-0" />
                            </a>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>{asset.url}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </TableCell>

                    {/* Path (truncated) */}
                    <TableCell className="text-muted-foreground">
                      {truncatePath(asset.path)}
                    </TableCell>

                    {/* Parameters */}
                    <TableCell>
                      <Badge variant="secondary" className="text-xs">
                        {formatParameters(asset.parameters)}
                      </Badge>
                    </TableCell>

                    {/* Last Seen */}
                    <TableCell className="text-muted-foreground text-sm">
                      {formatDistanceToNow(asset.last_seen_at, { addSuffix: true })}
                    </TableCell>

                    {/* Actions */}
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => {
                          setSelectedAsset(asset);
                          setDialogOpen(true);
                        }}
                      >
                        <Eye className="h-4 w-4" />
                        <span className="sr-only">View Details</span>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
      </div>

      {/* Pagination Controls */}
      {!isLoading && !isError && assets.length > 0 && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {startIndex + 1}-{Math.min(endIndex, sortedAssets.length)} of{' '}
              {sortedAssets.length}
            </p>
            <div className="flex items-center gap-2">
              <p className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Items per page:</span>
            <select
              id="page-size"
              value={pageSize}
              onChange={(e) => setPageSize(Number(e.target.value))}
              className="h-8 rounded-md border border-input bg-background px-3 text-sm"
              aria-label="Items per page"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
        </div>
      )}

      {/* Asset Detail Dialog */}
      {selectedAsset && (
        <AssetDetailDialog
          asset={selectedAsset}
          open={dialogOpen}
          onOpenChange={setDialogOpen}
        />
      )}
    </div>
  );
}
