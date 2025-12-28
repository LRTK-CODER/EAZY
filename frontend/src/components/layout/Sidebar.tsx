import clsx from "clsx";
import { Link, useLocation } from "react-router-dom";

const sidebarNavItems = [
    {
        title: "Dashboard",
        href: "/dashboard",
    },
    {
        title: "Projects",
        href: "/projects",
    },
];

export function Sidebar() {
    const pathname = useLocation().pathname;

    return (
        <aside className="fixed top-14 z-30 -ml-2 hidden h-[calc(100vh-3.5rem)] w-full shrink-0 md:sticky md:block">
            <nav className="grid items-start gap-2">
                {sidebarNavItems.map((item, index) => (
                    <Link
                        key={index}
                        to={item.href}
                    >
                        <span
                            className={clsx(
                                "group flex items-center rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground",
                                pathname === item.href ? "bg-accent" : "transparent"
                            )}
                        >
                            {item.title}
                        </span>
                    </Link>
                ))}
            </nav>
        </aside>
    );
}
