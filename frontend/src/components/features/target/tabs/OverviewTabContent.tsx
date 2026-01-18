import { ScanControl } from '@/components/features/target/ScanControl';

interface OverviewTabContentProps {
  /** Project ID for triggering scan */
  projectId: number;
  /** Target ID for fetching latest task */
  targetId: number;
  /** Target name for accessibility labels */
  targetName: string;
}

/**
 * Overview tab content displaying scan controls and target summary.
 *
 * @example
 * ```tsx
 * <OverviewTabContent projectId={1} targetId={1} targetName="Example" />
 * ```
 */
export function OverviewTabContent({
  projectId,
  targetId,
  targetName,
}: OverviewTabContentProps) {
  return (
    <div className="space-y-6" data-testid="overview-tab-content">
      <ScanControl
        projectId={projectId}
        targetId={targetId}
        targetName={targetName}
      />
    </div>
  );
}
