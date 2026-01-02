import { useLocation, Link } from "react-router-dom";
import { useState, useRef, useEffect } from "react";
import {
    LayoutDashboard,
    Settings,
    BarChart3,
    Activity,
    Plus,
    Trash2,
    MoreVertical,
    Edit,
    Archive,
    ArrowLeft,
    AlertCircle,
    Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useProjects, useArchivedProjects } from "@/hooks/useProjects";
import type { Project } from "@/types/project";
import { CreateProjectForm } from "@/components/features/project/CreateProjectForm";
import { EditProjectForm } from "@/components/features/project/EditProjectForm";
import { ArchivedDialog } from "@/components/features/project/ArchivedDialog";

// Dashboard 메뉴
const dashboardMenus = [
    { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
    { label: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
    { label: "Activity", href: "/dashboard/activity", icon: Activity },
];

// Settings 메뉴
const settingsMenus = [
    { label: "General", href: "/settings", icon: Settings },
    { label: "Security", href: "/settings/security", icon: Settings },
    { label: "API Keys", href: "/settings/api-keys", icon: Settings },
];

// 프로젝트 아이템 컴포넌트
function ProjectItem({
    project,
    isSelected,
    onToggle,
    onEdit,
    onDelete,
}: {
    project: Project;
    isSelected: boolean;
    onToggle: () => void;
    onEdit: () => void;
    onDelete: () => void;
}) {
    const textRef = useRef<HTMLAnchorElement>(null);
    const [isTruncated, setIsTruncated] = useState(false);

    useEffect(() => {
        const element = textRef.current;
        if (element) {
            setIsTruncated(element.scrollWidth > element.clientWidth);
        }
    }, []);

    return (
        <div
            className={cn(
                "group flex items-center gap-3 px-2 py-2 rounded-md transition-colors mb-1",
                "hover:bg-accent",
                isSelected && "bg-accent border-l-2 border-primary"
            )}
        >
            <Checkbox checked={isSelected} onCheckedChange={onToggle} />

            {isTruncated ? (
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Link
                            ref={textRef}
                            to={`/projects/${project.id}`}
                            className="flex-1 text-sm truncate py-1"
                        >
                            {project.name}
                        </Link>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" align="start">
                        {project.name}
                    </TooltipContent>
                </Tooltip>
            ) : (
                <Link
                    ref={textRef}
                    to={`/projects/${project.id}`}
                    className="flex-1 text-sm truncate py-1"
                >
                    {project.name}
                </Link>
            )}

            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                    >
                        <MoreVertical className="h-3 w-3" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={onEdit}>
                        <Edit className="h-3 w-3 mr-2" />
                        Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={onDelete}>
                        <Archive className="h-3 w-3 mr-2" />
                        Move to Archive
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    );
}

export function Sidebar() {
    const location = useLocation();
    const [selectedProjects, setSelectedProjects] = useState<number[]>([]);

    // Dialog states
    const [createOpen, setCreateOpen] = useState(false);
    const [editOpen, setEditOpen] = useState(false);
    const [deleteOpen, setDeleteOpen] = useState(false);

    // Context states for dialogs
    const [editingProject, setEditingProject] = useState<Project | null>(null);
    const [deleteIds, setDeleteIds] = useState<number[]>([]);
    const [deleteNames, setDeleteNames] = useState<string[]>([]);

    // 현재 경로에 따라 활성 섹션 결정
    const activeSection = location.pathname.startsWith("/projects")
        ? "projects"
        : location.pathname.startsWith("/settings")
        ? "settings"
        : "dashboard";

    const isArchivePage = location.pathname === "/projects/archived";

    // Fetch projects only when in projects section
    const { data: projects = [], isLoading, isError } = useProjects(
        undefined,
        activeSection === "projects"
    );

    // Fetch archived projects count
    const { data: archivedProjects = [] } = useArchivedProjects();

    // 프로젝트 선택 토글
    const toggleProject = (id: number) => {
        setSelectedProjects((prev) =>
            prev.includes(id) ? prev.filter((pid) => pid !== id) : [...prev, id]
        );
    };

    // 전체 선택/해제
    const toggleAll = () => {
        if (selectedProjects.length === projects.length) {
            setSelectedProjects([]);
        } else {
            setSelectedProjects(projects.map((p) => p.id));
        }
    };

    // Handlers for dialogs
    const handleCreateProject = () => {
        setCreateOpen(true);
    };

    const handleEditProject = (project: Project) => {
        setEditingProject(project);
        setEditOpen(true);
    };

    const handleDeleteProject = (project: Project) => {
        setDeleteIds([project.id]);
        setDeleteNames([project.name]);
        setDeleteOpen(true);
    };

    const handleBulkDelete = () => {
        const names = projects
            .filter((p) => selectedProjects.includes(p.id))
            .map((p) => p.name);
        setDeleteIds(selectedProjects);
        setDeleteNames(names);
        setDeleteOpen(true);
        setSelectedProjects([]); // Clear selection after opening dialog
    };

    // Dashboard Sidebar
    if (activeSection === "dashboard") {
        return (
            <aside className="h-full w-[250px] bg-card border-r flex flex-col">
                <div className="p-4 border-b">
                    <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
                        Dashboard
                    </h2>
                </div>
                <nav className="flex-1 p-3 space-y-1">
                    {dashboardMenus.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                to={item.href}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                                    "hover:bg-accent hover:text-accent-foreground",
                                    isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground"
                                )}
                            >
                                <Icon className="h-4 w-4" />
                                <span>{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>
                <div className="p-4 border-t text-xs text-muted-foreground">EAZY v0.1.0</div>
            </aside>
        );
    }

    // Settings Sidebar
    if (activeSection === "settings") {
        return (
            <aside className="h-full w-[250px] bg-card border-r flex flex-col">
                <div className="p-4 border-b">
                    <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
                        Settings
                    </h2>
                </div>
                <nav className="flex-1 p-3 space-y-1">
                    {settingsMenus.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                to={item.href}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                                    "hover:bg-accent hover:text-accent-foreground",
                                    isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground"
                                )}
                            >
                                <Icon className="h-4 w-4" />
                                <span>{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>
                <div className="p-4 border-t text-xs text-muted-foreground">EAZY v0.1.0</div>
            </aside>
        );
    }

    // Projects Sidebar
    return (
        <TooltipProvider delayDuration={100}>
            <aside className="h-full w-[250px] bg-card border-r flex flex-col">
                {/* Header: 타이틀 & 버튼 */}
                <div className="p-3 border-b">
                    <div className="flex items-center justify-between">
                        <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
                            Projects
                        </h2>
                        <div className="flex items-center gap-1">
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        className="h-7 w-7 p-0"
                                        disabled={selectedProjects.length === 0}
                                        onClick={handleBulkDelete}
                                    >
                                        <Archive className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                    {selectedProjects.length > 0
                                        ? `Archive ${selectedProjects.length} project${selectedProjects.length > 1 ? 's' : ''}`
                                        : 'Archive'}
                                </TooltipContent>
                            </Tooltip>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        className="h-7 w-7 p-0"
                                        onClick={handleCreateProject}
                                    >
                                        <Plus className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>New Project</TooltipContent>
                            </Tooltip>
                        </div>
                    </div>
                </div>

                {/* Navigation Link (상단) */}
                {!isArchivePage ? (
                    <Link
                        to="/projects/archived"
                        className="flex items-center gap-2 px-3 py-2 text-sm font-medium transition-colors border-b hover:bg-accent hover:text-accent-foreground text-muted-foreground"
                    >
                        <Archive className="h-4 w-4" />
                        <span>
                            View Archived {archivedProjects.length > 0 && `(${archivedProjects.length})`}
                        </span>
                    </Link>
                ) : (
                    <Link
                        to="/projects"
                        className="flex items-center gap-2 px-3 py-2 text-sm font-medium transition-colors border-b hover:bg-accent hover:text-accent-foreground text-muted-foreground"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        <span>Back to Projects</span>
                    </Link>
                )}

                {/* Project List */}
                <div className="flex-1 overflow-auto p-2 custom-scrollbar">
                    {isLoading ? (
                        /* Loading state */
                        <div className="flex flex-col items-center justify-center p-6 text-center">
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mb-2" />
                            <p className="text-sm text-muted-foreground">Loading...</p>
                        </div>
                    ) : isError ? (
                        /* Error state */
                        <div className="flex flex-col items-center justify-center p-6 text-center">
                            <AlertCircle className="h-6 w-6 text-destructive mb-2" />
                            <p className="text-sm text-destructive">Error loading projects</p>
                        </div>
                    ) : projects.length > 0 ? (
                        <>
                            {/* Select All 버튼 */}
                            <div className="flex justify-end px-2 mb-1">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 text-xs text-muted-foreground hover:text-foreground"
                                    onClick={toggleAll}
                                >
                                    {selectedProjects.length === projects.length ? "Deselect All" : "Select All"}
                                </Button>
                            </div>

                            {/* 프로젝트 아이템들 */}
                            {projects.map((project) => (
                                <ProjectItem
                                    key={project.id}
                                    project={project}
                                    isSelected={selectedProjects.includes(project.id)}
                                    onToggle={() => toggleProject(project.id)}
                                    onEdit={() => handleEditProject(project)}
                                    onDelete={() => handleDeleteProject(project)}
                                />
                            ))}
                        </>
                    ) : (
                        /* 빈 상태 */
                        <div className="flex flex-col items-center justify-center p-6 text-center">
                            <p className="text-sm text-muted-foreground mb-4">No projects yet</p>
                            <Button size="sm" variant="outline" onClick={handleCreateProject}>
                                <Plus className="h-3 w-3 mr-1" />
                                Create First Project
                            </Button>
                        </div>
                    )}
                </div>

                {/* Footer: 버전 */}
                <div className="border-t p-4 text-xs text-muted-foreground">
                    EAZY v0.1.0
                </div>
            </aside>

            {/* Dialogs */}
            <CreateProjectForm open={createOpen} onOpenChange={setCreateOpen} />

            {editingProject && (
                <EditProjectForm
                    open={editOpen}
                    onOpenChange={setEditOpen}
                    project={editingProject}
                />
            )}

            <ArchivedDialog
                open={deleteOpen}
                onOpenChange={setDeleteOpen}
                projectIds={deleteIds}
                projectNames={deleteNames}
            />
        </TooltipProvider>
    );
}
