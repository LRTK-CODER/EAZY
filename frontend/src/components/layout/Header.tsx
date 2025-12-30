import { Shield, Menu, Bell } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface HeaderProps {
    onMenuClick: () => void;
}

const navItems = [
    { label: "Dashboard", href: "/dashboard" },
    { label: "Projects", href: "/projects" },
    { label: "Settings", href: "/settings" },
];

export function Header({ onMenuClick }: HeaderProps) {
    const location = useLocation();

    return (
        <header className="h-16 border-b bg-background flex items-center">
            {/* Left: Logo Area (사이드바 넓이와 동일) */}
            <div className="w-[250px] flex items-center justify-center border-r px-4">
                {/* Hamburger Menu (Mobile Only) - 절대 위치로 왼쪽 끝에 */}
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={onMenuClick}
                    className="md:hidden absolute left-4"
                >
                    <Menu className="h-5 w-5" />
                </Button>

                {/* Logo - 중앙 정렬 */}
                <Link to="/" className="flex items-center gap-2">
                    <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary">
                        <Shield className="h-5 w-5 text-primary-foreground" />
                    </div>
                    <span className="text-xl font-bold">EAZY</span>
                </Link>
            </div>

            {/* Center: Navigation Menu */}
            <div className="flex-1 flex items-center justify-center">
                <nav className="hidden md:flex items-center gap-1">
                    {navItems.map((item) => (
                        <Link
                            key={item.href}
                            to={item.href}
                            className={cn(
                                "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                                "hover:bg-accent hover:text-accent-foreground",
                                location.pathname === item.href || location.pathname.startsWith(item.href + "/")
                                    ? "bg-accent text-accent-foreground"
                                    : "text-muted-foreground"
                            )}
                        >
                            {item.label}
                        </Link>
                    ))}
                </nav>
            </div>

            {/* Right: Notifications + Theme Toggle */}
            <div className="flex items-center gap-2 px-4">
                {/* Notification Button */}
                <Button variant="ghost" size="icon" className="relative h-9 w-9">
                    <Bell className="h-5 w-5" />
                    <Badge
                        variant="destructive"
                        className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
                    >
                        3
                    </Badge>
                    <span className="sr-only">Notifications</span>
                </Button>

                {/* Theme Toggle */}
                <ThemeToggle />
            </div>
        </header>
    );
}
