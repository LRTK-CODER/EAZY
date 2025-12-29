import type { Meta, StoryObj } from "@storybook/react";
import { Switch } from "./switch";
import { Label } from "./label";

const meta = {
    title: "UI/Switch",
    component: Switch,
    tags: ["autodocs"],
} satisfies Meta<typeof Switch>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <div className="flex items-center space-x-2">
            <Switch id="airplane-mode" {...args} />
            <Label htmlFor="airplane-mode">Airplane Mode</Label>
        </div>
    ),
};
