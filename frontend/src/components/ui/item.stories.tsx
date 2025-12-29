import type { Meta, StoryObj } from "@storybook/react"
import { Item, ItemContent, ItemEnd, ItemStart } from "./item"
import { Badge } from "./badge"
import { Switch } from "./switch"
import { Button } from "./button"
import { Bell, ChevronRight, Settings, User } from "lucide-react"

const meta = {
    title: "UI/Item",
    component: Item,
    tags: ["autodocs"],
} satisfies Meta<typeof Item>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
    render: (args) => (
        <Item {...args} className="border-border/40 bg-card">
            <ItemStart>
                <User className="h-5 w-5" />
            </ItemStart>
            <ItemContent>
                <div className="font-medium text-foreground">Profile Information</div>
                <div className="text-xs text-muted-foreground">Manage your public profile</div>
            </ItemContent>
            <ItemEnd>
                <ChevronRight className="h-4 w-4" />
            </ItemEnd>
        </Item>
    ),
}

export const WithAction: Story = {
    render: (args) => (
        <Item {...args} className="border-border">
            <ItemStart>
                <Bell className="h-5 w-5" />
            </ItemStart>
            <ItemContent>
                <div className="font-medium text-foreground">Notifications</div>
                <div className="text-xs text-muted-foreground">Receive daily email updates</div>
            </ItemContent>
            <ItemEnd>
                <Switch />
            </ItemEnd>
        </Item>
    ),
}

export const Clickable: Story = {
    args: {
        clickable: true,
    },
    render: (args) => (
        <Item {...args} className="border border-border">
            <ItemStart>
                <Settings className="h-5 w-5" />
            </ItemStart>
            <ItemContent>
                <div className="font-medium">Settings</div>
            </ItemContent>
            <ItemEnd>
                <Badge variant="secondary">New</Badge>
            </ItemEnd>
        </Item>
    ),
}

export const Grouped: Story = {
    render: (args) => (
        <div className="flex flex-col gap-1 rounded-lg border bg-card p-2">
            <Item clickable>
                <ItemStart><User className="h-4 w-4" /></ItemStart>
                <ItemContent>Account</ItemContent>
                <ItemEnd><ChevronRight className="h-4 w-4" /></ItemEnd>
            </Item>
            <Item clickable>
                <ItemStart><Settings className="h-4 w-4" /></ItemStart>
                <ItemContent>Preferences</ItemContent>
                <ItemEnd><ChevronRight className="h-4 w-4" /></ItemEnd>
            </Item>
            <Item clickable>
                <ItemStart><Bell className="h-4 w-4" /></ItemStart>
                <ItemContent>Notifications</ItemContent>
                <ItemEnd><Badge>3</Badge></ItemEnd>
            </Item>
        </div>
    ),
}
