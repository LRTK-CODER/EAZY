import type { Meta, StoryObj } from "@storybook/react";
import { Alert, AlertDescription, AlertTitle } from "./alert";
import { Terminal } from "lucide-react";

const meta = {
    title: "UI/Alert",
    component: Alert,
    tags: ["autodocs"],
    argTypes: {
        variant: {
            control: "select",
            options: ["default", "destructive"],
        }
    }
} satisfies Meta<typeof Alert>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <Alert {...args}>
            <Terminal className="h-4 w-4" />
            <AlertTitle>Heads up!</AlertTitle>
            <AlertDescription>
                You can add components to your app using the cli.
            </AlertDescription>
        </Alert>
    ),
};

export const Destructive: Story = {
    render: (args) => (
        <Alert variant="destructive" {...args}>
            <Terminal className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
                Your session has expired. Please log in again.
            </AlertDescription>
        </Alert>
    ),
};
