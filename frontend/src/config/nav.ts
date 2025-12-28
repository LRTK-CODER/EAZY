export interface NavItem {
    title: string;
    href: string;
    disabled?: boolean;
    external?: boolean;
}

export const sidebarNavItems: NavItem[] = [
    {
        title: "Dashboard",
        href: "/dashboard",
    },
    {
        title: "Projects",
        href: "/projects",
    },
];
