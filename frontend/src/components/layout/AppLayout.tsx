import { Link, Outlet, useLocation } from "react-router-dom";
import { LayoutDashboard, FolderKanban, Key, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

export function AppLayout() {
    const location = useLocation();

    const navItems = [
        { name: "Dashboard", path: "/", icon: LayoutDashboard },
        { name: "Projects", path: "/projects", icon: FolderKanban },
        { name: "Global Keys", path: "/settings/api-keys", icon: Key },
    ];

    return (
        <div className="flex h-screen bg-background">
            {/* Sidebar */}
            <aside className="w-64 bg-sidebar border-r border-sidebar-border hidden md:flex flex-col">
                <div className="p-6">
                    <h1 className="text-2xl font-bold text-primary">EAZY</h1>
                </div>
                <nav className="flex-1 px-4 space-y-2">
                    {navItems.map((item) => (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={cn(
                                "flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                                location.pathname === item.path
                                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            {item.name}
                        </Link>
                    ))}
                </nav>
                <div className="p-4 border-t border-sidebar-border">
                    <div className="flex items-center gap-3 px-4 py-2 text-sm text-sidebar-foreground/70">
                        <Settings className="h-4 w-4" />
                        <span>v0.1.0</span>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto p-8">
                <Outlet />
            </main>
        </div>
    );
}
