import { History } from 'lucide-react';

/**
 * Scan History tab content with "Coming Soon" placeholder.
 *
 * @example
 * ```tsx
 * <HistoryTabContent />
 * ```
 */
export function HistoryTabContent() {
  return (
    <div
      className="flex items-center justify-center h-[200px] border rounded-md bg-muted/50"
      data-testid="history-tab-content"
    >
      <div className="text-center text-muted-foreground">
        <History className="h-12 w-12 mx-auto mb-4 opacity-50" aria-hidden="true" />
        <p className="text-lg font-medium">Coming Soon</p>
        <p className="text-sm">Scan history will be available in a future update.</p>
      </div>
    </div>
  );
}
