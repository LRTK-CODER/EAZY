import { useParams, Link } from 'react-router-dom';
import { Loader2, ArrowLeft } from 'lucide-react';
import { useProject } from '@/hooks/useProjects';
import { useTarget } from '@/hooks/useTargets';
import { useTargetAssets } from '@/hooks/useAssets';
import { AssetTable } from '@/components/features/asset/AssetTable';
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

/**
 * TargetResultsPage component displays scan results and discovered assets for a target
 *
 * Features:
 * - Breadcrumb navigation (Home → Projects → Project Detail → Results)
 * - Target information header (Name, URL, Scope badge)
 * - AssetTable integration showing discovered assets
 * - Loading, error, and empty states
 * - "Back to Project" navigation button
 *
 * Route: /projects/:projectId/targets/:targetId/results
 */
export function TargetResultsPage() {
  // Extract route parameters
  const { projectId, targetId } = useParams<{ projectId: string; targetId: string }>();

  // Convert to numbers (NaN is allowed, hooks will handle validation)
  const projectIdNum = Number(projectId);
  const targetIdNum = Number(targetId);

  // Fetch data from hooks
  const {
    data: project,
    isLoading: isProjectLoading,
    isError: isProjectError
  } = useProject(projectIdNum);

  const {
    data: target,
    isLoading: isTargetLoading,
    isError: isTargetError
  } = useTarget(projectIdNum, targetIdNum);

  const {
    data: assets
  } = useTargetAssets(projectIdNum, targetIdNum);

  // Loading state: show spinner if project or target is loading
  if (isProjectLoading || isTargetLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Project error state
  if (isProjectError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Project not found</h2>
        </div>
      </div>
    );
  }

  // Target error state: check both isTargetError and !target
  if (isTargetError || !target) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Target not found</h2>
          <p className="text-muted-foreground">
            The target you're looking for doesn't exist
          </p>
        </div>
      </div>
    );
  }

  // Main render: project, target, and assets all loaded successfully
  return (
    <div className="p-6">
      {/* Breadcrumb Navigation */}
      <Breadcrumb className="mb-6">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/">Home</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/projects">Projects</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to={`/projects/${projectIdNum}`}>{project?.name}</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>Results</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      {/* Target Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold">{target.name}</h1>
          <Badge>{target.scope}</Badge>
        </div>
        <a
          href={target.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline dark:text-blue-400"
        >
          {target.url}
        </a>
      </div>

      {/* Assets Section */}
      {assets && assets.length === 0 ? (
        <div className="flex items-center justify-center py-12 border rounded-md bg-muted/30">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">No assets found</h3>
            <p className="text-muted-foreground">
              run a scan to discover attack surfaces
            </p>
          </div>
        </div>
      ) : (
        <div className="mb-6">
          <AssetTable projectId={projectIdNum} targetId={targetIdNum} />
        </div>
      )}

      {/* Back to Project Button */}
      <div className="mt-6">
        <Link to={`/projects/${projectIdNum}`}>
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Project
          </Button>
        </Link>
      </div>
    </div>
  );
}
