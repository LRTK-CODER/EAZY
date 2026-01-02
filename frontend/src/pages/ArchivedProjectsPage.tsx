import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Archive, ArrowLeft, RotateCcw, Trash2 } from 'lucide-react';
import { useArchivedProjects } from '@/hooks/useProjects';
import { Button } from '@/components/ui/button';
import { ArchivedProjectItem } from '@/components/features/project/ArchivedProjectItem';
import { RestoreDialog } from '@/components/features/project/RestoreDialog';
import { PermanentDeleteDialog } from '@/components/features/project/PermanentDeleteDialog';

export function ArchivedProjectsPage() {
  const { data: projects = [], isLoading, isError } = useArchivedProjects();
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);

  // Dialog states
  const [restoreOpen, setRestoreOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  // For single item actions
  const [singleRestoreIds, setSingleRestoreIds] = useState<number[]>([]);
  const [singleRestoreNames, setSingleRestoreNames] = useState<string[]>([]);
  const [singleDeleteIds, setSingleDeleteIds] = useState<number[]>([]);
  const [singleDeleteNames, setSingleDeleteNames] = useState<string[]>([]);

  const toggleProject = (id: number) => {
    setSelectedProjects((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    if (selectedProjects.length === projects.length) {
      setSelectedProjects([]);
    } else {
      setSelectedProjects(projects.map((p) => p.id));
    }
  };

  const handleBulkRestore = () => {
    setSingleRestoreIds(selectedProjects);
    setSingleRestoreNames(
      projects
        .filter((p) => selectedProjects.includes(p.id))
        .map((p) => p.name)
    );
    setRestoreOpen(true);
  };

  const handleBulkDelete = () => {
    setSingleDeleteIds(selectedProjects);
    setSingleDeleteNames(
      projects
        .filter((p) => selectedProjects.includes(p.id))
        .map((p) => p.name)
    );
    setDeleteOpen(true);
  };

  const handleSingleRestore = (id: number, name: string) => {
    setSingleRestoreIds([id]);
    setSingleRestoreNames([name]);
    setRestoreOpen(true);
  };

  const handleSingleDelete = (id: number, name: string) => {
    setSingleDeleteIds([id]);
    setSingleDeleteNames([name]);
    setDeleteOpen(true);
  };

  const handleRestoreClose = (open: boolean) => {
    setRestoreOpen(open);
    if (!open) {
      setSelectedProjects([]);
      setSingleRestoreIds([]);
      setSingleRestoreNames([]);
    }
  };

  const handleDeleteClose = (open: boolean) => {
    setDeleteOpen(open);
    if (!open) {
      setSelectedProjects([]);
      setSingleDeleteIds([]);
      setSingleDeleteNames([]);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-muted-foreground">Loading archived projects...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-destructive">Failed to load archived projects</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Archived Projects</h1>
          <p className="text-muted-foreground">
            {projects.length} archived project{projects.length !== 1 ? 's' : ''}
          </p>
        </div>

        <Link to="/projects">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Projects
          </Button>
        </Link>
      </div>

      {/* Bulk Actions */}
      {selectedProjects.length > 0 && (
        <div className="flex gap-2 mb-4">
          <Button onClick={handleBulkRestore}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Restore ({selectedProjects.length})
          </Button>
          <Button variant="destructive" onClick={handleBulkDelete}>
            <Trash2 className="h-4 w-4 mr-2" />
            Delete Permanently ({selectedProjects.length})
          </Button>
        </div>
      )}

      {/* Project List */}
      {projects.length === 0 ? (
        <div className="text-center py-12">
          <Archive className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium mb-2">No archived projects</h3>
          <p className="text-muted-foreground">
            Projects you archive will appear here.
          </p>
        </div>
      ) : (
        <>
          {/* Select All 버튼 */}
          <div className="flex justify-end mb-2">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-xs text-muted-foreground hover:text-foreground"
              onClick={toggleAll}
            >
              {selectedProjects.length === projects.length ? "Deselect All" : "Select All"}
            </Button>
          </div>

          {/* 프로젝트 목록 */}
          <div className="grid gap-4">
            {projects.map((project) => (
              <ArchivedProjectItem
                key={project.id}
                project={project}
                isSelected={selectedProjects.includes(project.id)}
                onToggle={() => toggleProject(project.id)}
                onRestore={() => handleSingleRestore(project.id, project.name)}
                onDelete={() => handleSingleDelete(project.id, project.name)}
              />
            ))}
          </div>
        </>
      )}

      {/* Dialogs */}
      <RestoreDialog
        open={restoreOpen}
        onOpenChange={handleRestoreClose}
        projectIds={singleRestoreIds}
        projectNames={singleRestoreNames}
      />
      <PermanentDeleteDialog
        open={deleteOpen}
        onOpenChange={handleDeleteClose}
        projectIds={singleDeleteIds}
        projectNames={singleDeleteNames}
      />
    </div>
  );
}
