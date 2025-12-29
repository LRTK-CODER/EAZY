import type { Meta, StoryObj } from "@storybook/react";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "./card";
import { Button } from "./button";
import { Input } from "./input";

const meta = {
    title: "UI/Card",
    component: Card,
    tags: ["autodocs"],
    argTypes: {
        className: { control: "text" },
    },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <Card className="w-[350px]" {...args}>
            <CardHeader>
                <CardTitle>Create project</CardTitle>
                <CardDescription>Deploy your new project in one-click.</CardDescription>
            </CardHeader>
            <CardContent>
                <form>
                    <div className="grid w-full items-center gap-4">
                        <div className="flex flex-col space-y-1.5">
                            <label htmlFor="name" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Name</label>
                            <Input id="name" placeholder="Name of your project" />
                        </div>
                        <div className="flex flex-col space-y-1.5">
                            <label htmlFor="framework" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Framework</label>
                            <Input id="framework" placeholder="Select framework" />
                        </div>
                    </div>
                </form>
            </CardContent>
            <CardFooter className="flex justify-between">
                <Button variant="outline">Cancel</Button>
                <Button>Deploy</Button>
            </CardFooter>
        </Card>
    ),
};

export const Simple: Story = {
    render: (args) => (
        <Card className="w-[350px]" {...args}>
            <CardHeader>
                <CardTitle>Notifications</CardTitle>
                <CardDescription>You have 3 unread messages.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
                <div className=" flex items-center space-x-4 rounded-md border p-4">
                    <div className="flex-1 space-y-1">
                        <p className="text-sm font-medium leading-none">
                            Push Notifications
                        </p>
                        <p className="text-sm text-muted-foreground">
                            Send notifications to device.
                        </p>
                    </div>
                </div>
            </CardContent>
            <CardFooter>
                <Button className="w-full">Mark all as read</Button>
            </CardFooter>
        </Card>
    ),
};
