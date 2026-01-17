/**
 * AssetExplorer Component
 * Burp Suite style tree view + detail panel layout
 */

import { useMemo, useCallback, useState, useEffect } from 'react';
import { FolderTree, PanelLeft } from 'lucide-react';
import { Panel, Group as PanelGroup, Separator as PanelSeparator } from 'react-resizable-panels';
import { GripVertical } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useIsMobile, useIsTablet } from '@/hooks/use-mobile';
import { useDebounce } from '@/hooks/use-debounce';
import { AssetExplorerProvider, useAssetExplorer } from '@/contexts/AssetExplorerContext';
import { AssetTreeView, type HttpMethod } from './tree/AssetTreeView';
import { SearchFilterBar } from './tree/SearchFilterBar';
import { AssetDetailPanel } from './detail/AssetDetailPanel';
import type { Asset } from '@/types/asset';

// ============================================================================
// Constants
// ============================================================================

/** Minimum tree panel width in pixels */
export const TREE_MIN_WIDTH_PX = 280;

/** Default tree panel width as percentage */
export const TREE_DEFAULT_PERCENT = 35;

// ============================================================================
// Utilities
// ============================================================================

/**
 * Calculate minimum panel size as percentage based on viewport width
 * Ensures tree panel is at least TREE_MIN_WIDTH_PX pixels
 */
export function getMinSizePercent(viewportWidth: number): number {
  return (TREE_MIN_WIDTH_PX / viewportWidth) * 100;
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * Custom hook for mobile sheet state management
 * Automatically closes sheet when an asset is selected
 */
export function useMobileSheet(selectedAssetId: number | null) {
  const [isOpen, setIsOpen] = useState(false);

  // Close sheet when selectedAssetId changes (asset selected)
  useEffect(() => {
    if (selectedAssetId !== null && isOpen) {
      setIsOpen(false);
    }
  }, [selectedAssetId, isOpen]);

  return {
    isOpen,
    setIsOpen,
    open: useCallback(() => setIsOpen(true), []),
    close: useCallback(() => setIsOpen(false), []),
    toggle: useCallback(() => setIsOpen((prev) => !prev), []),
  };
}

/**
 * Props for AssetExplorer component
 */
interface AssetExplorerProps {
  /** Array of assets to display */
  assets: Asset[];
  /** Target URL for fallback domain extraction */
  targetUrl?: string;
  /** Loading state */
  isLoading?: boolean;
}

/** Debounce delay for search input (ms) */
const SEARCH_DEBOUNCE_DELAY = 300;

/**
 * Tree panel content with AssetTreeView and SearchFilterBar
 */
function TreePanelContent({ assets, targetOrigin }: { assets: Asset[]; targetOrigin?: string }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterMethod, setFilterMethod] = useState<HttpMethod | null>(null);

  // Debounce search query to avoid filtering on every keystroke
  const debouncedSearchQuery = useDebounce(searchQuery, SEARCH_DEBOUNCE_DELAY);

  if (assets.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <p>No assets found</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b p-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <FolderTree className="h-4 w-4" />
          Asset Tree
        </h2>
        <p className="mt-1 text-xs text-muted-foreground">
          {assets.length} assets
        </p>
      </div>
      <div className="border-b p-2">
        <SearchFilterBar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          filterMethod={filterMethod}
          onFilterMethodChange={setFilterMethod}
        />
      </div>
      <div className="flex-1 overflow-hidden">
        <AssetTreeView
          assets={assets}
          targetOrigin={targetOrigin}
          searchQuery={debouncedSearchQuery}
          filterMethod={filterMethod ?? undefined}
          className="h-full"
        />
      </div>
    </div>
  );
}

/**
 * Detail panel content with AssetDetailPanel
 */
function DetailPanelContent({ assets }: { assets: Asset[] }) {
  const { selectedAssetId } = useAssetExplorer();

  const selectedAsset = useMemo(() => {
    if (selectedAssetId === null) return null;
    return assets.find((a) => a.id === selectedAssetId) ?? null;
  }, [assets, selectedAssetId]);

  return <AssetDetailPanel asset={selectedAsset} className="h-full" />;
}

/**
 * Loading skeleton
 */
function LoadingSkeleton() {
  return (
    <div data-testid="asset-explorer-loading" className="flex h-full gap-4 p-4">
      <div className="w-1/3 space-y-2">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-4 w-2/3" />
      </div>
      <div className="flex-1 space-y-2">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    </div>
  );
}

/**
 * Desktop layout with resizable panels
 */
function DesktopLayout({ assets, targetOrigin }: { assets: Asset[]; targetOrigin?: string }) {
  if (assets.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center">
          <FolderTree className="mx-auto h-12 w-12 opacity-20" />
          <p className="mt-2">No assets discovered yet</p>
        </div>
      </div>
    );
  }

  return (
    <PanelGroup
      orientation="horizontal"
      className="flex h-full w-full asset-explorer-panel-group"
    >
      <Panel
        id="tree-panel"
        defaultSize="25"
        minSize="20"
        maxSize="50"
        data-testid="asset-explorer-tree-panel"
      >
        <TreePanelContent assets={assets} targetOrigin={targetOrigin} />
      </Panel>

      <PanelSeparator
        className="relative flex w-1 items-center justify-center bg-border transition-colors hover:bg-primary/20 after:absolute after:inset-y-0 after:left-1/2 after:w-3 after:-translate-x-1/2 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        data-testid="asset-explorer-resize-handle"
      >
        <div className="z-10 flex h-6 w-4 items-center justify-center rounded-sm border bg-border">
          <GripVertical className="h-3 w-3" />
        </div>
      </PanelSeparator>

      <Panel
        id="detail-panel"
        defaultSize="75"
        minSize="40"
        data-testid="asset-explorer-detail-panel"
      >
        <DetailPanelContent assets={assets} />
      </Panel>
    </PanelGroup>
  );
}

/**
 * Tablet layout with vertical resizable panels
 */
function TabletLayout({ assets, targetOrigin }: { assets: Asset[]; targetOrigin?: string }) {
  if (assets.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center">
          <FolderTree className="mx-auto h-12 w-12 opacity-20" />
          <p className="mt-2">No assets discovered yet</p>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="asset-explorer-tablet" className="h-full">
      <PanelGroup
        orientation="vertical"
        className="flex h-full w-full flex-col asset-explorer-panel-group-tablet"
      >
        <Panel
          id="tree-panel-tablet"
          defaultSize="40"
          minSize="20"
          maxSize="60"
          data-testid="asset-explorer-tree-panel-tablet"
        >
          <TreePanelContent assets={assets} targetOrigin={targetOrigin} />
        </Panel>

        <PanelSeparator
          className="relative flex h-1 w-full items-center justify-center bg-border transition-colors hover:bg-primary/20"
          data-testid="asset-explorer-resize-handle-tablet"
        >
          <div className="z-10 flex h-4 w-6 items-center justify-center rounded-sm border bg-border rotate-90">
            <GripVertical className="h-3 w-3" />
          </div>
        </PanelSeparator>

        <Panel
          id="detail-panel-tablet"
          defaultSize="60"
          minSize="30"
          data-testid="asset-explorer-detail-panel-tablet"
        >
          <DetailPanelContent assets={assets} />
        </Panel>
      </PanelGroup>
    </div>
  );
}

/**
 * Mobile layout with sheet drawer
 * Sheet automatically closes when an asset is selected
 */
function MobileLayout({ assets, targetOrigin }: { assets: Asset[]; targetOrigin?: string }) {
  const { selectedAssetId } = useAssetExplorer();
  const { isOpen, setIsOpen } = useMobileSheet(selectedAssetId);

  // Get selected asset for trigger button display
  const selectedAsset = useMemo(() => {
    if (selectedAssetId === null) return null;
    return assets.find((a) => a.id === selectedAssetId) ?? null;
  }, [assets, selectedAssetId]);

  // Get display text for trigger button
  const triggerText = useMemo(() => {
    if (selectedAsset?.path) {
      // Show truncated path for selected asset
      const path = selectedAsset.path;
      return path.length > 20 ? `...${path.slice(-17)}` : path;
    }
    return 'Tree';
  }, [selectedAsset]);

  if (assets.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center">
          <FolderTree className="mx-auto h-12 w-12 opacity-20" />
          <p className="mt-2">No assets discovered yet</p>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="asset-explorer-mobile" className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b p-2">
        <Sheet open={isOpen} onOpenChange={setIsOpen}>
          <SheetTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              data-testid="mobile-sheet-trigger"
              className="max-w-[200px]"
            >
              <PanelLeft className="mr-2 h-4 w-4 shrink-0" />
              <span className="truncate">{triggerText}</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[300px] p-0">
            <SheetHeader className="sr-only">
              <SheetTitle>Asset Tree</SheetTitle>
            </SheetHeader>
            <TreePanelContent assets={assets} targetOrigin={targetOrigin} />
          </SheetContent>
        </Sheet>
        <span className="text-sm text-muted-foreground">
          {assets.length} assets
        </span>
      </div>
      <div className="flex-1">
        <DetailPanelContent assets={assets} />
      </div>
    </div>
  );
}

/**
 * Extract origin from URL (protocol + hostname + port)
 */
function extractOriginFromUrl(url?: string): string | undefined {
  if (!url) return undefined;
  try {
    const parsed = new URL(url);
    return parsed.origin;  // e.g., "https://example.com"
  } catch {
    return undefined;
  }
}

/**
 * Inner component that uses the context
 */
function AssetExplorerInner({ assets, targetUrl, isLoading }: AssetExplorerProps) {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();

  // Extract domain from target URL for fallback
  const targetOrigin = useMemo(() => extractOriginFromUrl(targetUrl), [targetUrl]);

  if (isLoading) {
    return (
      <div
        role="region"
        aria-label="Asset Explorer"
        className="h-full"
      >
        <LoadingSkeleton />
      </div>
    );
  }

  const getLayout = () => {
    if (isMobile) return <MobileLayout assets={assets} targetOrigin={targetOrigin} />;
    if (isTablet) return <TabletLayout assets={assets} targetOrigin={targetOrigin} />;
    return <DesktopLayout assets={assets} targetOrigin={targetOrigin} />;
  };

  return (
    <div
      role="region"
      aria-label="Asset Explorer"
      className="h-full"
    >
      {getLayout()}
    </div>
  );
}

/**
 * AssetExplorer
 * Main component for exploring assets in a tree view with detail panel
 * Wraps content in AssetExplorerProvider for state management
 */
export function AssetExplorer({ assets, targetUrl, isLoading = false }: AssetExplorerProps) {
  return (
    <AssetExplorerProvider>
      <AssetExplorerInner assets={assets} targetUrl={targetUrl} isLoading={isLoading} />
    </AssetExplorerProvider>
  );
}
