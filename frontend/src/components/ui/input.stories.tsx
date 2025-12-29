import type { Meta, StoryObj } from "@storybook/react";
import { Input } from "./input";
import { Button } from "./button";

const meta = {
    title: "UI/Input",
    component: Input,
    tags: ["autodocs"],
    argTypes: {
        type: {
            control: "select",
            options: ["text", "password", "email", "number", "file", "date"],
        },
        disabled: { control: "boolean" },
    },
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
        type: "text",
        placeholder: "Email",
    },
};

export const File: Story = {
    args: {
        type: "file",
    },
};

export const Disabled: Story = {
    args: {
        type: "email",
        placeholder: "Email",
        disabled: true,
    },
};

export const WithButton: Story = {
    render: (args) => (
        <div className="flex w-full max-w-sm items-center space-x-2">
            <Input {...args} placeholder="Email" />
            <Button type="submit">Subscribe</Button>
        </div>
    ),
};

export const WithLabel: Story = {
    render: (args) => (
        <div className="grid w-full max-w-sm items-center gap-1.5">
            <label htmlFor="email">Email</label>
            <Input {...args} type="email" id="email" placeholder="Email" />
        </div>
    ),
}
