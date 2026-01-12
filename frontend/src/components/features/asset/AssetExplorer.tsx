/**
 * AssetExplorer Component
 * Burp Suite style tree view + detail panel layout
 */

import { useMemo, useCallback, useState } from 'react';
import { FolderTree, PanelLeft } from 'lucide-react';
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from '@/components/ui/resizable';
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
import { AssetExplorerProvider, useAssetExplorer } from '@/contexts/AssetExplorerContext';
import { AssetTreeView } from './tree/AssetTreeView';
import { AssetDetailPanel } from './detail/AssetDetailPanel';
import type { Asset } from '@/types/asset';

/**
 * Custom hook for persisting panel layout to localStorage
 */
type Layout = { [panelId: string]: number };

function usePanelLayout(storageKey: string, defaultLayout: Layout) {
  const [layout, setLayout] = useState<Layout>(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        return JSON.parse(stored) as Layout;
      }
    } catch {
      // Ignore localStorage errors
    }
    return defaultLayout;
  });

  const onLayoutChange = useCallback(
    (newLayout: Layout) => {
      setLayout(newLayout);
      try {
        localStorage.setItem(storageKey, JSON.stringify(newLayout));
      } catch {
        // Ignore localStorage errors
      }
    },
    [storageKey]
  );

  return { layout, onLayoutChange };
}

/**
 * Props for AssetExplorer component
 */
interface AssetExplorerProps {
  /** Array of assets to display */
  assets: Asset[];
  /** Loading state */
  isLoading?: boolean;
}

/**
 * Tree panel content with AssetTreeView
 */
function TreePanelContent({ assets }: { assets: Asset[] }) {
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
      <div className="flex-1 overflow-hidden">
        <AssetTreeView assets={assets} className="h-full" />
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
function DesktopLayout({ assets }: { assets: Asset[] }) {
  const { layout, onLayoutChange } = usePanelLayout('asset-explorer-desktop', {
    'tree-panel': 30,
    'detail-panel': 70,
  });

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
    <ResizablePanelGroup
      orientation="horizontal"
      className="asset-explorer-panel-group"
      defaultLayout={layout}
      onLayoutChange={onLayoutChange}
    >
      <ResizablePanel
        id="tree-panel"
        defaultSize={layout['tree-panel'] ?? 30}
        minSize={20}
        maxSize={50}
        data-testid="asset-explorer-tree-panel"
      >
        <TreePanelContent assets={assets} />
      </ResizablePanel>

      <ResizableHandle
        withHandle
        data-testid="asset-explorer-resize-handle"
      />

      <ResizablePanel
        id="detail-panel"
        defaultSize={layout['detail-panel'] ?? 70}
        minSize={40}
        data-testid="asset-explorer-detail-panel"
      >
        <DetailPanelContent assets={assets} />
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}

/**
 * Tablet layout with vertical resizable panels
 */
function TabletLayout({ assets }: { assets: Asset[] }) {
  const { layout, onLayoutChange } = usePanelLayout('asset-explorer-tablet', {
    'tree-panel-tablet': 40,
    'detail-panel-tablet': 60,
  });

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
      <ResizablePanelGroup
        orientation="vertical"
        className="asset-explorer-panel-group-tablet"
        defaultLayout={layout}
        onLayoutChange={onLayoutChange}
      >
        <ResizablePanel
          id="tree-panel-tablet"
          defaultSize={layout['tree-panel-tablet'] ?? 40}
          minSize={20}
          maxSize={60}
          data-testid="asset-explorer-tree-panel-tablet"
        >
          <TreePanelContent assets={assets} />
        </ResizablePanel>

        <ResizableHandle
          withHandle
          data-testid="asset-explorer-resize-handle-tablet"
        />

        <ResizablePanel
          id="detail-panel-tablet"
          defaultSize={layout['detail-panel-tablet'] ?? 60}
          minSize={30}
          data-testid="asset-explorer-detail-panel-tablet"
        >
          <DetailPanelContent assets={assets} />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}

/**
 * Mobile layout with sheet drawer
 */
function MobileLayout({ assets }: { assets: Asset[] }) {
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
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="outline" size="sm">
              <PanelLeft className="mr-2 h-4 w-4" />
              Tree
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[300px] p-0">
            <SheetHeader className="sr-only">
              <SheetTitle>Asset Tree</SheetTitle>
            </SheetHeader>
            <TreePanelContent assets={assets} />
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
 * Inner component that uses the context
 */
function AssetExplorerInner({ assets, isLoading }: AssetExplorerProps) {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();

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
    if (isMobile) return <MobileLayout assets={assets} />;
    if (isTablet) return <TabletLayout assets={assets} />;
    return <DesktopLayout assets={assets} />;
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
export function AssetExplorer({ assets, isLoading = false }: AssetExplorerProps) {
  return (
    <AssetExplorerProvider>
      <AssetExplorerInner assets={assets} isLoading={isLoading} />
    </AssetExplorerProvider>
  );
}
