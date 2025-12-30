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

// 더미 프로젝트 데이터
const dummyProjects = [
    { id: 1, name: "E-commerce Security Test" },
    { id: 2, name: "API Penetration Test" },
    { id: 3, name: "Mobile App DAST" },
    { id: 4, name: "Banking Portal Scan" },
    { id: 5, name: "Healthcare System Test" },
];

// 프로젝트 아이템 컴포넌트
function ProjectItem({
    project,
    isSelected,
    onToggle,
}: {
    project: { id: number; name: string };
    isSelected: boolean;
    onToggle: () => void;
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
                    <DropdownMenuItem>
                        <Edit className="h-3 w-3 mr-2" />
                        Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-destructive">
                        <Trash2 className="h-3 w-3 mr-2" />
                        Delete
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    );
}

export function Sidebar() {
    const location = useLocation();
    const [selectedProjects, setSelectedProjects] = useState<number[]>([]);

    // 현재 경로에 따라 활성 섹션 결정
    const activeSection = location.pathname.startsWith("/projects")
        ? "projects"
        : location.pathname.startsWith("/settings")
        ? "settings"
        : "dashboard";

    const isArchivePage = location.pathname === "/projects/archived";

    // 프로젝트 선택 토글
    const toggleProject = (id: number) => {
        setSelectedProjects((prev) =>
            prev.includes(id) ? prev.filter((pid) => pid !== id) : [...prev, id]
        );
    };

    // 전체 선택/해제
    const toggleAll = () => {
        if (selectedProjects.length === dummyProjects.length) {
            setSelectedProjects([]);
        } else {
            setSelectedProjects(dummyProjects.map((p) => p.id));
        }
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
                                        onClick={() => setSelectedProjects([])}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                    {selectedProjects.length > 0
                                        ? `Delete ${selectedProjects.length} project${selectedProjects.length > 1 ? 's' : ''}`
                                        : 'Delete'}
                                </TooltipContent>
                            </Tooltip>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button size="sm" variant="ghost" className="h-7 w-7 p-0">
                                        <Plus className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>New Project</TooltipContent>
                            </Tooltip>
                        </div>
                    </div>
                </div>

                {/* Archived Link (상단) */}
                {!isArchivePage && (
                    <Link
                        to="/projects/archived"
                        className="flex items-center gap-2 px-3 py-2 text-sm font-medium transition-colors border-b hover:bg-accent hover:text-accent-foreground text-muted-foreground"
                    >
                        <Archive className="h-4 w-4" />
                        <span>View Archived</span>
                    </Link>
                )}

                {/* Project List */}
                <div className="flex-1 overflow-auto p-2 custom-scrollbar">
                    {!isArchivePage && (
                        <>
                            {dummyProjects.length > 0 ? (
                                <>
                                    {/* Select All 버튼 */}
                                    <div className="flex justify-end px-2 mb-1">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="h-6 text-xs text-muted-foreground hover:text-foreground"
                                            onClick={toggleAll}
                                        >
                                            {selectedProjects.length === dummyProjects.length ? "Deselect All" : "Select All"}
                                        </Button>
                                    </div>

                                    {/* 프로젝트 아이템들 */}
                                    {dummyProjects.map((project) => (
                                        <ProjectItem
                                            key={project.id}
                                            project={project}
                                            isSelected={selectedProjects.includes(project.id)}
                                            onToggle={() => toggleProject(project.id)}
                                        />
                                    ))}
                                </>
                            ) : (
                                /* 빈 상태 */
                                <div className="flex flex-col items-center justify-center p-6 text-center">
                                    <p className="text-sm text-muted-foreground mb-4">No projects yet</p>
                                    <Button size="sm" variant="outline">
                                        <Plus className="h-3 w-3 mr-1" />
                                        Create First Project
                                    </Button>
                                </div>
                            )}
                        </>
                    )}

                    {/* 아카이브 페이지 */}
                    {isArchivePage && (
                        <div className="flex flex-col items-center justify-center p-6 text-center">
                            <Archive className="h-8 w-8 text-muted-foreground/50 mb-2" />
                            <p className="text-sm text-muted-foreground">No archived projects</p>
                        </div>
                    )}
                </div>

                {/* Footer: 버전 */}
                <div className="border-t p-4 text-xs text-muted-foreground">
                    EAZY v0.1.0
                </div>
            </aside>
        </TooltipProvider>
    );
}
