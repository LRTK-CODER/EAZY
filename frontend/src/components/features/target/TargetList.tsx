import { useState, useEffect } from 'react';
import { Loader2, Edit, Trash2, Play, CheckCircle2, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useTargets, useTriggerScan, targetKeys } from '@/hooks/useTargets';
import * as taskService from '@/services/taskService';
import type { Target } from '@/types/target';
import { TaskStatus } from '@/types/task';
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

interface TargetListProps {
  projectId: number;
}

/**
 * Component to display scan status badge for a target
 * Uses task service to fetch and display the latest task status
 * Handles errors gracefully by not showing a badge when task data is unavailable
 */
function ScanStatusBadge({ projectId, targetId }: { projectId: number; targetId: number }) {
  // Use useQuery directly with error handling to avoid undefined return issues
  const { data: task } = useQuery({
    queryKey: ['tasks', 'detail', targetId],
    queryFn: async () => {
      try {
        const result = await taskService.getTaskStatus(targetId);
        // If result is undefined (from unmocked service), return null instead
        return result ?? null;
      } catch {
        // Return null on error instead of undefined to satisfy React Query
        return null;
      }
    },
    enabled: !!targetId,
    retry: false,
  });

  // Don't show badge if there's no task data
  if (!task) {
    return null;
  }

  switch (task.status) {
    case TaskStatus.PENDING:
      return (
        <Badge variant="secondary" className="text-muted-foreground">
          Pending
        </Badge>
      );
    case TaskStatus.RUNNING:
      return (
        <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800">
          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
          Running
        </Badge>
      );
    case TaskStatus.COMPLETED:
      return (
        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 dark:bg-green-950/30 dark:text-green-400 dark:border-green-800">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          Completed
        </Badge>
      );
    case TaskStatus.FAILED:
      return (
        <Badge variant="destructive" className="border border-destructive/50">
          <XCircle className="h-3 w-3 mr-1" />
          Failed
        </Badge>
      );
    default:
      return null;
  }
}

/**
 * TargetList component displays a table of targets with actions
 * Features:
 * - Table rendering with columns: Name, URL, Scope, Created At, Actions
 * - Loading/Error/Empty states
 * - Edit/Delete/Scan actions for each target
 * - Scan status badges with real-time updates
 */
export function TargetList({ projectId }: TargetListProps) {
  const queryClient = useQueryClient();
  const { data: targets = [], isLoading, isError } = useTargets(projectId);
  const triggerScan = useTriggerScan();

  // Dialog states
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState<Target | null>(null);

  // When delete dialog closes, invalidate queries to refetch targets
  useEffect(() => {
    if (!deleteOpen) {
      // Dialog was closed, invalidate target queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: targetKeys.lists() });
    }
  }, [deleteOpen, queryClient]);

  // Handlers for action buttons
  const handleEdit = (target: Target) => {
    setSelectedTarget(target);
    setEditOpen(true);
  };

  const handleDelete = (target: Target) => {
    setSelectedTarget(target);
    setDeleteOpen(true);
  };

  const handleScan = async (target: Target) => {
    try {
      await triggerScan.mutateAsync({
        projectId: target.project_id,
        targetId: target.id,
      });
      toast.success(`Scan started for ${target.name}`);
    } catch {
      toast.error(`Failed to start scan for ${target.name}`);
    }
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

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
                <TableHead>Created At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={5} className="h-24 text-center">
                <div className="flex items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mr-2" />
                  <p className="text-sm text-muted-foreground">Loading targets...</p>
                </div>
              </TableCell>
            </TableRow>
          ) : isError ? (
            <TableRow>
              <TableCell colSpan={5} className="h-24 text-center">
                <p className="text-sm text-destructive">Error loading targets</p>
              </TableCell>
            </TableRow>
          ) : targets.length === 0 ? (
            <TableRow>
              <TableCell colSpan={5} className="h-24 text-center">
                <p className="text-sm text-muted-foreground">No targets found</p>
              </TableCell>
            </TableRow>
          ) : (
            targets.map((target) => (
            <TableRow key={target.id}>
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  <span>{target.name}</span>
                  <ScanStatusBadge projectId={target.project_id} targetId={target.id} />
                </div>
              </TableCell>
              <TableCell className="text-muted-foreground">{target.url}</TableCell>
              <TableCell>
                <Badge variant="secondary" className="text-xs">
                  {target.scope}
                </Badge>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {formatDate(target.created_at)}
              </TableCell>
              <TableCell className="text-right">
                <TooltipProvider>
                  <div className="flex items-center justify-end gap-2">
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
