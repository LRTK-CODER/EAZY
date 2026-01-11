import { useState, useEffect, useCallback, useMemo } from 'react';
import { Loader2, Edit, Trash2, Play, BarChart } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { useQueryClient } from '@tanstack/react-query';
import { useTargets, useTriggerScan, targetKeys } from '@/hooks/useTargets';
import { useLatestTasks } from '@/hooks/useTasks';
import type { Target } from '@/types/target';
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
import { EditTargetForm } from './EditTargetForm';
import { DeleteTargetDialog } from './DeleteTargetDialog';
import { ScanStatusBadge } from './ScanStatusBadge';

interface TargetListProps {
  projectId: number;
}

/**
 * TargetList component displays a table of targets with actions
 * Features:
 * - Table rendering with columns: Name, URL, Scope, Status, Created At, Actions
 * - Loading/Error/Empty states
 * - Edit/Delete/Scan actions for each target
 * - Scan status badges with real-time updates
 */
// Format date for display (extracted outside component to avoid recreation)
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export function TargetList({ projectId }: TargetListProps) {
  const queryClient = useQueryClient();
  const { data: targets = [], isLoading, isError } = useTargets(projectId);
  const triggerScan = useTriggerScan();

  // Batch fetch tasks for all targets (solves N+1 polling problem)
  const targetIds = useMemo(() => targets.map((t) => t.id), [targets]);
  const { tasksMap, isLoading: tasksLoading } = useLatestTasks(targetIds);

  // Dialog states
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState<Target | null>(null);
  const [prevDeleteOpen, setPrevDeleteOpen] = useState(false);

  // When delete dialog closes, invalidate queries to refetch targets
  // Fixed: Only trigger when dialog transitions from open to closed
  useEffect(() => {
    if (prevDeleteOpen && !deleteOpen) {
      queryClient.invalidateQueries({ queryKey: targetKeys.lists() });
    }
    setPrevDeleteOpen(deleteOpen);
  }, [deleteOpen, prevDeleteOpen, queryClient]);

  // Handlers with useCallback to prevent unnecessary re-renders
  const handleEdit = useCallback((target: Target) => {
    setSelectedTarget(target);
    setEditOpen(true);
  }, []);

  const handleDelete = useCallback((target: Target) => {
    setSelectedTarget(target);
    setDeleteOpen(true);
  }, []);

  const handleScan = useCallback(async (target: Target) => {
    try {
      await triggerScan.mutateAsync({
        projectId: target.project_id,
        targetId: target.id,
      });
      toast.success(`Scan started for ${target.name}`);
    } catch {
      toast.error(`Failed to start scan for ${target.name}`);
    }
  }, [triggerScan]);

  // Table with targets - show table structure even when loading/error/empty
  return (
    <>
      <div className="rounded-md border">
        <ScrollArea className="w-full">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>URL</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={6} className="h-24 text-center">
                <div className="flex items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mr-2" />
                  <p className="text-sm text-muted-foreground">Loading targets...</p>
                </div>
              </TableCell>
            </TableRow>
          ) : isError ? (
            <TableRow>
              <TableCell colSpan={6} className="h-24 text-center">
                <p className="text-sm text-destructive">Error loading targets</p>
              </TableCell>
            </TableRow>
          ) : targets.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="h-24 text-center">
                <p className="text-sm text-muted-foreground">No targets found</p>
              </TableCell>
            </TableRow>
          ) : (
            targets.map((target) => (
            <TableRow key={target.id}>
              <TableCell className="font-medium">{target.name}</TableCell>
              <TableCell className="text-muted-foreground">{target.url}</TableCell>
              <TableCell>
                <Badge variant="secondary" className="text-xs">
                  {target.scope}
                </Badge>
              </TableCell>
              <TableCell>
                <ScanStatusBadge
                  task={tasksMap.get(target.id)}
                  isLoading={tasksLoading}
                />
              </TableCell>
              <TableCell className="text-muted-foreground">
                {formatDate(target.created_at)}
              </TableCell>
              <TableCell className="text-right">
                <TooltipProvider>
                  <div className="flex items-center justify-end gap-2">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="outline" size="sm" asChild>
                          <Link
                            to={`/projects/${projectId}/targets/${target.id}/results`}
                            aria-label={`View scan results for ${target.name}`}
                            title="View scan results"
                          >
                            <BarChart className="h-4 w-4" />
                            <span className="ml-2 hidden sm:inline">View Results</span>
                          </Link>
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>View Scan Results</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(target)}
                        >
                          <Edit className="h-4 w-4" />
                          <span className="sr-only">Edit target</span>
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Edit</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(target)}
                        >
                          <Trash2 className="h-4 w-4" />
                          <span className="sr-only">Delete target</span>
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Delete</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleScan(target)}
                          disabled={triggerScan.isPending}
                        >
                          <Play className="h-4 w-4" />
                          <span className="sr-only">Scan target</span>
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Scan</TooltipContent>
                    </Tooltip>
                  </div>
                </TooltipProvider>
              </TableCell>
            </TableRow>
            ))
          )}
        </TableBody>
      </Table>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
      </div>

      {/* Dialogs */}
      {selectedTarget && (
        <>
          <EditTargetForm
            open={editOpen}
            onOpenChange={setEditOpen}
            target={selectedTarget}
          />
          <DeleteTargetDialog
            open={deleteOpen}
            onOpenChange={setDeleteOpen}
            target={selectedTarget}
            projectId={projectId}
          />
        </>
      )}
    </>
  );
}
