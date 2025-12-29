import type { Meta, StoryObj } from "@storybook/react"
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarProvider,
    SidebarRail,
    SidebarTrigger,
} from "./sidebar"
import { Calendar, Home, Inbox, Search, Settings } from "lucide-react"

const meta = {
    title: "Layout/Sidebar",
    component: Sidebar,
    tags: ["autodocs"],
    decorators: [
        (Story) => (
            <SidebarProvider>
                <Story />
            </SidebarProvider>
        ),
    ],
} satisfies Meta<typeof Sidebar>

export default meta
type Story = StoryObj<typeof meta>

// Menu items.
const items = [
    {
        title: "Home",
        url: "#",
        icon: Home,
    },
    {
        title: "Inbox",
        url: "#",
        icon: Inbox,
    },
    {
        title: "Calendar",
        url: "#",
        icon: Calendar,
    },
    {
        title: "Search",
        url: "#",
        icon: Search,
    },
    {
        title: "Settings",
        url: "#",
        icon: Settings,
    },
]

export const Default: Story = {
    render: () => (
        <div className="flex h-[500px] w-full border border-dashed">
            <Sidebar className="absolute left-0 top-0 h-full border-r">
                <SidebarHeader>
                    <div className="flex items-center gap-2 px-2 py-1">
                        <div className="h-6 w-6 rounded bg-primary" />
                        <span className="font-semibold">Acme Inc</span>
                    </div>
                </SidebarHeader>
                <SidebarContent>
                    <SidebarGroup>
                        <SidebarGroupLabel>Application</SidebarGroupLabel>
                        <SidebarGroupContent>
                            <SidebarMenu>
                                {items.map((item) => (
                                    <SidebarMenuItem key={item.title}>
                                        <SidebarMenuButton asChild>
                                            <a href={item.url}>
                                                <item.icon />
                                                <span>{item.title}</span>
                                            </a>
                                        </SidebarMenuButton>
                                    </SidebarMenuItem>
                                ))}
                            </SidebarMenu>
                        </SidebarGroupContent>
                    </SidebarGroup>
                </SidebarContent>
                <SidebarFooter>
                    <div className="p-2 text-xs text-muted-foreground">
                        © 2024 Acme Inc.
                    </div>
                </SidebarFooter>
                <SidebarRail />
            </Sidebar>
            <div className="flex flex-1 flex-col p-4">
                <div className="flex items-center gap-2">
                    <SidebarTrigger />
                    <h1 className="text-xl font-bold">Dashboard</h1>
                </div>
                <div className="mt-4 flex-1 rounded-lg border border-dashed p-4">
                    Content Area
                </div>
            </div>
        </div>
    ),
}

export const Collapsible: Story = {
    render: () => (
        <div className="flex h-[500px] w-full border border-dashed">
            <Sidebar className="absolute left-0 top-0 h-full border-r" collapsible="icon">
                <SidebarHeader>
                    <SidebarMenu>
                        <SidebarMenuItem>
                            <SidebarMenuButton size="lg" asChild>
                                <a href="#">
                                    <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                                        <Home className="size-4" />
                                    </div>
                                    <div className="grid flex-1 text-left text-sm leading-tight">
                                        <span className="truncate font-semibold">Acme Inc</span>
                                        <span className="truncate text-xs">Startup</span>
                                    </div>
                                </a>
                            </SidebarMenuButton>
                        </SidebarMenuItem>
                    </SidebarMenu>
                </SidebarHeader>
                <SidebarContent>
                    <SidebarGroup>
                        <SidebarGroupLabel>Application</SidebarGroupLabel>
                        <SidebarGroupContent>
                            <SidebarMenu>
                                {items.map((item) => (
                                    <SidebarMenuItem key={item.title}>
                                        <SidebarMenuButton asChild>
                                            <a href={item.url}>
                                                <item.icon />
                                                <span>{item.title}</span>
                                            </a>
                                        </SidebarMenuButton>
                                    </SidebarMenuItem>
                                ))}
                            </SidebarMenu>
                        </SidebarGroupContent>
                    </SidebarGroup>
                </SidebarContent>
                <SidebarFooter>
                    <div className="p-2 text-xs text-muted-foreground group-data-[collapsible=icon]:hidden">
                        Non-collapsed Footer
                    </div>
                </SidebarFooter>
                <SidebarRail />
            </Sidebar>
            <div className="flex flex-1 flex-col p-4">
                <div className="flex items-center gap-2">
                    <SidebarTrigger />
                    <h1 className="text-xl font-bold">Project Overview</h1>
                </div>
                <div className="mt-4 flex-1 rounded-lg border border-dashed p-4">
                    Try clicking the trigger or dragging the rail.
                </div>
            </div>
        </div>
    )
}

import { AppSidebar } from "../app-sidebar"

export const ApplicationShell: Story = {
    render: () => (
        <SidebarProvider>
            <div className="flex min-h-[500px] w-full border border-dashed">
                <AppSidebar />
                <main className="flex flex-1 flex-col p-4">
                    <div className="flex items-center gap-2">
                        <SidebarTrigger />
                        <h1 className="text-xl font-bold">Application Shell</h1>
                    </div>
                    <div className="mt-4 flex-1 rounded-lg border border-dashed p-4">
                        This shows the AppSidebar in action within a SidebarProvider.
                    </div>
                </main>
            </div>
        </SidebarProvider>
    ),
    decorators: [
        (Story) => (
            /* Override the default decorator because this story includes its own SidebarProvider */
            <Story />
        )
    ]
}
