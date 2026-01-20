import { useParams, Link, Navigate } from 'react-router-dom';
import { Loader2, ArrowLeft, LayoutDashboard, FolderTree, History } from 'lucide-react';
import { parseNumericParam, isValidId } from '@/utils/params';
import { useProject } from '@/hooks/useProjects';
import { useTarget } from '@/hooks/useTargets';
import { useTargetAssets } from '@/hooks/useAssets';
import { AssetExplorer } from '@/components/features/asset/AssetExplorer';
import { OverviewTabContent } from '@/components/features/target/tabs/OverviewTabContent';
import { HistoryTabContent } from '@/components/features/target/tabs/HistoryTabContent';
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

/**
 * TargetResultsPage component displays scan results and discovered assets for a target
 *
 * Features:
 * - Breadcrumb navigation (Home → Projects → Project Detail → Results)
 * - Target information header (Name, URL, Scope badge)
 * - AssetExplorer integration showing discovered assets
 * - Loading, error, and empty states
 * - "Back to Project" navigation button
 *
 * Route: /projects/:projectId/targets/:targetId/results
 */
export function TargetResultsPage() {
  // Extract and validate route parameters
  const { projectId, targetId } = useParams<{ projectId: string; targetId: string }>();
  const projectIdNum = parseNumericParam(projectId);
  const targetIdNum = parseNumericParam(targetId);

  // Redirect to 404 if parameters are invalid
  if (!isValidId(projectIdNum) || !isValidId(targetIdNum)) {
    return <Navigate to="/404" replace />;
  }

  return (
    <TargetResultsContent
      projectId={projectIdNum}
      targetId={targetIdNum}
    />
  );
}

interface TargetResultsContentProps {
  projectId: number;
  targetId: number;
}

/**
 * Inner component that handles data fetching after validation
 */
function TargetResultsContent({ projectId, targetId }: TargetResultsContentProps) {
  // Fetch data from hooks
  const {
    data: project,
    isLoading: isProjectLoading,
    isError: isProjectError
  } = useProject(projectId);

  const {
    data: target,
    isLoading: isTargetLoading,
    isError: isTargetError
  } = useTarget(projectId, targetId);

  const {
    data: assets,
    isLoading: isAssetsLoading
  } = useTargetAssets(projectId, targetId);

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
              <Link to={`/projects/${projectId}`}>{project?.name}</Link>
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

      {/* Tabs Section */}
      <Tabs defaultValue="overview" className="mb-6">
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          <TabsTrigger value="overview" className="gap-2">
            <LayoutDashboard className="h-4 w-4" aria-hidden="true" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="assets" className="gap-2">
            <FolderTree className="h-4 w-4" aria-hidden="true" />
            Assets
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <History className="h-4 w-4" aria-hidden="true" />
            Scan History
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-4">
          <OverviewTabContent
            projectId={projectId}
            targetId={targetId}
            targetName={target.name}
          />
        </TabsContent>

        {/* Assets Tab */}
        <TabsContent value="assets" className="mt-4">
          <div className="h-[calc(100vh-320px)] min-h-[400px] border rounded-md overflow-hidden">
            <AssetExplorer
              assets={assets ?? []}
              targetUrl={target.url}
              isLoading={isAssetsLoading}
            />
          </div>
        </TabsContent>

        {/* Scan History Tab */}
        <TabsContent value="history" className="mt-4">
          <HistoryTabContent targetId={targetId} />
        </TabsContent>
      </Tabs>

      {/* Back to Project Button */}
      <div className="mt-6">
        <Link to={`/projects/${projectId}`}>
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Project
          </Button>
        </Link>
      </div>
    </div>
  );
}
